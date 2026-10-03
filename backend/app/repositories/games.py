from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Game, Move


class GameRepository:
    """Data access only. Flushes but never commits; the service decides when to commit."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self) -> Game:
        game = Game(moves=[])
        self._session.add(game)
        self._session.flush()
        return game

    def get_with_moves(self, game_id: int) -> Game | None:
        statement = select(Game).where(Game.id == game_id).options(selectinload(Game.moves))
        return self._session.scalars(statement).one_or_none()

    def list_active_with_moves(self, *, newest_first: bool) -> Sequence[Game]:
        """Non-archived games with their moves loaded, ordered by created_at then id."""
        order = (
            (Game.created_at.desc(), Game.id.desc())
            if newest_first
            else (Game.created_at.asc(), Game.id.asc())
        )
        statement = (
            select(Game)
            .where(Game.is_archived.is_(False))
            .options(selectinload(Game.moves))
            .order_by(*order)
        )
        return self._session.scalars(statement).all()

    def add_move(self, game: Game, board: int, cell: int) -> Move:
        move = Move(game_id=game.id, board=board, cell=cell)
        self._session.add(move)
        self._session.flush()
        return move

    def archive(self, game: Game) -> None:
        game.is_archived = True
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()
