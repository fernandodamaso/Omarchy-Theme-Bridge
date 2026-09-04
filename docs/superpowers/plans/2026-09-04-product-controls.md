# Product Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver PR 3: a polished popup and options page for connection status, global pause/resume, exact-hostname Adaptive/Accent/Off overrides, degraded-page recovery, and sanitized local diagnostics.

**Architecture:** The service worker remains the only owner of privileged browser state. Extension pages send narrowly validated commands; the worker resolves the active tab and exact hostname, persists settings, broadcasts changes to matching tabs, and returns sanitized view models. Popup and options code use plain TypeScript, HTML, and CSS with no framework or remote resources.

**Tech Stack:** TypeScript, Vite, Vitest, Playwright, Chrome Manifest V3 extension pages, `chrome.storage.local`, `chrome.storage.session`, and local Blob-based diagnostic export.

**Spec:** `docs/superpowers/specs/2026-09-04-omarchy-theme-bridge-design.md`

## Global Constraints

- Begin only after PR 2 is merged; branch from updated `main` as `feat/product-controls`.
- Global default remains Adaptive; users may choose Adaptive, Accent, or Off per exact hostname.
- Global pause removes generated styles from open tabs; resume reapplies each effective mode.
- Do not add accounts, sync, telemetry, remote APIs, remote compatibility updates, or a palette editor.
- Do not request `tabs`, `downloads`, `identity`, `cookies`, `history`, `bookmarks`, or clipboard permissions.
- Popup/options must work with existing broad HTTP/HTTPS host permissions and current Manifest V3 permissions.
- Hostnames are lowercased ASCII and exact-match only.
- Content-script messages cannot trigger native reconnect, settings writes, diagnostic export, or arbitrary tab injection.
- Diagnostics exclude full URLs, query strings, page titles, DOM text, selectors, usernames, profile paths, tokens, form content, screenshots, raw CSS, and native filesystem paths.
- Hostname inclusion is opt-in for each export.
- All UI assets are packaged locally; no external font, icon, script, or stylesheet request.

---

## File Map

- `extension/src/background/settings-store.ts` — schema migration and serialized settings writes.
- `extension/src/background/renderer-status-store.ts` — bounded per-tab/frame status in `chrome.storage.session`.
- `extension/src/background/tab-coordinator.ts` — exact-hostname broadcasts, pause/resume, and explicit retry.
- `extension/src/background/service-worker.ts` — validated UI command router.
- `extension/src/shared/internal-messages.ts` — expanded request/response contracts.
- `extension/src/shared/view-models.ts` — popup/options-safe state shapes.
- `extension/src/shared/browser.ts` — browser label and eligible URL helpers.
- `extension/src/shared/diagnostics.ts` — sanitization and export contract.
- `extension/src/popup/` — current-tab status and controls.
- `extension/src/options/` — global settings, overrides, status, and diagnostics.
- `extension/tests/unit/` — state, sanitization, and UI rendering tests.
- `extension/tests/integration/` — service-worker routing and tab-update tests.
- `extension/tests/browser/controls.spec.ts` — extension-page interactions against fixture tabs.

---

### Task 1: Persist settings safely and update matching tabs immediately

**Files:**
- Create: `extension/src/background/settings-store.ts`
- Create: `extension/src/background/renderer-status-store.ts`
- Create: `extension/src/shared/view-models.ts`
- Modify: `extension/src/shared/internal-messages.ts`
- Modify: `extension/src/background/state-store.ts`
- Modify: `extension/src/background/tab-coordinator.ts`
- Modify: `extension/src/background/service-worker.ts`
- Test: `extension/tests/unit/settings-store.test.ts`
- Test: `extension/tests/unit/renderer-status-store.test.ts`
- Test: `extension/tests/integration/settings-routing.test.ts`

