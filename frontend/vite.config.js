import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // local dev: forward /api to the FastAPI backend on :8000
      "/api": "http://localhost:8000",
    },
  },
});
