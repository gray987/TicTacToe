import type { GameDetail, GameStatus } from "../api/types";

/** Presentation helpers only. All rule decisions (active board, statuses) come from the server. */

const BOARD_NAMES = [
  "top-left",
  "top-center",
  "top-right",
  "middle-left",
  "center",
  "middle-right",
  "bottom-left",
  "bottom-center",
  "bottom-right",
];

export const STATUS_LABEL: Record<GameStatus, string> = {
  in_progress: "In progress",
  won: "Won",
  drawn: "Drawn",
};

export function boardName(index: number): string {
  return BOARD_NAMES[index] ?? `board ${index}`;
}

export function statusLine(game: GameDetail): string {
  if (game.status === "won") {
    return game.winner ? `${game.winner.toUpperCase()} wins` : "Game over";
  }
  if (game.status === "drawn") return "Draw";
  const player = game.current_player.toUpperCase();
  if (game.active_board === null) return `${player} to move: any open board`;
  return `${player} must play in the ${boardName(game.active_board)} board`;
}

export function formatCreated(iso: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(iso),
  );
}
