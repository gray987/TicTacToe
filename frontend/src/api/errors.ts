import type { components } from "./schema";

export type ErrorBody = components["schemas"]["ErrorResponse"];

export class ApiError extends Error {
  readonly status: number;
  readonly code: ErrorBody["code"] | "unknown";

  constructor(status: number, code: ErrorBody["code"] | "unknown", detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

function isErrorBody(value: unknown): value is ErrorBody {
  return (
    typeof value === "object" &&
    value !== null &&
    "code" in value &&
    "detail" in value &&
    typeof (value as { detail: unknown }).detail === "string"
  );
}

/** Turn an openapi-fetch result into its data, or throw an ApiError (for TanStack Query). */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined) {
    if (isErrorBody(result.error)) {
      throw new ApiError(result.response.status, result.error.code, result.error.detail);
    }
    throw new ApiError(result.response.status, "unknown", "Unexpected error from the server");
  }
  if (result.data === undefined) {
    throw new ApiError(result.response.status, "unknown", "Empty response from the server");
  }
  return result.data;
}

/** A readable message for any thrown value, suitable for showing to the user. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof TypeError) return "Could not reach the server. Check your connection.";
  if (error instanceof Error && error.message) return error.message;
  return "Something went wrong.";
}