**Interfaces:**
- Produces: `SettingsStore.get()`, `setEnabled(enabled)`, `setHostnameMode(hostname, mode)`, and `removeHostnameOverride(hostname)`.
- Produces: `RendererStatusStore.record(sender, status)`, `getForTab(tabId)`, and `removeTab(tabId)`.
- Produces: `PopupViewModel` and `OptionsViewModel`.
- Produces: validated UI commands `popup.state.get`, `options.state.get`, `settings.enabled.set`, `site.mode.set`, `site.override.remove`, and `renderer.retry`.
- Consumes: PR 1 storage/connection state and PR 2 renderer messages.

- [ ] **Step 1: Write failing settings migration and serialized-write tests**

```ts
// extension/tests/unit/settings-store.test.ts
import {beforeEach, describe, expect, it} from "vitest";
import {installFakeChrome} from "../helpers/fake-chrome";
import {SettingsStore} from "../../src/background/settings-store";

beforeEach(() => installFakeChrome());

describe("SettingsStore", () => {
  it("migrates missing state to schema 1 defaults", async () => {
    const store = new SettingsStore();
    expect(await store.get()).toEqual({
      schemaVersion: 1,
      enabled: true,
      defaultMode: "adaptive",
      hostnameOverrides: {},
    });
  });

  it("serializes concurrent exact-hostname updates", async () => {
    const store = new SettingsStore();
    await Promise.all([
      store.setHostnameMode("YouTube.com", "accent"),
      store.setHostnameMode("github.com", "off"),
    ]);
    expect(await store.get()).toMatchObject({
      hostnameOverrides: {"youtube.com": "accent", "github.com": "off"},
    });
  });

  it("removes Adaptive overrides because Adaptive is the default", async () => {
    const store = new SettingsStore();
    await store.setHostnameMode("youtube.com", "off");
    await store.setHostnameMode("youtube.com", "adaptive");
    expect((await store.get()).hostnameOverrides).toEqual({});
  });
});
```

- [ ] **Step 2: Write failing renderer-status bounds tests**

Required assertions:

- status is keyed by `tabId:frameId` and cannot contain hostname or URL;
- only validated `renderer.status` messages from `sender.tab.id` are accepted;
- top-frame status is preferred for popup display;
- at most 512 frame records are retained, least-recently-updated first;
- `tabs.onRemoved` deletes every record for that tab;
- repeated renderer failures store only enum codes and count up to `2`.

- [ ] **Step 3: Write failing routing and broadcast tests**

Test:

1. `site.mode.set` from an extension page normalizes the hostname, persists it, and sends `state.apply` to every open non-discarded tab whose exact hostname matches.
2. `youtube.com` does not update `music.youtube.com`.
3. `settings.enabled.set(false)` sends Off-equivalent state to every eligible open tab.
4. `settings.enabled.set(true)` recalculates effective modes from current settings.
5. commands from content-script senders are rejected.
6. protected/non-HTTP tabs are skipped without retry.
7. discarded tabs are not awakened.

- [ ] **Step 4: Run tests and verify the red state**

```bash
cd extension
npm test -- tests/unit/settings-store.test.ts tests/unit/renderer-status-store.test.ts tests/integration/settings-routing.test.ts
```

Expected: FAIL because the stores and command routes do not exist.

- [ ] **Step 5: Implement serialized settings writes**

```ts
export class SettingsStore {
  #writeChain: Promise<void> = Promise.resolve();

  async get(): Promise<ExtensionSettings> {
    const stored = await chrome.storage.local.get("bridge.settings");
    return migrateSettings(stored["bridge.settings"]);
  }

  async #update(mutator: (current: ExtensionSettings) => ExtensionSettings): Promise<ExtensionSettings> {
    let result!: ExtensionSettings;
    this.#writeChain = this.#writeChain.then(async () => {
      const current = await this.get();
      result = freezeSettings(mutator(current));
      await chrome.storage.local.set({"bridge.settings": result});
    });
    await this.#writeChain;
    return result;
  }
}
```

