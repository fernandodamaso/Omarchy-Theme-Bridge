import {defineConfig} from "@playwright/test";

export default defineConfig({
  testDir: "tests/browser",
  fullyParallel: false,
  use: {headless: true},
});
