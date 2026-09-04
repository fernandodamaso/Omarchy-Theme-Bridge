import {mkdir, readFile, rm, writeFile} from "node:fs/promises";
import {resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {build} from "vite";
import {buildManifest} from "../manifest.config";
import {BUILD_DEFINES} from "../vite.config";

const root = fileURLToPath(new URL("..", import.meta.url));
const dist = resolve(root, "dist");

await rm(dist, {recursive: true, force: true});
await mkdir(dist, {recursive: true});

await build({
  configFile: false,
  root,
  define: BUILD_DEFINES,
  build: {
    outDir: dist,
    emptyOutDir: false,
    sourcemap: true,
    rollupOptions: {
      input: resolve(root, "src/background/service-worker.ts"),
      output: {
        format: "es",
        entryFileNames: "background/service-worker.js",
      },
    },
  },
});

await build({
  configFile: false,
  root,
  define: BUILD_DEFINES,
  build: {
    outDir: dist,
    emptyOutDir: false,
    sourcemap: true,
    lib: {
      entry: resolve(root, "src/content/content-script.ts"),
      name: "OmarchyThemeBridgeContent",
      formats: ["iife"],
      fileName: () => "content/content-script.js",
    },
    rollupOptions: {output: {inlineDynamicImports: true}},
  },
});

await build({
  configFile: false,
  root: resolve(root, "src"),
  define: BUILD_DEFINES,
  build: {
    outDir: dist,
    emptyOutDir: false,
    sourcemap: true,
    rollupOptions: {
      input: {
        popup: resolve(root, "src/popup/index.html"),
        options: resolve(root, "src/options/index.html"),
      },
    },
  },
});

const publicKey = await readFile(resolve(root, "dev-public-key.txt"), "utf8");
await writeFile(
  resolve(dist, "manifest.json"),
  `${JSON.stringify(buildManifest(publicKey), null, 2)}\n`,
  "utf8",
);
