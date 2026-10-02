import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const BOT_SERVER = "http://localhost:7860";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": BOT_SERVER,
      "/ws": { target: BOT_SERVER.replace("http", "ws"), ws: true },
    },
  },
  test: {
    include: ["src/**/*.test.ts"],
  },
});
