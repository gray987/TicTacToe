import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router";
import { errorMessage } from "../api/errors";
import { gameQuery, useArchiveGame, useCreateGame, usePlayMove } from "../api/games";
import { ErrorMessage } from "../components/ErrorMessage";
import { GameBoard } from "../components/GameBoard";
import { statusLine } from "../lib/game";

const buttonClass = "rounded border-2 border-slate-900 px-3 py-1 font-medium disabled:opacity-50";

function parseGameId(raw: string | undefined): number | null {
  return raw !== undefined && /^\d+$/.test(raw) ? Number(raw) : null;
}

export function GamePage() {
  const { id } = useParams();
  const gameId = parseGameId(id);
  const navigate = useNavigate();

  const game = useQuery({ ...gameQuery(gameId ?? 0), enabled: gameId !== null });
  const play = usePlayMove(gameId ?? 0);
  const archive = useArchiveGame();
  const create = useCreateGame();

  const data = game.data;
  const actionError = play.error
    ? errorMessage(play.error)
    : archive.error
      ? `Could not archive the game: ${errorMessage(archive.error)}`
      : create.error
        ? `Could not create the game: ${errorMessage(create.error)}`
        : "";

  return (
    <>
      <h1 className="text-2xl font-semibold">Game {id}</h1>
      <p className="mt-2">
        <Link to="/" className="underline">
          Back to games
        </Link>
      </p>

      <div className="mt-4">
        {gameId === null ? (
          <ErrorMessage message="Invalid game id." />
        ) : data ? (
          <>
            <p role="status" className="text-lg font-medium">
              {statusLine(data)}
            </p>
            {data.is_archived && <p className="mt-1">This game is archived.</p>}

            {/* Always mounted so screen readers announce move errors (e.g. 409) when they appear. */}
            <div role="alert" aria-live="assertive" className="my-3 min-h-6 font-medium text-red-800">
              {actionError}
            </div>

            <GameBoard
              game={data}
              busy={play.isPending}
              onPlay={(board, cell) => play.mutate({ board, cell })}
            />

            <div className="mt-6 flex gap-4">
              {!data.is_archived && (
                <button
                  type="button"
                  disabled={archive.isPending}
                  onClick={() =>
                    archive.mutate(data.id, { onSuccess: () => navigate("/") })
                  }
                  className={buttonClass}
                >
                  Archive game
                </button>
              )}
              {data.status !== "in_progress" && (
                <button
                  type="button"
                  disabled={create.isPending}
                  onClick={() =>
                    create.mutate(undefined, {
                      onSuccess: (created) => navigate(`/games/${created.id}`),
                    })
                  }
                  className={buttonClass}
                >
                  New game
                </button>
              )}
            </div>
          </>
        ) : game.isError ? (
          <ErrorMessage
            message={`Could not load the game: ${errorMessage(game.error)}`}
            onRetry={() => void game.refetch()}
          />
        ) : (
          <p role="status">Loading game…</p>
        )}
      </div>
    </>
  );
}
