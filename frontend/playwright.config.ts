import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "off",
  },
  webServer: [
    {
      command:
        "cd .. && PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: true,
      timeout: 120000,
    },
    {
      command: "npm run build && npm run preview",
      url: "http://127.0.0.1:4173",
      reuseExistingServer: true,
      timeout: 180000,
    },
  ],
});
