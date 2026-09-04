# Compatibility and Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver PR 4 and qualify the Developer MVP with the complete deterministic fixture matrix, bundled YouTube and GitHub compatibility rules, performance/leak/security gates, truthful Chrome/Chromium runbooks, and final documentation.

**Architecture:** Compatibility remains declarative and bundled. Deterministic local fixtures model difficult browser behaviors; live YouTube and GitHub are manual smoke targets rather than the automated specification. Qualification separates automated evidence from local browser/Omarchy evidence and leaves unavailable checks explicitly pending.

**Tech Stack:** TypeScript, Vite, Vitest, Playwright, Chrome DevTools Protocol for bounded diagnostics, pytest, shell verification, Manifest V3.

**Spec:** `docs/superpowers/specs/2026-09-04-omarchy-theme-bridge-design.md`

## Global Constraints

- Begin only after PR 3 is merged; branch from updated `main` as `feat/compatibility-qualification`.
- Compatibility rules are packaged, declarative, schema-validated, selector-based, and covered by tests.
- Do not download remote rules or execute site-provided configuration.
- User-selected Adaptive, Accent, or Off always overrides bundled compatibility behavior.
- Preserve media, authored content, charts/data series, maps, canvas/WebGL/WebGPU, QR/barcodes/CAPTCHA, and color-sensitive design surfaces.
- Closed Shadow DOM, browser internal pages, the built-in PDF viewer, and media/canvas recoloring remain unsupported.
- Do not claim a live site, browser, Omarchy environment, performance number, accessibility result, or privacy result that was not actually tested.
- Record Chrome and Chromium evidence separately as PASS, FAIL, or PENDING.
- No final completion claim is allowed until the complete verification command and acceptance checklist have fresh evidence.

---

## File Map

- `extension/tests/fixtures/light-article/` — typography and neutral hierarchy.
- `extension/tests/fixtures/dark-dashboard/` — nested surfaces, statuses, charts.
- `extension/tests/fixtures/media-feed/` — thumbnails, avatars, video, metadata.
- `extension/tests/fixtures/forms/` — controls, disabled, validation, focus, autofill-like states.
- `extension/tests/fixtures/spa-feed/` — route changes, mutation bursts, virtualization.
- `extension/tests/fixtures/shadow-dom/` — open/closed roots and adopted stylesheets.
- `extension/tests/fixtures/frames/` — same-origin, cross-origin, about:blank, blob, and sandbox cases.
- `extension/tests/fixtures/css-torture/` — variables, alpha, gradients, shadows, filters, blend modes, pseudo-elements, top layer.
- `extension/tests/fixtures/editor/` — themed app chrome with preserved authored body and color swatches.
- `extension/tests/fixtures/youtube-like/` — stable structural target for YouTube rule tests.
- `extension/tests/fixtures/github-like/` — stable structural target for GitHub rule tests.
- `extension/src/compat/sites/youtube.ts` — YouTube rule.
- `extension/src/compat/sites/github.ts` — GitHub rule.
- `extension/src/compat/rules.ts` — ordered bundled registry.
- `extension/src/renderer/debug-counters.ts` — test-build-only bounded lifecycle counters.
- `extension/tests/browser/` — matrix, site-rule, accessibility, performance, and lifecycle tests.
- `extension/tests/security/` — static policy and manifest checks.
- `docs/smoke/youtube.md` — live YouTube runbook.
- `docs/smoke/github.md` — live GitHub runbook.
- `docs/troubleshooting.md` — bounded failure guidance.
- `docs/limitations.md` — explicit unsupported/partial cases.
- `docs/qualification.md` — evidence table and final acceptance mapping.
- `scripts/verify-mvp.sh` — complete repository gate.

---

### Task 1: Complete the deterministic browser fixture matrix

**Files:**
- Create: `extension/tests/fixtures/light-article/**`
- Create: `extension/tests/fixtures/dark-dashboard/**`
- Create: `extension/tests/fixtures/media-feed/**`
- Create: `extension/tests/fixtures/forms/**`
- Create: `extension/tests/fixtures/spa-feed/**`
- Create: `extension/tests/fixtures/shadow-dom/**`
- Create: `extension/tests/fixtures/frames/**`
- Create: `extension/tests/fixtures/css-torture/**`
- Create: `extension/tests/fixtures/editor/**`
- Create: `extension/tests/browser/fixture-matrix.spec.ts`
- Create: `extension/tests/browser/shadow-frames.spec.ts`
- Create: `extension/tests/browser/forced-colors-print.spec.ts`
- Modify: `extension/tests/fixtures/server.ts`
- Modify: `extension/playwright.config.ts`