`setHostnameMode()` removes the key when mode is `adaptive`, because Adaptive is already the fixed global default. Store at most 2,000 hostname overrides and reject writes beyond the cap with `SETTINGS_LIMIT_REACHED`.

- [ ] **Step 6: Define safe view models**

```ts
export interface PopupViewModel {
  connected: boolean;
  connectionError?: ConnectionErrorCode;
  themeError?: ThemeErrorCode;
  theme: {name: string; mode: "dark" | "light"; generation: string} | null;
  globalEnabled: boolean;
  tab: {
    eligible: boolean;
    hostname: string | null;
    effectiveMode: SiteMode | null;
    rendererState: "idle" | "active" | "degraded" | "unavailable";
    rendererMode?: "adaptive" | "accent";
    rendererError?: RendererErrorCode;
    compatibilityRuleId?: string;
  };
}

export interface OptionsViewModel {
  connected: boolean;
  connectionError?: ConnectionErrorCode;
  themeError?: ThemeErrorCode;
  theme: {name: string; mode: "dark" | "light"; generation: string} | null;
  browser: "chrome" | "chromium" | "unknown";
  extensionVersion: string;
  settings: ExtensionSettings;
}
```

The service worker may derive the hostname from `tabs.Tab.url` for local browser behavior, but it never forwards a full URL to extension pages or the native host.

- [ ] **Step 7: Implement validated UI command routing**

Require all write/reconnect/retry requests to come from extension pages:

```ts
function assertExtensionPageSender(sender: chrome.runtime.MessageSender): void {
  if (sender.id !== chrome.runtime.id || sender.tab != null) {
    throw new Error("FORBIDDEN_SENDER");
  }
}
```

`popup.state.get` resolves the active tab through `chrome.tabs.query({active: true, currentWindow: true})`, extracts only an eligible exact hostname, and combines bridge/settings/renderer status into `PopupViewModel`.

`options.state.get` returns `OptionsViewModel` without tab data.

- [ ] **Step 8: Implement exact-hostname tab broadcasts**

Add:

```ts
async broadcastHostname(hostname: string): Promise<void>
async broadcastAllEligible(): Promise<void>
async retryTab(tabId: number): Promise<void>
```

Use bounded concurrency `4`, visible tabs first, and the same eligible URL predicate from PR 1. `retryTab()` sends `renderer.retry`; if there is no receiver, perform one packaged-script recovery injection and resend.

- [ ] **Step 9: Run state and routing tests**

```bash
npm run typecheck
npm test -- tests/unit/settings-store.test.ts tests/unit/renderer-status-store.test.ts tests/integration/settings-routing.test.ts
```

Expected: PASS.

- [ ] **Step 10: Commit settings and routing**

```bash
git add extension/src/background extension/src/shared extension/tests/unit/settings-store.test.ts extension/tests/unit/renderer-status-store.test.ts extension/tests/integration/settings-routing.test.ts
git commit -m "feat: manage global and site theme modes"
```

---

### Task 2: Build the current-site popup

**Files:**
- Modify: `extension/src/popup/index.html`
- Modify: `extension/src/popup/index.ts`
- Modify: `extension/src/popup/styles.css`
- Create: `extension/src/popup/view.ts`
- Create: `extension/tests/unit/popup-view.test.ts`
- Create: `extension/tests/browser/popup.spec.ts`

**Interfaces:**
- Produces: `renderPopup(root: HTMLElement, model: PopupViewModel, actions: PopupActions): void`.
- Produces: `PopupActions` with `setMode`, `retryRenderer`, `reconnectHost`, and `openOptions`.
- Consumes: `popup.state.get`, `site.mode.set`, `renderer.retry`, and `native.reconnect` commands from Task 1.

- [ ] **Step 1: Write failing popup rendering tests**

Required states:

