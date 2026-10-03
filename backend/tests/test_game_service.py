import pytest
from sqlalchemy.orm import Session

from app.core.enums import GameSort, GameStatus, Player
from app.repositories.games import GameRepository
from app.services.errors import (
    AlreadyArchivedError,
    BoardAlreadyDecidedError,
    GameArchivedError,
    GameNotFoundError,
)
from app.services.games import GameService
from app.services.rules import MovePosition
from tests.helpers import build_game
from tests.seeding import seed_game

X = Player.X


def make_service(session: Session) -> GameService:
    return GameService(GameRepository(session))


def list_ids(
    service: GameService,
    *,
    status: GameStatus | None = None,
    sort: GameSort = GameSort.NEWEST,
    page: int = 1,
    page_size: int = 25,
) -> list[int]:
    result = service.list_games(status=status, sort=sort, page=page, page_size=page_size)
    return [item.id for item in result.items]


# ---- status filtering (status is derived, never stored) -----------------------------------


@pytest.fixture
def mixed(session: Session) -> dict[str, list[int]]:
    won_moves = build_game([(0, X), (1, X), (2, X)])
    drawn_moves = build_game([(board, None) for board in range(9)])
    return {
        "in_progress": [
            seed_game(session),
            seed_game(session, [MovePosition(4, 4)]),
        ],
        "won": [seed_game(session, won_moves), seed_game(session, won_moves)],
        "drawn": [seed_game(session, drawn_moves)],
    }


@pytest.mark.parametrize("status", list(GameStatus))
def test_status_filter_returns_only_matching_games(
    session: Session, mixed: dict[str, list[int]], status: GameStatus
) -> None:
    result = make_service(session).list_games(
        status=status, sort=GameSort.OLDEST, page=1, page_size=25
    )
    assert [item.id for item in result.items] == mixed[status.value]
    assert result.total == len(mixed[status.value])
    assert all(item.state.status is status for item in result.items)


def test_no_status_filter_returns_everything(
    session: Session, mixed: dict[str, list[int]]
) -> None:
    result = make_service(session).list_games(
        status=None, sort=GameSort.OLDEST, page=1, page_size=25
    )
    assert result.total == 5


def test_total_reflects_the_filtered_count_not_the_page(
    session: Session, mixed: dict[str, list[int]]
) -> None:
    result = make_service(session).list_games(
        status=GameStatus.WON, sort=GameSort.OLDEST, page=1, page_size=1
    )
    assert len(result.items) == 1
    assert result.total == 2


def test_archived_games_are_excluded_from_items_and_total(session: Session) -> None:
    kept = seed_game(session)
    seed_game(session, is_archived=True)
    result = make_service(session).list_games(
        status=None, sort=GameSort.NEWEST, page=1, page_size=25
    )
    assert [item.id for item in result.items] == [kept]
    assert result.total == 1


def test_sort_directions(session: Session) -> None:
    ids = [seed_game(session) for _ in range(3)]
    service = make_service(session)
    assert list_ids(service, sort=GameSort.NEWEST) == ids[::-1]
    assert list_ids(service, sort=GameSort.OLDEST) == ids


# ---- pagination boundaries ----------------------------------------------------------------


@pytest.fixture
def five(session: Session) -> list[int]:
    return [seed_game(session) for _ in range(5)]  # oldest-first ids


def test_first_page(session: Session, five: list[int]) -> None:
    service = make_service(session)
    assert list_ids(service, sort=GameSort.OLDEST, page=1, page_size=2) == five[0:2]


def test_last_partial_page(session: Session, five: list[int]) -> None:
    service = make_service(session)
    assert list_ids(service, sort=GameSort.OLDEST, page=3, page_size=2) == five[4:5]


def test_page_past_the_end_is_empty_with_correct_total(
    session: Session, five: list[int]
) -> None:
    result = make_service(session).list_games(
        status=None, sort=GameSort.OLDEST, page=4, page_size=2
    )
    assert result.items == []
    assert result.total == 5
    assert result.page == 4


def test_page_size_one(session: Session, five: list[int]) -> None:
    service = make_service(session)
    pages = [list_ids(service, sort=GameSort.OLDEST, page=n, page_size=1) for n in range(1, 7)]
    assert pages == [[g] for g in five] + [[]]


def test_page_size_max_is_100(session: Session) -> None:
    ids = [seed_game(session) for _ in range(101)]
    service = make_service(session)
    first = list_ids(service, sort=GameSort.OLDEST, page=1, page_size=100)
    second = list_ids(service, sort=GameSort.OLDEST, page=2, page_size=100)
    assert first == ids[:100]
    assert second == ids[100:]


def test_empty_list(session: Session) -> None:
    result = make_service(session).list_games(
        status=None, sort=GameSort.NEWEST, page=1, page_size=25
    )
    assert result.items == []
    assert result.total == 0


# ---- commands -----------------------------------------------------------------------------


def test_unknown_game_raises_not_found(session: Session) -> None:
    service = make_service(session)
    with pytest.raises(GameNotFoundError):
        service.get_game(999)
    with pytest.raises(GameNotFoundError):
        service.play_move(999, 0, 0)
    with pytest.raises(GameNotFoundError):
        service.archive_game(999)
    with pytest.raises(GameNotFoundError):
        service.list_moves(999, page=1, page_size=10)


def test_play_move_derives_player_and_move_number(session: Session) -> None:
    service = make_service(session)
    game_id = service.create_game().id
    first = service.play_move(game_id, 2, 5)
    second = service.play_move(game_id, 2, 6)
    assert (first.player, first.move_number) == (Player.X, 1)
    assert (second.player, second.move_number) == (Player.O, 2)


def test_refused_move_is_not_persisted(session: Session) -> None:
    service = make_service(session)
    game_id = seed_game(session, build_game([(0, X)]))
    before = service.get_game(game_id).state.move_count
    with pytest.raises(BoardAlreadyDecidedError):
        service.play_move(game_id, 0, 8)
    assert service.get_game(game_id).state.move_count == before


def test_archive_then_move_is_refused_and_archive_again_conflicts(session: Session) -> None:
    service = make_service(session)
    game_id = service.create_game().id
    assert service.archive_game(game_id).is_archived is True
    with pytest.raises(GameArchivedError):
        service.play_move(game_id, 0, 0)
    with pytest.raises(AlreadyArchivedError):
        service.archive_game(game_id)
