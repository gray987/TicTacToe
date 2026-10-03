import { describe, expect, it } from "vitest";
import { forcedBoardGame, drawnGame, makeGame, wonGame } from "../test/fixtures";
import { boardName, statusLine } from "./game";

describe("statusLine", () => {
  it("announces free choice", () => {
    expect(statusLine(makeGame())).toBe("X to move: any open board");
  });

  it("announces the forced board by position", () => {
    expect(statusLine(forcedBoardGame())).toBe("O must play in the top-right board");
  });

  it("announces a win and a draw", () => {
    expect(statusLine(wonGame())).toBe("X wins");
    expect(statusLine(drawnGame())).toBe("Draw");
  });
});

describe("boardName", () => {
  it("names all nine positions row by row", () => {
    expect(Array.from({ length: 9 }, (_, i) => boardName(i))).toEqual([
      "top-left", "top-center", "top-right",
      "middle-left", "center", "middle-right",
      "bottom-left", "bottom-center", "bottom-right",
    ]);
  });
});
