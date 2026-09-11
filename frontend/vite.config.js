import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy: every API call in this app uses relative URLs like
// "/api/weather/current/" — no base URL, no CORS handling needed.
// Point PROXY_TARGET at your Django server; defaults to localhost:8000.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