**Interfaces:**
- Produces: deterministic routes `/light-article`, `/dark-dashboard`, `/media-feed`, `/forms`, `/spa-feed`, `/shadow-dom`, `/frames`, `/css-torture`, and `/editor`.
- Produces: a second local origin for cross-origin frame tests.
- Consumes: extension test context and renderer delivered by PRs 1–3.

- [ ] **Step 1: Define one machine-readable expectation file per fixture**

Each fixture includes `expectations.json` with only stable IDs and policies:

```json
{
  "themed": ["canvas", "surface", "primary-text", "muted-text", "accent-control"],
  "preserved": ["photo", "video", "chart", "authored-content"],
  "layoutStable": ["canvas", "surface", "accent-control"]
}
```

Tests load these files instead of duplicating selector lists in test code.

- [ ] **Step 2: Implement the light article fixture**

Include:

- white canvas and two neutral surface depths;
- body text, heading, muted metadata, link, blockquote, code block;
- a decorative high-chroma brand badge that should remain unchanged;
- pseudo-element quote mark;
- print stylesheet.

Assert Adaptive maps neutral hierarchy, keeps the brand badge, preserves layout, and disables generated theming during print media.

- [ ] **Step 3: Implement the dark dashboard fixture**

Include:

- existing dark canvas with nested panels;
- red error, green success, yellow warning, blue information states;
- an SVG chart with themed axes and preserved series marked by explicit compatibility selectors;
- dialog, tooltip, and page-owned popover;
- backdrop blur over a neutral surface.

Assert the page is retinted rather than darkened twice and semantic states remain pairwise distinguishable by delta-E and text label.

- [ ] **Step 4: Implement the media feed fixture**

Include fixed PNG/SVG thumbnails, avatars, `<picture>`, `<video poster>`, inline UI SVG, external SVG image, and metadata text. Store SHA-256 or exact pixel baselines for media crops.

Assert:

- no `filter`, `mix-blend-mode`, or opacity override is applied to media;
- every preserved crop is pixel-identical between Off and Adaptive;
- inline monochrome toolbar SVG follows text/accent;
- logo/illustration SVG remains unchanged.

- [ ] **Step 5: Implement the forms fixture**

Include text/search/email inputs, textarea, select, checkbox, radio, range, progress, date, time, color input, disabled controls, placeholder, invalid/valid states, and a simulated autofill class plus `:-webkit-autofill` stylesheet.

Assert readable foreground/background, visible `:focus-visible`, exact color swatch preservation, disabled distinction, and Accent-only behavior.

- [ ] **Step 6: Implement SPA and virtualized-list fixtures**

The fixture must:

- replace route-root content with `history.pushState()`;
- append 1,000 logical items through a 20-row virtual window;
- inject and replace `<style>` elements;
- update CSS variables;
- issue a burst of 200 irrelevant text mutations.

Assert only visible shared styles are transformed, generated style count remains bounded, irrelevant text mutations do not create theme work, and route updates theme within 500 ms.

- [ ] **Step 7: Implement open/closed Shadow DOM fixtures**

Create:

- an open shadow root with ordinary `<style>`;
- an open shadow root using `adoptedStyleSheets`;
- a nested open root;
- a closed root with a test-only host screenshot target.

Assert open roots are themed, adopted stylesheet changes propagate, nested open roots are handled, and the closed root remains original without an exception or monkey-patched `attachShadow()` override.

- [ ] **Step 8: Implement frame fixtures on two local origins**

Cover:

- same-origin iframe;
- cross-origin HTTP iframe on the second server;
- `about:blank` child written by the parent;
- `blob:` frame;
- sandboxed frame without script permission;
- inaccessible/protected-frame simulation.

Assert permitted frames theme independently, opaque fallback frames receive state only when Chrome’s declared matching allows it, and sandbox/protected failures remain bounded and do not trigger repeated injection.

- [ ] **Step 9: Implement CSS torture and editor fixtures**

CSS torture includes:

- nested CSS variables and variable replacement;
- hex, rgb/rgba, hsl/hsla, transparent alpha;
- supported gradients and box/text shadows;
- unsupported `color-mix()`/wide-gamut values that must be preserved when the vendored parser cannot safely map them;
- `mix-blend-mode`, masks, filters, pseudo-elements, top-layer dialog/popover;
- `@media print` and forced-colors styles.

