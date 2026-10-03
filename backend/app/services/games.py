"""Orchestrates repositories and the pure rules. No HTTP knowledge."""

from dataclasses import dataclass
from datetime import datetime

from app.core.enums import GameSort, GameStatus, Player
from app.models import Game
from app.repositories.games import GameRepository
from app.services.errors import AlreadyArchivedError, GameNotFoundError
from app.services.rules import (
    GameState,
    MovePosition,
    derive_state,
    player_for_move_count,
    validate_move,
)


@dataclass(frozen=True)
class GameSnapshot:
    id: int
    created_at: datetime
    is_archived: bool
    state: GameState


@dataclass(frozen=True)
class MoveView:
    id: int
    game_id: int
    board: int
    cell: int
    created_at: datetime
    player: Player
    move_number: int


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    total: int
    page: int
    page_size: int


def _snapshot(game: Game) -> GameSnapshot:
    state = derive_state([MovePosition(move.board, move.cell) for move in game.moves])
    return GameSnapshot(
        id=game.id,
        created_at=game.created_at,
        is_archived=game.is_archived,
        state=state,
    )


def _paginate[T](items: list[T], page: int, page_size: int) -> Page[T]:
    start = (page - 1) * page_size
    window = items[start : start + page_size]
    return Page(items=window, total=len(items), page=page, page_size=page_size)


class GameService:
    def __init__(self, repository: GameRepository) -> None:
        self._repository = repository

    def _require(self, game_id: int) -> Game:
        game = self._repository.get_with_moves(game_id)
        if game is None:
            raise GameNotFoundError(f"Game {game_id} not found")
        return game

    def create_game(self) -> GameSnapshot:
        game = self._repository.create()
        self._repository.commit()
        return _snapshot(game)

    def get_game(self, game_id: int) -> GameSnapshot:
        return _snapshot(self._require(game_id))

    def list_games(
        self,
        *,
        status: GameStatus | None,
        sort: GameSort,
        page: int,
        page_size: int,
    ) -> Page[GameSnapshot]:
        """Status is derived, so derive for every candidate, then filter, then paginate."""
        games = self._repository.list_active_with_moves(newest_first=sort is GameSort.NEWEST)
        snapshots = [_snapshot(game) for game in games]
        if status is not None:
            snapshots = [item for item in snapshots if item.state.status is status]
        return _paginate(snapshots, page, page_size)

    def play_move(self, game_id: int, board: int, cell: int) -> MoveView:
        game = self._require(game_id)
        state = derive_state([MovePosition(move.board, move.cell) for move in game.moves])
        validate_move(state, MovePosition(board, cell), is_archived=game.is_archived)
        row = self._repository.add_move(game, board, cell)
        self._repository.commit()
        return MoveView(
            id=row.id,
            game_id=game.id,
            board=row.board,
            cell=row.cell,
            created_at=row.created_at,
            player=state.current_player,
            move_number=state.move_count + 1,
        )

    def list_moves(self, game_id: int, *, page: int, page_size: int) -> Page[MoveView]:
        game = self._require(game_id)
        views = [
            MoveView(
                id=move.id,
                game_id=game.id,
                board=move.board,
                cell=move.cell,
                created_at=move.created_at,
                player=player_for_move_count(index),
                move_number=index + 1,
            )
            for index, move in enumerate(game.moves)
        ]
        return _paginate(views, page, page_size)

    def archive_game(self, game_id: int) -> GameSnapshot:
        game = self._require(game_id)
        if game.is_archived:
            raise AlreadyArchivedError(f"Game {game_id} is already archived")
        self._repository.archive(game)
        self._repository.commit()
        return _snapshot(game)
