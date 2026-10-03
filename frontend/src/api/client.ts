import createClient from "openapi-fetch";
import type { paths } from "./schema";

/** Empty means same origin. The OpenAPI paths already include the /api/v1 prefix. */
export const baseUrl: string = import.meta.env.VITE_API_BASE_URL ?? "";

export const api = createClient<paths>({
  baseUrl,
  // Resolve fetch at call time so test-time interception (MSW) and polyfills are honoured.
  fetch: (request) => globalThis.fetch(request),
});
