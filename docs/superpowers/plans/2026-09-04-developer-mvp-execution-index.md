# Developer MVP Execution Index

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide the authoritative execution order and self-review corrections for the four Omarchy Theme Bridge implementation plans.

**Architecture:** Four linear pull requests deliver the native bridge, renderer, controls, and compatibility qualification. This index must be read before each phase and overrides any conflicting example or instruction in a phase plan.

**Tech Stack:** Python 3.11+, TypeScript, Vite, Vitest, Playwright, Chrome Manifest V3, Dark Reader v4.9.130 at `f235365a039183e75fc91d7e22edd724d7b697ec`.

**Design:** `docs/superpowers/specs/2026-09-04-omarchy-theme-bridge-design.md`

## Execution order

1. `docs/superpowers/plans/2026-09-04-foundation-native-bridge.md`
2. `docs/superpowers/plans/2026-09-04-renderer-semantic-mapper.md`
3. `docs/superpowers/plans/2026-09-04-product-controls.md`
4. `docs/superpowers/plans/2026-09-04-compatibility-qualification.md`

Each phase starts only after the preceding pull request is merged. Branch from the then-current `main`, not from an old implementation branch.

Before creating the PR 1 branch, use:

```bash
git switch main
git pull --ff-only
git merge-base --is-ancestor 092884622db4ae9e89b41a018b3250d05c0ba7ad HEAD
git switch -c feat/foundation-native-bridge
```

The ancestry command must exit `0`. This replaces the older PR 1 example that detached directly at the design commit, because `main` now also contains the approved implementation plans.

## Cross-phase rules

- Tests are written and observed failing before production code for each behavior.
- Use exact dependency versions and commit lockfiles.
- Use `ThemeEngine.dynamicTheme`; the pinned upstream enum value is the string `dynamicTheme`. Do not use a numeric magic value.
- No private extension signing key, generated build output, personal browser data, profile path, token, screenshot containing personal content, or local qualification claim may be committed.
- Runtime diagnostics contain bounded enums and counters only. Raw exceptions, CSS, selectors, DOM text, URLs, hostnames, and filesystem paths do not cross trust boundaries.
- Chrome and Chromium local evidence remain separate. An unavailable browser or Omarchy session is `PENDING`, never inferred as passing.

## PR 1 corrections — foundation and native bridge

These points replace conflicting examples in `2026-09-04-foundation-native-bridge.md`.

### Build and dependency setup

- Install `@playwright/test` directly. Do not install the standalone `playwright` package and later uninstall it.
- Add an engines constraint of Node.js `>=20` to `extension/package.json`.
- Avoid `import.meta.dirname`. Resolve the extension root portably:

```ts
import {fileURLToPath} from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
```

- Remove the unused `cp` import from the build script.
- Export one `BUILD_DEFINES` object from `vite.config.ts`, import it into `scripts/build.ts`, and pass `define: BUILD_DEFINES` to every programmatic `vite.build()` call. No entry may compile with different flags.
- The forbidden-permission test uses an ordinary array assertion:

```ts
const permissions = manifest.permissions as string[];
expect(permissions).not.toEqual(expect.arrayContaining([
  "bookmarks",
  "cookies",
  "downloads",
  "history",
  "identity",
]));
```

- The PR 1 popup and options pages must contain valid local HTML, their local TypeScript entry, and the visible sentence `Renderer arrives in PR 2`. The README must state the same limitation. PR 1 must not imply that Adaptive rendering is already present.

### Shared fixtures and message handlers

- Create `extension/tests/helpers/themes.ts` during PR 1 and export a complete immutable `TOKYO_THEME`. Later plans extend this helper instead of inventing another copy.
- Chrome runtime handlers that perform asynchronous work must use `sendResponse` and return `true`; do not rely on returning a Promise from `chrome.runtime.onMessage` listeners.
- The content entry must be idempotent for static declaration plus recovery injection. Guard initialization with a unique isolated-world global key such as `__omarchyThemeBridgeContentV1`; a second injection must reuse or ignore the existing controller.

### Native configuration and validation

- `HostConfig.load()` must verify the decoded JSON is a dictionary before evaluating its keys:

```python
if not isinstance(value, dict) or set(value) != {"allowedOrigin"}:
    raise ConfigError("Host configuration has unexpected fields")
```

- Define safe Python error enums/constants in `errors.py`; protocol stdout must never contain an exception string.
- Add this exact helper to `ThemePaths`:

```python
@classmethod
def from_theme_dir(cls, theme_dir: Path) -> "ThemePaths":
    directory = theme_dir.expanduser().resolve()
    return cls(
        theme_dir=directory,
        colors_file=directory / "colors.toml",
        name_file=directory / "theme.name",
        light_marker=directory / "light.mode",
    )
```

- `tests/fixtures/tokyo-night/theme.name` contains `Tokyo Night` followed by a newline.
- `tests/fixtures/invalid/colors.toml` contains malformed TOML, for example `background = [`.
- The last-known-good round-trip test must save the complete result of `load_and_normalize()` from the Tokyo Night fixture. An object with empty `colors` and `source` is not a valid snapshot.
- `LastGoodStore.load()` and `.save()` call the same normalized-theme validator used by the host, rather than maintaining a weaker duplicate schema.
- Numeric RGB channels are validated as finite and inside `0..255`, then rounded to the nearest byte. They are not silently clamped from out-of-range input.

### Linux watching and installer behavior

- Inotify tests skip with `sys.platform != "linux"`, not merely `os.name != "posix"`.
- `InotifyWatcher` explicitly exposes the test helper `wait_for_events(timeout: float) -> WatchBatch` in addition to `fileno`, `read_events`, `rearm`, and `close`.
- The Omarchy hook writes the constant word `changed`; it does not persist the supplied theme name:

```bash
printf '%s\n' changed > "$tmp"
```

- Verification invokes the installed self-check as:

```bash
python3 -m omarchy_theme_bridge_host --self-check
```

- Remove the duplicated malformed `git commit` example in Task 7 and use only the corrected two-command block.

## PR 2 corrections — renderer and semantic mapper

These points replace conflicting examples in `2026-09-04-renderer-semantic-mapper.md`.

### Reproducible vendoring

- Implement `vendor-darkreader-lib.ts` and `vendor-darkreader.ts`, not `.mjs` files. Run them with the already pinned `tsx` dependency:

```json
{
  "vendor:darkreader": "tsx scripts/vendor-darkreader.ts --update",
  "vendor:check": "tsx scripts/vendor-darkreader.ts --check"
}
```

- Use the TypeScript compiler API (`ts.preProcessFile`) to enumerate static imports and re-exports. Do not use regular expressions as the authoritative parser.
- Configure Vite alias `@plus` to `third_party/darkreader/src/stubs` for every build and test path that compiles vendored code.
- The vendoring check scans every `declare const __NAME__` in the copied closure and fails unless `BUILD_DEFINES` explicitly supplies that symbol.
- Runtime DOM identifiers from the vendored engine must not collide with an installed Dark Reader extension. The reproducible local patch namespaces:
  - class `darkreader` and prefix `darkreader--` to `omarchy-theme-bridge` and `omarchy-theme-bridge--`;
  - CSS custom-property prefix `--darkreader-` to `--omarchy-theme-bridge-`;
  - attribute prefix `data-darkreader-` to `data-omarchy-theme-bridge-`.
- Add a fixture assertion that generated DOM contains no class beginning `darkreader`, no attribute beginning `data-darkreader-`, and no generated CSS variable beginning `--darkreader-`. Source paths and attribution may retain the upstream project name.

### Contextual color hook

The five-kind hook in the phase plan is too narrow by itself. Replace it with this contextual contract:

```ts
export type OmarchyColorKind = "background" | "text" | "border" | "shadow" | "gradient";

export interface OmarchyColorContext {
  kind: OmarchyColorKind;
  property: string | null;
  selectorText: string | null;
  important: boolean;
}

export type OmarchyColorHook = (
  context: OmarchyColorContext,
  color: RGBA,
) => string | null;
```

Patch the declaration pipeline so direct colors, gradients, and shadows pass the best available property and stylesheet selector. User-agent fallback calls pass `null` selector and an explicit property. Variable paths pass the usage property when known and otherwise `null`.

Raw selectors are transient inputs only. They are never logged, persisted, included in renderer status, or used directly in a cache key. The project adapter converts selector/property context into a bounded `SemanticHint` using bundled compatibility rules; only the hint enters mapper caches.

The patch must preserve upstream behavior when no hook is installed. `SOURCE-MANIFEST.json` marks every modified upstream file, not just `modify-colors.ts`.

### Renderer behavior

