# Omarchy Theme Bridge — Developer MVP Design

**Status:** Approved and self-reviewed

**Date:** 2026-09-04

**Repository:** `fernandodamaso/Omarchy-Theme-Bridge`

## 1. Summary

Omarchy Theme Bridge is a Manifest V3 extension plus a user-scoped Linux native messaging host. It reads the currently active Omarchy theme and adapts regular website interfaces to the same semantic palette.

The Developer MVP targets Google Chrome and Chromium on Omarchy. Adaptive mode is enabled by default on ordinary HTTP and HTTPS pages. Each exact hostname can be changed to Accent mode or Off.

The product themes website interface chrome, not the media or authored content displayed inside it. Backgrounds, surfaces, text, borders, controls, and semantic states may change. Photos, video, thumbnails, canvas output, chart data series, maps, design canvases, and user-authored document bodies remain unchanged by default.

## 2. Goals

1. Follow the active Omarchy dark or light theme without reloading websites.
2. Map normal website interfaces to Omarchy semantic colors while preserving hierarchy and readable contrast.
3. Handle modern dynamic websites, including SPAs, CSS variables, pseudo-elements, open Shadow DOM, adopted stylesheets, and frames where Chrome permits injection.
4. Preserve media, color-sensitive content, and user-authored content by default.
5. Provide `Adaptive`, `Accent`, and `Off` per exact hostname, with Adaptive as the global default.
6. Keep all website analysis inside the browser. The native host receives no URL, hostname, DOM, text, CSS source, cookie, form value, title, screenshot, or browsing history.
7. Install and remove cleanly as a user-scoped developer build for Google Chrome and Chromium.
8. Ship deterministic tests, fixture pages, diagnostics, and honest limitation documentation.

## 3. Non-goals

The Developer MVP does not include:

- Chrome Web Store publication or store packaging.
- Firefox or mobile-browser support.
- Closed Shadow DOM traversal.
- Recoloring canvas, WebGL, WebGPU, maps, photos, video, or chart data series.
- Chrome internal pages, extension pages, the Chrome Web Store, or the built-in PDF viewer.
- Cloud synchronization, accounts, telemetry, or remote APIs.
- Remote compatibility-rule updates or remotely hosted executable code.
- A user palette editor or custom palette marketplace.
- Guaranteed perfect support for every website.
- Installing the native host from inside the extension.

## 4. Locked decisions

| Area | Decision |
|---|---|
| Product | Omarchy Theme Bridge |
| Scope | Developer MVP |
| Browsers | Google Chrome and Chromium |
| Extension platform | Manifest V3 |
| Site access | Automatic on ordinary HTTP and HTTPS pages |
| Omarchy themes | Dark and light |
| Global default | Adaptive |
| Per-hostname modes | Adaptive, Accent, Off |
| Extension stack | TypeScript, Vite, Vitest, Playwright |
| Native host | Python 3.11+, runtime standard library only |
| Filesystem events | Linux inotify through Python `ctypes`; no continuous polling |
| Renderer base | Pinned and attributed subset of Dark Reader v4.9.130 at commit `f235365a039183e75fc91d7e22edd724d7b697ec` |
| Color policy | Project-owned Omarchy semantic mapper |
| Browser storage | Local only; no account or sync |
| Host name | `com.omarchy.theme_bridge` |

## 5. Guiding rules

### 5.1 Semantic mapping, never blanket replacement

The renderer classifies a declaration by CSS property, source color, transparency, hierarchy, and likely interface role. It must never solve theming with a global override such as:

```css
* {
  background: var(--omarchy-background) !important;
  color: var(--omarchy-foreground) !important;
}
```

Typical mappings are:

- page canvas → Omarchy `background`;
- nested and raised surfaces → Omarchy background variants or nearby derived variants;
- primary and secondary text → Omarchy foreground variants;
- dividers and subtle outlines → Omarchy `muted`;
- links, primary actions, focus rings, carets, and selected controls → Omarchy `accent`;
- text selection → Omarchy `selection`;
- errors, success, warnings, and information → Omarchy red, green, yellow, and blue/cyan families.

Derived variants are allowed only for hierarchy, interaction states, and contrast repair. They must remain visually close to the active Omarchy palette.

### 5.2 Preserve when uncertain

When the renderer cannot confidently identify interface styling, it preserves the original declaration. A partially themed but usable website is preferable to a fully themed broken one.

### 5.3 Apply generations atomically

A theme generation is prepared and validated separately, then committed in one swap. Failed generation work never replaces the last valid generated stylesheet. Work for an older generation is cancelled when a newer generation arrives.

### 5.4 Keep the bridge private

The native bridge transmits theme state only. Website classification, CSS transformation, compatibility rules, and content-preservation decisions all run locally inside extension contexts.

