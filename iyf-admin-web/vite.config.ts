import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 管理SPA。認証SPAのため index.html への fallback（history API）を有効化。
export default defineConfig({
  plugins: [react()],
  server: { port: 5174 },
  preview: { port: 4174 },
});
