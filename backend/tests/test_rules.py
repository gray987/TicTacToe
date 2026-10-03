"""Game-rule tests. Pure: no database, no HTTP."""

import pytest

from app.core.enums import BoardStatus, ErrorCode, GameStatus, Player
from app.services.errors import (
    BoardAlreadyDecidedError,
    CellOccupiedError,
    DomainError,
    GameArchivedError,
    GameFinishedError,
    WrongBoardError,
)
from app.services.rules import (
    WIN_LINES,
    GameState,
    MovePosition,
    derive_state,
    meta_winner,
    player_for_move_count,
    small_board_status,
    validate_move,
)
from tests.helpers import FIRST_TIE_CELLS, SECOND_TIE_CELLS, build_game

X, O = Player.X, Player.O  # noqa: E741
OPEN, TIED = BoardStatus.OPEN, BoardStatus.TIED

def play(*pairs: tuple[int, int]) -> GameState:
    return derive_state([MovePosition(b, c) for b, c in pairs])


# ---- small-board detection ----------------------------------------------------------------


@pytest.mark.parametrize("player", [X, O])
@pytest.mark.parametrize("line", WIN_LINES)
def test_every_small_board_line_wins(line: tuple[int, int, int], player: Player) -> None:
    cells: list[Player | None] = [None] * 9
    for index in line:
        cells[index] = player
    expected = BoardStatus.X if player is X else BoardStatus.O
    assert small_board_status(cells) is expected


def test_two_in_a_line_is_still_open() -> None:
    assert small_board_status([X, X, None, None, None, None, None, None, None]) is OPEN


def test_full_board_without_winner_is_tied() -> None:
    cells: list[Player | None] = [None] * 9
    for index in FIRST_TIE_CELLS:
        cells[index] = X
    for index in SECOND_TIE_CELLS:
        cells[index] = O
    assert small_board_status(cells) is TIED


# ---- meta-board ---------------------------------------------------------------------------


@pytest.mark.parametrize("line", WIN_LINES)
def test_every_meta_line_wins_through_play(line: tuple[int, int, int]) -> None:
    moves = build_game([(board, X) for board in line])
    state = derive_state(moves)
    assert state.status is GameStatus.WON
    assert state.winner is X
    assert state.active_board is None
    assert state.move_count == len(moves)


@pytest.mark.parametrize("player", [X, O])
@pytest.mark.parametrize("line", WIN_LINES)
def test_meta_winner_for_both_players(line: tuple[int, int, int], player: Player) -> None:
    statuses = [OPEN] * 9
    for index in line:
        statuses[index] = BoardStatus.X if player is X else BoardStatus.O
    assert meta_winner(statuses) is player


def test_tied_board_counts_for_nobody_in_a_line() -> None:
    assert meta_winner([TIED, TIED, TIED] + [OPEN] * 6) is None
    assert meta_winner([BoardStatus.X, TIED, BoardStatus.X] + [OPEN] * 6) is None


def test_two_won_boards_plus_a_tied_board_does_not_win_the_game() -> None:
    state = derive_state(build_game([(0, X), (1, None), (2, X)]))
    assert state.board_statuses[1] is TIED
    assert state.status is GameStatus.IN_PROGRESS
    assert state.winner is None


def test_full_game_draw_with_mixed_results() -> None:
    results: list[Player | None] = [X, O, X, O, X, O, O, X, None]
    moves = build_game(list(enumerate(results)))
    state = derive_state(moves)
    assert state.status is GameStatus.DRAWN
    assert state.winner is None
    assert state.active_board is None
    assert all(status is not OPEN for status in state.board_statuses)


def test_full_game_draw_all_boards_tied() -> None:
    state = derive_state(build_game([(board, None) for board in range(9)]))
    assert state.move_count == 81
    assert state.status is GameStatus.DRAWN
    assert state.board_statuses == (TIED,) * 9


# ---- turn order and forced board ----------------------------------------------------------


def test_new_game_x_moves_first_with_free_choice() -> None:
    state = derive_state([])
    assert state.current_player is X
    assert state.active_board is None
    assert state.status is GameStatus.IN_PROGRESS
    assert state.move_count == 0


@pytest.mark.parametrize("board", range(9))
def test_first_move_allowed_in_any_board(board: int) -> None:
    validate_move(derive_state([]), MovePosition(board, 4))


def test_players_alternate_every_move() -> None:
    assert [player_for_move_count(n) for n in range(4)] == [X, O, X, O]


