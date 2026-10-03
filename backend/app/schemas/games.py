from datetime import datetime
from typing import Self

from pydantic import Field

from app.core.enums import BoardStatus, GameStatus, Player
from app.schemas.common import ApiModel
from app.services.games import GameSnapshot, MoveView, Page


class BoardOut(ApiModel):
    index: int
    status: BoardStatus
    cells: list[Player | None]


class GameSummary(ApiModel):
    id: int
    created_at: datetime
    status: GameStatus
    winner: Player | None
    current_player: Player
    move_count: int

    @classmethod
    def from_snapshot(cls, snapshot: GameSnapshot) -> Self:
        state = snapshot.state
        return cls(
            id=snapshot.id,
            created_at=snapshot.created_at,
            status=state.status,
            winner=state.winner,
            current_player=state.current_player,
            move_count=state.move_count,
        )


class GameDetail(ApiModel):
    id: int
    created_at: datetime
    is_archived: bool
    boards: list[BoardOut]
    current_player: Player
    active_board: int | None
    status: GameStatus
    winner: Player | None
    move_count: int

    @classmethod
    def from_snapshot(cls, snapshot: GameSnapshot) -> Self:
        state = snapshot.state
        return cls(
            id=snapshot.id,
            created_at=snapshot.created_at,
            is_archived=snapshot.is_archived,
            boards=[
                BoardOut(index=index, status=state.board_statuses[index], cells=list(cells))
                for index, cells in enumerate(state.cells)
            ],
            current_player=state.current_player,
            active_board=state.active_board,
            status=state.status,
            winner=state.winner,
            move_count=state.move_count,
        )


class MoveCreate(ApiModel):
    """The player is never sent by the client; extra fields are rejected."""

    board: int = Field(ge=0, le=8)
    cell: int = Field(ge=0, le=8)


class MoveOut(ApiModel):
    id: int
    game_id: int
    board: int
    cell: int
    created_at: datetime
    player: Player
    move_number: int

    @classmethod
    def from_view(cls, view: MoveView) -> Self:
        return cls(
            id=view.id,
            game_id=view.game_id,
            board=view.board,
            cell=view.cell,
            created_at=view.created_at,
            player=view.player,
            move_number=view.move_number,
        )


class GameListEnvelope(ApiModel):
    items: list[GameSummary]
    total: int
    page: int
    page_size: int

    @classmethod
    def from_page(cls, page: Page[GameSnapshot]) -> Self:
        return cls(
            items=[GameSummary.from_snapshot(item) for item in page.items],
            total=page.total,
            page=page.page,
            page_size=page.page_size,
        )


class MoveListEnvelope(ApiModel):
    items: list[MoveOut]
    total: int
    page: int
    page_size: int

    @classmethod
    def from_page(cls, page: Page[MoveView]) -> Self:
        return cls(
            items=[MoveOut.from_view(item) for item in page.items],
            total=page.total,
            page=page.page,
            page_size=page.page_size,
        )
