"""Test helpers: build legal move logs. Importable as tests.helpers."""

from app.core.enums import Player
from app.services.rules import MovePosition, player_for_move_count

# A tied 3x3 layout: the first mover owns FIRST_TIE_CELLS, the second owns SECOND_TIE_CELLS.
FIRST_TIE_CELLS = (0, 2, 3, 7, 8)
SECOND_TIE_CELLS = (1, 4, 5, 6)


def board_script(board: int, target: Player | None, first: Player) -> list[MovePosition]:
    """Moves that decide `board` as `target` (None = tie), given who moves first in it.

    All moves stay in one board, so they are legal under the literal forced-board rule.
    """
    if target is None:
        order = [
            FIRST_TIE_CELLS[0], SECOND_TIE_CELLS[0], FIRST_TIE_CELLS[1], SECOND_TIE_CELLS[1],
            FIRST_TIE_CELLS[2], SECOND_TIE_CELLS[2], FIRST_TIE_CELLS[3], SECOND_TIE_CELLS[3],
            FIRST_TIE_CELLS[4],
        ]  # fmt: skip
    elif target == first:
        order = [0, 3, 1, 4, 2]  # first takes the top row in 5 moves
    else:
        order = [3, 0, 4, 1, 8, 2]  # second takes the top row on move 6
    return [MovePosition(board, cell) for cell in order]


def build_game(targets: list[tuple[int, Player | None]]) -> list[MovePosition]:
    moves: list[MovePosition] = []
    for board, target in targets:
        first = player_for_move_count(len(moves))
        moves.extend(board_script(board, target, first))
    return moves