## 6. Architecture

```text
Omarchy theme activation
        │
        ├── ~/.config/omarchy/hooks/theme-set-omarchy-theme-bridge
        │       └── atomically touches a private signal marker
        │
        └── ~/.local/state/omarchy/current directory changes
                    │
                    ▼
Python native messaging host
  - watches with inotify
  - reads complete colors.toml
  - resolves aliases and mode
  - validates and normalizes palette
  - retains last known good generation
                    │
                    │ Chrome Native Messaging
                    ▼
Manifest V3 service worker
  - owns native connection
  - caches current generation
  - stores global and hostname settings
  - coordinates tabs and frames
                    │
                    ▼
Content renderer
  - early canvas bootstrap
  - dynamic stylesheet transformation
  - Omarchy semantic mapping
  - compatibility rules
  - media and authored-content preservation
                    │
                    ▼
Website interface

Popup and options page
  - host and theme status
  - current-site mode
  - global pause
  - hostname overrides
  - sanitized diagnostics
```

## 7. Repository structure

```text
Omarchy-Theme-Bridge/
├── extension/
│   ├── package.json
│   ├── manifest.config.ts
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
│   │   ├── validation.py
│   │   └── watcher.py
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
│   └── superpowers/specs/
└── README.md
```

The implementation may split a focused module further when needed, but native integration, browser coordination, renderer infrastructure, semantic mapping, compatibility rules, and UI remain separate boundaries.

## 8. Omarchy integration

### 8.1 Normative active-theme paths

Current Omarchy uses these active paths directly:

```text
$HOME/.local/state/omarchy/current/theme/colors.toml
$HOME/.local/state/omarchy/current/theme.name
```

The host must use those exact locations by default. It must not assume Omarchy follows `XDG_STATE_HOME` for its active theme.

For deterministic tests and local development, `OMARCHY_THEME_BRIDGE_THEME_DIR` may override the active theme directory. Browser or page data can never influence that environment variable.

### 8.2 Activation behavior

Omarchy builds a clean staging theme, moves it into `~/.local/state/omarchy/current/theme`, writes `theme.name`, and then fires `~/.config/omarchy/hooks/theme-set*` hooks.

A watcher attached only to the old `colors.toml` inode could silently stop after the directory replacement. The host therefore watches:

- `$HOME/.local/state/omarchy/current` for active-directory create, move, replacement, and write events;
- the currently active theme directory after it exists;
- the private theme-set signal marker described below.

The installer creates this uniquely named executable hook:

```text
$HOME/.config/omarchy/hooks/theme-set-omarchy-theme-bridge
```

The hook atomically touches:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-theme-bridge/theme-set.signal
```

The hook is only a low-latency reload hint. It does not send a path, execute browser code, or start a daemon. The parent-directory watcher remains the fallback for manual edits and activation-flow changes.

### 8.3 Event strategy

The standard-library-only watcher calls Linux inotify through `ctypes` and libc. It:

- observes create, close-write, move-to, move-self, delete-self, and relevant attribute events;
- re-arms watches after active-directory replacement;
- coalesces rapid event bursts before reading;
- retries only in direct response to a transient event-driven load failure;
- performs no periodic filesystem polling;
- always reads the active theme once at host startup.

## 9. Native host

### 9.1 Process and protocol

The native host is launched by Chrome for a long-lived `chrome.runtime.connectNative()` port. It communicates through Chrome's 32-bit native-endian length-prefixed UTF-8 JSON protocol.

Runtime code uses Python 3.11+ standard-library modules only. Python tests use pytest as a development dependency.

stdout contains framed protocol messages only. Human-readable diagnostics go to stderr.

### 9.2 Theme parsing

The host parses TOML with `tomllib` and mirrors the Omarchy resolution needed by this extension:

1. Canonical semantic keys win.
2. Legacy aliases such as `bg`, `fg`, `dark_bg`, and `bright_fg` are accepted.
3. ANSI fallbacks such as `color0` through `color15` are accepted where Omarchy uses them.
4. Theme-mode precedence is `mode`, legacy `theme_type`, adjacent `light.mode`, background-brightness inference, then `dark`.
5. Resolved `background` and `foreground` are mandatory.
6. Optional semantic and named colors are taken from valid aliases or deterministically derived from the available palette.

Foundational palette values accepted by the MVP are:

- `#RGB`;
- `#RGBA`;
- `#RRGGBB`;
- `#RRGGBBAA`;
- numeric or percentage `rgb()`/`rgba()` in comma or space-separated CSS forms.

All accepted values are normalized to lowercase eight-bit sRGB plus alpha. Gradient strings, shell border expressions, `var()`, `color-mix()`, and other context-dependent values are rejected as foundational palette values. Rejection keeps the last valid generation.

