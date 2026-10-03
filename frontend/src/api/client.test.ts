import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "../test/server";
import { api } from "./client";
import { ApiError, errorMessage, unwrap } from "./errors";

describe("api client", () => {
  it("returns typed data for a 2xx response", async () => {
    server.use(
      http.get("*/api/v1/games", () =>
        HttpResponse.json({ items: [], total: 0, page: 1, page_size: 25 }),
      ),
    );
    const data = unwrap(await api.GET("/api/v1/games"));
    expect(data.total).toBe(0);
    expect(data.items).toEqual([]);
  });

  it("sends query parameters", async () => {
    let seen: URLSearchParams | undefined;
    server.use(
      http.get("*/api/v1/games", ({ request }) => {
        seen = new URL(request.url).searchParams;
        return HttpResponse.json({ items: [], total: 0, page: 2, page_size: 10 });
      }),
    );
    await api.GET("/api/v1/games", {
      params: { query: { status: "won", sort: "created_at", page: 2, page_size: 10 } },
    });
    expect(seen?.get("status")).toBe("won");
    expect(seen?.get("sort")).toBe("created_at");
    expect(seen?.get("page")).toBe("2");
    expect(seen?.get("page_size")).toBe("10");
  });

  it("throws an ApiError carrying the code and detail for a 409", async () => {
    server.use(
      http.post("*/api/v1/games/:id/moves", () =>
        HttpResponse.json(
          { code: "wrong_board", detail: "Must play in board 2" },
          { status: 409 },
        ),
      ),
    );
    const call = async () =>
      unwrap(
        await api.POST("/api/v1/games/{game_id}/moves", {
          params: { path: { game_id: 1 } },
          body: { board: 0, cell: 0 },
        }),
      );
    await expect(call()).rejects.toMatchObject({
      name: "ApiError",
      status: 409,
      code: "wrong_board",
      message: "Must play in board 2",
    });
  });

  it("throws an unknown ApiError when the error body is not the envelope", async () => {
    server.use(
      http.get("*/api/v1/games", () => HttpResponse.json({ oops: true }, { status: 500 })),
    );
    await expect(async () => unwrap(await api.GET("/api/v1/games"))).rejects.toMatchObject({
      status: 500,
      code: "unknown",
    });
  });
});

describe("errorMessage", () => {
  it("uses the API detail for an ApiError", () => {
    expect(errorMessage(new ApiError(409, "cell_occupied", "Cell is occupied"))).toBe(
      "Cell is occupied",
    );
  });

  it("explains a network failure", () => {
    expect(errorMessage(new TypeError("Failed to fetch"))).toMatch(/could not reach the server/i);
  });

  it("falls back for unknown values", () => {
    expect(errorMessage("boom")).toBe("Something went wrong.");
  });
});
