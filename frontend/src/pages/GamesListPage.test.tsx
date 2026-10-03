import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { delay, http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { listEnvelope, makeGame, makeSummary } from "../test/fixtures";
import { renderApp } from "../test/render";
import { server } from "../test/server";

const LIST = "*/api/v1/games";

describe("GamesListPage states", () => {
  it("shows a loading state", async () => {
    server.use(
      http.get(LIST, async () => {
        await delay("infinite");
        return HttpResponse.json(listEnvelope([]));
      }),
    );
    renderApp("/");
    expect(await screen.findByText("Loading games…")).toBeInTheDocument();
  });

  it("shows an empty state when there are no games", async () => {
    renderApp("/");
    expect(await screen.findByText("No games yet. Start a new game.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New game" })).toBeEnabled();
  });

  it("shows an error with a retry that works", async () => {
    let calls = 0;
    server.use(
      http.get(LIST, () => {
        calls += 1;
        return calls === 1
          ? HttpResponse.json({ oops: true }, { status: 500 })
          : HttpResponse.json(listEnvelope([makeSummary({ id: 4 })]));
      }),
    );
    const user = userEvent.setup();
    renderApp("/");

    expect(await screen.findByRole("alert")).toHaveTextContent(/could not load games/i);
    await user.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByText("Game 4")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows rows with status text, move count, winner and the right link labels", async () => {
    server.use(
      http.get(LIST, () =>
        HttpResponse.json(
          listEnvelope([
            makeSummary({ id: 3, status: "won", winner: "x", move_count: 17 }),
            makeSummary({ id: 2, status: "in_progress", move_count: 4 }),
            makeSummary({ id: 1, status: "drawn", move_count: 81 }),
          ]),
        ),
      ),
    );
    renderApp("/");

    const won = within(await screen.findByRole("row", { name: /Game 3/ }));
    expect(won.getByText("Won")).toBeInTheDocument();
    expect(won.getByText("17")).toBeInTheDocument();
    expect(won.getByText("Winner: X")).toBeInTheDocument();
    expect(won.getByRole("link", { name: "View game 3" })).toHaveAttribute("href", "/games/3");
    expect(won.getByRole("button", { name: "Archive game 3" })).toBeInTheDocument();

    const active = within(screen.getByRole("row", { name: /Game 2/ }));
    expect(active.getByText("In progress")).toBeInTheDocument();
    expect(active.getByRole("link", { name: "Resume game 2" })).toBeInTheDocument();
    expect(active.getByText("No winner")).toBeInTheDocument();

    const drawn = within(screen.getByRole("row", { name: /Game 1/ }));
    expect(drawn.getByText("Drawn")).toBeInTheDocument();
    expect(drawn.getByRole("link", { name: "View game 1" })).toBeInTheDocument();
  });
});

