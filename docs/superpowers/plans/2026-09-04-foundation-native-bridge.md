# Foundation and Native Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver PR 1: a buildable Manifest V3 extension that connects to a tested Python native host, reads and watches the active Omarchy theme, persists a validated theme snapshot, and can bootstrap or remove a temporary page canvas style.

**Architecture:** A Python 3.11+ native process reads Omarchy’s active `colors.toml`, normalizes it into a versioned semantic payload, and communicates over Chrome Native Messaging. A Manifest V3 service worker owns that connection, persists state in `chrome.storage.local`, reconnects through `chrome.alarms`, and coordinates statically declared content scripts plus recovery injection for already-open tabs.

**Tech Stack:** Python 3.11 standard library, pytest, TypeScript, Vite, Vitest, Playwright tooling, Chrome Manifest V3, npm.

**Spec:** `docs/superpowers/specs/2026-09-04-omarchy-theme-bridge-design.md`

## Global Constraints

- Work from design commit `092884622db4ae9e89b41a018b3250d05c0ba7ad` on branch `feat/foundation-native-bridge`.
- Target Google Chrome and Chromium with Manifest V3.
- Use npm and commit `extension/package-lock.json`.
- Use Python 3.11+; native-host runtime code may use only the Python standard library.
- Native host name is exactly `com.omarchy.theme_bridge`.
- Default Omarchy paths are exactly `$HOME/.local/state/omarchy/current/theme/colors.toml` and `$HOME/.local/state/omarchy/current/theme.name`.
- `OMARCHY_THEME_BRIDGE_THEME_DIR` is the only active-theme directory override.
- Native messages are UTF-8 JSON framed with a 32-bit native-endian length and capped by the application at 65,536 bytes.
- The host must never receive or log URLs, hostnames, page content, CSS source, cookies, form values, titles, screenshots, browsing history, or browser profile paths.
- Watch files with Linux inotify through `ctypes`; do not add continuous filesystem polling.
- Use a committed public development manifest key; never commit its private key.
- Do not claim Chrome, Chromium, or local Omarchy qualification unless it was actually run and recorded.

---

## File Map

### Root

- `.gitignore` — generated output, virtual environments, caches, screenshots, and temporary developer keys.
- `README.md` — PR 1 development status, build commands, and intentionally incomplete renderer warning.
- `scripts/verify-pr1.sh` — one deterministic command for TypeScript, Python, installer, and build checks.

### Extension

- `extension/package.json` — npm scripts and development dependencies.
- `extension/package-lock.json` — exact npm dependency resolution.
- `extension/tsconfig.json` — strict TypeScript configuration.
- `extension/vite.config.ts` — Vite multi-entry build orchestration.
- `extension/vitest.config.ts` — unit-test configuration.
- `extension/playwright.config.ts` — browser-test configuration scaffold used by later plans.
- `extension/manifest.config.ts` — typed Manifest V3 source.
- `extension/dev-public-key.txt` — base64 DER public key only.
- `extension/scripts/build.ts` — creates the extension build and writes `dist/manifest.json`.
- `extension/scripts/generate-dev-key.sh` — creates a disposable private key, writes only the public key, then deletes the private material.
- `extension/src/background/service-worker.ts` — privileged entry point.
- `extension/src/background/native-connection.ts` — native-port handshake and reconnection state machine.
- `extension/src/background/state-store.ts` — storage-backed application state.
- `extension/src/background/tab-coordinator.ts` — eligible-tab recovery injection and update ordering.
- `extension/src/content/bootstrap.ts` — temporary early canvas style.
- `extension/src/content/content-script.ts` — frame-local controller entry point for PR 1.
- `extension/src/popup/index.html`, `index.ts`, `styles.css` — minimal status shell; full UX is PR 3.
- `extension/src/options/index.html`, `index.ts`, `styles.css` — minimal options shell; full UX is PR 3.
- `extension/src/shared/theme.ts` — normalized theme contract.
- `extension/src/shared/native-messages.ts` — browser/host protocol types and validators.
- `extension/src/shared/internal-messages.ts` — service-worker/content/UI message types and validators.
- `extension/src/shared/settings.ts` — settings contract and exact-hostname resolution.
- `extension/src/shared/errors.ts` — bounded error enums.
- `extension/src/shared/validation.ts` — reusable schema guards.
- `extension/tests/unit/` — Vitest tests.
- `extension/tests/helpers/fake-chrome.ts` — narrow Chrome API fake.

### Native host

- `native-host/pyproject.toml` — Python package metadata and pytest configuration.
- `native-host/omarchy_theme_bridge_host/__init__.py` — version constant.
- `native-host/omarchy_theme_bridge_host/__main__.py` — executable entry point.
- `native-host/omarchy_theme_bridge_host/config.py` — installed configuration and caller-origin validation.
- `native-host/omarchy_theme_bridge_host/errors.py` — safe protocol error codes.
- `native-host/omarchy_theme_bridge_host/protocol.py` — native framing and message validation.
- `native-host/omarchy_theme_bridge_host/color.py` — foundational CSS-color parsing and deterministic color helpers.
- `native-host/omarchy_theme_bridge_host/theme_loader.py` — active-path resolution and TOML loading.
- `native-host/omarchy_theme_bridge_host/theme_normalizer.py` — Omarchy alias, mode, fallback, semantic palette, and generation logic.
- `native-host/omarchy_theme_bridge_host/last_good.py` — atomic normalized snapshot persistence.
- `native-host/omarchy_theme_bridge_host/watcher.py` — inotify wrapper and watch re-arming.
- `native-host/omarchy_theme_bridge_host/host.py` — selector-driven native process loop.
- `native-host/tests/` — pytest unit and integration tests.
- `native-host/install/install.sh` — user-scoped idempotent installer.
- `native-host/install/uninstall.sh` — ownership-bounded removal.
- `native-host/install/verify.sh` — installed-file validation.
- `native-host/install/theme-set-hook.sh` — hook template that atomically signals a reload.

### Documentation

- `docs/installation.md` — build, load-unpacked, install, verify, and remove steps.
- `docs/architecture.md` — PR 1 data flow and trust boundary.
- `docs/privacy.md` — native-host data boundary.

---

### Task 1: Scaffold the repository and deterministic extension build

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `extension/package.json`
- Create: `extension/package-lock.json`
- Create: `extension/tsconfig.json`
- Create: `extension/vite.config.ts`
- Create: `extension/vitest.config.ts`
- Create: `extension/playwright.config.ts`
- Create: `extension/manifest.config.ts`
- Create: `extension/scripts/build.ts`
- Create: `extension/scripts/generate-dev-key.sh`
- Create: `extension/dev-public-key.txt`
- Create: `extension/src/background/service-worker.ts`
- Create: `extension/src/content/content-script.ts`
- Create: `extension/src/popup/index.html`
- Create: `extension/src/popup/index.ts`
- Create: `extension/src/popup/styles.css`
- Create: `extension/src/options/index.html`
- Create: `extension/src/options/index.ts`
- Create: `extension/src/options/styles.css`
- Test: `extension/tests/unit/manifest.test.ts`

**Interfaces:**
- Produces: `buildManifest(publicKey: string): Record<string, unknown>` from `extension/manifest.config.ts`.
- Produces: build artifacts at `extension/dist/` with `background/service-worker.js`, `content/content-script.js`, `popup/index.html`, `options/index.html`, and `manifest.json`.
- Consumes: no earlier task interfaces.

- [ ] **Step 1: Create the implementation branch**

```bash
git switch --detach 092884622db4ae9e89b41a018b3250d05c0ba7ad
git switch -c feat/foundation-native-bridge
```

Expected: `git branch --show-current` prints `feat/foundation-native-bridge`.

- [ ] **Step 2: Write the failing manifest contract test**

```ts
// extension/tests/unit/manifest.test.ts
import {describe, expect, it} from "vitest";
import {buildManifest} from "../../manifest.config";

const PUBLIC_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A";

describe("buildManifest", () => {
  it("declares only the approved permissions and ordinary web matches", () => {
    const manifest = buildManifest(PUBLIC_KEY);

    expect(manifest).toMatchObject({
      manifest_version: 3,
      name: "Omarchy Theme Bridge",
      version: "0.1.0",
      permissions: ["alarms", "nativeMessaging", "scripting", "storage"],
      host_permissions: ["http://*/*", "https://*/*"],
      background: {
        service_worker: "background/service-worker.js",
        type: "module",
      },
    });

    expect(manifest).not.toHaveProperty("permissions", expect.arrayContaining([
      "bookmarks",
      "cookies",
      "downloads",
      "history",
      "identity",
    ]));
  });

  it("declares a document-start isolated content script in every eligible frame", () => {
    const manifest = buildManifest(PUBLIC_KEY) as {
      content_scripts: Array<Record<string, unknown>>;
    };

    expect(manifest.content_scripts[0]).toMatchObject({
      matches: ["http://*/*", "https://*/*"],
      js: ["content/content-script.js"],
      run_at: "document_start",
      all_frames: true,
      match_about_blank: true,
      match_origin_as_fallback: true,
    });
  });
});
```

