import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  // GitHub Pages 上是 project page（https://<user>.github.io/matsuboard/），
  // 不是網域根目錄，資產路徑要帶上 repo 名稱這個 base path。
  base: "/matsuboard/",
  plugins: [react()],
});
