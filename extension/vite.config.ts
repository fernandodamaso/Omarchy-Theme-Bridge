import {defineConfig} from "vite";

export const BUILD_DEFINES = {
  __TEST__: "false",
  __CHROMIUM_MV3__: "true",
  __PLUS__: "false",
} as const;

export default defineConfig({
  define: BUILD_DEFINES,
});
