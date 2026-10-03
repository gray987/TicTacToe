import { defineConfig } from "@playwright/test";

const BACKEND = "http://localhost:8000";
const FRONTEND = "http://localhost:5173";

export default defineConfig({
  testDir: "e2e",
  fullyParallel: false,
  use: { baseURL: FRONTEND },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
  webServer: [
    {
      // Migrate a dedicated e2e database, then serve the API.
      command:
        "uv run --directory ../backend alembic upgrade head && uv run --directory ../backend uvicorn app.main:app --port 8000",
      url: `${BACKEND}/health`,
      env: { DATABASE_URL: "sqlite:///./data/e2e.db" },
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: "npm run dev -- --port 5173 --strictPort",
      url: FRONTEND,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
});