- [ ] **Step 3: Initialize npm and install exact development dependencies**

```bash
cd extension
npm init -y
npm install --save-exact --save-dev \
  @types/chrome \
  @types/node \
  happy-dom \
  playwright \
  typescript \
  vite \
  vitest
```

Then replace the generated scripts and metadata with:

```json
{
  "name": "omarchy-theme-bridge-extension",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "tsx scripts/build.ts",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:browser": "playwright test",
    "verify": "npm run typecheck && npm test && npm run build"
  }
}
```

Install the build-script runner and preserve the exact lockfile:

```bash
npm install --save-exact --save-dev tsx
```

- [ ] **Step 4: Run the manifest test and verify the red state**

```bash
npm test -- tests/unit/manifest.test.ts
```

Expected: FAIL because `extension/manifest.config.ts` does not exist.

- [ ] **Step 5: Generate and retain only the public development key**

```bash
cat > scripts/generate-dev-key.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

openssl genrsa -out "$tmp/dev-private.pem" 2048 >/dev/null 2>&1
openssl rsa -in "$tmp/dev-private.pem" -pubout -outform DER 2>/dev/null \
  | base64 -w0 > "$root/dev-public-key.txt"
printf '\n' >> "$root/dev-public-key.txt"
chmod 0644 "$root/dev-public-key.txt"
printf 'Wrote public development key to %s\n' "$root/dev-public-key.txt"
EOF
chmod +x scripts/generate-dev-key.sh
./scripts/generate-dev-key.sh
```

Verify no private key exists under the repository:

```bash
find .. -type f \( -name '*.pem' -o -name '*.key' \) -print
```

Expected: no output.

- [ ] **Step 6: Implement the manifest source**

```ts
// extension/manifest.config.ts
export function buildManifest(publicKey: string): Record<string, unknown> {
  const key = publicKey.trim();
  if (!key) {
    throw new Error("Development public key is required");
  }

  return {
    manifest_version: 3,
    name: "Omarchy Theme Bridge",
    description: "Adapt website interfaces to the active Omarchy theme.",
    version: "0.1.0",
    key,
    permissions: ["alarms", "nativeMessaging", "scripting", "storage"],
    host_permissions: ["http://*/*", "https://*/*"],
    background: {
      service_worker: "background/service-worker.js",
      type: "module",
    },
    action: {
      default_title: "Omarchy Theme Bridge",
      default_popup: "popup/index.html",
    },
    options_ui: {
      page: "options/index.html",
      open_in_tab: true,
    },
    content_scripts: [
      {
        matches: ["http://*/*", "https://*/*"],
        js: ["content/content-script.js"],
        run_at: "document_start",
        all_frames: true,
        match_about_blank: true,
        match_origin_as_fallback: true,
      },
    ],
  };
}
```

- [ ] **Step 7: Implement the Vite build orchestration**

Use `vite.build()` three times so the service worker remains ESM, the content script becomes one classic IIFE, and popup/options HTML are processed by Vite:

```ts
// extension/scripts/build.ts
import {cp, mkdir, readFile, rm, writeFile} from "node:fs/promises";
import {resolve} from "node:path";
import {build} from "vite";
import {buildManifest} from "../manifest.config";

const root = resolve(import.meta.dirname, "..");
const dist = resolve(root, "dist");

await rm(dist, {recursive: true, force: true});
await mkdir(dist, {recursive: true});

await build({
  configFile: false,
  root,
  build: {
    outDir: dist,
    emptyOutDir: false,
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
  build: {
    outDir: dist,
    emptyOutDir: false,
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
  build: {
    outDir: dist,
    emptyOutDir: false,
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
```

Keep `vite.config.ts` as the testable shared defaults:

```ts
// extension/vite.config.ts
import {defineConfig} from "vite";

export default defineConfig({
  define: {
    __TEST__: "false",
    __CHROMIUM_MV3__: "true",
    __PLUS__: "false",
  },
});
```

- [ ] **Step 8: Add strict TypeScript and test configuration**

```json
// extension/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "types": ["chrome", "node", "vitest/globals"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "useUnknownInCatchVariables": true,
    "skipLibCheck": true,
    "noEmit": true
  },
  "include": ["manifest.config.ts", "scripts", "src", "tests", "vite.config.ts", "vitest.config.ts", "playwright.config.ts"]
}
```

```ts
// extension/vitest.config.ts
import {defineConfig} from "vitest/config";

export default defineConfig({
  test: {
    environment: "happy-dom",
    include: ["tests/unit/**/*.test.ts", "tests/integration/**/*.test.ts"],
    restoreMocks: true,
    clearMocks: true,
  },
});
```

```ts
// extension/playwright.config.ts
import {defineConfig} from "@playwright/test";

export default defineConfig({
  testDir: "tests/browser",
  fullyParallel: false,
  use: {headless: true},
});
```

Add `@playwright/test` exactly and remove the unused direct `playwright` package if npm installed it:

```bash
npm uninstall playwright
npm install --save-exact --save-dev @playwright/test
```

- [ ] **Step 9: Add minimal entries that are valid but make no renderer claim**

```ts
// extension/src/background/service-worker.ts
chrome.runtime.onInstalled.addListener(() => {
  console.info("Omarchy Theme Bridge installed");
});
```

```ts
// extension/src/content/content-script.ts
void chrome.runtime.sendMessage({type: "content.ready"}).catch(() => undefined);
```

Use plain accessible HTML in popup/options with the exact notice `Renderer arrives in PR 2`; do not advertise Adaptive theming as complete in PR 1.

- [ ] **Step 10: Run manifest, type, and build checks**

```bash
npm run typecheck
npm test -- tests/unit/manifest.test.ts
npm run build
node -e 'const m=require("./dist/manifest.json"); if(m.manifest_version!==3) process.exit(1)'
find dist -maxdepth 3 -type f -print | sort
```

Expected: all commands exit 0 and the file list contains the five required artifacts.

- [ ] **Step 11: Add root ignore rules and commit**

```gitignore
# .gitignore
extension/node_modules/
extension/dist/
extension/test-results/
extension/playwright-report/
native-host/.venv/
**/__pycache__/
.pytest_cache/
*.pyc
*.pem
*.key
.DS_Store
```

```bash
git add .gitignore README.md extension
git commit -m "build: scaffold Manifest V3 extension"
```

---

### Task 2: Define shared theme, settings, and message contracts

**Files:**
- Create: `extension/src/shared/theme.ts`
- Create: `extension/src/shared/errors.ts`
- Create: `extension/src/shared/settings.ts`
- Create: `extension/src/shared/native-messages.ts`
- Create: `extension/src/shared/internal-messages.ts`
- Create: `extension/src/shared/validation.ts`
- Test: `extension/tests/unit/validation.test.ts`
- Test: `extension/tests/unit/settings.test.ts`

**Interfaces:**
- Produces: `OmarchyTheme`, `ThemeMode`, `SiteMode`, `ExtensionSettings`, `ThemeErrorCode`, `ExtensionToHost`, `HostToExtension`, `InternalRequest`, and `InternalResponse`.
- Produces: `isOmarchyTheme(value: unknown): value is OmarchyTheme`.
- Produces: `parseHostMessage(value: unknown): HostToExtension` and `parseExtensionMessage(value: unknown): ExtensionToHost`.
- Produces: `resolveSiteMode(settings: ExtensionSettings, hostname: string): SiteMode`.
- Consumes: no earlier task interfaces beyond TypeScript scaffold.

- [ ] **Step 1: Write failing validation and settings tests**

```ts
// extension/tests/unit/validation.test.ts
import {describe, expect, it} from "vitest";
import {isOmarchyTheme} from "../../src/shared/theme";
import {parseHostMessage} from "../../src/shared/native-messages";

const theme = {
  schemaVersion: 1,
  generation: `sha256:${"a".repeat(64)}`,
  name: "Tokyo Night",
  mode: "dark",
  colors: {
    canvas: "#1a1b26",
    surface: "#202230",
    surfaceRaised: "#24283b",
    surfaceInset: "#13141c",
    text: "#a9b1d6",
    textStrong: "#c0caf5",
    textMuted: "#565f89",
    border: "#414868",
    accent: "#7aa2f7",
    selection: "#292e42",
    danger: "#f7768e",
    success: "#9ece6a",
    warning: "#e0af68",
    info: "#7aa2f7",
    magenta: "#bb9af7",
    cyan: "#7dcfff"
  },
  source: {background: "#1a1b26", foreground: "#a9b1d6"}
} as const;

describe("theme validation", () => {
  it("accepts a complete normalized theme", () => {
    expect(isOmarchyTheme(theme)).toBe(true);
  });

  it("rejects a non-canonical generation", () => {
    expect(isOmarchyTheme({...theme, generation: "tokyo"})).toBe(false);
  });

  it("rejects unbounded host payload fields", () => {
    expect(() => parseHostMessage({type: "theme.changed", theme, url: "https://example.com"})).toThrow();
  });
});
```