```ts
it("renders connected Tokyo Night state and the selected exact-site mode", () => {
  renderPopup(root, connectedModel({effectiveMode: "adaptive"}), actions);
  expect(root.querySelector("[data-status]")?.textContent).toContain("Connected");
  expect(root.textContent).toContain("Tokyo Night");
  expect(root.querySelector('[data-mode="adaptive"]')?.getAttribute("aria-pressed")).toBe("true");
});

it("renders host installation guidance without exposing a filesystem path", () => {
  renderPopup(root, missingHostModel(), actions);
  expect(root.textContent).toContain("Native host not detected");
  expect(root.textContent).not.toContain("/home/");
});
```

Also test protected tab, no active tab, global pause, light theme, degraded renderer, protocol mismatch, and keyboard activation of the segmented controls.

- [ ] **Step 2: Run popup unit tests and verify the red state**

```bash
npm test -- tests/unit/popup-view.test.ts
```

Expected: FAIL because popup view module does not exist.

- [ ] **Step 3: Implement accessible popup markup**

Use this stable structure:

```html
<main id="app" aria-live="polite">
  <header class="header">
    <div>
      <h1>Omarchy Theme Bridge</h1>
      <p id="theme-name"></p>
    </div>
    <span id="connection-status" data-status></span>
  </header>
  <section id="site-controls" aria-labelledby="site-heading">
    <h2 id="site-heading">This website</h2>
    <p id="hostname"></p>
    <div class="segmented" role="group" aria-label="Website theme mode">
      <button type="button" data-mode="adaptive" aria-pressed="false">Adaptive</button>
      <button type="button" data-mode="accent" aria-pressed="false">Accent</button>
      <button type="button" data-mode="off" aria-pressed="false">Off</button>
    </div>
  </section>
  <section id="message"></section>
  <footer>
    <button type="button" id="secondary-action"></button>
    <button type="button" id="open-settings">Settings</button>
  </footer>
</main>
```

The view must set text through `textContent`, never `innerHTML` with dynamic values.

- [ ] **Step 4: Style the popup from the active Omarchy palette**

Set CSS custom properties from the returned theme summary plus a separately fetched safe palette subset from the worker. When no theme is available, use packaged neutral fallbacks.

Requirements:

- width `360px`, minimum height `260px`;
- visible `:focus-visible` outline;
- 44px minimum interactive target height;
- selected segment uses accent and a contrast-checked label;
- no animations when `prefers-reduced-motion: reduce`;
- connection status is never color-only: include text and icon shape;
- no remote fonts or SVG URLs.

- [ ] **Step 5: Wire popup actions with a single busy state**

On startup:

```ts
const model = await chrome.runtime.sendMessage({type: "popup.state.get"});
renderPopup(document.querySelector("#app")!, model, actions);
```

For a mode button:

1. disable all mode controls;
2. send `{type: "site.mode.set", hostname, mode}`;
3. fetch a fresh popup model;
4. rerender;
5. restore controls even on bounded error.

Do not optimistically claim the renderer applied before a fresh status snapshot.

- [ ] **Step 6: Add Playwright popup behavior tests**

Open a fixture tab, then open `chrome-extension://<id>/popup/index.html` directly in the test context. Seed worker state and assert:

- current hostname appears without path/query;
- Adaptive is selected initially;
- clicking Accent updates storage and fixture rendering;
- clicking Off restores fixture presentation;
- a degraded state exposes `Try again`, `Use Accent`, and `Turn off here`;
- protected-page model disables site controls.

- [ ] **Step 7: Run popup tests and build**

```bash
npm run typecheck
npm test -- tests/unit/popup-view.test.ts
npm run build
npm run test:browser -- tests/browser/popup.spec.ts
```

Expected: PASS.

- [ ] **Step 8: Commit popup UX**

```bash
git add extension/src/popup extension/tests/unit/popup-view.test.ts extension/tests/browser/popup.spec.ts
git commit -m "feat: add current-site theme controls"
```

---

### Task 3: Build the global options page and override manager

