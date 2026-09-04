# Omarchy Theme Bridge — Developer MVP Design

**Status:** Approved design

**Date:** 2026-09-04

**Repository:** `fernandodamaso/Omarchy-Theme-Bridge`

## 1. Summary

Omarchy Theme Bridge is a Manifest V3 browser extension plus a user-scoped Linux native messaging host. It reads the currently active Omarchy color theme and adapts regular website interfaces to the same palette.

The MVP targets Google Chrome and Chromium on Omarchy. Adaptive mode is enabled by default for ordinary HTTP and HTTPS websites. A per-hostname override can switch a site to Accent mode or turn theming off.

The product changes website interface styling, not the media or authored content shown inside that interface. Backgrounds, surfaces, text, borders, controls, and semantic states may be recolored. Photos, video, thumbnails, canvas output, chart data series, maps, design canvases, and user-authored document bodies remain unchanged by default.

## 2. Goals

1. Follow the active Omarchy dark or light theme without requiring a browser reload.
2. Recolor normal website interfaces using Omarchy semantic colors while preserving visual hierarchy and readable contrast.
3. Work on modern dynamic websites, including SPAs, CSS variables, pseudo-elements, open Shadow DOM, and frames where Chrome permits injection.
4. Preserve media, color-sensitive content, and user-authored content by default.
5. Provide `Adaptive`, `Accent`, and `Off` modes per hostname, with Adaptive as the global default.
6. Keep page data inside the browser. The native host must receive no URL, DOM, text, cookie, form, screenshot, or browsing-history data.
7. Be installable and removable as a user-scoped developer build on both Google Chrome and Chromium.
8. Provide deterministic tests, fixtures, diagnostics, and documented limitations.

## 3. Non-goals

The Developer MVP does not include:

- Chrome Web Store publication or store packaging.
- Firefox or mobile-browser support.
- Closed Shadow DOM traversal.
- Recoloring canvas, WebGL, WebGPU, maps, photos, video, or chart data series.
- Chrome internal pages, extension pages, the Chrome Web Store, or the built-in PDF viewer.
- Cloud synchronization, accounts, telemetry, or remote APIs.
- Remote compatibility-rule updates or remotely hosted executable code.
- User-created custom palettes or a theme editor.
- Guaranteed perfect support for every website.
- Automatic installation of the native host from inside the extension.

## 4. Locked product decisions

| Area | Decision |
|---|---|
| Product name | Omarchy Theme Bridge |
| Scope | Developer MVP |
| Browsers | Google Chrome and Chromium |
| Browser platform | Manifest V3 |
| Website access | Automatic on regular HTTP and HTTPS websites |
| Theme support | Omarchy dark and light themes |
| Global default | Adaptive |
| Per-site modes | Adaptive, Accent, Off |
| Extension stack | TypeScript, Vite, Vitest, Playwright |
| Native host | Python 3.11+, runtime standard library only |
| File watching | Linux inotify, without continuous polling |
| Rendering base | Pinned, attributed subset of Dark Reader's MIT-licensed dynamic renderer |
| Color policy | Custom Omarchy semantic mapper |
| Settings storage | Browser-local only; no sync or account |

## 5. Guiding rules

### 5.1 Semantic theming, not blind replacement

The renderer must classify a declaration by property, source color, transparency, local hierarchy, and likely element role. It must not apply a global rule such as `* { background: ... !important; color: ... !important; }`.

Typical mappings are:

- page canvas → Omarchy background
- nested and raised surfaces → Omarchy background variants or derived nearby variants
- primary and secondary text → Omarchy foreground variants
- dividers and outlines → Omarchy muted
- links, primary actions, focus rings, carets, and selected controls → Omarchy accent
- text selection → Omarchy selection
- errors, success, warnings, and information → Omarchy red, green, yellow, and blue/cyan families

Derived variants are allowed for interaction states, hierarchy, and contrast repair. They must remain close to the active Omarchy palette.

### 5.2 Preserve when uncertain

When the renderer cannot confidently identify interface styling, it preserves the original declaration. A partially themed but usable site is preferable to an aggressively themed broken site.

### 5.3 Fail atomically

A theme generation is prepared and validated separately, then committed in one swap. A failed transformation keeps or restores the last valid generated stylesheet. Old-generation work is cancelled after a newer generation arrives.

### 5.4 Local and private

Theme detection, color mapping, website classification, compatibility rules, and diagnostics all run locally. No browsing data leaves the browser or is sent to the native host.

## 6. Architecture

