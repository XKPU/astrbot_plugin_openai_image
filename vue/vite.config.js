import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

/* Build straight into the plugin's page directory; relative base keeps the
 * token-URL asset paths working under /plugin-view/. */
export default defineConfig({
  base: "./",
  plugins: [vue()],
  build: {
    outDir: "../views/config",
    emptyOutDir: true,
  },
});