**Files:**
- Modify: `extension/src/options/index.html`
- Modify: `extension/src/options/index.ts`
- Modify: `extension/src/options/styles.css`
- Create: `extension/src/options/view.ts`
- Create: `extension/src/options/override-list.ts`
- Create: `extension/tests/unit/options-view.test.ts`
- Create: `extension/tests/unit/override-list.test.ts`
- Create: `extension/tests/browser/options.spec.ts`

**Interfaces:**
- Produces: `renderOptions(root, model, actions)`.
- Produces: pure `filterOverrides(overrides, query)` and `sortOverrides(overrides)`.
- Consumes: options/settings commands from Task 1.

- [ ] **Step 1: Write failing pure override-list tests**

```ts
it("filters ASCII hostnames case-insensitively and sorts them", () => {
  const overrides = {"youtube.com": "accent", "github.com": "off"} as const;
  expect(filterOverrides(overrides, "HUB")).toEqual([
    {hostname: "github.com", mode: "off"},
  ]);
  expect(filterOverrides(overrides, "")).toEqual([
    {hostname: "github.com", mode: "off"},
    {hostname: "youtube.com", mode: "accent"},
  ]);
});
```

Also test 2,000-item rendering uses pagination of 100 rows rather than placing all rows into the DOM.

- [ ] **Step 2: Write failing options rendering tests**

Assert four visible sections with exact headings:

```text
Status
Defaults
Site overrides
Diagnostics
```

Test connected/disconnected state, global enable checkbox, zero overrides, filtered overrides, mode change, deletion, and protocol mismatch.

- [ ] **Step 3: Run tests and verify the red state**

```bash
npm test -- tests/unit/options-view.test.ts tests/unit/override-list.test.ts
```

Expected: FAIL because options modules do not exist.

- [ ] **Step 4: Implement the options document structure**

Use semantic `<main>`, `<section>`, `<h1>`, `<h2>`, `<label>`, `<table>`, and `<button>` elements. The overrides table columns are `Website`, `Mode`, and `Actions`.

The global control is a real checkbox:

```html
<label class="switch-row">
  <span>
    <strong>Theme websites</strong>
    <small>Pause or resume generated styles on regular websites.</small>
  </span>
  <input id="global-enabled" type="checkbox">
</label>
```

No custom switch may hide the native input from keyboard or screen-reader users.

- [ ] **Step 5: Implement override search, mode update, and removal**

Use event delegation on the table body. Dynamic hostnames are assigned with `textContent` and `data-hostname` after validation.

Changing an override sends `site.mode.set`; choosing Adaptive removes the stored override and row after a fresh model fetch. Remove sends `site.override.remove`.

Search is local, debounced by 100 ms, and never persisted or logged.

- [ ] **Step 6: Implement global pause/resume status**

Changing the checkbox sends `settings.enabled.set`. While paused:

- preserve hostname overrides in storage;
- show `Paused` in Status;
- disable no override editing controls;
- worker broadcasts Off-equivalent state;
- resume reapplies each stored override.

- [ ] **Step 7: Add browser tests**

Assert:

- pausing removes renderer output in two open fixture tabs;
- resuming restores Adaptive and Accent according to each exact override;
- editing `youtube.com` does not affect `music.youtube.com` fixture host aliases;
- deleting an override returns it to Adaptive;
- search never exposes path/query because only exact hostnames exist in the model.

- [ ] **Step 8: Run options tests and build**

```bash
npm run typecheck
npm test -- tests/unit/options-view.test.ts tests/unit/override-list.test.ts
npm run build
npm run test:browser -- tests/browser/options.spec.ts
```

Expected: PASS.

- [ ] **Step 9: Commit options UX**

```bash
git add extension/src/options extension/tests/unit/options-view.test.ts extension/tests/unit/override-list.test.ts extension/tests/browser/options.spec.ts
git commit -m "feat: add global settings and site overrides"
```

---

### Task 4: Add sanitized diagnostics, onboarding, and degraded recovery

