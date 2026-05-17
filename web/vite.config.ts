import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

const QWEBCHANNEL_SCRIPT =
  '<script src="qrc:///qtwebchannel/qwebchannel.js"></script>';

/** Garantit qwebchannel.js avant le bundle Vite (évite l’injection en <head> seul). */
function qwebChannelFirst(): { name: string; transformIndexHtml: (html: string) => string } {
  return {
    name: "qwebchannel-first",
    transformIndexHtml(html) {
      let out = html.replace(
        /\s*<script src="qrc:\/\/\/qtwebchannel\/qwebchannel\.js"><\/script>\s*/g,
        "",
      );
      if (!out.includes("qwebchannel.js")) {
        out = out.replace(/(<script type="module")/i, `${QWEBCHANNEL_SCRIPT}\n    $1`);
      }
      return out;
    },
  };
}

export default defineConfig({
  plugins: [react(), qwebChannelFirst()],
  base: "./",
  resolve: {
    alias: {
      "@shared": path.resolve(rootDir, "shared"),
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