```text
Omarchy theme activation
        │
        ├── theme-set hook marker
        └── active-theme parent-directory changes
                    │
                    ▼
Python native messaging host
  - reads and validates colors.toml
  - resolves aliases and theme mode
  - normalizes semantic palette
  - retains last known good generation
  - watches with inotify
                    │
                    │ Chrome Native Messaging
                    ▼
Manifest V3 service worker
  - maintains native connection
  - caches active generation
  - stores global and hostname settings
  - broadcasts state to frames and tabs
                    │
                    ▼
Content renderer
  - early canvas bootstrap
  - dynamic CSS transformation
  - Omarchy semantic mapping
  - compatibility rules
  - media and authored-content preservation
                    │
                    ▼
Website UI

Popup and options page
  - status
  - current-site mode
  - global pause
  - hostname overrides
  - sanitized diagnostics
```

## 7. Repository structure

```text
Omarchy-Theme-Bridge/
├── extension/
│   ├── manifest.config.ts
│   ├── package.json
│   ├── vite.config.ts
│   ├── vitest.config.ts
│   ├── playwright.config.ts
│   ├── public/
│   ├── src/
│   │   ├── background/
│   │   │   ├── native-connection.ts
│   │   │   ├── settings-store.ts
│   │   │   ├── tab-coordinator.ts
│   │   │   └── service-worker.ts
│   │   ├── content/
│   │   │   ├── bootstrap.ts
│   │   │   ├── content-script.ts
│   │   │   ├── renderer-controller.ts
│   │   │   └── preservation.ts
│   │   ├── renderer/
│   │   │   ├── engine-adapter.ts
│   │   │   ├── omarchy-mapper.ts
│   │   │   ├── contrast.ts
│   │   │   ├── color-cache.ts
│   │   │   └── generation.ts
│   │   ├── compat/
│   │   │   ├── schema.ts
│   │   │   ├── rules.ts
│   │   │   └── sites/
│   │   ├── popup/
│   │   ├── options/
│   │   └── shared/
│   │       ├── messages.ts
│   │       ├── settings.ts
│   │       ├── theme.ts
│   │       └── validation.ts
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── fixtures/
│   │   └── browser/
│   └── third_party/
│       └── darkreader/
│           ├── LICENSE
│           ├── UPSTREAM.md
│           └── selected-source/
├── native-host/
│   ├── pyproject.toml
│   ├── omarchy_theme_bridge_host/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── protocol.py
│   │   ├── theme_loader.py
│   │   ├── theme_normalizer.py
│   │   ├── watcher.py
│   │   └── validation.py
│   ├── install/
│   │   ├── install.sh
│   │   ├── uninstall.sh
│   │   ├── verify.sh
│   │   └── theme-set-hook.sh
│   └── tests/
├── docs/
│   ├── architecture.md
│   ├── installation.md
│   ├── compatibility.md
│   ├── privacy.md
│   └── superpowers/
│       └── specs/
└── README.md
```

The exact file split may be refined during implementation, but the boundaries between native integration, browser coordination, rendering, semantic mapping, compatibility rules, and UI must remain explicit.

## 8. Component design

### 8.1 Native host

The native host is named `com.omarchy.theme_bridge` and communicates over stdin/stdout using Chrome's length-prefixed native messaging protocol.

Runtime code uses only the Python 3.11+ standard library. Tests may use development-only tooling such as pytest.

#### Theme locations

The default active theme locations are derived from XDG directories:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/omarchy/current/theme/colors.toml
${XDG_STATE_HOME:-$HOME/.local/state}/omarchy/current/theme.name
```

The host supports an explicit development/test override through `OMARCHY_THEME_BRIDGE_THEME_DIR`. The override must point to a directory; page or browser data can never influence it.

#### Theme activation observation

Omarchy stages a complete theme and moves it into the active `current/theme` directory. The host therefore watches the parent `current` directory rather than attaching only to the old `colors.toml` inode.

The installer also places an executable, uniquely named Omarchy `theme-set` hook under:

```text
${XDG_CONFIG_HOME:-$HOME/.config}/omarchy/hooks/
```

The hook atomically touches a marker in:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-theme-bridge/theme-set.signal
```

The hook is only a low-latency hint. It does not pass a theme path to the host and does not start a daemon. The parent-directory inotify watcher remains the fallback for manual changes and future activation-flow differences.

The watcher:

- observes create, close-write, move, delete-self, move-self, and attribute events relevant to the active directory and marker;
- re-arms directory watches after replacement;
- coalesces rapid event bursts before reading;
- never performs continuous polling;
- always reads the active theme immediately at startup.

#### Parsing and normalization

The host parses `colors.toml` with `tomllib` and implements Omarchy-compatible resolution for the palette needed by the extension:

1. Canonical semantic keys take precedence.
2. Legacy aliases such as `bg`, `fg`, `dark_bg`, and `bright_fg` are accepted.
3. ANSI fallbacks such as `color0` through `color15` are accepted where Omarchy uses them.
4. Theme mode precedence is `mode`, legacy `theme_type`, adjacent `light.mode`, background luminance inference, then `dark`.
5. The canonical background and foreground are mandatory after fallback resolution.
6. Optional semantic and named colors are resolved from valid aliases or deterministically derived from the available palette.

Only finite, parseable color values accepted by the extension's shared color parser may be published. The initial MVP accepts standard hexadecimal forms used by Omarchy and may normalize supported rgb/rgba forms. Unsupported gradient-like shell values are not accepted as foundational page palette colors.

#### Last known good behavior

The host computes a SHA-256 generation from the normalized, canonical message payload. It publishes only complete, validated generations.

If the active theme is missing, partially written, malformed, or contains invalid required colors:

- the current browser session retains the last valid generation;
- the host emits a bounded structured error status without local paths;
- the watcher waits for a later filesystem event and retries;
- no partial palette is sent.

A last-known-good snapshot may be stored under the project's XDG state directory so the browser can recover after a host restart. It contains only normalized theme name, mode, generation, and colors.

#### Native protocol safety

- stdout contains only correctly framed JSON messages;
- diagnostics go to stderr;
- incoming and outgoing schemas are validated;
- application-level messages are capped at 64 KiB;
- unknown message types receive a structured error or are ignored according to protocol version;
- the host exits cleanly when the native port closes;
- no URL, hostname, page text, DOM, CSS source, cookie, form value, title, screenshot, or profile path is accepted or logged.

### 8.2 Service worker

The Manifest V3 service worker owns privileged state and the native connection.

Responsibilities:

- connect to `com.omarchy.theme_bridge` with `chrome.runtime.connectNative()`;
- perform protocol handshake and schema-version checks;
- cache the latest valid normalized theme in `chrome.storage.local`;
- store global enable state and exact-hostname overrides;
- resolve effective mode for each tab/frame;
- broadcast new theme generations and settings changes;
- reconnect with bounded exponential backoff after native-host failure;
- respond to popup and options-page commands;
- provide only sanitized status to content scripts.

The long-lived native port keeps the host process available while connected. Service-worker startup always attempts to reconnect and content scripts can request the cached state immediately.

### 8.3 Content bootstrap and controller

A tiny content bootstrap runs at `document_start` on permitted HTTP and HTTPS pages. It applies a temporary canvas color from the cached theme to reduce bright startup flashes.

The full controller then:

1. obtains the effective mode and current theme generation;
2. removes the bootstrap once the renderer is ready;
3. starts Adaptive or Accent rendering, or removes generated styles for Off;
4. listens for theme and setting updates;
5. applies generation changes atomically;
6. reports only bounded renderer status and error codes to the service worker.

The content script runs in an isolated world. Page-originated messages are not trusted and there is no externally connectable page API.

### 8.4 Renderer engine boundary

The extension vendors a pinned, minimal subset of Dark Reader's MIT-licensed dynamic-rendering implementation under `extension/third_party/darkreader`.

The vendored code must include:

- the upstream license;
- an `UPSTREAM.md` file with repository, commit, selected paths, and local modifications;
- no Dark Reader UI, synchronization, analytics, theme-list, or unrelated product features;
- a narrow adapter interface owned by this project.

The project-specific interface is conceptually:

```ts
interface RendererEngine {
  start(options: RendererStartOptions): Promise<void>;
  update(options: RendererUpdateOptions): Promise<void>;
  stop(): Promise<void>;
  getStatus(): RendererStatus;
}
```

The adapter supplies stylesheet discovery, CSS parsing hooks, variable tracking, dynamic style observation, inline-style handling, pseudo-element rules, open Shadow DOM handling, adopted stylesheets, and permitted frame support. The custom Omarchy mapper owns every palette and preservation decision.

### 8.5 Omarchy semantic mapper

The mapper transforms CSS declarations rather than performing repeated full-page computed-style sweeps.

Inputs include:

- CSS property;
- parsed source color and alpha;
- source relative luminance, OKLCH lightness, and chroma;
- declaration context and CSS-variable usage;
- effective or inferred background role;
- element and selector hints available without reading user text;
- compatibility-rule instructions;
- active Omarchy mode and normalized palette.

The mapper builds a perceptual neutral ramp from the active Omarchy background variants and foreground variants. It anchors page canvas to Omarchy `background`, then preserves relative source hierarchy when mapping nested surfaces, borders, primary text, and muted text.

Chromatic mapping priorities are:

