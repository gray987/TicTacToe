import type { BoardOut, GameDetail, GameListEnvelope, GameSummary, MoveOut, Player } from "../api/types";

/** Scripted server responses. These deliberately contain no game rules. */

export function emptyBoards(): BoardOut[] {
  return Array.from({ length: 9 }, (_, index): BoardOut => ({
    index,
    status: "open",
    cells: new Array<Player | null>(9).fill(null),
  }));
}

export function makeGame(overrides: Partial<GameDetail> = {}): GameDetail {
  return {
    id: 1,
    created_at: "2026-10-01T12:00:00Z",
    is_archived: false,
    boards: emptyBoards(),
    current_player: "x",
    active_board: null,
    status: "in_progress",
    winner: null,
    move_count: 0,
    ...overrides,
  };
}

/** X has played board 2, cell 5; O must now play in board 2. */
export function forcedBoardGame(id = 1): GameDetail {
  const boards = emptyBoards();
  boards[2]!.cells[5] = "x";
  return makeGame({ id, boards, current_player: "o", active_board: 2, move_count: 1 });
}

/** Boards 0, 1 and 2 are claimed by X: X has won the game. */
export function wonGame(id = 1): GameDetail {
  const boards = emptyBoards();
  for (const index of [0, 1, 2]) boards[index]!.status = "x";
  return makeGame({ id, boards, status: "won", winner: "x", move_count: 17 });
}

export function drawnGame(id = 1): GameDetail {
  const boards = emptyBoards().map((board): BoardOut => ({ ...board, status: "tied" }));
  return makeGame({ id, boards, status: "drawn", winner: null, move_count: 81 });
}

export function makeSummary(overrides: Partial<GameSummary> = {}): GameSummary {
  return {
    id: 1,
    created_at: "2026-10-01T12:00:00Z",
    status: "in_progress",
    winner: null,
    current_player: "x",
    move_count: 0,
    ...overrides,
  };
}

export function listEnvelope(
  items: GameSummary[],
  total = items.length,
  page = 1,
  pageSize = 10,
): GameListEnvelope {
  return { items, total, page, page_size: pageSize };
}

export function makeMove(overrides: Partial<MoveOut> = {}): MoveOut {
  return {
    id: 1,
    game_id: 1,
    board: 0,
    cell: 0,
    created_at: "2026-10-01T12:00:00Z",
    player: "x",
    move_number: 1,
    ...overrides,
  };
}