Editor includes themed toolbar/sidebar/dialogs plus a preserved `contenteditable` authored body, canvas preview, and exact color swatches.

- [ ] **Step 10: Write fixture-matrix tests**

For every route and each of these palettes/modes:

```text
Tokyo Night dark + Adaptive
warm dark + Adaptive
light palette + Adaptive
low-contrast palette + Adaptive
Tokyo Night dark + Accent
Tokyo Night dark + Off
```

Verify computed tokens, layout boxes within one CSS pixel, preserved media pixels, focus visibility, Off restoration, and absence of duplicate generated style roots.

- [ ] **Step 11: Test forced-colors and print behavior**

Use Playwright `page.emulateMedia({forcedColors: "active"})` where supported and `page.emulateMedia({media: "print"})`.

Expected:

- forced-colors removes/does not apply project-generated colors and leaves system colors authoritative;
- print removes generated page theming;
- returning to screen/forced-colors none restores the current generation without a reload.

- [ ] **Step 12: Run the complete deterministic matrix**

```bash
cd extension
npm run build
npm run test:browser -- \
  tests/browser/fixture-matrix.spec.ts \
  tests/browser/shadow-frames.spec.ts \
  tests/browser/forced-colors-print.spec.ts
```

Expected: PASS.

- [ ] **Step 13: Commit the fixture laboratory**

```bash
git add extension/tests extension/playwright.config.ts
git commit -m "test: cover difficult website rendering cases"
```

---

### Task 2: Add and validate the YouTube compatibility rule

**Files:**
- Create: `extension/src/compat/sites/youtube.ts`
- Modify: `extension/src/compat/rules.ts`
- Create: `extension/tests/fixtures/youtube-like/index.html`
- Create: `extension/tests/fixtures/youtube-like/styles.css`
- Create: `extension/tests/unit/youtube-rule.test.ts`
- Create: `extension/tests/browser/youtube-rule.spec.ts`
- Create: `docs/smoke/youtube.md`

**Interfaces:**
- Produces: bundled rule ID `youtube` matching `youtube.com` and `*.youtube.com`.
- Consumes: compatibility schema and rule translation from PR 2.

- [ ] **Step 1: Build a stable YouTube-like structural fixture**

Model only interface archetypes, not copied live content:

```html
<aside id="guide-content">
  <a class="guide-entry" aria-current="page">Home</a>
</aside>
<header id="masthead-container">
  <div id="search"></div>
  <div id="logo"><svg role="img" aria-label="YouTube logo"></svg></div>
</header>
<nav id="chips">
  <button aria-selected="true">All</button>
</nav>
<main id="contents">
  <article class="video-card">
    <div class="thumbnail"><img alt="video thumbnail"></div>
    <img class="avatar" alt="channel avatar">
    <h3 class="title">Title</h3>
    <p id="metadata-line">Metadata</p>
  </article>
</main>
<div id="movie_player"><video></video><div class="ytp-play-progress"></div></div>
```

Use fixed media assets with exact pixel baselines.

- [ ] **Step 2: Write failing rule-schema and visual tests**

Assert:

- rule validates and is selected for `youtube.com`, `www.youtube.com`, and `music.youtube.com`;
- it does not match `notyoutube.com`;
- page/masthead/sidebar/menu/chips follow Omarchy neutral surfaces;
- selected navigation/chip uses accent/selection;
- titles and metadata map to primary/muted text;
- thumbnail, avatar, logo, video, and playback/progress branding remain pixel/color unchanged;
- route/mutation-added video cards theme without reload;
- Accent keeps YouTube’s original base background.

- [ ] **Step 3: Implement the YouTube rule**

