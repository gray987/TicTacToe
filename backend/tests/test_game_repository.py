from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Game
from app.repositories.games import GameRepository
from app.services.rules import MovePosition
from tests.seeding import seed_game


def at(day: int) -> datetime:
    return datetime(2026, 1, day, tzinfo=UTC)


def test_create_persists_an_empty_game(session: Session) -> None:
    game = GameRepository(session).create()
    assert game.id is not None
    assert game.moves == []
    assert game.is_archived is False


def test_get_with_moves_returns_moves_in_play_order(session: Session) -> None:
    game_id = seed_game(session, [MovePosition(4, 4), MovePosition(4, 0), MovePosition(4, 8)])
    game = GameRepository(session).get_with_moves(game_id)
    assert game is not None
    assert [(m.board, m.cell) for m in game.moves] == [(4, 4), (4, 0), (4, 8)]


def test_get_with_moves_returns_none_for_unknown_id(session: Session) -> None:
    assert GameRepository(session).get_with_moves(999) is None


def test_list_loads_moves_eagerly(session: Session) -> None:
    seed_game(session, [MovePosition(0, 0)])
    session.expire_all()
    games = GameRepository(session).list_active_with_moves(newest_first=True)
    assert all("moves" in game.__dict__ for game in games)


def test_list_sorts_newest_first(session: Session) -> None:
    first = seed_game(session, created_at=at(1))
    third = seed_game(session, created_at=at(3))
    second = seed_game(session, created_at=at(2))
    games = GameRepository(session).list_active_with_moves(newest_first=True)
    assert [g.id for g in games] == [third, second, first]


def test_list_sorts_oldest_first(session: Session) -> None:
    first = seed_game(session, created_at=at(1))
    third = seed_game(session, created_at=at(3))
    second = seed_game(session, created_at=at(2))
    games = GameRepository(session).list_active_with_moves(newest_first=False)
    assert [g.id for g in games] == [first, second, third]


def test_equal_created_at_is_ordered_by_id(session: Session) -> None:
    ids = [seed_game(session, created_at=at(1)) for _ in range(3)]
    repo = GameRepository(session)
    assert [g.id for g in repo.list_active_with_moves(newest_first=False)] == ids
    assert [g.id for g in repo.list_active_with_moves(newest_first=True)] == ids[::-1]


def test_list_excludes_archived_games(session: Session) -> None:
    kept = seed_game(session)
    archived = seed_game(session, is_archived=True)
    ids = [g.id for g in GameRepository(session).list_active_with_moves(newest_first=True)]
    assert kept in ids
    assert archived not in ids


def test_add_move_persists_and_returns_the_move(session: Session) -> None:
    repo = GameRepository(session)
    game = repo.create()
    move = repo.add_move(game, 3, 5)
    repo.commit()
    session.expire_all()
    reloaded = repo.get_with_moves(game.id)
    assert reloaded is not None
    assert [(m.id, m.board, m.cell) for m in reloaded.moves] == [(move.id, 3, 5)]


def test_archive_sets_the_flag(session: Session) -> None:
    repo = GameRepository(session)
    game = repo.create()
    repo.archive(game)
    repo.commit()
    session.expire_all()
    reloaded = session.get(Game, game.id)
    assert reloaded is not None
    assert reloaded.is_archived is True