```ts
// extension/tests/unit/settings.test.ts
import {describe, expect, it} from "vitest";
import {DEFAULT_SETTINGS, normalizeHostname, resolveSiteMode} from "../../src/shared/settings";

describe("site settings", () => {
  it("uses Adaptive by default", () => {
    expect(resolveSiteMode(DEFAULT_SETTINGS, "youtube.com")).toBe("adaptive");
  });

  it("uses exact-hostname overrides only", () => {
    const settings = {
      ...DEFAULT_SETTINGS,
      hostnameOverrides: {"youtube.com": "accent" as const},
    };
    expect(resolveSiteMode(settings, "youtube.com")).toBe("accent");
    expect(resolveSiteMode(settings, "music.youtube.com")).toBe("adaptive");
  });

  it("normalizes Unicode and trailing dots to lowercase ASCII", () => {
    expect(normalizeHostname("BÜCHER.example.")).toBe("xn--bcher-kva.example");
  });
});
```

- [ ] **Step 2: Run tests and verify the red state**

```bash
cd extension
npm test -- tests/unit/validation.test.ts tests/unit/settings.test.ts
```

Expected: FAIL because shared modules do not exist.

- [ ] **Step 3: Implement exact contracts**

```ts
// extension/src/shared/theme.ts
export type ThemeMode = "dark" | "light";
export type CanonicalColor = `#${string}`;
export type ThemeGeneration = `sha256:${string}`;

export interface OmarchyTheme {
  schemaVersion: 1;
  generation: ThemeGeneration;
  name: string;
  mode: ThemeMode;
  colors: {
    canvas: CanonicalColor;
    surface: CanonicalColor;
    surfaceRaised: CanonicalColor;
    surfaceInset: CanonicalColor;
    text: CanonicalColor;
    textStrong: CanonicalColor;
    textMuted: CanonicalColor;
    border: CanonicalColor;
    accent: CanonicalColor;
    selection: CanonicalColor;
    danger: CanonicalColor;
    success: CanonicalColor;
    warning: CanonicalColor;
    info: CanonicalColor;
    magenta: CanonicalColor;
    cyan: CanonicalColor;
  };
  source: {
    background: CanonicalColor;
    darkBackground?: CanonicalColor;
    darkerBackground?: CanonicalColor;
    lighterBackground?: CanonicalColor;
    foreground: CanonicalColor;
    darkForeground?: CanonicalColor;
    lightForeground?: CanonicalColor;
    brightForeground?: CanonicalColor;
  };
}
```

```ts
// extension/src/shared/settings.ts
export type SiteMode = "adaptive" | "accent" | "off";

export interface ExtensionSettings {
  schemaVersion: 1;
  enabled: boolean;
  defaultMode: "adaptive";
  hostnameOverrides: Record<string, SiteMode>;
}

export const DEFAULT_SETTINGS: ExtensionSettings = {
  schemaVersion: 1,
  enabled: true,
  defaultMode: "adaptive",
  hostnameOverrides: {},
};

export function normalizeHostname(input: string): string {
  const trimmed = input.trim().replace(/\.$/, "");
  if (!trimmed || /[\s/@:]/u.test(trimmed)) {
    throw new Error("Invalid hostname");
  }
  const hostname = new URL(`http://${trimmed}`).hostname.toLowerCase();
  if (!hostname || hostname.length > 253) {
    throw new Error("Invalid hostname");
  }
  return hostname;
}

export function resolveSiteMode(settings: ExtensionSettings, hostname: string): SiteMode {
  if (!settings.enabled) return "off";
  return settings.hostnameOverrides[normalizeHostname(hostname)] ?? settings.defaultMode;
}
```

Define the bounded enums exactly:

```ts
// extension/src/shared/errors.ts
export type ThemeErrorCode =
  | "THEME_NOT_FOUND"
  | "THEME_INVALID"
  | "THEME_UNSUPPORTED_COLOR"
  | "CALLER_FORBIDDEN"
  | "PROTOCOL_MISMATCH";

export type ConnectionErrorCode =
  | "HOST_NOT_FOUND"
  | "HOST_DISCONNECTED"
  | "HOST_PROTOCOL_ERROR"
  | "HOST_MESSAGE_INVALID";
```

- [ ] **Step 4: Implement validators that reject extra native fields**

Use a reusable `hasExactKeys()` guard and canonical `#rrggbb` or `#rrggbbaa` validation. Native messages must reject extra fields rather than silently retaining page-shaped data.

```ts
// extension/src/shared/validation.ts
export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

export function isCanonicalColor(value: unknown): value is `#${string}` {
  return typeof value === "string" && /^#[0-9a-f]{6}(?:[0-9a-f]{2})?$/.test(value);
}
```

Implement `isOmarchyTheme()` by checking exact top-level keys, exact semantic color keys, allowed optional `source` keys, `schemaVersion === 1`, mode, bounded name length `1..128`, and `/^sha256:[0-9a-f]{64}$/`.

Implement native unions exactly as specified:

```ts
export type ExtensionToHost =
  | {type: "hello"; protocolVersion: 1; extensionVersion: string}
  | {type: "theme.reload"}
  | {type: "ping"; requestId: string};

export type HostToExtension =
  | {type: "host.ready"; protocolVersion: 1; hostVersion: string}
  | {type: "theme.snapshot"; theme: OmarchyTheme}
  | {type: "theme.changed"; theme: OmarchyTheme}
  | {type: "theme.error"; code: ThemeErrorCode; retainedGeneration?: string}
  | {type: "pong"; requestId: string};
```

Bound `extensionVersion`, `hostVersion`, and `requestId` to 128 characters.

- [ ] **Step 5: Define internal messages without privileged passthrough**

```ts
// extension/src/shared/internal-messages.ts
import type {ConnectionErrorCode, ThemeErrorCode} from "./errors";
import type {SiteMode} from "./settings";
import type {OmarchyTheme} from "./theme";

export type RendererState = "idle" | "bootstrapped" | "off" | "waiting";

export type InternalRequest =
  | {type: "content.ready"}
  | {type: "state.get"}
  | {type: "native.reconnect"};

export type ApplyState = {
  type: "state.apply";
  enabled: boolean;
  mode: SiteMode;
  theme: OmarchyTheme | null;
};

export type InternalResponse =
  | ApplyState
  | {
      type: "status.snapshot";
      connected: boolean;
      connectionError?: ConnectionErrorCode;
      themeError?: ThemeErrorCode;
      theme: OmarchyTheme | null;
      rendererState?: RendererState;
    };