1. links, primary actions, selected controls, focus, caret, and form accents → accent;
2. selection backgrounds → selection;
3. red-like semantic state → danger;
4. green-like semantic state → success;
5. yellow/orange semantic state → warning;
6. blue/cyan informational state → info;
7. purple/pink interface decoration → magenta family;
8. ambiguous brand or decorative color → preserve or gently retint, never force into a semantic state without sufficient evidence.

Interaction states derive nearby variants in OKLCH:

- hover: modest perceptual-lightness change while preserving contrast;
- active: opposite modest lightness shift;
- disabled: reduced chroma and reduced emphasis without becoming unreadable;
- focus-visible: strong accent outline with at least UI-component contrast.

Generated colors are memoized by theme generation, source color, CSS property category, alpha, and semantic classification. Caches are bounded and discarded on generation change.

### 8.6 Contrast repair

The mapper checks output combinations when a reliable foreground/background pair is available.

Baseline requirements:

- normal text: at least 4.5:1 contrast;
- large text: at least 3:1 when the renderer can establish the large-text condition;
- essential UI boundaries and focus indicators: at least 3:1 where applicable.

Repair order:

1. preserve intended Omarchy hue family;
2. adjust OKLCH lightness;
3. adjust chroma only when needed;
4. prefer an existing stronger Omarchy foreground variant;
5. fall back to a deterministic derived color.

The extension does not claim complete WCAG conformance for arbitrary animated, blended, gradient, video, or image-backed content.

### 8.7 Popup

The popup is compact and current-site focused:

```text
Omarchy Theme Bridge

● Connected
Tokyo Night · Dark

This website
[ Adaptive ] [ Accent ] [ Off ]

Theme applied successfully
```

It shows:

- native-host connection state;
- current Omarchy theme name and mode;
- effective mode for the active exact hostname;
- renderer state for the active tab;
- a link to full settings.

Changing a mode updates all open tabs for that exact hostname immediately.

### 8.8 Options page

The options page contains:

1. **Status** — host connection, active theme, browser type, extension version.
2. **Defaults** — global enable/pause state and Adaptive default.
3. **Site overrides** — searchable exact-hostname list with Adaptive, Accent, and Off.
4. **Diagnostics** — sanitized connection, renderer, generation, and compatibility-rule status.

No accounts, cloud sync, theme editor, marketplace, or telemetry are included.

## 9. Data contracts

### 9.1 Normalized theme

```ts
interface OmarchyTheme {
  schemaVersion: 1;
  generation: `sha256:${string}`;
  name: string;
  mode: "dark" | "light";
  colors: {
    canvas: string;
    surface: string;
    surfaceRaised: string;
    surfaceInset: string;
    text: string;
    textStrong: string;
    textMuted: string;
    border: string;
    accent: string;
    selection: string;
    danger: string;
    success: string;
    warning: string;
    info: string;
    magenta: string;
    cyan: string;
  };
  source: {
    background: string;
    darkBackground?: string;
    darkerBackground?: string;
    lighterBackground?: string;
    foreground: string;
    darkForeground?: string;
    lightForeground?: string;
    brightForeground?: string;
  };
}
```

`source` contains normalized palette values only. It contains no filesystem paths.

### 9.2 Native messages

Extension to host:

```ts
type ExtensionToHost =
  | { type: "hello"; protocolVersion: 1; extensionVersion: string }
  | { type: "theme.reload" }
  | { type: "ping"; requestId: string };
```

Host to extension:

```ts
type HostToExtension =
  | { type: "host.ready"; protocolVersion: 1; hostVersion: string }
  | { type: "theme.snapshot"; theme: OmarchyTheme }
  | { type: "theme.changed"; theme: OmarchyTheme }
  | { type: "theme.error"; code: ThemeErrorCode; retainedGeneration?: string }
  | { type: "pong"; requestId: string };
```

Error codes are enumerated and safe, for example `THEME_NOT_FOUND`, `THEME_INVALID`, `THEME_UNSUPPORTED_COLOR`, and `PROTOCOL_MISMATCH`. Error messages sent to the extension never contain local paths or raw theme-file content.

### 9.3 Settings

```ts
type SiteMode = "adaptive" | "accent" | "off";

interface ExtensionSettings {
  schemaVersion: 1;
  enabled: boolean;
  defaultMode: "adaptive";
  hostnameOverrides: Record<string, SiteMode>;
}
```

Hostnames are normalized to lowercase ASCII form before storage. Overrides are exact-hostname matches in the MVP.

### 9.4 Compatibility rules

