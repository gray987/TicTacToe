# Changelog

## Unreleased
- Step 6: multi-stage non-root Dockerfiles and `.dockerignore` for both apps, nginx config, `docker-compose.yml` (named SQLite volume, healthchecks, commented-out Postgres), GitHub Actions CI (backend, frontend, API-type drift, e2e, docker), `.gitattributes`, README, and a version-pinning helper.
- Step 5: games list page (create, filter, sort, paginate, resume/view, archive) and game page (9x9 board from server state, forced-board highlight and status line, 409 messages in a live region, archive, new game); TanStack Query hooks; MSW fixtures and handlers for every endpoint; component and flow tests; Playwright smoke test.
- Step 4: frontend scaffold: OpenAPI export script and `gen:api`, openapi-fetch client with `ApiError`/`unwrap`, TanStack Query client, data-router routes with placeholder pages, MSW test infrastructure, ESLint (jsx-a11y) config, and tests for the client and routes.
- Step 3: repository, game service, `/api/v1` endpoints (games, moves, archive), error envelope and exception handlers, app factory; repository, service and API tests.
- Lint fix: Ruff `known-third-party` for alembic; `path_separator = os` in `alembic.ini`.
- Step 2: `Game` and `Move` models, Alembic migration `0001`, enums, domain errors, pure rules service
  (small-board and meta-board detection, forced-board calculation, move validation, replay) with tests.
- Step 1: project scaffold and tooling configuration. Verified on Windows: `uv sync` on Python 3.14.8, Ruff, mypy strict, `vite build`.
