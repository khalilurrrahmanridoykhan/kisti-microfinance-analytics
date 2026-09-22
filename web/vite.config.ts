import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Served at https://khalilurrrahmanridoykhan.github.io/kisti-microfinance-analytics/, so every
// asset and fetch path must be relative to that base, not the domain root.
export default defineConfig({
  base: "/kisti-microfinance-analytics/",
  plugins: [react()],
  build: {
    outDir: "dist",
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    globals: true,
    css: false,
  },
});
