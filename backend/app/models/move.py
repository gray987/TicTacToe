from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.game import Game


class Move(Base):
    """The only stored gameplay data. The player is never stored; it follows from move order."""

    __tablename__ = "moves"
    __table_args__ = (
        UniqueConstraint("game_id", "board", "cell"),
        CheckConstraint("board BETWEEN 0 AND 8", name="board_range"),
        CheckConstraint("cell BETWEEN 0 AND 8", name="cell_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    board: Mapped[int]
    cell: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    game: Mapped[Game] = relationship(back_populates="moves")
