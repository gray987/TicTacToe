# Ultimate Tic-Tac-Toe

Two humans, one device. A 3x3 grid of small tic-tac-toe boards where the next player must
play in the **same board the previous player just played in** until that board is decided.
Games are saved and can be resumed from a list.

- `backend/` FastAPI, SQLAlchemy 2, Alembic, SQLite. The backend is the only place the rules live.
- `frontend/` React, React Router, TanStack Query, Tailwind v4. It renders the server's derived state.

This README covers running and testing locally only. There is no deployment target.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (it installs Python 3.14 for you)
- Node.js 24 (LTS) and npm
- Docker Desktop (Windows: with the WSL 2 backend), only if you want the compose setup

Windows PowerShell: if `npm` fails with "running scripts is disabled", run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or call `npm.cmd`.

## Run locally (two terminals)

Backend, from `backend/`:

```bash
cp .env.example .env            # Windows: copy .env.example .env (optional, defaults work)
uv sync
uv run alembic upgrade head     # creates data/uttt.db; the app never creates tables itself
uv run uvicorn app.main:app --reload
```

The API is at http://localhost:8000 (interactive docs at `/docs`, health at `/health`).

Frontend, from `frontend/`:

```bash
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` to the backend.

## Run with Docker

From the repository root:

```bash
docker compose up --build
```

Open http://localhost:8080. nginx serves the frontend and forwards `/api` to the backend.
SQLite lives in the named volume `uttt-data`; the backend runs migrations on start.
`docker compose down` keeps the data; add `--volumes` to delete it.

## API types

The frontend's API types are generated from the backend's OpenAPI document and committed
(`frontend/src/api/schema.d.ts`). After changing any endpoint or schema, from `frontend/`:

```bash
npm run gen:api
```

CI regenerates the file and fails if the committed copy differs.

## Tests and checks

Backend, from `backend/`:

```bash
uv run ruff check
uv run mypy
uv run pytest
```

Frontend, from `frontend/`:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

End-to-end smoke test (starts both servers itself, using a separate `data/e2e.db`), from `frontend/`:

```bash
npx playwright install chromium   # first time only
npm run e2e
```

## Files that must be committed

Generated files that Docker and CI need, and that a fresh checkout will not have unless they are
in version control: `backend/uv.lock` (from `uv sync`), `frontend/package-lock.json` (from
`npm install`) and `frontend/src/api/schema.d.ts` (from `npm run gen:api`). If a Docker build says
`"/uv.lock": not found`, run `uv sync` in `backend/`; if the frontend build cannot find
`./schema`, run `npm run gen:api` in `frontend/`.

## Notes

- Derived values (board states, current player, active board, status, winner, move count)
  are never stored. Only the move log is, and everything else is replayed from it.
- Board and cell numbers on screen and in the API run 0 to 8, row by row.
- Design choices and out-of-scope observations are in `DECISIONS.md`; history is in `CHANGELOG.md`.
