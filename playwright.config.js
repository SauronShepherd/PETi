import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  fullyParallel: false,
  reporter: [["list"], ["json", { outputFile: "release/evidence/navigation/web-playwright-results.json" }]],
  use: { baseURL: process.env.PETI_WEB_BASE_URL || "http://127.0.0.1:4173", screenshot: "on", trace: "retain-on-failure" },
  webServer: process.env.PETI_WEB_BASE_URL
    ? undefined
    : { command: "python -m http.server 4173 --bind 127.0.0.1 -d web", url: "http://127.0.0.1:4173/?demo=1", reuseExistingServer: true, timeout: 30_000 },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
    { name: "tablet", use: { ...devices["Desktop Chrome"], viewport: { width: 1024, height: 768 }, isMobile: false } },
    { name: "mobile", use: { ...devices["Pixel 5"], viewport: { width: 390, height: 844 } } },
  ],
});