- `CompatibilityRule.matches` accepts exactly three forms: `"*"`, an exact ASCII hostname, or a leading `*.` wildcard hostname. The generic rule’s `"*"` is valid.
- Create `extension/tests/fixtures/server.ts` in PR 2; PR 4 extends it.
- Use `ThemeEngine.dynamicTheme` in `toDarkReaderTheme()`.
- Disable Dark Reader image analysis and image filtering for this product. Compatibility fixtures must prove background images, inline images, video, canvas, and external SVG media are not hidden, inverted, dimmed, replaced, or converted to generated data URLs.
- Adaptive-to-Accent prepares the Accent sheet in a disabled or detached state, then removes Adaptive and enables Accent in one commit turn. Accent-to-Adaptive keeps Accent active until the new Adaptive generation is verified, then removes Accent. Never tear down the active layer before its replacement is ready.
- The mapper may inspect selectors only through bounded compatibility classification. It may not infer semantic state from arbitrary class-name words such as `danger` or `success` unless a packaged rule explicitly declares that selector.
- Missing named semantic colors use fixed OKLCH target hue families while retaining safe theme-relative lightness and chroma: danger `25°`, warning `85°`, success `145°`, cyan `205°`, info/accent `265°`, magenta `320°`.

## PR 3 corrections — product controls

These points replace incomplete examples in `2026-09-04-product-controls.md`.

- Add this safe palette subset to both popup and options view models so extension pages can follow Omarchy without requesting raw source data:

```ts
export interface UiPalette {
  canvas: string;
  surface: string;
  surfaceRaised: string;
  text: string;
  textStrong: string;
  textMuted: string;
  border: string;
  accent: string;
  selection: string;
}
```

- Implement the file already named in the phase file map: `extension/src/shared/browser.ts`. It exports `browserLabel()` and `hostnameFromEligibleUrl()`. The hostname helper accepts only `http:` and `https:`, returns normalized ASCII hostname or `null`, and never returns a full URL.
- Extend `tests/helpers/fake-chrome.ts` with `storage.session`, `tabs.onRemoved`, active-tab querying, and frame IDs before renderer-status tests are written.
- A content-script sender may submit only `content.ready` and `renderer.status`. Every settings, reconnect, retry, options, popup, and diagnostics command requires an extension-page sender.
- In popup browser tests, keep the fixture website as the active tab while the test opens the popup document as a separate extension page. `popup.state.get` must therefore resolve the fixture tab, not the popup test page.
- Host-alias browser tests launch the fixture server with explicit Chromium host resolver rules for `youtube.test` and `music.youtube.test`; they must not rely on DNS or external network access.

## PR 4 corrections — compatibility and qualification

These points replace over-broad authored-content examples in `2026-09-04-compatibility-qualification.md`.

- The YouTube rule does not preserve entire comment or chat text containers. Preserve only explicitly author-colored descendants, for example:

```ts
preserveUserContent: [
  "ytd-comments #content-text [style*='color']",
  "ytd-comments #content-text [style*='background']",
  "yt-live-chat-text-message-renderer #message [style*='color']",
  "yt-live-chat-text-message-renderer #message [style*='background']",
]
```

Normal comment/chat text remains themeable so it cannot disappear against an Adaptive surface.

- The GitHub rule does not place `.markdown-body`, `.comment-body`, or `.js-comment-body` wholesale in `preserveUserContent`. Use authored inline-style descendants only:

```ts
preserveUserContent: [
  ".markdown-body [style*='color']",
  ".markdown-body [style*='background']",
  ".comment-body [style*='color']",
  ".comment-body [style*='background']",
  ".js-comment-body [style*='color']",
  ".js-comment-body [style*='background']",
]
```

Markdown text and code containers remain themeable; embedded images and declared data visualizations remain preserved through their own selectors.

- Exact and wildcard rule matching follows the PR 2 matcher contract. `youtube.com` and `github.com` are separate exact entries from their `*.domain` entries.
- A live selector that no longer matches is not replaced with an unstable generated class. Prefer stable element names, accessibility states, semantic IDs, or leave that surface to generic mapping.

## Plan self-review gate

Before implementation begins, the worker must confirm:

- [ ] The design commit is an ancestor of current `main`.
- [ ] All four phase plan files and this index are present.
- [ ] The current phase is the next unmerged phase in the execution order.
- [ ] Corrections in this index have been applied when copying examples from a phase plan.
- [ ] No unresolved placeholder marker exists in the current implementation branch.
- [ ] The test command that will establish the first red state is available.

The plan set is documentation only. No extension, native host, installer, renderer, popup, or compatibility implementation is complete merely because these files exist.