```

Do not add a generic `{type: string; payload: unknown}` route and do not expose arbitrary native-message forwarding.

- [ ] **Step 6: Run tests and typecheck**

```bash
npm run typecheck
npm test -- tests/unit/validation.test.ts tests/unit/settings.test.ts
```

Expected: PASS.

- [ ] **Step 7: Commit shared contracts**

```bash
git add extension/src/shared extension/tests/unit/validation.test.ts extension/tests/unit/settings.test.ts
git commit -m "feat: define bridge data contracts"
```

---

### Task 3: Implement native framing, configuration, and caller validation

**Files:**
- Create: `native-host/pyproject.toml`
- Create: `native-host/omarchy_theme_bridge_host/__init__.py`
- Create: `native-host/omarchy_theme_bridge_host/errors.py`
- Create: `native-host/omarchy_theme_bridge_host/config.py`
- Create: `native-host/omarchy_theme_bridge_host/protocol.py`
- Test: `native-host/tests/test_protocol.py`
- Test: `native-host/tests/test_config.py`

**Interfaces:**
- Produces: `read_message(stream: BinaryIO) -> dict[str, object] | None`.
- Produces: `write_message(stream: BinaryIO, message: Mapping[str, object]) -> None`.
- Produces: `parse_extension_message(value: object) -> ExtensionMessage`.
- Produces: `HostConfig.load(path: Path) -> HostConfig` and `HostConfig.assert_caller(argv: Sequence[str]) -> None`.
- Consumes: protocol values from Task 2, mirrored in Python with the same field names.

- [ ] **Step 1: Create Python package metadata**

```toml
# native-host/pyproject.toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "omarchy-theme-bridge-host"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
test = ["pytest>=8.3,<10"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

```python
# native-host/omarchy_theme_bridge_host/__init__.py
__version__ = "0.1.0"
PROTOCOL_VERSION = 1
HOST_NAME = "com.omarchy.theme_bridge"
MAX_MESSAGE_BYTES = 65_536
```

- [ ] **Step 2: Write failing framing and caller tests**

```python
# native-host/tests/test_protocol.py
import io
import json
import struct

import pytest

from omarchy_theme_bridge_host.protocol import MessageTooLarge, read_message, write_message


def test_round_trip_native_message() -> None:
    stream = io.BytesIO()
    write_message(stream, {"type": "ping", "requestId": "abc"})
    stream.seek(0)
    assert read_message(stream) == {"type": "ping", "requestId": "abc"}


def test_read_rejects_message_over_application_limit() -> None:
    stream = io.BytesIO(struct.pack("=I", 65_537) + b"{}")
    with pytest.raises(MessageTooLarge):
        read_message(stream)


def test_write_uses_compact_utf8_json() -> None:
    stream = io.BytesIO()
    write_message(stream, {"type": "theme.reload"})
    payload = stream.getvalue()[4:]
    assert payload == json.dumps({"type": "theme.reload"}, separators=(",", ":")).encode()
```

```python
# native-host/tests/test_config.py
import json
from pathlib import Path

import pytest

from omarchy_theme_bridge_host.config import CallerForbidden, HostConfig


EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop"
ORIGIN = f"chrome-extension://{EXTENSION_ID}/"


def test_config_accepts_exact_installed_origin(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"allowedOrigin": ORIGIN}), encoding="utf-8")
    HostConfig.load(path).assert_caller(["host", ORIGIN])


def test_config_rejects_other_extension(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"allowedOrigin": ORIGIN}), encoding="utf-8")
    with pytest.raises(CallerForbidden):
        HostConfig.load(path).assert_caller(["host", "chrome-extension://pppppppppppppppppppppppppppppppp/"])
```

- [ ] **Step 3: Run tests and verify the red state**

```bash
cd native-host
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
pytest tests/test_protocol.py tests/test_config.py -q
```

Expected: FAIL because the modules do not exist.

- [ ] **Step 4: Implement bounded framing**

```python
# native-host/omarchy_theme_bridge_host/protocol.py
from __future__ import annotations

import json
import struct
from collections.abc import Mapping
from typing import BinaryIO, TypeAlias

from . import MAX_MESSAGE_BYTES

JsonObject: TypeAlias = dict[str, object]


class ProtocolError(RuntimeError):
    pass


class MessageTooLarge(ProtocolError):
    pass


def _read_exact(stream: BinaryIO, length: int) -> bytes:
    chunks: list[bytes] = []
    remaining = length
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            raise ProtocolError("Unexpected EOF")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_message(stream: BinaryIO) -> JsonObject | None:
    header = stream.read(4)
    if header == b"":
        return None
    if len(header) != 4:
        raise ProtocolError("Truncated message header")
    (length,) = struct.unpack("=I", header)
    if length > MAX_MESSAGE_BYTES:
        raise MessageTooLarge("Message exceeds 64 KiB limit")
    payload = _read_exact(stream, length)
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("Invalid UTF-8 JSON") from exc
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ProtocolError("Message must be a JSON object")
    return value


def write_message(stream: BinaryIO, message: Mapping[str, object]) -> None:
    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_MESSAGE_BYTES:
        raise MessageTooLarge("Message exceeds 64 KiB limit")
    stream.write(struct.pack("=I", len(payload)))
    stream.write(payload)
    stream.flush()
```

- [ ] **Step 5: Implement configuration and exact caller-origin checks**

```python
# native-host/omarchy_theme_bridge_host/config.py
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence

ORIGIN_RE = re.compile(r"^chrome-extension://[a-p]{32}/$")


class ConfigError(RuntimeError):
    pass


class CallerForbidden(ConfigError):
    pass


@dataclass(frozen=True, slots=True)
class HostConfig:
    allowed_origin: str

    @classmethod
    def load(cls, path: Path) -> "HostConfig":
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError("Host configuration is invalid") from exc
        if set(value) != {"allowedOrigin"}:
            raise ConfigError("Host configuration has unexpected fields")
        origin = value["allowedOrigin"]
        if not isinstance(origin, str) or not ORIGIN_RE.fullmatch(origin):
            raise ConfigError("Allowed origin is invalid")
        return cls(allowed_origin=origin)

    def assert_caller(self, argv: Sequence[str]) -> None:
        caller = argv[1] if len(argv) > 1 else ""
        if caller != self.allowed_origin:
            raise CallerForbidden("Caller origin is not allowed")
```

- [ ] **Step 6: Implement exact extension-message validation**

Define frozen dataclasses `HelloMessage`, `ReloadMessage`, and `PingMessage`. `parse_extension_message()` must require exact field sets:

```python
match value.get("type"):
    case "hello" if set(value) == {"type", "protocolVersion", "extensionVersion"}:
        ...
    case "theme.reload" if set(value) == {"type"}:
        ...
    case "ping" if set(value) == {"type", "requestId"}:
        ...
    case _:
        raise ProtocolError("Unsupported message")
```

Require protocol version `1` and bound version/request strings to `1..128` characters.

- [ ] **Step 7: Run Python checks**

```bash
. .venv/bin/activate
python -m compileall -q omarchy_theme_bridge_host
pytest tests/test_protocol.py tests/test_config.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit native protocol foundation**

```bash
git add native-host/pyproject.toml native-host/omarchy_theme_bridge_host native-host/tests/test_protocol.py native-host/tests/test_config.py
git commit -m "feat: add native messaging protocol"
```

---

### Task 4: Parse and normalize Omarchy themes with last-known-good persistence

**Files:**
- Create: `native-host/omarchy_theme_bridge_host/color.py`
- Create: `native-host/omarchy_theme_bridge_host/theme_loader.py`
- Create: `native-host/omarchy_theme_bridge_host/theme_normalizer.py`
- Create: `native-host/omarchy_theme_bridge_host/last_good.py`
- Create: `native-host/tests/fixtures/tokyo-night/colors.toml`
- Create: `native-host/tests/fixtures/tokyo-night/theme.name`
- Create: `native-host/tests/fixtures/light/colors.toml`
- Create: `native-host/tests/fixtures/legacy/colors.toml`
- Create: `native-host/tests/fixtures/invalid/colors.toml`
- Test: `native-host/tests/test_color.py`
- Test: `native-host/tests/test_theme_normalizer.py`
- Test: `native-host/tests/test_last_good.py`

**Interfaces:**
- Produces: `Rgba`, `parse_css_color(value: str) -> Rgba`, `to_hex(color: Rgba) -> str`, and deterministic color mixing/conversion helpers.
- Produces: `ThemePaths.resolve(home: Path, override: str | None) -> ThemePaths`.
- Produces: `load_and_normalize(paths: ThemePaths) -> dict[str, object]`.
- Produces: `LastGoodStore.load() -> dict[str, object] | None` and `LastGoodStore.save(theme: Mapping[str, object]) -> None`.
- Consumes: `MAX_MESSAGE_BYTES` and error enums from Task 3.

- [ ] **Step 1: Add deterministic theme fixtures**

```toml
# native-host/tests/fixtures/tokyo-night/colors.toml
mode = "dark"
accent = "#7aa2f7"
selection = "#292e42"
muted = "#414868"
background = "#1a1b26"
dark_background = "#13141c"
darker_background = "#0e0e14"
lighter_background = "#24283b"
foreground = "#a9b1d6"
dark_foreground = "#565f89"
light_foreground = "#b4bee6"
bright_foreground = "#c0caf5"
red = "#f7768e"
green = "#9ece6a"
yellow = "#e0af68"
blue = "#7aa2f7"
magenta = "#bb9af7"
cyan = "#7dcfff"
```

```toml
# native-host/tests/fixtures/light/colors.toml
mode = "light"
background = "rgb(250 250 252)"
foreground = "rgb(30 32 40)"
accent = "rgb(56 96 200)"
selection = "rgb(210 222 255 / 80%)"
muted = "#8b8f9d"
red = "#b42318"
green = "#16803c"
yellow = "#8a6100"
blue = "#3860c8"
magenta = "#8a3ffc"
cyan = "#087f8c"
```

```toml
# native-host/tests/fixtures/legacy/colors.toml
bg = "#101218"
fg = "#d0d4e0"
color1 = "#ff6677"
color2 = "#77cc88"
color3 = "#ddbb55"
color4 = "#6699ee"
color5 = "#bb88ee"
color6 = "#66cccc"
```

- [ ] **Step 2: Write failing color and normalization tests**

```python
# native-host/tests/test_color.py
import pytest

from omarchy_theme_bridge_host.color import ColorParseError, parse_css_color, to_hex


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("#abc", "#aabbcc"),
        ("#abcd", "#aabbccdd"),
        ("#AABBCC", "#aabbcc"),
        ("rgb(122, 162, 247)", "#7aa2f7"),
        ("rgb(47.843% 63.529% 96.863% / 50%)", "#7aa2f780"),
    ],
)
def test_parse_foundational_css_colors(source: str, expected: str) -> None:
    assert to_hex(parse_css_color(source)) == expected