```ts
interface CompatibilityRule {
  id: string;
  matches: string[];
  preserve?: string[];
  preserveUserContent?: string[];
  canvas?: string[];
  surface?: string[];
  text?: string[];
  mutedText?: string[];
  border?: string[];
  accent?: string[];
  themeInlineSvg?: string[];
  preserveInlineSvg?: string[];
  disableSelector?: string[];
}
```

Rules are declarative, bundled, schema-validated, and covered by tests. No remote JavaScript or remote rule bundle is loaded.

## 10. Mode behavior

### 10.1 Adaptive

Adaptive is the default. It themes:

- page canvas and nested neutral surfaces;
- primary and secondary text;
- borders, dividers, and shadows;
- links, buttons, selected navigation, focus, form accents, and selection;
- menus, dialogs, popovers, tooltips, and scrollbars;
- semantic status colors;
- monochrome inline SVG interface icons when confidently identified.

It preserves media and authored-content boundaries.

### 10.2 Accent

Accent preserves the site's existing background and text foundation. It themes only interactive emphasis such as:

- links;
- primary buttons;
- selected controls and navigation;
- focus rings;
- checkboxes, radio buttons, and range controls;
- caret and text selection;
- compatible scrollbars.

Accent is a manual per-site fallback for design-sensitive or partially incompatible sites.

### 10.3 Off

Off removes all generated theme styles for the hostname and restores the website's original presentation. The content controller remains minimal so a later popup change can reactivate theming without reload where possible.

## 11. Content-preservation policy

### Preserved by default

- `img`, `picture`, and video pixels;
- thumbnails, photos, artwork, and avatars;
- canvas, OffscreenCanvas, WebGL, and WebGPU output;
- external SVG images;
- maps, heatmaps, QR codes, barcodes, and CAPTCHA;
- chart data-series colors;
- design-tool and image-editor canvases;
- rich-text document bodies and authored email bodies;
- user-created content regions identified by reliable semantics or compatibility rules;
- actual selected colors in color pickers and swatches.

### Themeable by default

- navigation, headers, sidebars, page backgrounds, panels, cards, and controls;
- search bars, inputs, textareas, selects, checkboxes, radios, and buttons;
- menus, dialogs, tooltips, popovers, and status bars;
- primary text, metadata, placeholder text, borders, separators, and shadows;
- monochrome interface icons and inline SVG controls when confidently identified.

## 12. Edge-case policy

| Case | MVP behavior |
|---|---|
| Existing dark mode | Retint existing hierarchy; never invert or darken twice |
| Existing light mode | Map hierarchy into the active Omarchy light or dark palette |
| Transparent backgrounds | Preserve alpha and map against the effective parent when available |
| Gradients | Transform parseable color stops; preserve direction, positions, and alpha |
| Shadows | Retint color while preserving blur, spread, inset, and opacity |
| Backdrop filters | Preserve filter and theme underlying surfaces |
| Complex blend modes | Preserve ambiguous declarations |
| Background image behind text | Preserve image; adjust a reliable overlay or text pair only when safe |
| CSS variables | Track definitions, dependency changes, and usage context |
| Modern CSS colors | Parse supported rgb/hsl/color-mix/OKLCH/P3 forms through a common representation; preserve unsupported forms |
| Pseudo-elements | Theme through transformed stylesheet rules |
| Inline `!important` | Override narrowly only when required |
| Popovers/top layer | Observe and theme page-owned UI surfaces |
| SPA route changes | Process deltas and shared rules; avoid full rescans |
| Virtualized lists | Theme shared rules rather than each row |
| Open Shadow DOM | Support, including adopted stylesheets where the engine permits |
| Closed Shadow DOM | Preserve; explicitly out of scope |
| Same-origin frames | Theme independently |
| Cross-origin frames | Theme only when manifest matching and Chrome injection rules permit |
| Protected/sandboxed frames | Preserve |
| Rich-text editors | Theme application chrome; preserve authored document content |
| Email | Theme mailbox UI; preserve authored message body |
| Design tools | Theme application chrome; preserve canvas and color-sensitive previews |
| Browser autofill | Handle `:-webkit-autofill` contrast without exposing values |
| Native date/time controls | Follow `color-scheme`; preserve actual values and swatches |
| Forced-colors mode | Disable custom theming and respect system accessibility colors |
| Printing | Disable generated page theming under `@media print` |
| Fullscreen/Picture-in-Picture | Preserve video; theme only page-owned controls |
| Chrome internal pages | Unsupported and unchanged |
| Built-in PDF viewer | Unsupported in the MVP |
| Another theme extension | Best-effort conflict warning; user chooses which extension handles the site |
| Malformed active theme | Retain last known good generation |
| Theme switch during navigation | Newest generation wins; stale work is cancelled |
| Many open tabs | Visible tabs update first; hidden or discarded tabs update lazily |

