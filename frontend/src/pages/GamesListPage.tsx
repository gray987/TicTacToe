import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { errorMessage } from "../api/errors";
import { useArchiveGame, useCreateGame, useGames } from "../api/games";
import type { GameSort, GameStatus } from "../api/types";
import { ErrorMessage } from "../components/ErrorMessage";
import { formatCreated, STATUS_LABEL } from "../lib/game";

const PAGE_SIZE = 10;
const buttonClass = "rounded border-2 border-slate-900 px-3 py-1 font-medium disabled:opacity-50";

export function GamesListPage() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<GameStatus | "all">("all");
  const [sort, setSort] = useState<GameSort>("-created_at");
  const [page, setPage] = useState(1);

  const games = useGames({
    status: statusFilter === "all" ? undefined : statusFilter,
    sort,
    page,
    pageSize: PAGE_SIZE,
  });
  const create = useCreateGame();
  const archive = useArchiveGame();

  function handleCreate() {
    create.mutate(undefined, { onSuccess: (game) => navigate(`/games/${game.id}`) });
  }

  function handleArchive(id: number, rowsOnPage: number) {
    archive.mutate(id, {
      onSuccess: () => {
        if (rowsOnPage === 1 && page > 1) setPage(page - 1);
      },
    });
  }

  const data = games.data;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <>
      <h1 className="text-2xl font-semibold">Games</h1>

      <div className="mt-4 flex flex-wrap items-end gap-6">
        <button type="button" onClick={handleCreate} disabled={create.isPending} className={buttonClass}>
          New game
        </button>
        <div className="flex flex-col">
          <label htmlFor="status-filter" className="text-sm font-medium">
            Status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value as GameStatus | "all");
              setPage(1);
            }}
            className="rounded border-2 border-slate-900 px-2 py-1"
          >
            <option value="all">All</option>
            <option value="in_progress">In progress</option>
            <option value="won">Won</option>
            <option value="drawn">Drawn</option>
          </select>
        </div>
        <div className="flex flex-col">
          <label htmlFor="sort-order" className="text-sm font-medium">
            Sort
          </label>
          <select
            id="sort-order"
            value={sort}
            onChange={(event) => {
              setSort(event.target.value as GameSort);
              setPage(1);
            }}
            className="rounded border-2 border-slate-900 px-2 py-1"
          >
            <option value="-created_at">Newest first</option>
            <option value="created_at">Oldest first</option>
          </select>
        </div>
      </div>

      {create.error && (
        <div className="mt-4">
          <ErrorMessage message={`Could not create the game: ${errorMessage(create.error)}`} />
        </div>
      )}
      {archive.error && (
        <div className="mt-4">
          <ErrorMessage message={`Could not archive the game: ${errorMessage(archive.error)}`} />
        </div>
      )}

      <div className="mt-6">
        {data ? (
          data.total === 0 ? (
            <p>{statusFilter === "all" ? "No games yet. Start a new game." : "No games match this filter."}</p>
          ) : (
            <>
              <table className="w-full border-collapse text-left">
                <caption className="sr-only">Saved games</caption>
                <thead>
                  <tr className="border-b-2 border-slate-900">
                    <th scope="col" className="py-2">Game</th>
                    <th scope="col">Created</th>
                    <th scope="col">Status</th>
                    <th scope="col">Moves</th>
                    <th scope="col">Winner</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((game) => (
                    <tr key={game.id} className="border-b border-slate-300">
                      <th scope="row" className="py-2 font-medium">Game {game.id}</th>
                      <td>
                        <time dateTime={game.created_at}>{formatCreated(game.created_at)}</time>
                      </td>
                      <td>{STATUS_LABEL[game.status]}</td>
                      <td>{game.move_count}</td>
                      <td>
                        {game.winner ? (
                          `Winner: ${game.winner.toUpperCase()}`
                        ) : (
                          <>
                            <span aria-hidden="true">—</span>
                            <span className="sr-only">No winner</span>
                          </>
                        )}
                      </td>
                      <td className="flex gap-4 py-2">
                        <Link to={`/games/${game.id}`} className="underline">
                          {game.status === "in_progress"
                            ? `Resume game ${game.id}`
                            : `View game ${game.id}`}
                        </Link>
                        <button
                          type="button"
                          aria-label={`Archive game ${game.id}`}
                          onClick={() => handleArchive(game.id, data.items.length)}
                          disabled={archive.isPending}
                          className="underline disabled:opacity-50"
                        >
                          Archive
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <nav aria-label="Pagination" className="mt-4 flex items-center gap-4">
                <button
                  type="button"
                  onClick={() => setPage(page - 1)}
                  disabled={page <= 1}
                  className={buttonClass}
                >
                  Previous
                </button>
                <span>
                  Page {page} of {totalPages}
                </span>
                <button
                  type="button"
                  onClick={() => setPage(page + 1)}
                  disabled={page >= totalPages}
                  className={buttonClass}
                >
                  Next
                </button>
              </nav>
            </>
          )
        ) : games.isError ? (
          <ErrorMessage
            message={`Could not load games: ${errorMessage(games.error)}`}
            onRetry={() => void games.refetch()}
          />
        ) : (
          <p role="status">Loading games…</p>
        )}
      </div>
    </>
  );
}
