import { expect, test } from "@playwright/test";

test("create a game, play moves, see the forced-board message, return and resume", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "New game" }).click();

  await expect(page).toHaveURL(/\/games\/\d+$/);
  const gameId = page.url().split("/").pop();
  await expect(page.getByText("X to move: any open board")).toBeVisible();

  await page.getByRole("button", { name: "Board 2, cell 5, empty" }).click();
  await expect(page.getByText("O must play in the top-right board")).toBeVisible();

  await page.getByRole("button", { name: "Board 2, cell 0, empty" }).click();
  await expect(page.getByText("X must play in the top-right board")).toBeVisible();

  await page.getByRole("link", { name: "Back to games" }).click();
  await expect(page).toHaveURL("/");

  await page.getByRole("link", { name: `Resume game ${gameId}` }).click();
  await expect(page.getByText("X must play in the top-right board")).toBeVisible();
  await expect(page.getByRole("button", { name: "Board 2, cell 5, X" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Board 2, cell 0, O" })).toBeDisabled();
});