```ts
export const YOUTUBE_RULE: CompatibilityRule = {
  id: "youtube",
  matches: ["youtube.com", "*.youtube.com"],
  preserve: [
    "ytd-thumbnail img",
    "yt-img-shadow img",
    "#movie_player",
    "#movie_player video",
    ".html5-video-container",
    ".ytp-play-progress",
    ".ytp-swatch-background-color",
  ],
  preserveUserContent: [
    "ytd-comments #content-text",
    "yt-live-chat-text-message-renderer #message",
  ],
  canvas: ["ytd-app", "#page-manager"],
  surface: [
    "#masthead-container",
    "#guide-content",
    "ytd-multi-page-menu-renderer",
    "tp-yt-paper-dialog",
    "ytd-popup-container",
  ],
  text: ["#video-title", "#title", "#content-text"],
  mutedText: ["#metadata-line", "#metadata", "#byline"],
  accent: [
    "[aria-current='page']",
    "[aria-selected='true']",
    "yt-chip-cloud-chip-renderer[chip-style='STYLE_DEFAULT_SELECTED']",
  ],
  preserveInlineSvg: [
    "ytd-topbar-logo-renderer svg",
    "#logo-icon",
  ],
  themeInlineSvg: [
    "button svg:not([role='img'])",
    "yt-icon-button svg:not([role='img'])",
  ],
};
```

If a selector proves obsolete in the live smoke check, update the rule and fixture together only when the selector still expresses a stable semantic boundary. Do not add brittle generated class names.

- [ ] **Step 4: Register rules in deterministic specificity order**

`getCompatibilityRule()` combines `generic` with all matching site rules. Exact hostname rules sort before wildcard rules; later rule arrays append and deduplicate. User mode still wins.

- [ ] **Step 5: Run automated YouTube-rule tests**

```bash
npm run typecheck
npm test -- tests/unit/youtube-rule.test.ts
npm run build
npm run test:browser -- tests/browser/youtube-rule.spec.ts
```

Expected: PASS.

- [ ] **Step 6: Write the live YouTube smoke runbook**

`docs/smoke/youtube.md` records:

```text
Date/time
Browser and exact version
Extension commit
Native-host version
Omarchy version/commit when known
Active theme name and mode
Global state and site mode
```

Checks:

1. home page canvas, sidebar, masthead, search, chips, titles, metadata, menus;
2. thumbnails, avatars, logo, Shorts/media, and video pixels unchanged;
3. video watch page and theater/fullscreen controls;
4. comments and live chat authored text remain usable;
5. infinite scroll and SPA navigation;
6. theme switch without reload;
7. Adaptive → Accent → Off restoration;
8. no persistent console errors or repeated generated styles.

Result must be PASS, FAIL with reproduction, or PENDING.

- [ ] **Step 7: Commit the YouTube rule**

```bash
git add extension/src/compat extension/tests docs/smoke/youtube.md
git commit -m "feat: add YouTube compatibility policy"
```

---

### Task 3: Add and validate the GitHub compatibility rule

**Files:**
- Create: `extension/src/compat/sites/github.ts`
- Modify: `extension/src/compat/rules.ts`
- Create: `extension/tests/fixtures/github-like/index.html`
- Create: `extension/tests/fixtures/github-like/styles.css`
- Create: `extension/tests/unit/github-rule.test.ts`
- Create: `extension/tests/browser/github-rule.spec.ts`
- Create: `docs/smoke/github.md`

**Interfaces:**
- Produces: bundled rule ID `github` matching `github.com` and `*.github.com` where ordinary page injection is allowed.
- Consumes: compatibility registry and mapper.

- [ ] **Step 1: Build a stable GitHub-like fixture**

Include:

- global header, repository tabs, sidebar, issue/PR cards, labels, buttons, dialog;
- avatar and repository social preview image;
- code table with line numbers and syntax token classes;
- Markdown body with image and code block;
- language bar, contribution graph, status checks, and diff additions/deletions.

Use stable semantic attributes such as `data-testid`, `aria-current`, and class names owned by the fixture.

- [ ] **Step 2: Write failing rule and browser tests**

Assert:

- neutral GitHub application surfaces retint to Omarchy;
- selected repository navigation and focus use accent;
- muted metadata remains readable;
- success/failure/warning status meaning is retained;
- avatars, Markdown images, social previews, language colors, contribution cells, and graph/data-series colors remain unchanged;
- code/diff syntax remains distinguishable and line layout remains stable;
- dialogs and dynamically inserted timeline items theme;
- Accent and Off behave correctly.

- [ ] **Step 3: Implement the GitHub rule**