### 9.3 Normalization

The host produces one stable semantic contract containing:

- canvas, surface, raised surface, and inset surface;
- normal, strong, and muted text;
- border, accent, and selection;
- danger, success, warning, information, magenta, and cyan;
- normalized source background and foreground variants.

Derived colors use deterministic sRGB/OKLCH conversions shared through test vectors with the TypeScript mapper. The browser remains authoritative for website-specific transformations; the host only normalizes the theme.

### 9.4 Generation and last-known-good behavior

The generation is `sha256:` plus a SHA-256 digest of the canonical normalized payload. Identical normalized themes produce identical generation IDs.

The host publishes only a complete validated generation. If a theme is missing, temporarily replaced, malformed, or invalid:

- the active browser session keeps the previous valid generation;
- the host emits a bounded enum error without filesystem paths or raw file content;
- future filesystem events trigger another load attempt;
- no partial palette is sent.

A last-known-good snapshot may be stored at:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-theme-bridge/last-good-theme.json
```

It contains normalized theme name, mode, generation, and colors only.

### 9.5 Safety limits

- Incoming and outgoing JSON is schema-validated.
- Application messages are capped at 64 KiB.
- Unknown protocol types are rejected with an enum error or ignored when forward-compatible.
- The caller origin passed by Chrome must match the configured extension origin.
- The process exits cleanly when the native port closes.
- No URL, hostname, page content, stylesheet, cookie, title, form value, screenshot, or browser profile path is accepted or logged.

## 10. Service worker

The Manifest V3 service worker owns privileged state and the native connection.

Responsibilities:

- connect to `com.omarchy.theme_bridge`;
- perform handshake and protocol-version validation;
- cache the latest valid theme in `chrome.storage.local`;
- store the global enabled state and exact-hostname overrides;
- resolve effective mode for tabs and frames;
- broadcast theme generations and settings changes;
- coordinate existing-tab injection after extension install/reload;
- reconnect after native-host failure;
- answer popup and options-page requests;
- expose only sanitized status to content scripts.

### 10.1 Reconnection

The worker performs immediate bounded reconnect attempts while its triggering event is active. If those fail, it schedules a one-shot `chrome.alarms` reconnect at Chrome's supported minimum interval. The alarm listener is registered at module top level, and the alarm is cleared after connection succeeds.

This avoids relying on long service-worker timers that may be cancelled on suspension. Every service-worker startup also checks the connection and recreates any required reconnect alarm.

### 10.2 Persistence

Global variables are treated as disposable. Theme, settings, schema versions, and connection status needed after suspension live in browser storage. Every event entry point can initialize from storage before acting.

## 11. Manifest and injection model

The MVP manifest includes:

```json
{
  "permissions": [
    "alarms",
    "nativeMessaging",
    "scripting",
    "storage"
  ],
  "host_permissions": [
    "http://*/*",
    "https://*/*"
  ]
}
```

It does not request history, bookmarks, downloads, cookies, clipboard, identity, file-scheme, or browsing-data permissions.

A statically declared isolated-world content script runs at `document_start` with:

- `matches`: ordinary HTTP and HTTPS pages;
- `all_frames: true`;
- `match_about_blank: true`;
- `match_origin_as_fallback: true` where supported.

The `scripting` permission is used only to inject the packaged controller into already-open eligible tabs after install/reload or an explicit recovery action. It is not used to run remote or user-supplied JavaScript.

The development manifest contains a non-secret public `key` so unpacked builds use a stable extension ID. No private signing key is committed. The installer accepts an override and validates extension IDs with `^[a-p]{32}$`.

## 12. Content bootstrap and controller

A small bootstrap runs at `document_start` and applies a temporary canvas color from the cached active theme to reduce white flashes.

The full content controller then:

1. requests the effective mode and current generation;
2. prepares the renderer in an isolated world;
3. removes the bootstrap when the full generated theme is ready;
4. starts Adaptive or Accent, or removes generated styles for Off;
5. listens for generation and setting updates;
6. reports only bounded renderer state and enum errors.

Page-originated messages are untrusted. The extension declares no page-facing `externally_connectable` API.

## 13. Renderer infrastructure

### 13.1 Dark Reader baseline

The MVP vendors the necessary subset of Dark Reader v4.9.130 at commit:

```text
f235365a039183e75fc91d7e22edd724d7b697ec
```

The vendored directory must include:

- Dark Reader's MIT license;
- `UPSTREAM.md` with repository, tag, commit, selected source paths, and local modifications;
- only the dynamic rendering infrastructure needed by this product;
- no Dark Reader UI, cloud/sync, analytics, site-list product behavior, or unrelated features.

The subset is isolated behind a project-owned adapter:

```ts
interface RendererEngine {
  start(options: RendererStartOptions): Promise<void>;
  update(options: RendererUpdateOptions): Promise<void>;
  stop(): Promise<void>;
  getStatus(): RendererStatus;
}
```

The adapter provides stylesheet discovery, parsing hooks, CSS-variable tracking, dynamic-style observation, inline-style handling, pseudo-element rules, open Shadow DOM support, adopted stylesheets, and frame-local operation. The Omarchy mapper owns all palette, semantic, contrast, and preservation decisions.

### 13.2 Dynamic-page behavior

The renderer transforms stylesheet declarations and variables. It must not repeatedly sweep every DOM node with `getComputedStyle()`.

It:

- observes added or replaced style/link nodes;
- batches style-related mutations;
- processes relevant inline-style changes narrowly;
- registers discovered open shadow roots;
- handles adopted stylesheets through the adapter;
- reuses transformed rule and color caches;
- ignores content mutations that do not affect styling;
- disposes observers, generated styles, and caches on Off or teardown.

## 14. Omarchy semantic mapper

Inputs include:

- CSS property category;
- parsed source color and alpha;
- source relative luminance, OKLCH lightness, and chroma;
- declaration and CSS-variable context;
- inferred effective background role;
- element/selector hints available without reading user text;
- compatibility-rule instructions;
- active Omarchy mode and normalized palette.

### 14.1 Neutral hierarchy

The mapper builds a perceptual target ramp from normalized Omarchy background and foreground variants. It anchors the page canvas to `background` and preserves relative source ordering for nested surfaces, borders, primary text, and muted text.

It does not assume that keys with names such as `dark_background` have the same numeric lightness relationship in every light and dark community theme. Actual parsed OKLCH lightness and the active mode determine ordering.

### 14.2 Chromatic hierarchy

Mapping priority is:

1. links, primary actions, selected controls, focus, caret, and form accents → accent;
2. text selection → selection;
3. red-like semantic state → danger;
4. green-like semantic state → success;
5. yellow/orange semantic state → warning;
6. blue/cyan informational state → information;
7. purple/pink interface decoration → magenta family;
8. ambiguous brand/decorative color → preserve or gently retint.

A color is never classified as an error, warning, or success from class-name text alone.

### 14.3 Interaction states

Nearby interaction colors are derived in OKLCH:

- hover: modest lightness change while retaining sufficient contrast;
- active: opposite modest lightness shift;
- disabled: lower chroma and emphasis without losing readability;
- focus-visible: strong accent outline with UI-component contrast.

### 14.4 Cache keys

Generated colors are memoized by:

- theme generation;
- source color and alpha;
- CSS property category;
- semantic classification;
- relevant effective-background bucket.

Caches are bounded and discarded when their generation is retired.

## 15. Contrast repair

When a reliable foreground/background pair is available, the mapper enforces these baselines:

- normal text: 4.5:1;
- large text: 3:1 when the large-text condition is known;
- essential control boundaries and focus indicators: 3:1 where applicable.

Repair order is:

1. retain the intended Omarchy hue family;
2. adjust OKLCH lightness;
3. adjust chroma only if needed;
4. prefer a stronger existing Omarchy foreground variant;
5. use a deterministic derived fallback.

The extension does not claim complete WCAG conformance for arbitrary image-backed, blended, animated, gradient, video, or canvas content.

## 16. Rendering modes

### 16.1 Adaptive — default

Adaptive themes:

- page canvas and nested neutral surfaces;
- primary and secondary text;
- borders, dividers, and interface shadows;
- links, buttons, selected navigation, focus, form accents, and text selection;
- menus, dialogs, popovers, tooltips, and scrollbars;
- semantic status colors;
- monochrome inline SVG interface icons when confidently identified.

It preserves media and authored-content boundaries.

### 16.2 Accent — per-site fallback

Accent keeps the website's original background and text foundation. It changes only interactive emphasis such as:

- links and primary buttons;
- selected controls and navigation;
- focus rings;
- checkboxes, radios, ranges, and compatible native accents;
- caret, text selection, and compatible scrollbars.

Accent is available for design-sensitive or partially incompatible sites.

### 16.3 Off

Off removes all generated theme styles for the exact hostname and restores the website's original presentation. The minimal controller remains so a popup change can reactivate theming without a reload when possible.

## 17. Preservation boundary

### 17.1 Preserved by default

- `img`, `picture`, and video pixels;
- thumbnails, photos, artwork, logos, and avatars;
- canvas, OffscreenCanvas, WebGL, and WebGPU output;
- external SVG images;
- maps, heatmaps, QR codes, barcodes, and CAPTCHA;
- chart data-series colors;
- design-tool and image-editor canvases;
- rich-text document bodies and authored email bodies;
- user-created content regions identified by reliable semantics or compatibility rules;
- actual selected colors in color pickers and swatches.

### 17.2 Themeable by default

- navigation, headers, sidebars, page backgrounds, panels, cards, and controls;
- search bars, inputs, textareas, selects, checkboxes, radios, and buttons;
- menus, dialogs, tooltips, popovers, and status bars;
- primary text, metadata, placeholder text, borders, separators, and shadows;
- monochrome interface icons and inline SVG controls when confidently identified.

### 17.3 SVG policy

```text
Inline monochrome toolbar icon → theme fill/stroke
Logo or illustration           → preserve
Chart axes and UI panel         → theme
Chart data series               → preserve
External SVG image              → preserve
```

## 18. Edge-case policy

| Case | MVP behavior |
|---|---|
| Existing dark mode | Retint the existing hierarchy; never invert or darken twice |
| Existing light mode | Map hierarchy into the active Omarchy light or dark palette |
| Transparent backgrounds | Preserve alpha and classify against the effective parent when available |
| Gradients | Transform supported color stops; preserve angle, positions, and alpha |
| Shadows | Retint shadow color; preserve blur, spread, inset, and opacity |
| Backdrop filters | Preserve the filter and theme underlying surfaces |
| Complex blend modes | Preserve ambiguous declarations |
| Text over imagery | Preserve the image; adjust only a reliable text/overlay pair |
| CSS variables | Track definitions, dependencies, changes, and usage context |
| Website color syntax | Parse supported CSS color forms through a common representation; preserve unsupported values |
| Pseudo-elements | Theme through transformed stylesheet rules |
| Inline `!important` | Override narrowly only when required |
| Popovers and top layer | Observe and theme page-owned UI surfaces |
| SPA route changes | Process deltas and shared rules; avoid full rescans |
| Virtualized lists | Theme shared rules instead of every row |
| Open Shadow DOM | Support, including adopted stylesheets where feasible |
| Closed Shadow DOM | Preserve; explicitly out of scope |
| Same-origin frames | Theme independently |
| Cross-origin frames | Theme only when manifest matching and Chrome injection rules permit |
| Protected/sandboxed frames | Preserve |
| Rich-text editors | Theme application chrome; preserve authored document content |
| Email | Theme mailbox UI; preserve authored message bodies |
| Design tools | Theme application chrome; preserve canvas and color-sensitive previews |
| Browser autofill | Theme `:-webkit-autofill` safely without reading values |
| Native date/time controls | Follow `color-scheme`; preserve values and swatches |
| Forced-colors mode | Disable generated theming and respect system accessibility colors |
| Printing | Disable generated page theming under `@media print` |
| Fullscreen/Picture-in-Picture | Preserve video; theme only page-owned controls |
| Chrome internal pages | Unsupported and unchanged |
| Built-in PDF viewer | Unsupported in the MVP |
| Other theme extensions | Best-effort conflict warning; user selects which extension handles the site |
| Malformed active theme | Retain last known good generation |
| Switch during navigation | Newest generation wins; stale work is cancelled |
| Many open tabs | Visible tabs update first; hidden/discarded tabs update when activated or next initialized |

## 19. Compatibility rules

Known problem sites may receive bundled declarative rules:

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

Rules are:

- packaged with the extension;
- schema-validated during build and runtime load;
- covered by tests;
- selector-based and declarative;
- unable to execute remote or arbitrary JavaScript.

User-selected Adaptive, Accent, or Off always overrides bundled compatibility defaults.

## 20. Atomic theme switching

1. The host publishes a complete validated generation.
2. The service worker stores and broadcasts it.
3. Each renderer creates generation-scoped transformation work.
4. A newer generation marks older work stale.
5. The new generated sheets replace the old sheets in one commit step.
6. Old-generation resources are released.
7. Failed preparation leaves the previous valid generation active.

No page reload is required.

## 21. Data contracts

### 21.1 Normalized theme

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

`source` contains normalized color values only, never filesystem paths.

### 21.2 Native messages

```ts
type ExtensionToHost =
  | { type: "hello"; protocolVersion: 1; extensionVersion: string }
  | { type: "theme.reload" }
  | { type: "ping"; requestId: string };

