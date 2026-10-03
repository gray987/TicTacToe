import {
  keepPreviousData,
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "./client";
import { unwrap } from "./errors";
import type { GameSort, GameStatus } from "./types";

export interface ListParams {
  status: GameStatus | undefined;
  sort: GameSort;
  page: number;
  pageSize: number;
}

export const gameKeys = {
  all: ["games"] as const,
  list: (params: ListParams) => ["games", "list", params] as const,
  detail: (id: number) => ["games", "detail", id] as const,
};

export function gamesQuery(params: ListParams) {
  return queryOptions({
    queryKey: gameKeys.list(params),
    queryFn: async () =>
      unwrap(
        await api.GET("/api/v1/games", {
          params: {
            query: {
              status: params.status,
              sort: params.sort,
              page: params.page,
              page_size: params.pageSize,
            },
          },
        }),
      ),
    placeholderData: keepPreviousData,
  });
}

export function gameQuery(id: number) {
  return queryOptions({
    queryKey: gameKeys.detail(id),
    queryFn: async () =>
      unwrap(await api.GET("/api/v1/games/{game_id}", { params: { path: { game_id: id } } })),
  });
}

export function useGames(params: ListParams) {
  return useQuery(gamesQuery(params));
}

export function useCreateGame() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => unwrap(await api.POST("/api/v1/games")),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: gameKeys.all });
    },
  });
}

export function useArchiveGame() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) =>
      unwrap(
        await api.POST("/api/v1/games/{game_id}/archive", { params: { path: { game_id: id } } }),
      ),
    // Returned promise keeps the mutation pending until the refetch finishes.
    onSuccess: () => queryClient.invalidateQueries({ queryKey: gameKeys.all }),
  });
}

export function usePlayMove(gameId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (move: { board: number; cell: number }) =>
      unwrap(
        await api.POST("/api/v1/games/{game_id}/moves", {
          params: { path: { game_id: gameId } },
          body: move,
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: gameKeys.all }),
  });
}