## 13. Dynamic-page strategy

The renderer must avoid a permanent page-wide observer that repeatedly reads computed styles.

It will:

- transform stylesheet declarations and variables;
- observe added or replaced style/link nodes;
- batch mutation work;
- process inline style changes narrowly;
- register discovered open shadow roots;
- transform adopted stylesheets through the renderer adapter;
- reuse transformed rule and color caches;
- ignore content mutations that do not affect styling;
- dispose observers, generated sheets, and caches on Off or controller teardown.

## 14. Atomic theme switching

1. The native host publishes a validated new generation.
2. The service worker caches it and broadcasts it.
3. Each renderer starts generation-scoped preparation.
4. Any older in-flight generation is marked stale.
5. The new generated sheets replace the previous sheets in one commit step.
6. The old generation's resources are released.
7. A failed preparation leaves the previous valid generation active.

A page reload is not required.

## 15. Error handling and degraded state

Errors are contained by component.

### Native host failures

- missing host: service worker exposes `HOST_NOT_FOUND` and onboarding instructions;
- host disconnect: cached theme remains available and reconnect is attempted;
- invalid theme: last valid theme remains active;
- protocol mismatch: theming can continue from cache, but live synchronization is disabled until versions match.

### Renderer failures

A page-level renderer failure must remove incomplete new-generation styles and retain either the previous valid generation or the original website.

After repeated failures within one navigation, the tab enters a degraded state. The popup offers:

```text
Could not safely theme this page.
[Try again] [Use Accent] [Turn off here]
```

Retries are bounded; there is no tight failure loop.

### Conflict handling

Detection of other theme extensions is best-effort because browser extensions are isolated. Known visible style markers may trigger a warning, but the extension never claims complete detection.

## 16. Browser manifest and permissions

The MVP requests only the privileges required by the approved automatic behavior:

```json
{
  "permissions": [
    "nativeMessaging",
    "storage",
    "scripting"
  ],
  "host_permissions": [
    "http://*/*",
    "https://*/*"
  ]
}
```

The final manifest may use statically declared content scripts plus `scripting` for lifecycle/reinjection cases. It must not request history, bookmarks, downloads, cookies, clipboard, identity, or file-scheme access.

Content scripts are configured for permitted frames and early injection. Chrome-owned, restricted, and unmatched surfaces remain unchanged.

The developer build uses a non-secret manifest public key or equivalent build-time mechanism to keep the unpacked extension ID stable. The native-host installer also accepts an explicit `--extension-id` override. No private signing key is committed.

## 17. Installation and removal

### User-scoped locations

The installer respects XDG overrides and defaults to:

```text
${XDG_DATA_HOME:-$HOME/.local/share}/omarchy-theme-bridge/host/
${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-theme-bridge/
${XDG_CONFIG_HOME:-$HOME/.config}/google-chrome/NativeMessagingHosts/com.omarchy.theme_bridge.json
${XDG_CONFIG_HOME:-$HOME/.config}/chromium/NativeMessagingHosts/com.omarchy.theme_bridge.json
```

### Installer contract

```bash
./native-host/install/install.sh --extension-id <32-character-id>
```

The installer:

1. verifies Linux and Python 3.11+;
2. validates the extension ID format;
3. installs an executable host launcher and Python package files;
4. writes absolute-path Native Messaging manifests for Chrome and Chromium;
5. pins `allowed_origins` to the supplied extension ID;
6. installs the uniquely named Omarchy theme-set hook;
7. preserves unrelated existing files;
8. verifies permissions, JSON, executable paths, and a host self-check;
9. prints every created or updated path.

It is idempotent and uses atomic writes.

The uninstaller removes only paths owned by the project. It refuses unsafe or unexpected paths and does not remove shared parent directories containing unrelated files.

## 18. First-run onboarding

The extension cannot install a native host itself. When no host is detected, it shows:

```text
Native host not detected

1. Clone Omarchy Theme Bridge
2. Build/load the unpacked extension
3. Run the printed native-host installation command
4. Select Check connection
```

Distinct diagnostics are provided for:

- host manifest not found;
- forbidden extension origin;
- missing host executable;
- unsupported Python version;
- active Omarchy theme not found;
- invalid palette;
- protocol mismatch.

Successful onboarding confirms host connection, active theme detection, and automatic Adaptive theming.

## 19. Privacy and diagnostics

### Native-host boundary

The host sends only validated theme and connection messages. The extension sends only protocol handshake, reload, and ping messages.

The host never receives or logs:

- URLs or hostnames;
- page titles or text;
- DOM or stylesheet source;
- cookies, tokens, or form values;
- screenshots;
- browser profile paths;
- browsing history.

### Persistent data

Browser storage contains:

- normalized active theme;
- connection status timestamps/codes;
- global enabled state;
- exact-hostname mode overrides;
- bounded renderer error codes;
- extension schema versions.

There is no telemetry.

### Sanitized export

A default diagnostics export may include:

```json
{
  "extensionVersion": "0.1.0",
  "browser": "chromium",
  "nativeHostConnected": true,
  "themeName": "Tokyo Night",
  "themeMode": "dark",
  "themeGeneration": "sha256:…",
  "siteMode": "adaptive",
  "rendererState": "active",
  "compatibilityRuleId": "youtube"
}
```

It excludes full URLs, query strings, titles, DOM text, usernames, profile paths, tokens, form contents, and raw stylesheets. Hostname inclusion is opt-in during export.

## 20. Test strategy

### 20.1 TypeScript unit tests

Vitest covers:

- theme and message schema validation;
- settings migration and exact-hostname resolution;
- color parsing and serialization;
- perceptual neutral-ramp construction;
- semantic classification;
- interaction-state derivation;
- contrast repair;
- preservation decisions;
- compatibility-rule validation;
- generation cancellation and cache bounds.

### 20.2 Python unit tests

Native-host tests cover:

- valid canonical palette;
- legacy palette aliases;
- ANSI fallbacks;
- dark and light mode precedence;
- missing optional colors;
- malformed TOML;
- invalid and unsupported color values;
- active-directory replacement;
- partial write and rapid consecutive changes;
- missing theme directory and later recovery;
- generation stability;
- Native Messaging framing, message limits, and safe errors;
- last-known-good retention.

### 20.3 Integration tests

Integration tests cover:

- host handshake and initial theme snapshot;
- theme-change propagation;
- host disconnect and reconnect;
- malformed-theme rollback;
- global pause/resume;
- per-hostname Adaptive, Accent, and Off changes;
- installer manifests for Chrome and Chromium;
- allowed-origin pinning;
- uninstall ownership boundaries.

### 20.4 Playwright fixture laboratory

Deterministic local pages cover:

| Fixture | Coverage |
|---|---|
| Light article | canvas, typography, links, quotes |
| Dark dashboard | nested surfaces, semantic status, chart boundaries |
| Media feed | thumbnails, avatars, video, metadata |
| Forms | inputs, selects, focus, placeholders, disabled/validation/autofill-like states |
| SPA feed | route changes, dynamic insertion, virtualization |
| Shadow DOM | open roots and adopted stylesheets |
| Frames | same-origin, cross-origin test server, sandbox restrictions |
| CSS torture | variables, gradients, alpha, shadows, modern color syntax |
| Editor | themed application chrome with preserved authored content |

Each visual fixture is exercised with:

- Tokyo Night dark;
- a warm dark palette;
- a light palette;
- a deliberately low-contrast palette;
- Adaptive;
- Accent;
- Off.

Screenshot and DOM assertions verify that layout remains unchanged, media is not filtered or repainted, semantic colors remain distinct, focus remains visible, and Off restores original styling.

### 20.5 Live smoke checks

YouTube and GitHub receive documented manual smoke checks. Live sites are not the sole automated specification because their markup changes independently of this project.

## 21. Performance requirements

The MVP must have:

- no continuous filesystem polling;
- no persistent full-page computed-style sweep;
- no idle mutation loop;
- batched style-related mutations;
- bounded color, rule, and error caches;
- no retransformation when the theme generation and relevant stylesheet inputs are unchanged;
- disposal of observers and generated resources when disabled;
- visible-tab update priority and lazy hidden/discarded-tab update behavior.

Initial engineering targets are:

- normal theme changes become visible within one second on an active ordinary page;
- idle extension and native host activity approaches zero between events;
- no page reload is required;
- repeated route and theme changes do not cause unbounded memory growth.

These are targets until measured. Documentation must not claim benchmark results that have not been run on the target Omarchy environment.

## 22. Security requirements

- Native and internal messages are schema-validated.
- Native payloads are bounded to 64 KiB at the application layer.
- Native host `allowed_origins` is pinned to the installed extension ID; wildcards are forbidden.
- Content scripts are treated as less trusted than the service worker.
- Content-script messages cannot trigger arbitrary filesystem, native, or browser-privileged operations.
- Page scripts cannot connect directly to the host or privileged extension API.
- There is no `eval`, `new Function`, remotely supplied executable code, or remote rule execution.
- Diagnostic output contains no browsing data.
- Installer writes are user-scoped, explicit, and atomic.
- Uninstall removes only project-owned paths.
- Vendored third-party code is pinned, attributed, reviewable, and isolated behind an adapter.

