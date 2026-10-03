from datetime import datetime

from sqlalchemy import DateTime, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow
from app.models.move import Move


class Game(Base):
    """A game row stores no gameplay state; everything is derived from its moves."""

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    is_archived: Mapped[bool] = mapped_column(default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    moves: Mapped[list[Move]] = relationship(
        back_populates="game",
        order_by="Move.id",
        cascade="all, delete-orphan",
    )
