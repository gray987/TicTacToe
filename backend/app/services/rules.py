"""Pure Ultimate Tic-Tac-Toe rules (literal forced-board variant).

No HTTP or SQL knowledge lives here. Everything is derived by replaying the move log.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from app.core.enums import BoardStatus, GameStatus, Player
from app.services.errors import (
    BoardAlreadyDecidedError,
    CellOccupiedError,
    GameArchivedError,
    GameFinishedError,
    WrongBoardError,
)

BOARD_COUNT = 9
CELL_COUNT = 9

WIN_LINES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)

Grid = tuple[tuple[Player | None, ...], ...]

_PLAYER_STATUS: dict[Player, BoardStatus] = {Player.X: BoardStatus.X, Player.O: BoardStatus.O}
_STATUS_PLAYER: dict[BoardStatus, Player] = {v: k for k, v in _PLAYER_STATUS.items()}


@dataclass(frozen=True)
class MovePosition:
    board: int
    cell: int

    def __post_init__(self) -> None:
        if not (0 <= self.board < BOARD_COUNT and 0 <= self.cell < CELL_COUNT):
            raise ValueError(f"board/cell out of range: {self.board}, {self.cell}")


@dataclass(frozen=True)
class GameState:
    cells: Grid
    board_statuses: tuple[BoardStatus, ...]
    current_player: Player
    active_board: int | None
    status: GameStatus
    winner: Player | None
    move_count: int


def player_for_move_count(move_count: int) -> Player:
    """X moves first, then players alternate every move."""
    return Player.X if move_count % 2 == 0 else Player.O


def small_board_status(cells: Sequence[Player | None]) -> BoardStatus:
    for a, b, c in WIN_LINES:
        owner = cells[a]
        if owner is not None and owner == cells[b] == cells[c]:
            return _PLAYER_STATUS[owner]
    if all(cell is not None for cell in cells):
        return BoardStatus.TIED
    return BoardStatus.OPEN


def meta_winner(statuses: Sequence[BoardStatus]) -> Player | None:
    """Three claimed boards in a line win. A tied board counts for nobody."""
    for a, b, c in WIN_LINES:
        first = statuses[a]
        if first in _STATUS_PLAYER and first == statuses[b] == statuses[c]:
            return _STATUS_PLAYER[first]
    return None


def game_status(statuses: Sequence[BoardStatus]) -> tuple[GameStatus, Player | None]:
    winner = meta_winner(statuses)
    if winner is not None:
        return GameStatus.WON, winner
    if all(status is not BoardStatus.OPEN for status in statuses):
        return GameStatus.DRAWN, None
    return GameStatus.IN_PROGRESS, None


def compute_active_board(
    last_board: int | None,
    statuses: Sequence[BoardStatus],
    status: GameStatus,
) -> int | None:
    """Literal rule: stay in the board just played until it is decided.

    None means free choice (first move, or the forced board was decided) or game over.
    The cell position of the previous move is irrelevant.
    """
    if status is not GameStatus.IN_PROGRESS or last_board is None:
        return None
    return last_board if statuses[last_board] is BoardStatus.OPEN else None


def _snapshot(
    cells: Sequence[Sequence[Player | None]],
    move_count: int,
    last_board: int | None,
) -> GameState:
    statuses = tuple(small_board_status(board) for board in cells)
    status, winner = game_status(statuses)
    return GameState(
        cells=tuple(tuple(board) for board in cells),
        board_statuses=statuses,
        current_player=player_for_move_count(move_count),
        active_board=compute_active_board(last_board, statuses, status),
        status=status,
        winner=winner,
        move_count=move_count,
    )


def validate_move(state: GameState, move: MovePosition, *, is_archived: bool = False) -> None:
    """Raise the first violated rule. Precedence is fixed and documented in DECISIONS.md:
    game_archived > game_finished > wrong_board > board_already_decided > cell_occupied.
    """
    if is_archived:
        raise GameArchivedError("Game is archived")
    if state.status is not GameStatus.IN_PROGRESS:
        raise GameFinishedError("Game is finished")
    if state.active_board is not None and move.board != state.active_board:
        raise WrongBoardError(f"Must play in board {state.active_board}")
    if state.board_statuses[move.board] is not BoardStatus.OPEN:
        raise BoardAlreadyDecidedError(f"Board {move.board} is already decided")
    if state.cells[move.board][move.cell] is not None:
        raise CellOccupiedError(f"Cell {move.cell} of board {move.board} is occupied")


def derive_state(moves: Sequence[MovePosition]) -> GameState:
    """Replay the move log, validating every move. A corrupt log raises a DomainError."""
    cells: list[list[Player | None]] = [[None] * CELL_COUNT for _ in range(BOARD_COUNT)]
    state = _snapshot(cells, 0, None)
    for index, move in enumerate(moves):
        validate_move(state, move)
        cells[move.board][move.cell] = state.current_player
        state = _snapshot(cells, index + 1, move.board)
    return state