def test_opponent_is_forced_into_the_same_board_not_the_cell_board() -> None:
    state = play((2, 5))
    assert state.current_player is O
    assert state.active_board == 2  # NOT 5: the cell position does not choose the next board
    with pytest.raises(WrongBoardError) as exc_info:
        validate_move(state, MovePosition(5, 0))
    assert exc_info.value.code is ErrorCode.WRONG_BOARD
    validate_move(state, MovePosition(2, 0))


def test_forced_board_repeats_every_turn_until_decided() -> None:
    state = play((2, 5), (2, 7), (2, 0))
    assert state.active_board == 2
    assert state.current_player is O


def test_free_choice_after_forced_board_is_won() -> None:
    moves = build_game([(0, X)])
    state = derive_state(moves)
    assert state.board_statuses[0] is BoardStatus.X
    assert state.active_board is None
    for board in range(1, 9):
        validate_move(state, MovePosition(board, 0))


def test_free_choice_after_forced_board_is_tied() -> None:
    state = derive_state(build_game([(0, None)]))
    assert state.board_statuses[0] is TIED
    assert state.active_board is None
    for board in range(1, 9):
        validate_move(state, MovePosition(board, 0))


# ---- refusals with specific codes ---------------------------------------------------------


def test_playing_in_a_decided_board_is_refused() -> None:
    state = derive_state(build_game([(0, X)]))
    with pytest.raises(BoardAlreadyDecidedError) as exc_info:
        validate_move(state, MovePosition(0, 8))
    assert exc_info.value.code is ErrorCode.BOARD_ALREADY_DECIDED


def test_playing_in_a_tied_board_is_refused() -> None:
    state = derive_state(build_game([(0, None)]))
    with pytest.raises(BoardAlreadyDecidedError):
        validate_move(state, MovePosition(0, 0))


def test_occupied_cell_is_refused() -> None:
    state = play((0, 0))
    with pytest.raises(CellOccupiedError) as exc_info:
        validate_move(state, MovePosition(0, 0))
    assert exc_info.value.code is ErrorCode.CELL_OCCUPIED


def test_finished_game_refuses_moves() -> None:
    state = derive_state(build_game([(board, X) for board in (0, 1, 2)]))
    with pytest.raises(GameFinishedError) as exc_info:
        validate_move(state, MovePosition(5, 0))
    assert exc_info.value.code is ErrorCode.GAME_FINISHED


def test_drawn_game_refuses_moves() -> None:
    state = derive_state(build_game([(board, None) for board in range(9)]))
    with pytest.raises(GameFinishedError):
        validate_move(state, MovePosition(0, 0))


def test_archived_game_refuses_moves() -> None:
    with pytest.raises(GameArchivedError) as exc_info:
        validate_move(derive_state([]), MovePosition(0, 0), is_archived=True)
    assert exc_info.value.code is ErrorCode.GAME_ARCHIVED


# ---- precedence: archived > finished > wrong_board > decided > occupied --------------------


def test_archived_beats_finished() -> None:
    state = derive_state(build_game([(board, X) for board in (0, 1, 2)]))
    with pytest.raises(GameArchivedError):
        validate_move(state, MovePosition(5, 0), is_archived=True)


def test_finished_beats_wrong_board_and_decided() -> None:
    state = derive_state(build_game([(board, X) for board in (0, 1, 2)]))
    with pytest.raises(GameFinishedError):
        validate_move(state, MovePosition(0, 0))


def test_wrong_board_beats_board_already_decided() -> None:
    moves = [*build_game([(0, X)]), MovePosition(3, 0)]  # board 0 decided, now forced into 3
    state = derive_state(moves)
    assert state.active_board == 3
    with pytest.raises(WrongBoardError):
        validate_move(state, MovePosition(0, 8))


def test_wrong_board_beats_cell_occupied() -> None:
    state = play((0, 0), (0, 1))  # forced into board 0
    with pytest.raises(WrongBoardError):
        validate_move(state, MovePosition(1, 0))


def test_board_decided_beats_cell_occupied() -> None:
    state = derive_state(build_game([(0, X)]))
    with pytest.raises(BoardAlreadyDecidedError):
        validate_move(state, MovePosition(0, 0))  # cell 0 is also occupied


# ---- replay robustness --------------------------------------------------------------------


def test_corrupt_log_raises_a_domain_error() -> None:
    with pytest.raises(DomainError):
        derive_state([MovePosition(0, 0), MovePosition(0, 0)])


def test_move_position_rejects_out_of_range_values() -> None:
    with pytest.raises(ValueError):
        MovePosition(9, 0)
    with pytest.raises(ValueError):
        MovePosition(0, -1)
