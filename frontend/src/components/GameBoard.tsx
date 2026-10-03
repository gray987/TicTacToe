import type { BoardOut, GameDetail } from "../api/types";

interface Props {
  game: GameDetail;
  /** True while a move request is in flight. */
  busy: boolean;
  onPlay: (board: number, cell: number) => void;
}

function outcome(board: BoardOut): string {
  return board.status === "tied" ? "tied" : `won by ${board.status.toUpperCase()}`;
}

function glyph(board: BoardOut): string {
  return board.status === "tied" ? "C" : board.status.toUpperCase();
}

export function GameBoard({ game, busy, onPlay }: Props) {
  const playing = game.status === "in_progress" && !game.is_archived;
  return (
    <div className="grid w-fit grid-cols-3 gap-3">
      {game.boards.map((board) => {
        const decided = board.status !== "open";
        // Rendering the server's contract: active_board null means any open board.
        const playable =
          playing && !decided && (game.active_board === null || game.active_board === board.index);
        return (
          <div
            key={board.index}
            role="group"
            aria-label={`Board ${board.index}`}
            data-playable={playable}
            className={
              playable
                ? "relative grid grid-cols-3 border-4 border-double border-slate-900 bg-amber-50 p-1"
                : "relative grid grid-cols-3 border-2 border-slate-300 p-1"
            }
          >
            {board.cells.map((cell, cellIndex) => (
              <button
                key={cellIndex}
                type="button"
                disabled={busy || !playable || cell !== null}
                onClick={() => onPlay(board.index, cellIndex)}
                aria-label={`Board ${board.index}, cell ${cellIndex}, ${cell ? cell.toUpperCase() : "empty"}`}
                className="h-12 w-12 border border-slate-400 text-xl font-bold focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-not-allowed disabled:bg-slate-100"
              >
                {cell ? cell.toUpperCase() : ""}
              </button>
            ))}
            {decided && (
              <div
                role="img"
                aria-label={`Board ${board.index} ${outcome(board)}`}
                className="pointer-events-none absolute inset-0 flex items-center justify-center bg-white/80 text-7xl font-bold"
              >
                {glyph(board)}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