def test_rejects_context_dependent_color() -> None:
    with pytest.raises(ColorParseError):
        parse_css_color("color-mix(in oklch, red, blue)")
```

```python
# native-host/tests/test_theme_normalizer.py
from pathlib import Path

from omarchy_theme_bridge_host.theme_loader import ThemePaths
from omarchy_theme_bridge_host.theme_normalizer import load_and_normalize

FIXTURES = Path(__file__).parent / "fixtures"


def test_normalizes_tokyo_night_semantics() -> None:
    paths = ThemePaths.from_theme_dir(FIXTURES / "tokyo-night")
    result = load_and_normalize(paths)
    assert result["name"] == "Tokyo Night"
    assert result["mode"] == "dark"
    assert result["colors"]["canvas"] == "#1a1b26"
    assert result["colors"]["surfaceRaised"] == "#24283b"
    assert result["colors"]["textStrong"] == "#c0caf5"
    assert result["colors"]["danger"] == "#f7768e"
    assert result["generation"].startswith("sha256:")


def test_legacy_palette_resolves_foundational_and_named_colors() -> None:
    result = load_and_normalize(ThemePaths.from_theme_dir(FIXTURES / "legacy"))
    assert result["source"]["background"] == "#101218"
    assert result["source"]["foreground"] == "#d0d4e0"
    assert result["colors"]["info"] == "#6699ee"


def test_identical_normalized_payload_has_stable_generation() -> None:
    paths = ThemePaths.from_theme_dir(FIXTURES / "tokyo-night")
    assert load_and_normalize(paths)["generation"] == load_and_normalize(paths)["generation"]
```

- [ ] **Step 3: Run tests and verify the red state**

```bash
cd native-host
. .venv/bin/activate
pytest tests/test_color.py tests/test_theme_normalizer.py -q
```

Expected: FAIL because parser and normalizer modules do not exist.

- [ ] **Step 4: Implement foundational color parsing**

Create an immutable `Rgba(r: int, g: int, b: int, a: int = 255)` dataclass that rejects channel values outside `0..255`.

Parsing requirements:

```python
HEX_RE = re.compile(r"^#(?P<hex>[0-9a-fA-F]{3,8})$")
RGB_RE = re.compile(r"^rgba?\((?P<body>.*)\)$", re.IGNORECASE)
```

- Expand 3- and 4-digit hex one nibble at a time.
- Accept only 3, 4, 6, or 8 hex digits.
- Accept comma syntax `rgb(1, 2, 3)` and space syntax `rgb(1 2 3 / 50%)`.
- Numeric RGB channels clamp only after validating the token is a finite decimal in `0..255`; percentage channels accept `0%..100%`.
- Alpha accepts `0..1` or `0%..100%`.
- Reject mixed comma/space syntax, `calc()`, `var()`, gradients, CSS keywords, and trailing junk.
- Serialize alpha only when it is not 255.

- [ ] **Step 5: Implement active path and display-name resolution**

```python
# native-host/omarchy_theme_bridge_host/theme_loader.py
@dataclass(frozen=True, slots=True)
class ThemePaths:
    theme_dir: Path
    colors_file: Path
    name_file: Path
    light_marker: Path

    @classmethod
    def resolve(cls, home: Path, override: str | None) -> "ThemePaths":
        if override:
            return cls.from_theme_dir(Path(override).expanduser().resolve())
        current = home / ".local" / "state" / "omarchy" / "current"
        return cls(
            theme_dir=current / "theme",
            colors_file=current / "theme" / "colors.toml",
            name_file=current / "theme.name",
            light_marker=current / "theme" / "light.mode",
        )
```

`read_theme_name()` uses `theme.name` when present, strips one line, bounds it to 128 characters, and converts kebab/snake names to title case. With a test override, also accept `theme_dir/theme.name`; otherwise use the directory name.

- [ ] **Step 6: Implement Omarchy-compatible resolution and deterministic semantic roles**

Use these precedence maps:

```python
CANONICAL_ALIASES = {
    "background": ("background", "bg", "color0"),
    "dark_background": ("dark_background", "dark_bg"),
    "darker_background": ("darker_background", "darker_bg"),
    "lighter_background": ("lighter_background", "lighter_bg"),
    "foreground": ("foreground", "fg", "color7"),
    "dark_foreground": ("dark_foreground", "dark_fg"),
    "light_foreground": ("light_foreground", "light_fg"),
    "bright_foreground": ("bright_foreground", "bright_fg"),
    "red": ("red", "color1"),
    "green": ("green", "color2"),
    "yellow": ("yellow", "color3"),
    "blue": ("blue", "color4"),
    "magenta": ("magenta", "purple", "color5"),
    "cyan": ("cyan", "color6"),
}
```

Mode precedence is exact:

```python
if raw.get("mode") in {"dark", "light"}:
    mode = raw["mode"]
elif raw.get("theme_type") in {"dark", "light"}:
    mode = raw["theme_type"]
elif paths.light_marker.is_file():
    mode = "light"
elif background.r + background.g + background.b > 382:
    mode = "light"
else:
    mode = "dark"
