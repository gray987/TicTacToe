import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Game, Move


def test_game_defaults(session: Session) -> None:
    game = Game()
    session.add(game)
    session.commit()
    assert game.id == 1
    assert game.is_archived is False
    assert game.created_at is not None


def test_only_the_move_log_is_stored() -> None:
    """Derived values (board states, player, status, winner, move count) have no columns."""
    assert set(Game.__table__.columns.keys()) == {"id", "is_archived", "created_at"}
    assert set(Move.__table__.columns.keys()) == {"id", "game_id", "board", "cell", "created_at"}


def test_moves_come_back_in_insertion_order(session: Session) -> None:
    game = Game()
    session.add(game)
    session.flush()
    for board, cell in [(4, 4), (4, 0), (4, 8)]:
        session.add(Move(game_id=game.id, board=board, cell=cell))
    session.commit()
    session.refresh(game)
    assert [(m.board, m.cell) for m in game.moves] == [(4, 4), (4, 0), (4, 8)]


def test_same_cell_cannot_be_stored_twice(session: Session) -> None:
    game = Game()
    session.add(game)
    session.flush()
    session.add_all(
        [Move(game_id=game.id, board=1, cell=2), Move(game_id=game.id, board=1, cell=2)]
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_same_cell_is_allowed_in_different_games(session: Session) -> None:
    first, second = Game(), Game()
    session.add_all([first, second])
    session.flush()
    session.add_all(
        [Move(game_id=first.id, board=1, cell=2), Move(game_id=second.id, board=1, cell=2)]
    )
    session.flush()


@pytest.mark.parametrize(("board", "cell"), [(-1, 0), (9, 0), (0, -1), (0, 9)])
def test_board_and_cell_must_be_0_to_8(session: Session, board: int, cell: int) -> None:
    game = Game()
    session.add(game)
    session.flush()
    session.add(Move(game_id=game.id, board=board, cell=cell))
    with pytest.raises(IntegrityError):
        session.flush()


def test_move_requires_an_existing_game(session: Session) -> None:
    session.add(Move(game_id=999, board=0, cell=0))
    with pytest.raises(IntegrityError):
        session.flush()