**Files:**
- Create: `extension/src/shared/diagnostics.ts`
- Create: `extension/src/options/diagnostics.ts`
- Modify: `extension/src/shared/internal-messages.ts`
- Modify: `extension/src/background/service-worker.ts`
- Modify: `extension/src/content/renderer-controller.ts`
- Modify: `extension/src/popup/view.ts`
- Modify: `extension/src/options/view.ts`
- Test: `extension/tests/unit/diagnostics.test.ts`
- Test: `extension/tests/integration/degraded-recovery.test.ts`
- Test: `extension/tests/browser/onboarding.spec.ts`

**Interfaces:**
- Produces: `createDiagnostics(model, options): DiagnosticsExport`.
- Produces: `downloadDiagnostics(exportValue): void` using an extension-page Blob URL.
- Produces: `renderer.retry` lifecycle with a maximum of two automatic failures per navigation.
- Consumes: connection, theme, settings, and renderer status from earlier tasks.

- [ ] **Step 1: Write a diagnostics denylist test**

```ts
const serialized = JSON.stringify(createDiagnostics(inputContainingUnsafeFields, {includeHostname: false}));
for (const forbidden of [
  "https://",
  "?token=",
  "Page title",
  "/home/fernando",
  "document.cookie",
  "rawStylesheet",
  "username",
]) {
  expect(serialized).not.toContain(forbidden);
}
expect(serialized).not.toContain("youtube.com");
```

With `includeHostname: true`, include only validated `hostname`, never URL/path/query.

Expected shape:

```ts
export interface DiagnosticsExport {
  schemaVersion: 1;
  generatedAt: string;
  extensionVersion: string;
  browser: "chrome" | "chromium" | "unknown";
  nativeHostConnected: boolean;
  connectionError?: ConnectionErrorCode;
  themeName?: string;
  themeMode?: "dark" | "light";
  themeGeneration?: string;
  globalEnabled: boolean;
  siteMode?: SiteMode;
  rendererState?: "idle" | "active" | "degraded" | "unavailable";
  rendererError?: RendererErrorCode;
  compatibilityRuleId?: string;
  hostname?: string;
}
```

- [ ] **Step 2: Write failing degraded recovery tests**

Assert:

- first render failure reports degraded but allows one explicit retry;
- two consecutive failures in one content-script lifetime suppress automatic loops;
- `renderer.retry` creates a fresh generation attempt once;
- `Use Accent` persists Accent for the exact hostname;
- `Turn off here` persists Off;
- navigation creates a new controller and resets the per-navigation failure count;
- failure status contains enum only, not exception message/stack/CSS.

- [ ] **Step 3: Run tests and verify the red state**

```bash
npm test -- tests/unit/diagnostics.test.ts tests/integration/degraded-recovery.test.ts
```

Expected: FAIL because diagnostics and recovery routes do not exist.

- [ ] **Step 4: Implement pure diagnostics sanitization**

Construct a new object from allowed fields only; never spread input state. Bound every string to 128 characters and validate generation, rule ID, and hostname formats.

`generatedAt` is `new Date().toISOString()`. Do not include timestamps from browsing events beyond this export time.

- [ ] **Step 5: Implement local download without `downloads` permission**

```ts
export function downloadDiagnostics(value: DiagnosticsExport): void {
  const blob = new Blob([`${JSON.stringify(value, null, 2)}\n`], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "omarchy-theme-bridge-diagnostics.json";
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
```

The options page shows an unchecked `Include this exact hostname` checkbox only when opened with an eligible active tab context.

- [ ] **Step 6: Implement bounded degraded recovery**

`RendererController` tracks `consecutiveFailures` in memory. It reports only:

```ts
{type: "renderer.status", state: "degraded", errorCode, retainedGeneration}
```

It never auto-retries after two failures. Explicit retry aborts stale work, cleans incomplete resources, and attempts once. Successful commit resets the count.

- [ ] **Step 7: Implement onboarding and connection-specific guidance**

Map bounded errors to exact user actions:

```text
HOST_NOT_FOUND → Native host not detected; open Installation instructions; Check connection
CALLER_FORBIDDEN → Re-run installer with this extension ID
PROTOCOL_MISMATCH → Update extension and native host together
THEME_NOT_FOUND → Activate an Omarchy theme and retry
THEME_INVALID / THEME_UNSUPPORTED_COLOR → Previous valid theme retained; inspect colors.toml locally
HOST_DISCONNECTED → Cached theme retained; Reconnect
```

Do not render a local path, exception, or raw host error.

- [ ] **Step 8: Add onboarding browser tests**

Seed each bounded error and verify popup/options copy, available action, absence of unsafe values, and no false `Connected` or `Theme applied successfully` message.

- [ ] **Step 9: Run diagnostics and onboarding checks**

```bash
npm run typecheck
npm test -- tests/unit/diagnostics.test.ts tests/integration/degraded-recovery.test.ts
npm run build
npm run test:browser -- tests/browser/onboarding.spec.ts
```

Expected: PASS.

- [ ] **Step 10: Commit diagnostics and recovery**

```bash
git add extension/src extension/tests/unit/diagnostics.test.ts extension/tests/integration/degraded-recovery.test.ts extension/tests/browser/onboarding.spec.ts
git commit -m "feat: add safe diagnostics and recovery states"
```

---

### Task 5: Verify product controls, document behavior, and open PR 3

**Files:**
- Modify: `README.md`
- Modify: `docs/installation.md`
- Modify: `docs/privacy.md`
- Modify: `docs/compatibility.md`
- Create: `docs/settings.md`
- Create: `scripts/verify-pr3.sh`

**Interfaces:**
- Produces: user-facing control documentation and one deterministic PR 3 verification command.
- Consumes: Tasks 1–4.

- [ ] **Step 1: Document exact control semantics**

`docs/settings.md` must state:

```text
Adaptive: full interface semantic mapping; media/content preserved
Accent: original page foundation; interaction accents only
Off: generated styles removed for that exact hostname
Global pause: temporary Off-equivalent behavior everywhere; overrides retained
```

Explain exact-hostname matching with the `youtube.com` versus `music.youtube.com` example.

- [ ] **Step 2: Document privacy and diagnostics**

List every exported field and every excluded category. Explain hostname opt-in and local Blob download. State there is no telemetry, account, sync, remote API, or remote rule source.

- [ ] **Step 3: Add full PR 3 verification script**

```bash
#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root/extension"
npm ci
npm run vendor:check
npm run typecheck
npm test
npm run build
npm run test:browser
```

- [ ] **Step 4: Run fresh verification**

```bash
./scripts/verify-pr3.sh
```

Expected: exit `0`; retain complete output.

- [ ] **Step 5: Perform local popup/options smoke checks when available**

In Chrome and Chromium separately:

1. verify connected theme name/mode;
2. switch one fixture or ordinary site Adaptive → Accent → Off;
3. verify all matching exact-hostname tabs update;
4. pause globally and resume;
5. export diagnostics without hostname, inspect JSON;
6. export with hostname, verify no path/query/title;
7. trigger or simulate a degraded state and use each recovery action.

Record PASS, FAIL, or PENDING per browser. Missing local access remains PENDING.

- [ ] **Step 6: Commit documentation and verifier**

```bash
git add README.md docs scripts/verify-pr3.sh
git commit -m "docs: explain extension controls and diagnostics"
```

- [ ] **Step 7: Review scope and open Draft PR 3**

```bash
git diff --check main...HEAD
git log --oneline main..HEAD
git diff --stat main...HEAD
git push -u origin feat/product-controls
```

Open a Draft PR to `main` titled:

```text
Controls: manage website modes and bridge status
```

Include fresh automated results, separate Chrome/Chromium status, permission diff proving no new sensitive permission, diagnostics privacy evidence, known compatibility limitations, and next plan path `docs/superpowers/plans/2026-09-04-compatibility-qualification.md`.