```ts
export const GITHUB_RULE: CompatibilityRule = {
  id: "github",
  matches: ["github.com", "*.github.com"],
  preserve: [
    "img.avatar",
    ".avatar img",
    ".markdown-body img",
    ".social-count img",
    ".js-calendar-graph",
    ".ContributionCalendar-grid",
    ".repository-lang-stats-graph",
    "[data-testid='language-color']",
    "canvas",
  ],
  preserveUserContent: [
    ".markdown-body",
    ".comment-body",
    ".js-comment-body",
  ],
  canvas: ["html", "body", ".application-main"],
  surface: [
    ".Header",
    ".AppHeader",
    ".Box",
    ".Overlay",
    "[role='dialog']",
    "[data-component='Dialog']",
  ],
  text: [".Link--primary", "[data-component='Text']:not(.color-fg-muted)"],
  mutedText: [".color-fg-muted", ".text-small"],
  accent: [
    "[aria-current='page']",
    "[aria-selected='true']",
    ".UnderlineNav-item.selected",
  ],
  preserveInlineSvg: [
    "svg[aria-label*='contribution']",
    "svg[aria-label*='language']",
  ],
  themeInlineSvg: [
    "button svg:not([role='img'])",
    "a svg:not([role='img'])",
  ],
};
```

Because `.markdown-body` includes both authored text and interface-like code surfaces, compatibility translation must preserve authored colors/media without suppressing neutral container styling. Implement this through generated descendant exclusions for color-sensitive children rather than placing the entire `.markdown-body` in Dark Reader’s `ignoreInlineStyle` list.

- [ ] **Step 4: Add explicit code/diff semantic tests**

Verify at least six syntax token categories remain distinguishable after Adaptive. Verify additions and deletions retain green/red meaning and readable text. Do not require exact original token hex values unless marked as authored/preserved data.

- [ ] **Step 5: Run automated GitHub-rule tests**

```bash
npm run typecheck
npm test -- tests/unit/github-rule.test.ts
npm run build
npm run test:browser -- tests/browser/github-rule.spec.ts
```

Expected: PASS.

- [ ] **Step 6: Write the live GitHub smoke runbook**

Check:

1. dashboard and repository pages;
2. issues/PR timeline, labels, status checks, menus, overlays;
3. code view, diffs, line selection, syntax distinction;
4. Markdown images, avatars, contribution graph, language bar preserved;
5. dynamic Turbo/SPA navigation;
6. theme switch without reload;
7. Adaptive → Accent → Off;
8. no persistent console errors or generated-style growth.

Record browser/theme/version data and PASS, FAIL, or PENDING exactly as in the YouTube runbook.

- [ ] **Step 7: Commit the GitHub rule**

```bash
git add extension/src/compat extension/tests docs/smoke/github.md
git commit -m "feat: add GitHub compatibility policy"
```

---

### Task 4: Add performance, leak, security, and lifecycle qualification gates

**Files:**
- Create: `extension/src/renderer/debug-counters.ts`
- Modify: `extension/src/content/renderer-controller.ts`
- Modify: `extension/scripts/build.ts`
- Create: `extension/tests/browser/performance.spec.ts`
- Create: `extension/tests/browser/lifecycle-leak.spec.ts`
- Create: `extension/tests/security/manifest.test.ts`
- Create: `extension/tests/security/runtime-source.test.ts`
- Create: `extension/tests/security/diagnostics-boundary.test.ts`
- Create: `native-host/tests/test_security_boundaries.py`
- Create: `scripts/check-runtime-source.sh`

**Interfaces:**
- Produces: test-build-only `debug.renderer.stats` command with numeric counters, no page data.
- Produces: static security checks and repeatable lifecycle budgets.
- Consumes: complete extension and native host.

- [ ] **Step 1: Add a compile-time test-build flag**

`extension/scripts/build.ts` reads `OMARCHY_THEME_BRIDGE_TEST_BUILD === "1"` and defines `__OTB_TEST_BUILD__` as a boolean literal. Production/default builds define false.

When false, Vite must tree-shake the debug message listener and counters. Add a build test that greps production output for `debug.renderer.stats` and expects no match.

- [ ] **Step 2: Implement bounded debug counters without content capture**

```ts
export interface RendererDebugCounters {
  activeGeneration: string | null;
  styleManagers: number;
  generatedStyleElements: number;
  openShadowRoots: number;
  pendingMutationBatches: number;
  colorCacheEntries: number;
  consecutiveFailures: number;
}
```

Counters contain numbers and generation only. They contain no URL, hostname, selector, CSS, DOM text, title, node reference, or stack.

- [ ] **Step 3: Write lifecycle-leak tests**

In one fixture tab:

1. switch between four theme generations 25 times;
2. navigate SPA routes 50 times;
3. append/remove 500 styled nodes in batches;
4. toggle Adaptive → Accent → Off → Adaptive 20 times;
5. force garbage collection through CDP when available;
6. inspect debug counters and DOM-generated style elements.

Pass conditions:

```text
one active generation
zero pending mutation batches after settling
no more than one controller-owned root per style kind
color cache <= configured 4096 entries
Off state has zero engine observers/styles/cache entries
style manager count returns within fixture baseline after removed nodes settle
```

Heap size is recorded as informational unless two post-GC runs show monotonic growth above both 20 MiB and 50% of the first settled sample. A failure must include numeric samples; a pass does not claim universal memory safety.

- [ ] **Step 4: Write theme-change latency and idle-activity tests**

On deterministic local fixtures only:

- record from service-worker broadcast to the content controller’s committed-generation status;
- run 20 switches and require median `<= 1,000 ms` and every sample `<= 2,500 ms` on the test environment;
- after settlement, wait 2 seconds and require no new mutation batch, stylesheet transformation, or host reload counter.

Label results as test-environment measurements, not universal browser benchmarks.

- [ ] **Step 5: Add static manifest and runtime-source tests**

Manifest expected permissions exactly:

```json
["alarms", "nativeMessaging", "scripting", "storage"]
```

Host permissions exactly:

```json
["http://*/*", "https://*/*"]
```

`check-runtime-source.sh` scans project-owned runtime source, excluding tests/docs/vendored upstream, and fails on:

```text
eval(
new Function
http://
https://
WebSocket(
XMLHttpRequest(
fetch(
chrome.cookies
chrome.history
chrome.bookmarks
chrome.downloads
```

Permit documented GitHub URLs only in build-time vendoring scripts and `UPSTREAM.md`, never extension runtime modules.

- [ ] **Step 6: Add message and diagnostic boundary tests**

Fuzz 1,000 unknown JSON objects through native and internal validators. Assert no validator throws an unbounded/raw exception into a UI response, no unknown field reaches storage, messages above 65,536 bytes are rejected, and host stderr does not echo payloads.

Run the host with forbidden caller origin, malformed config, malformed theme, and oversized message. Assert only bounded exit/error behavior and no full path in protocol stdout.

- [ ] **Step 7: Run performance and security gates**

```bash
cd extension
OMARCHY_THEME_BRIDGE_TEST_BUILD=1 npm run build
npm run test:browser -- tests/browser/performance.spec.ts tests/browser/lifecycle-leak.spec.ts
npm test -- tests/security/manifest.test.ts tests/security/runtime-source.test.ts tests/security/diagnostics-boundary.test.ts
cd ../native-host
. .venv/bin/activate
pytest tests/test_security_boundaries.py -q
cd ..
./scripts/check-runtime-source.sh
```

Expected: PASS. Preserve measurements as CI/test artifacts or copied tables, not as hard-coded marketing claims.

- [ ] **Step 8: Confirm production build contains no debug API**

```bash
cd extension
rm -rf dist
npm run build
! grep -R "debug.renderer.stats" dist
```

Expected: exit `0`.

- [ ] **Step 9: Commit qualification gates**

```bash
git add extension/src/renderer/debug-counters.ts extension/src/content/renderer-controller.ts extension/scripts/build.ts extension/tests native-host/tests/test_security_boundaries.py scripts/check-runtime-source.sh
git commit -m "test: add renderer performance and security gates"
```

---