```

Semantic derivation rules:

- `canvas` is exact resolved `background`.
- `text` is exact resolved `foreground`.
- `surfaceRaised` prefers `lighter_background`; otherwise mix `canvas` 12% toward `text`.
- `surface` mixes `canvas` 6% toward `surfaceRaised` when `lighter_background` exists, otherwise 7% toward `text`.
- `surfaceInset` prefers the valid background variant with OKLCH lightness farther from `text` than `canvas`; otherwise mix `canvas` 10% toward black in dark mode or white in light mode.
- `textStrong` prefers `bright_foreground`, then `light_foreground`, otherwise mixes `text` 18% toward white in dark mode or black in light mode.
- `textMuted` prefers `dark_foreground`, then `muted`, otherwise mixes `text` 42% toward `canvas`.
- `border` prefers `muted`, otherwise mixes `text` 72% toward `canvas`.
- `accent` prefers `accent`, then `blue`, otherwise mixes `text` 20% toward `canvas`.
- `selection` prefers `selection`, otherwise mixes `accent` 68% toward `canvas`.
- `danger`, `success`, `warning`, `info`, `magenta`, and `cyan` prefer named values; absent values are deterministic hue-preserving fallbacks derived from `accent` and checked for readable contrast.

Canonical JSON for hashing is `json.dumps(payload_without_generation, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`.

- [ ] **Step 7: Add atomic last-known-good storage tests and implementation**

```python
# native-host/tests/test_last_good.py
import json
from pathlib import Path

from omarchy_theme_bridge_host.last_good import LastGoodStore


def test_last_good_round_trip_is_atomic_and_normalized(tmp_path: Path) -> None:
    store = LastGoodStore(tmp_path / "last-good-theme.json")
    theme = {"schemaVersion": 1, "generation": "sha256:" + "a" * 64, "name": "Tokyo Night", "mode": "dark", "colors": {}, "source": {}}
    store.save(theme)
    assert store.load() == theme
    assert list(tmp_path.glob("*.tmp")) == []
    assert json.loads((tmp_path / "last-good-theme.json").read_text()) == theme
```

Implement save with a temporary file in the same directory, mode `0600`, `flush()`, `os.fsync()`, and `os.replace()`. Reject snapshots over 65,536 bytes and validate the expected theme shape before returning from `load()`.

- [ ] **Step 8: Run theme tests**

```bash
. .venv/bin/activate
pytest tests/test_color.py tests/test_theme_normalizer.py tests/test_last_good.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit theme normalization**

```bash
git add native-host/omarchy_theme_bridge_host native-host/tests
git commit -m "feat: normalize active Omarchy themes"
```

---

### Task 5: Implement the event-driven native host runtime

**Files:**
- Create: `native-host/omarchy_theme_bridge_host/watcher.py`
- Create: `native-host/omarchy_theme_bridge_host/host.py`
- Create: `native-host/omarchy_theme_bridge_host/__main__.py`
- Test: `native-host/tests/test_watcher.py`
- Test: `native-host/tests/test_host.py`

**Interfaces:**
- Produces: `InotifyWatcher(paths: ThemePaths, signal_file: Path)` with `fileno()`, `read_events()`, `rearm()`, and `close()`.
- Produces: `NativeHost.run(stdin: BinaryIO, stdout: BinaryIO) -> int`.
- Consumes: configuration, framing, normalizer, and `LastGoodStore` from Tasks 3–4.

- [ ] **Step 1: Write a failing real-inotify replacement test**

```python
# native-host/tests/test_watcher.py
import os
from pathlib import Path

import pytest

from omarchy_theme_bridge_host.theme_loader import ThemePaths
from omarchy_theme_bridge_host.watcher import InotifyWatcher

pytestmark = pytest.mark.skipif(os.name != "posix", reason="Linux inotify required")


def test_detects_atomic_active_theme_directory_replacement(tmp_path: Path) -> None:
    current = tmp_path / "current"
    theme = current / "theme"
    theme.mkdir(parents=True)
    (theme / "colors.toml").write_text('background="#000000"\nforeground="#ffffff"\n')
    paths = ThemePaths(
        theme_dir=theme,
        colors_file=theme / "colors.toml",
        name_file=current / "theme.name",
        light_marker=theme / "light.mode",
    )
    signal = tmp_path / "state" / "theme-set.signal"
    watcher = InotifyWatcher(paths, signal)

    replacement = current / "next-theme"
    replacement.mkdir()
    (replacement / "colors.toml").write_text('background="#111111"\nforeground="#eeeeee"\n')
    old = current / "old-theme"
    theme.rename(old)
    replacement.rename(theme)

    events = watcher.wait_for_events(timeout=1.0)
    assert events.reload_requested is True
    watcher.close()
```

- [ ] **Step 2: Write failing host handshake and last-good tests**

Create a subprocess harness that passes a temporary config path, theme override, state directory, and caller origin. Assert this sequence:

1. send `hello`;
2. receive `host.ready`;
3. receive `theme.snapshot`;
4. atomically replace the fixture theme;
5. receive `theme.changed` with a different generation;
6. write malformed TOML;
7. receive `theme.error` with `THEME_INVALID` and the retained generation;
8. terminate stdin and observe exit code `0`.

The harness must parse framed messages through the same `read_message()` helper rather than line-based JSON.

- [ ] **Step 3: Run watcher and host tests to verify the red state**

```bash
cd native-host
. .venv/bin/activate
pytest tests/test_watcher.py tests/test_host.py -q
```

Expected: FAIL because watcher and host modules do not exist.

- [ ] **Step 4: Implement the inotify wrapper with libc and `ctypes`**

Use exact Linux constants and structure parsing:

```python
_EVENT = struct.Struct("iIII")
IN_ATTRIB = 0x00000004
IN_CLOSE_WRITE = 0x00000008
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_DELETE_SELF = 0x00000400
IN_MOVE_SELF = 0x00000800
IN_IGNORED = 0x00008000
IN_CLOEXEC = 0x00080000
IN_NONBLOCK = 0x00000800
WATCH_MASK = IN_ATTRIB | IN_CLOSE_WRITE | IN_MOVED_FROM | IN_MOVED_TO | IN_CREATE | IN_DELETE | IN_DELETE_SELF | IN_MOVE_SELF
```

Load libc with `ctypes.CDLL(None, use_errno=True)`, set argument/result types for `inotify_init1`, `inotify_add_watch`, and `inotify_rm_watch`, and raise `OSError(ctypes.get_errno(), ...)` on `-1`.

Watch:

- `theme_dir.parent` (`current`) for `theme`, `theme.name`, and directory replacement events;
- `theme_dir` when it exists for `colors.toml`, `light.mode`, self-move, and self-delete;
- `signal_file.parent` when it exists for `theme-set.signal` writes/moves.

`read_events()` drains the nonblocking fd, parses every event, returns a bounded `WatchBatch(reload_requested: bool, rearm_requested: bool)`, and stores no raw filenames after classification.

- [ ] **Step 5: Implement a selector-driven host loop without periodic polling**

Use `selectors.DefaultSelector()` for stdin and the inotify fd. A pending filesystem event sets `reload_deadline = monotonic() + 0.075`. The next `select()` timeout is `max(0, reload_deadline - monotonic())`; when there is no pending event, timeout is `None`.

Handshake behavior:

```text
before hello: accept only hello or EOF
on valid hello: send host.ready, then theme.snapshot or a safe theme.error
on theme.reload: load immediately and publish changed only if generation differs
on ping: reply with the same bounded requestId
on filesystem burst: coalesce, re-arm when required, load once
on load failure: retain current generation and send one safe enum error per distinct error state
on EOF: close watcher and exit 0
```

Send human-readable diagnostics only to stderr. Do not include paths or source values in protocol errors.

- [ ] **Step 6: Implement the executable entry point**

```python
# native-host/omarchy_theme_bridge_host/__main__.py
from __future__ import annotations

import os
import sys
from pathlib import Path

from .config import HostConfig
from .host import NativeHost


def main() -> int:
    package_root = Path(__file__).resolve().parent.parent
    config_path = Path(os.environ.get("OMARCHY_THEME_BRIDGE_CONFIG", package_root / "config.json"))
    config = HostConfig.load(config_path)
    config.assert_caller(sys.argv)
    host = NativeHost.from_environment(config=config, home=Path.home(), environ=os.environ)
    return host.run(sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    raise SystemExit(main())
```

`OMARCHY_THEME_BRIDGE_CONFIG` is installer/fixture plumbing only; it is never controlled by a browser message.

- [ ] **Step 7: Run native runtime tests**

```bash
. .venv/bin/activate
python -m compileall -q omarchy_theme_bridge_host
pytest tests/test_watcher.py tests/test_host.py -q
```

Expected: PASS with no skipped watcher tests on Linux.

- [ ] **Step 8: Commit event-driven host runtime**

```bash
git add native-host/omarchy_theme_bridge_host native-host/tests/test_watcher.py native-host/tests/test_host.py
git commit -m "feat: watch Omarchy theme changes"
```

---

### Task 6: Add safe Chrome and Chromium installation, verification, and removal

**Files:**
- Create: `native-host/install/install.sh`
- Create: `native-host/install/uninstall.sh`
- Create: `native-host/install/verify.sh`
- Create: `native-host/install/theme-set-hook.sh`
- Test: `native-host/tests/test_installer.py`

**Interfaces:**
- Produces: `install.sh --extension-id <id> [--chrome-dir <dir>] [--chromium-dir <dir>]`.
- Produces: `verify.sh [--chrome-dir <dir>] [--chromium-dir <dir>]`.
- Produces: `uninstall.sh [--chrome-dir <dir>] [--chromium-dir <dir>]`.
- Consumes: Python package and executable entry point from Tasks 3–5.

- [ ] **Step 1: Write failing installer ownership tests**

Use a temporary `HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`, and browser directories. Tests must assert:

```python
EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop"


def test_install_is_idempotent_and_pins_both_browser_manifests(...):
    run_install()
    run_install()
    chrome = json.loads(chrome_manifest.read_text())
    chromium = json.loads(chromium_manifest.read_text())
    assert chrome == chromium
    assert chrome["name"] == "com.omarchy.theme_bridge"
    assert chrome["type"] == "stdio"
    assert chrome["allowed_origins"] == [f"chrome-extension://{EXTENSION_ID}/"]
    assert Path(chrome["path"]).is_absolute()


def test_uninstall_keeps_unrelated_hook_and_parent_directories(...):
    unrelated = home / ".config/omarchy/hooks/unrelated"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("keep")
    run_install()
    run_uninstall()
    assert unrelated.read_text() == "keep"
    assert unrelated.parent.is_dir()
```

Also assert invalid IDs, root execution, unsupported Python, unexpected symlink targets, and ownership-marker mismatch fail without deleting anything.

- [ ] **Step 2: Run installer tests and verify the red state**

```bash
cd native-host
. .venv/bin/activate
pytest tests/test_installer.py -q
```

Expected: FAIL because install scripts do not exist.

- [ ] **Step 3: Implement the unique Omarchy hook**

```bash
#!/usr/bin/env bash
set -euo pipefail
state_home=${XDG_STATE_HOME:-"$HOME/.local/state"}
dir="$state_home/omarchy-theme-bridge"
mkdir -p "$dir"
tmp=$(mktemp "$dir/.theme-set.signal.XXXXXX")
printf '%s\n' "${1:-unknown}" > "$tmp"
chmod 0600 "$tmp"
mv -f "$tmp" "$dir/theme-set.signal"
```

The host treats contents as irrelevant and does not forward the theme name. The write exists only to produce an atomic event.

- [ ] **Step 4: Implement the installer with explicit owned paths**

Installer defaults:

```bash
DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
STATE_HOME=${XDG_STATE_HOME:-"$HOME/.local/state"}
HOST_ROOT="$DATA_HOME/omarchy-theme-bridge/host"
CHROME_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
CHROMIUM_DIR="$HOME/.config/chromium/NativeMessagingHosts"
HOOK="$HOME/.config/omarchy/hooks/theme-set-omarchy-theme-bridge"
```

Requirements:

- reject effective UID `0`;
- require Linux and Python `>=3.11`;
- validate `^[a-p]{32}$`;
- resolve the repository root from the installer location;
- copy the Python package into a staging directory under `HOST_ROOT`’s parent;
- write `config.json` with mode `0600` and exact `allowedOrigin`;
- write an executable launcher with an absolute package path;
- atomically replace `HOST_ROOT` only after staging validates;
- write each browser manifest through `mktemp` + `mv`;
- write an ownership file containing exactly `omarchy-theme-bridge-v1`;
- install the uniquely named hook without touching other hooks;
- print every updated path.

Native manifest shape:

```json
{
  "name": "com.omarchy.theme_bridge",
  "description": "Read the active Omarchy theme for Omarchy Theme Bridge",
  "path": "/absolute/path/to/omarchy-theme-bridge-host",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://abcdefghijklmnopabcdefghijklmnop/"]
}
```

- [ ] **Step 5: Implement verification and ownership-bounded uninstall**

`verify.sh` checks:

- host launcher is absolute, regular, owned by the current user, and executable;
- package files are regular files, not symlinks;
- config and browser manifests parse as JSON;
- browser manifests contain the same path and exact origin;
- the hook is executable and project-owned;
- `python3 -m omarchy_theme_bridge_host` can start a self-check mode without requiring browser data.

Add `--self-check` in `__main__.py` before caller validation. It validates config, package imports, theme-path resolution, and inotify availability, prints one line to stderr, and exits `0`; it emits no native message.

`uninstall.sh` removes only:

- manifests whose `name`, launcher path, and ownership root match this installation;
- the exact unique hook when its checksum matches the installed template or it contains the ownership marker;
- `HOST_ROOT` only when its ownership file matches exactly.

Reject symlinked or unexpected targets and leave parent directories intact.

- [ ] **Step 6: Run installer tests twice and verify removal**

```bash
. .venv/bin/activate
pytest tests/test_installer.py -q
pytest tests/test_installer.py -q
```

Expected: both runs PASS.

- [ ] **Step 7: Commit installer tooling**

```bash
git add native-host/install native-host/tests/test_installer.py native-host/omarchy_theme_bridge_host/__main__.py
git commit -m "feat: install native host for Chrome and Chromium"
```

---

### Task 7: Connect the Manifest V3 service worker to the native host

**Files:**
- Create: `extension/src/background/state-store.ts`
- Create: `extension/src/background/native-connection.ts`
- Modify: `extension/src/background/service-worker.ts`
- Create: `extension/tests/helpers/fake-chrome.ts`
- Test: `extension/tests/unit/state-store.test.ts`
- Test: `extension/tests/unit/native-connection.test.ts`
- Test: `extension/tests/integration/service-worker.test.ts`

**Interfaces:**
- Produces: `BridgeStateStore.initialize(): Promise<BridgeState>`.
- Produces: `BridgeStateStore.applyHostMessage(message: HostToExtension): Promise<BridgeState>`.
- Produces: `NativeConnection.start(): void`, `requestReconnect(): Promise<void>`, and `dispose(): void`.
- Produces: storage keys `bridge.theme`, `bridge.connection`, `bridge.settings`, and `bridge.schemaVersion`.
- Consumes: shared contracts from Task 2 and host protocol from Tasks 3–5.

- [ ] **Step 1: Write failing storage initialization tests**

```ts
// extension/tests/unit/state-store.test.ts
import {beforeEach, describe, expect, it} from "vitest";
import {installFakeChrome} from "../helpers/fake-chrome";
import {BridgeStateStore} from "../../src/background/state-store";

beforeEach(() => installFakeChrome());

describe("BridgeStateStore", () => {
  it("creates safe defaults when storage is empty", async () => {
    const state = await new BridgeStateStore().initialize();
    expect(state.settings).toEqual({
      schemaVersion: 1,
      enabled: true,
      defaultMode: "adaptive",
      hostnameOverrides: {},
    });
    expect(state.theme).toBeNull();
    expect(state.connection.connected).toBe(false);
  });
});
```

The fake implements only `runtime.connectNative`, `runtime.onMessage`, `runtime.onInstalled`, `runtime.onStartup`, `storage.local`, `alarms`, `tabs`, and `scripting`. Each method records calls and supports listener dispatch.

- [ ] **Step 2: Write failing native handshake and reconnect tests**

Test exact behavior:

```ts
it("sends hello and accepts ready plus snapshot", async () => {
  const port = fakeChrome.nativePort();
  const connection = createConnection();
  connection.start();
  expect(port.postMessage).toHaveBeenCalledWith({
    type: "hello",
    protocolVersion: 1,
    extensionVersion: "0.1.0",
  });
  port.emitMessage({type: "host.ready", protocolVersion: 1, hostVersion: "0.1.0"});
  port.emitMessage({type: "theme.snapshot", theme: TOKYO_THEME});
  await flushPromises();
  expect((await store.get()).theme?.generation).toBe(TOKYO_THEME.generation);
});
```

Also test:

- invalid host messages are rejected and stored as `HOST_MESSAGE_INVALID`;
- disconnect with `chrome.runtime.lastError.message` matching missing host stores `HOST_NOT_FOUND`;
- bounded immediate retries occur at most twice in the active event;
- failure creates one alarm named `native-reconnect`;
- successful connection clears that alarm;
- alarm listener is registered at module top level;
- a duplicate generation causes no redundant storage write or broadcast.

- [ ] **Step 3: Run extension tests and verify the red state**

```bash
cd extension
npm test -- tests/unit/state-store.test.ts tests/unit/native-connection.test.ts tests/integration/service-worker.test.ts
```

Expected: FAIL because background modules do not exist.

- [ ] **Step 4: Implement storage-backed bridge state**

```ts
export interface ConnectionState {
  connected: boolean;
  hostVersion?: string;
  error?: ConnectionErrorCode;
  changedAt: number;
}

export interface BridgeState {
  schemaVersion: 1;
  theme: OmarchyTheme | null;
  settings: ExtensionSettings;
  connection: ConnectionState;
  themeError?: ThemeErrorCode;
}
```

Every public method first awaits one memoized initialization promise. Global variables cache convenience only; persisted storage is authoritative after worker restart.

`applyHostMessage()` must:

- validate through `parseHostMessage()`;
- persist complete valid themes only;
- ignore duplicate generations;
- retain theme on `theme.error`;
- never persist raw unknown data;
- return an immutable snapshot.

- [ ] **Step 5: Implement the native connection state machine**

Use `chrome.runtime.connectNative("com.omarchy.theme_bridge")` and immediately send hello. Register port listeners before posting.

Reconnect constants:

```ts
export const RECONNECT_ALARM = "native-reconnect";
export const MAX_IMMEDIATE_RETRIES = 2;
export const RECONNECT_DELAY_MINUTES = 0.5;
```

Do not use long `setTimeout()` values for delayed recovery. Use `chrome.alarms.create(RECONNECT_ALARM, {delayInMinutes: RECONNECT_DELAY_MINUTES})`.

Guard against concurrent connection attempts with one `connecting: Promise<void> | null`. On disconnect, null the port before retry. A disposed connection ignores late callbacks.

- [ ] **Step 6: Wire top-level service-worker listeners**

```ts
const store = new BridgeStateStore();
const connection = new NativeConnection(store, chrome.runtime.getManifest().version);

chrome.runtime.onInstalled.addListener(() => {
  void store.initialize().then(() => connection.requestReconnect());
});

chrome.runtime.onStartup.addListener(() => {
  void store.initialize().then(() => connection.requestReconnect());
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === RECONNECT_ALARM) {
    void connection.requestReconnect();
  }
});

void store.initialize().then(() => connection.start());
```

Add validated `state.get` and `native.reconnect` message handlers. Only extension pages may request reconnect: require `sender.id === chrome.runtime.id` and `sender.tab == null`. Content scripts receive state but cannot trigger reconnect.

- [ ] **Step 7: Run service-worker tests and build**

```bash
npm run typecheck
npm test -- tests/unit/state-store.test.ts tests/unit/native-connection.test.ts tests/integration/service-worker.test.ts
npm run build
```

Expected: PASS.

- [ ] **Step 8: Commit service-worker bridge**

```bash
git add extension/src/background extension/tests extension/src/shared
 git commit -m "feat: connect extension to Omarchy native host"
```

Remove the accidental leading space before `git commit` if your shell copies commands literally:

```bash
git add extension/src/background extension/tests extension/src/shared
git commit -m "feat: connect extension to Omarchy native host"
```

---

### Task 8: Bootstrap eligible pages and recover already-open tabs

**Files:**
- Create: `extension/src/content/bootstrap.ts`
- Modify: `extension/src/content/content-script.ts`
- Create: `extension/src/background/tab-coordinator.ts`
- Modify: `extension/src/background/service-worker.ts`
- Test: `extension/tests/unit/bootstrap.test.ts`
- Test: `extension/tests/unit/tab-coordinator.test.ts`
- Test: `extension/tests/integration/content-handshake.test.ts`

**Interfaces:**
- Produces: `applyBootstrap(theme: OmarchyTheme): void` and `removeBootstrap(): void`.
- Produces: `TabCoordinator.recoverExistingTabs(): Promise<void>`.
- Consumes: `BridgeStateStore`, `resolveSiteMode()`, and internal message contracts from Tasks 2 and 7.

- [ ] **Step 1: Write failing bootstrap tests**

```ts
// extension/tests/unit/bootstrap.test.ts
import {afterEach, describe, expect, it} from "vitest";
import {applyBootstrap, BOOTSTRAP_STYLE_ID, removeBootstrap} from "../../src/content/bootstrap";
import {TOKYO_THEME} from "../helpers/themes";

afterEach(removeBootstrap);

describe("bootstrap", () => {
  it("uses only the cached canvas and color scheme", () => {
    applyBootstrap(TOKYO_THEME);
    const style = document.getElementById(BOOTSTRAP_STYLE_ID);
    expect(style?.textContent).toContain("#1a1b26");
    expect(style?.textContent).toContain("color-scheme: dark");
    expect(style?.textContent).toContain("@media print");
    expect(style?.textContent).not.toContain("img");
  });

  it("replaces rather than duplicates the style", () => {
    applyBootstrap(TOKYO_THEME);
    applyBootstrap({...TOKYO_THEME, mode: "light"});
    expect(document.querySelectorAll(`#${BOOTSTRAP_STYLE_ID}`)).toHaveLength(1);
  });
});
```

- [ ] **Step 2: Write failing existing-tab recovery tests**

Assert only `http:` and `https:` tabs are injected; skip `chrome:`, `chrome-extension:`, `file:`, discarded tabs, and tabs without IDs. Active/visible tabs are injected before inactive tabs. A recoverable missing-receiver error triggers packaged `content/content-script.js` injection once; permission and protected-page errors are stored as bounded diagnostics without retries.

- [ ] **Step 3: Run tests and verify the red state**

```bash
cd extension
npm test -- tests/unit/bootstrap.test.ts tests/unit/tab-coordinator.test.ts tests/integration/content-handshake.test.ts
```

Expected: FAIL because bootstrap and coordinator modules do not exist.

- [ ] **Step 4: Implement the temporary canvas bootstrap**

```ts
export const BOOTSTRAP_STYLE_ID = "omarchy-theme-bridge-bootstrap";

