import { http, HttpResponse, type RequestHandler } from "msw";
import { listEnvelope, makeGame, makeMove } from "./fixtures";

/** A 409 handler for POST moves; tests opt in with server.use(moveConflictHandler()). */
export function moveConflictHandler(
  code = "wrong_board",
  detail = "Must play in board 2",
): RequestHandler {
  return http.post("*/api/v1/games/:id/moves", () =>
    HttpResponse.json({ code, detail }, { status: 409 }),
  );
}

/** Default happy-path handlers: one per endpoint. Tests override with server.use(...). */
export const handlers: RequestHandler[] = [
  http.post("*/api/v1/games", () =>
    HttpResponse.json(makeGame({ id: 1 }), {
      status: 201,
      headers: { Location: "/api/v1/games/1" },
    }),
  ),
  http.get("*/api/v1/games", () => HttpResponse.json(listEnvelope([]))),
  http.get("*/api/v1/games/:id", ({ params }) =>
    HttpResponse.json(makeGame({ id: Number(params.id) })),
  ),
  http.post("*/api/v1/games/:id/moves", ({ params }) =>
    HttpResponse.json(makeMove({ game_id: Number(params.id) }), {
      status: 201,
      headers: { Location: `/api/v1/games/${String(params.id)}/moves` },
    }),
  ),
  http.get("*/api/v1/games/:id/moves", () =>
    HttpResponse.json({ items: [], total: 0, page: 1, page_size: 100 }),
  ),
  http.post("*/api/v1/games/:id/archive", ({ params }) =>
    HttpResponse.json(makeGame({ id: Number(params.id), is_archived: true })),
  ),
];
