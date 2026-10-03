"""DB seeding helper for tests that need games in specific states."""

from sqlalchemy.orm import Session

from app.models import Game, Move
from app.services.rules import MovePosition


def seed_game(
    session: Session,
    moves: list[MovePosition] | None = None,
    **game_fields: object,
) -> int:
    """Insert a game and its moves directly (no validation) and return the game id."""
    game = Game(moves=[], **game_fields)
    session.add(game)
    session.flush()
    for position in moves or []:
        session.add(Move(game_id=game.id, board=position.board, cell=position.cell))
    session.commit()
    return game.id
