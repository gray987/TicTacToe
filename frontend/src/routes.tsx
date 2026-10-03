import type { RouteObject } from "react-router";
import { RootLayout } from "./components/RootLayout";
import { RouteError } from "./components/RouteError";
import { GamePage } from "./pages/GamePage";
import { GamesListPage } from "./pages/GamesListPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <RootLayout />,
    errorElement: <RouteError />,
    children: [
      { index: true, element: <GamesListPage /> },
      { path: "games/:id", element: <GamePage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