type HostToExtension =
  | { type: "host.ready"; protocolVersion: 1; hostVersion: string }
  | { type: "theme.snapshot"; theme: OmarchyTheme }
  | { type: "theme.changed"; theme: OmarchyTheme }
  | { type: "theme.error"; code: ThemeErrorCode; retainedGeneration?: string }
  | { type: "pong"; requestId: string };
```

Safe error codes include `THEME_NOT_FOUND`, `THEME_INVALID`, `THEME_UNSUPPORTED_COLOR`, `CALLER_FORBIDDEN`, and `PROTOCOL_MISMATCH`.

### 21.3 Settings

```ts
type SiteMode = "adaptive" | "accent" | "off";

interface ExtensionSettings {
  schemaVersion: 1;
  enabled: boolean;
  defaultMode: "adaptive";
  hostnameOverrides: Record<string, SiteMode>;
}
```

Hostnames are normalized to lowercase ASCII form before storage. Overrides match exact hostnames in the MVP.

## 22. Popup and options UX

### 22.1 Popup

```text
Omarchy Theme Bridge

● Connected
Tokyo Night · Dark

This website
[ Adaptive ] [ Accent ] [ Off ]

Theme applied successfully
```

The popup shows:

- host connection state;
- active Omarchy theme name and mode;
- effective mode for the active exact hostname;
- renderer state for the active tab;
- a link to full settings.

Changing a mode updates all open tabs for that exact hostname.

### 22.2 Options page

The options page contains:

1. **Status** — host connection, active theme, browser type, extension version.
2. **Defaults** — global enable/pause and Adaptive default.
3. **Site overrides** — searchable exact-hostname list with Adaptive, Accent, and Off.
4. **Diagnostics** — sanitized connection, renderer, generation, and compatibility-rule status.

### 22.3 Degraded state

After repeated bounded renderer failures within one navigation, the popup shows:

```text
Could not safely theme this page.
[Try again] [Use Accent] [Turn off here]
```

There is no tight retry loop. Failed new-generation styles are removed before this state is shown.

## 23. Installation and removal

### 23.1 User-scoped locations

Project-owned runtime files respect XDG directories and default to:

```text
${XDG_DATA_HOME:-$HOME/.local/share}/omarchy-theme-bridge/host/
${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-theme-bridge/
```

Chrome Native Messaging manifests use the browser's standard user-level locations:

```text
$HOME/.config/google-chrome/NativeMessagingHosts/com.omarchy.theme_bridge.json
$HOME/.config/chromium/NativeMessagingHosts/com.omarchy.theme_bridge.json
```

The Omarchy hook uses Omarchy's standard location:

```text
$HOME/.config/omarchy/hooks/theme-set-omarchy-theme-bridge
```

Installer flags may override browser manifest directories for nonstandard developer profiles, but defaults remain the standard paths above.

### 23.2 Installer contract

```bash
./native-host/install/install.sh --extension-id <32-character-a-through-p-id>
```

The installer:

1. verifies Linux and Python 3.11+;
2. validates the extension ID with `^[a-p]{32}$`;
3. installs an executable host launcher and Python package files;
4. writes absolute-path Native Messaging manifests for Chrome and Chromium;
5. pins `allowed_origins` to the supplied extension ID;
6. installs the unique Omarchy theme-set hook;
7. preserves unrelated files;
8. performs a host self-check and validates JSON, permissions, and executable paths;
9. prints every created or updated path.

Writes are atomic and the installer is idempotent.

The uninstaller removes only paths owned by this project. It rejects unsafe/unexpected paths and leaves shared parent directories or unrelated hook files untouched.

## 24. First-run onboarding

The extension cannot install the native host. When the connection fails with host-not-found, onboarding shows:

```text
Native host not detected

1. Clone Omarchy Theme Bridge
2. Build and load the unpacked extension
3. Run the printed native-host install command
4. Select Check connection
```

Separate diagnostics cover:

- host manifest not found;
- forbidden extension origin;
- host executable missing or not executable;
- Python version unsupported;
- active Omarchy theme missing;
- invalid palette;
- protocol mismatch.

Successful onboarding confirms host connection, active theme detection, and automatic Adaptive theming.

## 25. Privacy and diagnostics

### 25.1 Native-host boundary

The browser sends only `hello`, `theme.reload`, and `ping` protocol messages. The host sends only connection state and normalized theme state.

The host never receives or stores:

- URLs or hostnames;
- page titles or text;
- DOM or stylesheet source;
- cookies, tokens, or form values;
- screenshots;
- browser profile paths;
- browsing history.

### 25.2 Browser-local state

Browser storage contains:

- the normalized current theme;
- safe connection state codes and timestamps;
- global enable state;
- exact-hostname overrides;
- bounded renderer error codes;
- schema versions.

There is no telemetry.

### 25.3 Sanitized export

A default diagnostics export may contain:

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

It excludes full URLs, query strings, page titles, DOM text, usernames, profile paths, tokens, form content, and raw stylesheets. Hostname inclusion is opt-in at export time.

## 26. Failure handling

### 26.1 Native failures

- **Host missing:** show onboarding and retain any valid cached theme.
- **Host disconnected:** retain cached theme, attempt bounded immediate reconnect, then schedule one alarm retry.
- **Invalid active theme:** retain the last valid theme and expose a safe enum error.
- **Protocol mismatch:** retain cached rendering, disable live synchronization, and show required version information.

### 26.2 Renderer failures

The renderer prepares replacement styles separately. If preparation or commit fails, it removes incomplete new-generation resources and keeps the previous generation or original website.

### 26.3 Theme-extension conflicts

Detection is best-effort because extensions are isolated. Known visible markers may produce a warning, but the product never claims complete Dark Reader, Stylus, or custom-theme-extension detection.

## 27. Testing

### 27.1 TypeScript unit tests with Vitest

- theme and message validation;
- settings migration and exact-hostname resolution;
- color parsing/serialization;
- perceptual neutral-ramp construction;
- semantic classification;
- interaction-state derivation;
- contrast repair;
- preservation decisions;
- compatibility-rule validation;
- generation cancellation and cache bounds.

### 27.2 Python unit tests with pytest

- canonical palette parsing;
- legacy aliases and ANSI fallbacks;
- mode precedence;
- each accepted foundational color syntax;
- missing optional colors;
- malformed TOML and unsupported colors;
- active-directory replacement;
- partial write and rapid event bursts;
- missing directory and later event-driven recovery;
- generation stability;
- Native Messaging framing and message bounds;
- caller-origin checks;
- safe errors and last-known-good retention.

### 27.3 Integration tests

- native handshake and initial snapshot;
- theme-change propagation;
- service-worker suspension-safe initialization;
- host disconnect, immediate reconnect, and alarm reconnect;
- malformed-theme rollback;
- global pause/resume;
- per-hostname Adaptive, Accent, and Off;
- static content injection and existing-tab reinjection;
- Chrome and Chromium native manifests;
- allowed-origin pinning;
- installer idempotency and uninstall ownership boundaries.

### 27.4 Playwright fixture laboratory

| Fixture | Coverage |
|---|---|
| Light article | canvas, typography, links, quotes |
| Dark dashboard | nested surfaces, semantic statuses, chart boundaries |
| Media feed | thumbnails, avatars, video, metadata |
| Forms | inputs, selects, focus, placeholders, disabled, validation, autofill-like states |
| SPA feed | routes, dynamic insertion, virtualization |
| Shadow DOM | open roots and adopted stylesheets |
| Frames | same-origin, cross-origin test server, sandbox restrictions |
| CSS torture | variables, gradients, alpha, shadows, modern color syntax |
| Editor | themed application chrome with preserved authored content |

Each visual fixture runs with:

- Tokyo Night dark;
- a warm dark Omarchy palette;
- a light Omarchy palette;
- a deliberately low-contrast palette;
- Adaptive;
- Accent;
- Off.

Screenshot and DOM assertions verify that layout remains stable, media is not filtered or repainted, semantic colors remain distinguishable, focus remains visible, and Off restores original styling.

### 27.5 Live smoke checks

YouTube and GitHub receive documented manual smoke checks. Live markup is not the sole automated specification.

## 28. Performance requirements

The MVP must have:

- no continuous filesystem polling;
- no persistent full-page computed-style sweep;
- no idle mutation loop;
- batched style-related mutations;
- bounded color, rule, and error caches;
- no retransformation when the theme generation and stylesheet inputs are unchanged;
- disposal of observers and generated resources when disabled;
- visible-tab priority and lazy hidden/discarded-tab updates.

Initial engineering targets are:

- a normal active page reflects a valid Omarchy theme change within one second;
- idle extension and host activity approaches zero between events;
- no page reload is required;
- repeated route and theme changes do not cause unbounded memory growth.

These are targets until measured. Documentation must not claim target-machine benchmark results that have not been run.

## 29. Security requirements

- Native and internal messages are schema-validated.
- Native messages are capped at 64 KiB by the application.
- `allowed_origins` is pinned to exactly one installed extension origin.
- The host also verifies Chrome's caller-origin argument.
- Content scripts are treated as less trusted than the service worker.
- Content-script messages cannot trigger arbitrary filesystem or native operations.
- Page scripts cannot connect to the native host or a privileged extension API.
- There is no `eval`, `new Function`, remotely supplied executable code, or remote rule execution.
- Diagnostic output contains no browsing data.
- Installer writes are user-scoped, explicit, and atomic.
- Uninstall removes only project-owned paths.
- Vendored third-party code is pinned, attributed, reviewable, and isolated behind an adapter.

## 30. Acceptance criteria

The Developer MVP is complete only when all of the following are true:

1. Google Chrome and Chromium load the unpacked Manifest V3 build with its stable development ID.
2. The user-scoped installer registers and verifies the Python native host for both browsers.
3. The host detects the active Omarchy dark or light theme and publishes a normalized palette.
4. Switching Omarchy themes updates ordinary open websites without a reload.
5. Adaptive themes interface surfaces, text, borders, controls, accents, and semantic states.
6. Images, thumbnails, avatars, video, canvas output, maps/data layers, and chart data series remain unchanged by default.
7. Exact hostnames switch among Adaptive, Accent, and Off, and matching open tabs update immediately.
8. Global pause removes generated styles and resume reapplies effective modes.
9. Invalid or transient active-theme states retain the last known good generation.
10. Dynamic SPA content, supported open Shadow DOM, adopted stylesheets, variables, pseudo-elements, and permitted frames are covered by deterministic tests.
11. Service-worker restart/suspension does not lose required state, and native reconnection has deterministic tests.
12. YouTube and GitHub pass the documented smoke checklist.
13. Unit, integration, installer, and Playwright fixture tests pass.
14. Installation, removal, architecture, privacy, compatibility, troubleshooting, and limitations are documented.
15. No unsupported live performance, privacy, compatibility, or accessibility claim is made.

## 31. Delivery sequence

### PR 1 — Foundation and native bridge

- project/tooling scaffold;
- shared schemas;
- Python host, normalizer, protocol, inotify watcher, and tests;
- installer, uninstaller, and verifier for Chrome and Chromium;
- minimal Manifest V3 service-worker handshake and reconnection;
- developer loading and connection documentation.

### PR 2 — Renderer and semantic mapper

- pinned Dark Reader subset and attribution;
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
- connection and degraded states;
- sanitized diagnostics.

### PR 4 — Compatibility and qualification

- complete fixture matrix;
- open Shadow DOM, adopted stylesheets, and frame coverage;
- YouTube and GitHub compatibility rules and smoke runbooks;
- performance and leak checks;
- architecture, privacy, compatibility, troubleshooting, and limitation documentation.

Each PR must state which local Omarchy and browser checks were actually run. Missing local evidence remains explicitly pending rather than being inferred.

## 32. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Arbitrary sites contain ambiguous roles | Preserve uncertain declarations; use compatibility rules and Accent fallback |
| Dark Reader internals change | Pin v4.9.130 commit, vendor a narrow subset, document modifications, isolate behind adapter |
| Omarchy replaces the active directory | Watch the parent directory, re-arm inotify, and use the hook marker as a hint |
| Omarchy active path is mistaken for an XDG path | Use the verified `~/.local/state/omarchy/current` default; override only for tests/development |
| Community themes are incomplete or low contrast | Deterministic fallback resolution, last-known-good behavior, and contrast repair |
| Broad host access reduces trust | Explain why it is required, minimize all other permissions, process locally, document privacy |
| MV3 suspends the service worker | Persist state, use top-level listeners, connectNative while active, use alarms for delayed reconnect |
| Dynamic sites cause CPU or memory growth | Transform shared styles, batch mutations, bound caches, cancel stale generations, test repeated changes |
| Design tools or authored content are altered | Strong preservation boundary plus manual Accent and Off modes |
| Another theme extension conflicts | Best-effort warning and user-controlled mode; no perfect-detection claim |
| Unpacked extension ID changes | Public development manifest key plus explicit installer override |

## 33. Verified references

Design facts were checked on 2026-09-04 against:

- Omarchy `quattro` at commit `493067741e081c3b09082da6bfd51e99ec24ef00`:
  - `https://github.com/omacom/omarchy/blob/493067741e081c3b09082da6bfd51e99ec24ef00/docs/theming.md`
  - `https://github.com/omacom/omarchy/blob/493067741e081c3b09082da6bfd51e99ec24ef00/bin/omarchy-theme-color`
- Chrome Native Messaging:
  - `https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging`
- Chrome extension messaging and content-script trust boundaries:
  - `https://developer.chrome.com/docs/extensions/develop/concepts/messaging`
- Chrome extension permissions:
  - `https://developer.chrome.com/docs/extensions/develop/concepts/declare-permissions`
- Chrome alarms:
  - `https://developer.chrome.com/docs/extensions/reference/api/alarms`
- Dark Reader v4.9.130, commit `f235365a039183e75fc91d7e22edd724d7b697ec`:
  - `https://github.com/darkreader/darkreader/tree/f235365a039183e75fc91d7e22edd724d7b697ec`
  - `https://github.com/darkreader/darkreader/blob/f235365a039183e75fc91d7e22edd724d7b697ec/LICENSE`

## 34. Design completion

This document contains the approved Developer MVP scope and no unresolved product decisions. Additional browsers, store publication, remote updates, user palettes, cloud features, or media/canvas recoloring require a separate design change.