## 23. Acceptance criteria

The Developer MVP is complete when all of the following are true:

1. Google Chrome and Chromium can load the unpacked Manifest V3 extension with a stable development ID.
2. The user-scoped installer registers and verifies the Python native host for both browsers.
3. The host detects the active Omarchy dark or light theme and publishes a normalized palette.
4. Switching Omarchy themes updates ordinary open websites without a reload.
5. Adaptive mode themes interface surfaces, text, borders, controls, accents, and semantic states.
6. Images, thumbnails, avatars, video, canvas output, map/data layers, and chart data series remain unchanged by default.
7. Exact hostnames can be switched among Adaptive, Accent, and Off, and open matching tabs update immediately.
8. Global pause removes generated styling and resume reapplies the effective modes.
9. Invalid or transient theme states retain the last known good generation.
10. Dynamic SPA content, supported open Shadow DOM, variables, pseudo-elements, and permitted frames are covered by deterministic tests.
11. YouTube and GitHub pass the documented smoke-test checklist.
12. Unit, integration, installer, and Playwright fixture tests pass.
13. Installation, removal, architecture, privacy, compatibility rules, troubleshooting, and known limitations are documented.
14. No unsupported live performance, privacy, compatibility, or accessibility claims are made.

## 24. Delivery sequence

Implementation is split into reviewable milestones:

### PR 1 — Foundation and native bridge

- repository/tooling scaffold;
- shared schemas;
- Python host, normalizer, protocol, watcher, and tests;
- installer/uninstaller/verifier for Chrome and Chromium;
- minimal Manifest V3 service worker handshake;
- documentation for loading and connecting the developer build.

### PR 2 — Renderer and semantic mapper

- pinned Dark Reader renderer subset and attribution;
- renderer adapter;
- Adaptive and Accent mapping;
- preservation policy;
- generation switching, contrast repair, and unit tests;
- core deterministic fixture pages.

### PR 3 — Product controls

- popup;
- options page;
- global pause/resume;
- exact-hostname overrides;
- connection/degraded states;
- sanitized diagnostics.

### PR 4 — Compatibility and qualification

- full fixture matrix;
- open Shadow DOM and frame coverage;
- YouTube and GitHub compatibility rules and smoke runbooks;
- performance/leak checks;
- architecture, privacy, compatibility, troubleshooting, and limitation documentation.

Each PR must remain honest about local Omarchy and browser validation that has or has not been run.

## 25. Primary risks and mitigations

| Risk | Mitigation |
|---|---|
| Arbitrary websites contain ambiguous colors and roles | Preserve uncertain declarations; use per-site compatibility rules and Accent fallback |
| Upstream Dark Reader internals change | Pin a commit, vendor a narrow subset, document modifications, isolate behind an adapter |
| Omarchy replaces the active theme directory | Watch the parent directory, re-arm inotify, and use the theme-set marker as a hint |
| Community themes have incomplete or poor-contrast palettes | Deterministic fallback resolution, last-known-good behavior, and contrast repair |
| Broad host access reduces trust | Explain the requirement, minimize other permissions, keep all processing local, and publish privacy documentation |
| MV3 service-worker suspension interrupts connection | Cache theme/settings, reconnect on startup/events, and use a long-lived native port while active |
| Dynamic sites cause CPU or memory growth | Transform shared styles, batch mutations, bound caches, cancel stale generations, and test repeated route/theme changes |
| Design tools or authored content are recolored incorrectly | Explicit preservation boundaries plus manual Accent and Off modes |
| Another theming extension conflicts | Best-effort warning and user-controlled site mode; no claim of perfect detection |
| Unpacked extension ID changes | Stable development manifest key plus explicit installer override |

## 26. References verified during design

- Omarchy theming and activation flow: `https://github.com/omacom/omarchy/blob/quattro/docs/theming.md`
- Omarchy palette resolution and mode precedence: `https://github.com/omacom/omarchy/blob/quattro/bin/omarchy-theme-color`
- Chrome Native Messaging: `https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging`
- Chrome extension messaging and trust boundaries: `https://developer.chrome.com/docs/extensions/develop/concepts/messaging`
- Chrome extension permissions: `https://developer.chrome.com/docs/extensions/develop/concepts/declare-permissions`
- Dark Reader source and MIT license: `https://github.com/darkreader/darkreader`

## 27. Design completion

This document contains the approved Developer MVP scope and has no unresolved product decisions. Any scope expansion—additional browsers, remote compatibility updates, custom palettes, canvas recoloring, store publication, or cloud features—requires a separate design change.