### Task 5: Finish documentation and verify every acceptance criterion

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/installation.md`
- Modify: `docs/privacy.md`
- Modify: `docs/compatibility.md`
- Modify: `docs/settings.md`
- Create: `docs/troubleshooting.md`
- Create: `docs/limitations.md`
- Create: `docs/qualification.md`
- Create: `scripts/verify-mvp.sh`

**Interfaces:**
- Produces: complete Developer MVP documentation, verification command, and evidence-to-acceptance mapping.
- Consumes: all previous plans and tasks.

- [ ] **Step 1: Complete README without unsupported claims**

README sections:

```text
What it does
Current Developer MVP status
Adaptive / Accent / Off
Preserved content
Requirements
Build and install
Privacy
Known limitations
Testing
Troubleshooting
Third-party attribution
```

Use `Developer MVP` rather than `universal website support`. Do not call it Chrome Web Store ready.

- [ ] **Step 2: Write troubleshooting by bounded error code**

Cover every connection, theme, settings, and renderer error code with:

- meaning;
- safe user action;
- verification command;
- data retained or removed;
- whether original website remains usable.

Do not instruct users to disable browser security, expose remote debugging, grant file access, run as root, or paste browser data.

- [ ] **Step 3: Write explicit limitations**

Include:

- arbitrary websites may require compatibility rules;
- closed Shadow DOM remains unchanged;
- browser pages and built-in PDF viewer cannot be themed;
- canvas/WebGL/WebGPU/maps/video/photos/data-series are preserved, not recolored;
- text over arbitrary imagery may not be repairable;
- cross-origin/sandbox frame behavior follows Chrome permissions;
- conflict detection with other theming extensions is best-effort;
- accessibility contrast repair is local and not a universal WCAG certification;
- live YouTube/GitHub markup can change;
- no Firefox/mobile/store publication.

- [ ] **Step 4: Create the complete verification script**

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

cd "$root/native-host"
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python -m compileall -q omarchy_theme_bridge_host
pytest -q

cd "$root"
./scripts/check-runtime-source.sh
```

This script must not install into the actual user profile or mutate real Omarchy/browser configuration.

- [ ] **Step 5: Map every acceptance criterion to evidence**

`docs/qualification.md` contains a table with the 15 spec acceptance criteria and these columns:

```text
Criterion
Automated evidence
Chrome local evidence
Chromium local evidence
Status
Notes
```

Rules:

- automated-only criteria may be PASS from fresh deterministic tests;
- browser/native-install/theme-switch criteria require actual local evidence for that browser;
- unavailable local evidence is PENDING;
- one browser PASS never implies the other browser PASS;
- any FAIL keeps the overall Developer MVP status incomplete;
- PENDING keeps local qualification incomplete without invalidating verified source/test work.

- [ ] **Step 6: Run fresh complete verification**

```bash
./scripts/verify-mvp.sh
```

Expected: exit `0`; retain complete output and test counts.

- [ ] **Step 7: Run native installer tests in isolated directories again**

```bash
cd native-host
. .venv/bin/activate
pytest tests/test_installer.py tests/test_host.py tests/test_watcher.py tests/test_security_boundaries.py -q
```

Expected: PASS.

- [ ] **Step 8: Perform real local Omarchy/Chrome checks only on an available target machine**

For Google Chrome and Chromium separately:

1. build unpacked extension;
2. record exact extension ID and browser version;
3. install native host with the documented user-scoped installer;
4. verify host connection and active theme snapshot;
5. switch between one dark and one light Omarchy theme;
6. confirm ordinary open pages update without reload;
7. run Adaptive/Accent/Off and global pause/resume;
8. run YouTube checklist;
9. run GitHub checklist;
10. uninstall and verify only owned files are removed.

Sanitize evidence: no profile path, page title, URL/query, username, token, raw screenshot containing personal content, or raw browser data.

- [ ] **Step 9: Update qualification truthfully**

Use one overall status:

```text
QUALIFIED — all automated and required Chrome/Chromium local checks PASS
SOURCE-COMPLETE / LOCAL-PENDING — automated gates PASS; one or more local checks unavailable
INCOMPLETE — any required automated or local check FAILS
```

Do not use `QUALIFIED` with PENDING rows.

- [ ] **Step 10: Commit final docs and verifier**

```bash
git add README.md docs scripts/verify-mvp.sh
git commit -m "docs: add Developer MVP qualification runbook"
```

- [ ] **Step 11: Review the complete branch**

```bash
git diff --check main...HEAD
git log --oneline main..HEAD
git diff --stat main...HEAD
find . -type f \( -name '*.pem' -o -name '*.key' \) -print
```

Expected private-key search: no output.

Confirm no build output, personal data, live-site captures, remote runtime code, unsupported permission, or fabricated local result is committed.

- [ ] **Step 12: Push and open Draft PR 4**

```bash
git push -u origin feat/compatibility-qualification
```

Open a Draft PR to `main` titled:

```text
Compatibility: qualify the Omarchy Theme Bridge MVP
```

The PR description must include:

- fresh `verify-mvp.sh` results;
- fixture matrix summary;
- YouTube and GitHub rule coverage;
- measured test-environment performance table;
- security/privacy gate summary;
- exact Chrome and Chromium status separately;
- current qualification status from `docs/qualification.md`;
- known limitations.

Do not mark ready for review or claim the MVP qualified while required evidence is FAIL or PENDING.
