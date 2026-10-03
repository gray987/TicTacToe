import type { components } from "./schema";

type Schemas = components["schemas"];

export type GameDetail = Schemas["GameDetail"];
export type GameSummary = Schemas["GameSummary"];
export type GameListEnvelope = Schemas["GameListEnvelope"];
export type BoardOut = Schemas["BoardOut"];
export type MoveOut = Schemas["MoveOut"];
export type GameStatus = Schemas["GameStatus"];
export type GameSort = Schemas["GameSort"];
export type Player = Schemas["Player"];
