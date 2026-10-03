import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { configDefaults, defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { "/api": "http://localhost:8000" } },
  test: {
    environment: "jsdom",
    setupFiles: ["src/test/setup.ts"],
    env: { VITE_API_BASE_URL: "http://localhost" },
    exclude: [...configDefaults.exclude, "e2e/**"],
  },
});
