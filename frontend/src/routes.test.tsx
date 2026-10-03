import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderApp } from "./test/render";

describe("routes", () => {
  it("renders the games list at /", async () => {
    renderApp("/");
    expect(await screen.findByRole("heading", { name: "Games" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("renders the game page at /games/:id with the id from the URL", async () => {
    renderApp("/games/7");
    expect(await screen.findByRole("heading", { name: "Game 7" })).toBeInTheDocument();
    expect(await screen.findByText("X to move: any open board")).toBeInTheDocument();
  });

  it("renders a not-found page with a way back for unknown paths", async () => {
    renderApp("/nope/nothing");
    expect(await screen.findByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to games" })).toHaveAttribute("href", "/");
  });
});
