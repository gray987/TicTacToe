import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { delay, http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import type { GameDetail } from "../api/types";
import {
  drawnGame,
  emptyBoards,
  forcedBoardGame,
  listEnvelope,
  makeGame,
  makeMove,
  wonGame,
} from "../test/fixtures";
import { moveConflictHandler } from "../test/handlers";
import { renderApp } from "../test/render";
import { server } from "../test/server";

const GAME = "*/api/v1/games/:id";
const CELL_NAME = /^Board \d, cell \d, /;

function serveGame(game: GameDetail) {
  server.use(http.get(GAME, () => HttpResponse.json(game)));
}

function allCells() {
  return screen.getAllByRole("button", { name: CELL_NAME });
}

describe("GamePage states", () => {
  it("shows a loading state", async () => {
    server.use(
      http.get(GAME, async () => {
        await delay("infinite");
        return HttpResponse.json(makeGame());
      }),
    );
    renderApp("/games/5");
    expect(await screen.findByText("Loading game…")).toBeInTheDocument();
  });

  it("shows an error with a retry that works", async () => {
    let calls = 0;
    server.use(
      http.get(GAME, () => {
        calls += 1;
        return calls === 1
          ? HttpResponse.json({ oops: true }, { status: 500 })
          : HttpResponse.json(makeGame({ id: 5 }));
      }),
    );
    const user = userEvent.setup();
    renderApp("/games/5");

    expect(await screen.findByRole("alert")).toHaveTextContent(/could not load the game/i);
    await user.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByText("X to move: any open board")).toBeInTheDocument();
  });

  it("shows the API message when the game does not exist", async () => {
    server.use(
      http.get(GAME, () =>
        HttpResponse.json(
          { code: "game_not_found", detail: "Game 999 not found" },
          { status: 404 },
        ),
      ),
    );
    renderApp("/games/999");
    expect(await screen.findByRole("alert")).toHaveTextContent("Game 999 not found");
    expect(screen.getByRole("link", { name: "Back to games" })).toBeInTheDocument();
  });

  it("rejects a non-numeric id without calling the server", async () => {
    let calls = 0;
    server.use(
      http.get(GAME, () => {
        calls += 1;
        return HttpResponse.json(makeGame());
      }),
    );
    renderApp("/games/abc");
    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid game id.");
    expect(calls).toBe(0);
  });

  it("renders an empty game: any open board is playable", async () => {
    serveGame(makeGame({ id: 5 }));
    renderApp("/games/5");

    expect(await screen.findByText("X to move: any open board")).toBeInTheDocument();
    const cells = await screen.findAllByRole("button", { name: /^Board \d, cell \d, empty$/ });
    expect(cells).toHaveLength(81);
    cells.forEach((cell) => expect(cell).toBeEnabled());
    expect(screen.queryByRole("button", { name: "New game" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Archive game" })).toBeInTheDocument();
  });
});

describe("GamePage rendering of server state", () => {
  it("highlights only the forced board and disables everything else", async () => {
    serveGame(forcedBoardGame(7));
    renderApp("/games/7");

    expect(await screen.findByText("O must play in the top-right board")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Board 2" })).toHaveAttribute("data-playable", "true");
    expect(screen.getByRole("group", { name: "Board 5" })).toHaveAttribute("data-playable", "false");
    expect(screen.getByRole("button", { name: "Board 2, cell 0, empty" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Board 2, cell 5, X" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Board 4, cell 4, empty" })).toBeDisabled();
  });

  it("shows large overlays on decided boards and disables their cells", async () => {
    const boards = emptyBoards();
    boards[0]!.status = "x";
    boards[4]!.status = "tied";
    serveGame(makeGame({ id: 3, boards, move_count: 20 }));
    renderApp("/games/3");

    const won = await screen.findByRole("img", { name: "Board 0 won by X" });
    expect(won).toHaveTextContent("X");
    expect(screen.getByRole("img", { name: "Board 4 tied" })).toHaveTextContent("C");
    expect(screen.getByRole("button", { name: "Board 0, cell 3, empty" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Board 4, cell 0, empty" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Board 1, cell 0, empty" })).toBeEnabled();
    expect(screen.getByRole("group", { name: "Board 0" })).toHaveAttribute("data-playable", "false");
  });

  it("shows a win: status text, everything disabled, New game offered", async () => {
    serveGame(wonGame(9));
    renderApp("/games/9");

    expect(await screen.findByText("X wins")).toBeInTheDocument();
    allCells().forEach((cell) => expect(cell).toBeDisabled());
    expect(screen.getByRole("button", { name: "New game" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Archive game" })).toBeInTheDocument();
  });

  it("shows a draw", async () => {
    serveGame(drawnGame(9));
    renderApp("/games/9");

    expect(await screen.findByText("Draw")).toBeInTheDocument();
    allCells().forEach((cell) => expect(cell).toBeDisabled());
    expect(screen.getByRole("button", { name: "New game" })).toBeInTheDocument();
  });

  it("shows an archived game as read-only", async () => {
    serveGame(makeGame({ id: 4, is_archived: true }));
    renderApp("/games/4");

    expect(await screen.findByText("This game is archived.")).toBeInTheDocument();
    allCells().forEach((cell) => expect(cell).toBeDisabled());
    expect(screen.queryByRole("button", { name: "Archive game" })).not.toBeInTheDocument();
  });
});

describe("GamePage flows", () => {
  it("plays a move, sends only board and cell, and shows the new server state", async () => {
    let current = makeGame({ id: 5 });
    let sent: unknown;
    server.use(
      http.get(GAME, () => HttpResponse.json(current)),
      http.post("*/api/v1/games/:id/moves", async ({ request }) => {
        sent = await request.json();
        current = forcedBoardGame(5);
        return HttpResponse.json(makeMove({ game_id: 5, board: 2, cell: 5 }), { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderApp("/games/5");

    await user.click(await screen.findByRole("button", { name: "Board 2, cell 5, empty" }));

    expect(await screen.findByText("O must play in the top-right board")).toBeInTheDocument();
    expect(sent).toEqual({ board: 2, cell: 5 });
    expect(screen.getByRole("button", { name: "Board 2, cell 5, X" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Board 5, cell 0, empty" })).toBeDisabled();
  });

  it("surfaces a 409 in the live region and leaves the board playable", async () => {
    serveGame(forcedBoardGame(5));
    server.use(moveConflictHandler("wrong_board", "Must play in board 2"));
    const user = userEvent.setup();
    renderApp("/games/5");

    await user.click(await screen.findByRole("button", { name: "Board 2, cell 0, empty" }));

    const live = await screen.findByRole("alert");
    await waitFor(() => expect(live).toHaveTextContent("Must play in board 2"));
    expect(live).toHaveAttribute("aria-live", "assertive");
    expect(screen.getByRole("button", { name: "Board 2, cell 0, empty" })).toBeEnabled();
    expect(screen.getByText("O must play in the top-right board")).toBeInTheDocument();
  });

  it("clears the message after the next successful move", async () => {
    let conflict = true;
    let current = forcedBoardGame(5);
    server.use(
      http.get(GAME, () => HttpResponse.json(current)),
      http.post("*/api/v1/games/:id/moves", () => {
        if (conflict) {
          return HttpResponse.json(
            { code: "cell_occupied", detail: "Cell 0 of board 2 is occupied" },
            { status: 409 },
          );
        }
        current = makeGame({ id: 5, boards: forcedBoardGame(5).boards, move_count: 2 });
        return HttpResponse.json(makeMove(), { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderApp("/games/5");

    await user.click(await screen.findByRole("button", { name: "Board 2, cell 0, empty" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("occupied"));

    conflict = false;
    await user.click(screen.getByRole("button", { name: "Board 2, cell 1, empty" }));
    await waitFor(() => expect(screen.getByRole("alert")).toBeEmptyDOMElement());
  });

  it("archives the game and returns to the list", async () => {
    serveGame(makeGame({ id: 5 }));
    server.use(http.get("*/api/v1/games", () => HttpResponse.json(listEnvelope([]))));
    const user = userEvent.setup();
    const { router } = renderApp("/games/5");

    await user.click(await screen.findByRole("button", { name: "Archive game" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
    expect(await screen.findByRole("heading", { name: "Games" })).toBeInTheDocument();
  });

  it("shows a readable message when archiving fails", async () => {
    serveGame(makeGame({ id: 5 }));
    server.use(
      http.post("*/api/v1/games/:id/archive", () =>
        HttpResponse.json(
          { code: "already_archived", detail: "Game 5 is already archived" },
          { status: 409 },
        ),
      ),
    );
    const user = userEvent.setup();
    const { router } = renderApp("/games/5");

    await user.click(await screen.findByRole("button", { name: "Archive game" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not archive the game: Game 5 is already archived",
    );
    expect(router.state.location.pathname).toBe("/games/5");
  });

  it("starts a new game from a finished one", async () => {
    serveGame(wonGame(5));
    server.use(http.post("*/api/v1/games", () => HttpResponse.json(makeGame({ id: 6 }), { status: 201 })));
    const user = userEvent.setup();
    const { router } = renderApp("/games/5");

    await user.click(await screen.findByRole("button", { name: "New game" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/games/6"));
  });

  it("goes back to the list with the Back to games link", async () => {
    serveGame(makeGame({ id: 5 }));
    const user = userEvent.setup();
    const { router } = renderApp("/games/5");

    await user.click(await screen.findByRole("link", { name: "Back to games" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });

  it("disables every cell inside a decided board", async () => {
    serveGame(wonGame(5));
    renderApp("/games/5");
    const group = within(await screen.findByRole("group", { name: "Board 0" }));
    group.getAllByRole("button").forEach((cell) => expect(cell).toBeDisabled());
  });
});