export function applyBootstrap(theme: OmarchyTheme): void {
  const root = document.documentElement;
  if (!root) return;
  let style = document.getElementById(BOOTSTRAP_STYLE_ID) as HTMLStyleElement | null;
  if (!style) {
    style = document.createElement("style");
    style.id = BOOTSTRAP_STYLE_ID;
    root.prepend(style);
  }
  style.textContent = `
    html { background-color: ${theme.colors.canvas} !important; color-scheme: ${theme.mode}; }
    @media print { html { background-color: initial !important; color-scheme: normal; } }
  `;
}

export function removeBootstrap(): void {
  document.getElementById(BOOTSTRAP_STYLE_ID)?.remove();
}
```

This is intentionally not the renderer. It may change only the root canvas during startup.

- [ ] **Step 5: Implement the content handshake**

At `document_start`:

1. read `bridge.theme` and `bridge.settings` from `chrome.storage.local`;
2. derive the effective exact hostname for ordinary pages;
3. apply bootstrap only when enabled, mode is not Off, and a valid cached theme exists;
4. send `content.ready`;
5. accept only validated `state.apply` messages from the extension;
6. update/remove bootstrap accordingly;
7. report no URL or hostname in messages.

For `about:blank`, `data:`, and `blob:` fallback frames, use the service worker’s sender/tab context for effective mode; do not try to invent a hostname from an opaque URL.

- [ ] **Step 6: Implement visible-first recovery injection**

```ts
function isEligibleUrl(url: string | undefined): boolean {
  if (!url) return false;
  try {
    const protocol = new URL(url).protocol;
    return protocol === "http:" || protocol === "https:";
  } catch {
    return false;
  }
}
```

`recoverExistingTabs()` queries all tabs, filters eligible non-discarded tabs with IDs, sorts active tabs first, then:

- sends `state.apply`;
- when there is no receiving end, executes `content/content-script.js` through `chrome.scripting.executeScript({target: {tabId, allFrames: true}, files: [...]})`;
- sends state once after injection;
- processes inactive tabs with bounded concurrency `4`;
- never injects into protected or non-web schemes.

- [ ] **Step 7: Wire install/reload and state broadcasts**

Call `recoverExistingTabs()` after installation/update and after explicit recovery. On a new valid theme generation, query visible tabs first and send `state.apply`; inactive tabs may receive the same message afterward with bounded concurrency. Do not wake discarded tabs.

- [ ] **Step 8: Run content and recovery tests**

```bash
npm run typecheck
npm test -- tests/unit/bootstrap.test.ts tests/unit/tab-coordinator.test.ts tests/integration/content-handshake.test.ts
npm run build
```

Expected: PASS.

- [ ] **Step 9: Commit page bootstrap and recovery**

```bash
git add extension/src/content extension/src/background extension/tests
git commit -m "feat: bootstrap and recover eligible tabs"
```

---

### Task 9: Document, verify, and open PR 1 without overstating qualification

**Files:**
- Create: `docs/installation.md`
- Create: `docs/architecture.md`
- Create: `docs/privacy.md`
- Modify: `README.md`
- Create: `scripts/verify-pr1.sh`

**Interfaces:**
- Produces: one repository-level verification command and PR 1 runbook.
- Consumes: every deliverable from Tasks 1–8.

- [ ] **Step 1: Write the repository verification script**

```bash
#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