describe("GamesListPage flows", () => {
  it("creates a game and navigates to it", async () => {
    server.use(
      http.post(LIST, () => HttpResponse.json(makeGame({ id: 42 }), { status: 201 })),
    );
    const user = userEvent.setup();
    const { router } = renderApp("/");

    await user.click(await screen.findByRole("button", { name: "New game" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/games/42"));
    expect(await screen.findByRole("heading", { name: "Game 42" })).toBeInTheDocument();
  });

  it("shows a readable message when creating fails", async () => {
    server.use(http.post(LIST, () => HttpResponse.json({ oops: true }, { status: 500 })));
    const user = userEvent.setup();
    const { router } = renderApp("/");

    await user.click(await screen.findByRole("button", { name: "New game" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not create the game: Unexpected error from the server",
    );
    expect(router.state.location.pathname).toBe("/");
  });

  it("resumes a game via its link", async () => {
    server.use(
      http.get(LIST, () => HttpResponse.json(listEnvelope([makeSummary({ id: 2 })]))),
    );
    const user = userEvent.setup();
    const { router } = renderApp("/");

    await user.click(await screen.findByRole("link", { name: "Resume game 2" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/games/2"));
  });

  it("archives a game and removes its row", async () => {
    let items = [makeSummary({ id: 2 }), makeSummary({ id: 1 })];
    server.use(
      http.get(LIST, () => HttpResponse.json(listEnvelope(items))),
      http.post("*/api/v1/games/:id/archive", ({ params }) => {
        items = items.filter((item) => item.id !== Number(params.id));
        return HttpResponse.json(makeGame({ id: Number(params.id), is_archived: true }));
      }),
    );
    const user = userEvent.setup();
    renderApp("/");

    await user.click(await screen.findByRole("button", { name: "Archive game 2" }));

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Archive game 2" })).not.toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: "Archive game 1" })).toBeInTheDocument();
  });

  it("shows a readable message when archiving fails", async () => {
    server.use(
      http.get(LIST, () => HttpResponse.json(listEnvelope([makeSummary({ id: 2 })]))),
      http.post("*/api/v1/games/:id/archive", () =>
        HttpResponse.json(
          { code: "already_archived", detail: "Game 2 is already archived" },
          { status: 409 },
        ),
      ),
    );
    const user = userEvent.setup();
    renderApp("/");

    await user.click(await screen.findByRole("button", { name: "Archive game 2" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not archive the game: Game 2 is already archived",
    );
  });

  it("filters by status through a labeled control", async () => {
    const seen: (string | null)[] = [];
    server.use(
      http.get(LIST, ({ request }) => {
        const status = new URL(request.url).searchParams.get("status");
        seen.push(status);
        return HttpResponse.json(
          listEnvelope(
            status === "won"
              ? [makeSummary({ id: 1, status: "won", winner: "o" })]
              : [makeSummary({ id: 1, status: "won", winner: "o" }), makeSummary({ id: 2 })],
          ),
        );
      }),
    );
    const user = userEvent.setup();
    renderApp("/");
    await screen.findByText("Game 2");

    await user.selectOptions(screen.getByLabelText("Status"), "won");

    await waitFor(() => expect(screen.queryByText("Game 2")).not.toBeInTheDocument());
    expect(screen.getByText("Game 1")).toBeInTheDocument();
    expect(seen[0]).toBeNull();
    expect(seen.at(-1)).toBe("won");
  });

  it("explains when a filter matches nothing", async () => {
    server.use(
      http.get(LIST, ({ request }) =>
        HttpResponse.json(
          new URL(request.url).searchParams.get("status") === "drawn"
            ? listEnvelope([])
            : listEnvelope([makeSummary({ id: 1 })]),
        ),
      ),
    );
    const user = userEvent.setup();
    renderApp("/");
    await screen.findByText("Game 1");

    await user.selectOptions(screen.getByLabelText("Status"), "drawn");

    expect(await screen.findByText("No games match this filter.")).toBeInTheDocument();
  });

  it("sorts through a labeled control", async () => {
    const seen: (string | null)[] = [];
    server.use(
      http.get(LIST, ({ request }) => {
        seen.push(new URL(request.url).searchParams.get("sort"));
        return HttpResponse.json(listEnvelope([makeSummary({ id: 1 })]));
      }),
    );
    const user = userEvent.setup();
    renderApp("/");
    await screen.findByText("Game 1");

    await user.selectOptions(screen.getByLabelText("Sort"), "Oldest first");

    await waitFor(() => expect(seen.at(-1)).toBe("created_at"));
    expect(seen[0]).toBe("-created_at");
  });
});

describe("GamesListPage pagination", () => {
  const all = Array.from({ length: 25 }, (_, i) => makeSummary({ id: 25 - i }));
  const pages: string[] = [];

  function servePages() {
    pages.length = 0;
    server.use(
      http.get(LIST, ({ request }) => {
        const page = Number(new URL(request.url).searchParams.get("page") ?? "1");
        pages.push(String(page));
        const start = (page - 1) * 10;
        return HttpResponse.json(listEnvelope(all.slice(start, start + 10), 25, page, 10));
      }),
    );
  }

  it("moves between pages and disables the ends", async () => {
    servePages();
    const user = userEvent.setup();
    renderApp("/");

    expect(await screen.findByText("Game 25")).toBeInTheDocument();
    expect(screen.getByText("Page 1 of 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByText("Game 15")).toBeInTheDocument();
    expect(screen.queryByText("Game 25")).not.toBeInTheDocument();
    expect(screen.getByText("Page 2 of 3")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByText("Game 5")).toBeInTheDocument();
    expect(screen.getByText("Page 3 of 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Previous" }));
    expect(await screen.findByText("Game 15")).toBeInTheDocument();
  });

  it("returns to page 1 when the filter changes", async () => {
    servePages();
    const user = userEvent.setup();
    renderApp("/");
    await screen.findByText("Game 25");
    await user.click(screen.getByRole("button", { name: "Next" }));
    await screen.findByText("Game 15");

    await user.selectOptions(screen.getByLabelText("Status"), "in_progress");

    await waitFor(() => expect(screen.getByText("Page 1 of 3")).toBeInTheDocument());
    await waitFor(() => expect(pages.at(-1)).toBe("1"));
  });
});