cd "$root/extension"
npm ci
npm run typecheck
npm test
npm run build

cd "$root/native-host"
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python -m compileall -q omarchy_theme_bridge_host
pytest -q
```

Make it executable and ensure it does not install the host into the real user account.

- [ ] **Step 2: Document exact developer installation**

`docs/installation.md` must include:

```bash
git clone https://github.com/fernandodamaso/Omarchy-Theme-Bridge.git
cd Omarchy-Theme-Bridge/extension
npm ci
npm run build
```

Then:

1. open `chrome://extensions` or `chromium://extensions`;
2. enable Developer mode;
3. Load unpacked from `extension/dist`;
4. copy the extension ID;
5. run `./native-host/install/install.sh --extension-id <copied-id>`;
6. run `./native-host/install/verify.sh`;
7. reload the extension;
8. inspect service-worker logs only for bounded status codes.

State clearly that PR 1 only proves theme detection, synchronization, storage, and temporary canvas bootstrap; full Adaptive styling is PR 2.

- [ ] **Step 3: Document architecture and privacy boundaries**

Include one diagram showing:

```text
Omarchy files/hook → Python host → Native Messaging → service worker → content frames
```

List every native message and explicitly state that host-bound messages contain no tab or page data. Document stdout framing-only and stderr diagnostics.

- [ ] **Step 4: Run fresh full verification**

```bash
./scripts/verify-pr1.sh
```

Expected: exit `0`; retain the complete terminal output for the PR description.

- [ ] **Step 5: Run optional local Chrome and Chromium checks only when available**

Use the installation runbook separately in Google Chrome and Chromium. Record each result as one of:

```text
PASS — command/browser/version and observed handshake
FAIL — exact bounded failure and reproduction
PENDING — environment unavailable; no inferred result
```

Do not convert missing browser or Omarchy access into PASS.

- [ ] **Step 6: Commit documentation and verifier**

```bash
git add README.md docs scripts/verify-pr1.sh
git commit -m "docs: add native bridge development runbook"
```

- [ ] **Step 7: Review the branch against PR 1 scope**

```bash
git diff --check main...HEAD
git log --oneline main..HEAD
git diff --stat main...HEAD
```

Confirm no renderer implementation, remote code, telemetry, private key, personal path, generated build output, or browser profile data is committed.

- [ ] **Step 8: Push and open Draft PR 1**

```bash
git push -u origin feat/foundation-native-bridge
```

Open a Draft PR to `main` titled:

```text
Foundation: add Omarchy native theme bridge
```

The PR description must contain:

- design/spec link;
- verification commands and fresh results;
- exact Chrome and Chromium status separately;
- privacy boundary;
- known PR 1 limitation: no Adaptive renderer yet;
- next phase: `docs/superpowers/plans/2026-09-04-renderer-semantic-mapper.md`.
