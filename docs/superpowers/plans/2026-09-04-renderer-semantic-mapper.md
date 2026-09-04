# Renderer and Semantic Mapper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver PR 2: Adaptive and Accent rendering backed by a pinned, attributed Dark Reader dynamic-engine subset, with a project-owned Omarchy semantic mapper, preservation policy, atomic generation switching, and deterministic browser fixtures.

**Architecture:** A reproducible vendoring script extracts the static import closure of Dark Reader’s dynamic renderer at the approved commit and applies one reviewable color-hook patch. The project-owned mapper converts Dark Reader’s parsed RGBA inputs into Omarchy semantic colors; the renderer controller owns source-mode inference, compatibility rules, preservation, generation cancellation, and atomic application.

**Tech Stack:** TypeScript, Vite, Vitest, Playwright, Manifest V3 content scripts, Dark Reader v4.9.130 source at commit `f235365a039183e75fc91d7e22edd724d7b697ec`.

**Spec:** `docs/superpowers/specs/2026-09-04-omarchy-theme-bridge-design.md`

## Global Constraints

- Begin only after PR 1 is merged; branch from updated `main` as `feat/renderer-semantic-mapper`.
- Keep Dark Reader pinned to v4.9.130 commit `f235365a039183e75fc91d7e22edd724d7b697ec`.
- Vendor only the dynamic-renderer dependency closure; include MIT license, source manifest, and explicit local-modification documentation.
- Do not include Dark Reader UI, settings, sync, telemetry, remote configuration, site lists, or analytics.
- Adaptive is the default. Accent and Off remain available per exact hostname.
- Preserve images, picture/video pixels, avatars, thumbnails, external SVG images, canvas/WebGL/WebGPU output, maps, heatmaps, chart data series, QR/barcodes/CAPTCHA, design canvases, and authored content by default.
- Do not use blanket `* { background/color: ... !important }` replacement.
- Do not perform persistent full-page `getComputedStyle()` sweeps or an idle mutation loop.
- Prepare each theme generation separately and commit it atomically; stale work must not replace newer work.
- Generated caches are bounded and generation-scoped.
- No remote executable code or runtime compatibility downloads.
- Do not claim complete WCAG compliance for arbitrary websites.

---

## File Map

- `extension/scripts/vendor-darkreader.mjs` — pinned checkout, dependency-closure copy, local patch, and hash manifest.
- `extension/scripts/vendor-darkreader-lib.mjs` — testable import resolver and hash helpers.
- `extension/third_party/darkreader/LICENSE` — exact upstream MIT license.
- `extension/third_party/darkreader/UPSTREAM.md` — tag, commit, entry point, extraction method, and modifications.
- `extension/third_party/darkreader/SOURCE-MANIFEST.json` — upstream and vendored SHA-256 hashes.
- `extension/third_party/darkreader/src/` — generated dependency closure.
- `extension/third_party/darkreader/src/inject/dynamic-theme/omarchy-color-hook.ts` — local hook introduced by the patch.
- `extension/src/renderer/types.ts` — renderer and semantic-mapping interfaces.
- `extension/src/renderer/color.ts` — RGBA, sRGB, OKLab, OKLCH, contrast, and serialization primitives.
- `extension/src/renderer/source-mode.ts` — one-time source dark/light/unknown inference.
- `extension/src/renderer/neutral-ramp.ts` — perceptual target ramp.
- `extension/src/renderer/contrast.ts` — deterministic contrast repair.
- `extension/src/renderer/omarchy-mapper.ts` — background/text/border/shadow/gradient semantic mapping.
- `extension/src/renderer/color-cache.ts` — bounded generation-scoped LRU cache.
- `extension/src/renderer/darkreader-theme.ts` — translation to the vendored engine’s `Theme` contract.
- `extension/src/renderer/engine-adapter.ts` — `RendererEngine` implementation.
- `extension/src/renderer/generation.ts` — stale-generation cancellation and atomic commit ownership.
- `extension/src/content/preservation.ts` — content-preservation classification.
- `extension/src/content/renderer-controller.ts` — frame-local mode lifecycle.
- `extension/src/content/accent-style.ts` — conservative Accent CSS.
- `extension/src/compat/schema.ts` — compatibility rule validation.
- `extension/src/compat/rules.ts` — bundled rule lookup and Dark Reader fix translation.
- `extension/src/compat/sites/generic.ts` — generic preserve rules.
- `extension/tests/helpers/themes.ts` — deterministic theme fixtures.
- `extension/tests/vectors/color-vectors.json` — cross-language color vectors.
- `extension/tests/fixtures/` — local deterministic fixture application.
- `extension/tests/browser/` — extension-driven Playwright tests.

---

### Task 1: Vendor and pin the Dark Reader dynamic renderer reproducibly

**Files:**
- Create: `extension/scripts/vendor-darkreader-lib.mjs`
- Create: `extension/scripts/vendor-darkreader.mjs`
- Create: `extension/third_party/darkreader/UPSTREAM.md`
- Create: `extension/third_party/darkreader/SOURCE-MANIFEST.json`
- Create: `extension/third_party/darkreader/LICENSE`
- Create: `extension/third_party/darkreader/src/**`
- Test: `extension/tests/unit/vendor-darkreader.test.ts`
- Modify: `extension/package.json`
- Modify: `extension/vite.config.ts`

**Interfaces:**
- Produces: `collectDependencyClosure(root: string, entries: string[]): Promise<string[]>`.
- Produces: `vendor-darkreader.mjs --update` and `vendor-darkreader.mjs --check`.
- Produces: patched exports `setOmarchyColorHook()` and `clearOmarchyColorHook()` in vendored source.
- Consumes: Vite build from PR 1.

- [ ] **Step 1: Write failing dependency-closure tests against a local fake source tree**

```ts
// extension/tests/unit/vendor-darkreader.test.ts
import {mkdtemp, mkdir, writeFile} from "node:fs/promises";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {describe, expect, it} from "vitest";
import {collectDependencyClosure} from "../../scripts/vendor-darkreader-lib.mjs";

async function fixture(): Promise<string> {
  const root = await mkdtemp(join(tmpdir(), "otb-vendor-"));
  await mkdir(join(root, "src/inject/dynamic-theme"), {recursive: true});
  await mkdir(join(root, "src/utils"), {recursive: true});
  await mkdir(join(root, "src/stubs/utils"), {recursive: true});
  await writeFile(join(root, "src/inject/dynamic-theme/index.ts"), [
    'import {x} from "../../utils/x";',
    'import {plus} from "@plus/utils/theme";',
    'export {local} from "./local";',
  ].join("\n"));
  await writeFile(join(root, "src/inject/dynamic-theme/local.ts"), "export const local = 1;\n");
  await writeFile(join(root, "src/utils/x.ts"), "export const x = 1;\n");
  await writeFile(join(root, "src/stubs/utils/theme.ts"), "export const plus = 1;\n");
  return root;
}

describe("collectDependencyClosure", () => {
  it("follows relative imports, re-exports, and @plus stubs", async () => {
    const root = await fixture();
    expect(await collectDependencyClosure(root, ["src/inject/dynamic-theme/index.ts"])).toEqual([
      "src/inject/dynamic-theme/index.ts",
      "src/inject/dynamic-theme/local.ts",
      "src/stubs/utils/theme.ts",
      "src/utils/x.ts",
    ]);
  });

  it("rejects imports outside the reviewed roots", async () => {
    const root = await fixture();
    await writeFile(join(root, "src/inject/dynamic-theme/local.ts"), 'import "../../../tasks/build";\n');
    await expect(collectDependencyClosure(root, ["src/inject/dynamic-theme/index.ts"])).rejects.toThrow("outside reviewed roots");
  });
});
```

- [ ] **Step 2: Run the vendor tests and verify the red state**

```bash
cd extension
npm test -- tests/unit/vendor-darkreader.test.ts
```

Expected: FAIL because the vendor library does not exist.

- [ ] **Step 3: Implement the static import resolver**

The resolver must parse these forms without executing upstream code:

```js
const IMPORT_PATTERNS = [
  /\b(?:import|export)\s+(?:type\s+)?(?:[^'";]*?\s+from\s+)?["']([^"']+)["']/g,
  /\bimport\s*\(\s*["']([^"']+)["']\s*\)/g,
];
```

Resolve:

- `./` and `../` against the importing file;
- `@plus/` to `src/stubs/` because the build defines `__PLUS__` as false;
- candidates in this order: exact path, `.ts`, `.tsx`, `.js`, `.json`, `/index.ts`.

Allow only:

```js
const ALLOWED_PREFIXES = [
  "src/definitions.d.ts",
  "src/generators/",
  "src/inject/dynamic-theme/",
  "src/inject/utils/",
  "src/stubs/",
  "src/utils/",
];
```

Reject bare third-party imports and resolved files outside those roots. Return a sorted, duplicate-free POSIX path list.

- [ ] **Step 4: Implement pinned checkout, copy, patch, and hash recording**

Use constants:

```js
const UPSTREAM_REPOSITORY = "https://github.com/darkreader/darkreader.git";
const UPSTREAM_TAG = "v4.9.130";
const UPSTREAM_COMMIT = "f235365a039183e75fc91d7e22edd724d7b697ec";
const ENTRY_FILES = ["src/inject/dynamic-theme/index.ts"];
```

`--update` must:

1. create a temporary directory;
2. run `git init`, add origin, fetch the exact commit with depth 1, and detach checkout;
3. verify `git rev-parse HEAD` equals the constant;
4. collect the dependency closure;
5. copy only listed files plus exact upstream `LICENSE`;
6. apply the color hook described in Step 5 through exact anchor replacements that fail if upstream text differs;
7. write `SOURCE-MANIFEST.json` containing `path`, `upstreamSha256`, `vendoredSha256`, `upstreamCommit`, and `locallyModified`;
8. write `UPSTREAM.md` with repository, tag, commit, entry point, extraction command, allowed roots, and modifications;
9. atomically replace `third_party/darkreader`.

`--check` performs no network access. It hashes committed files, verifies every manifest row, rejects untracked files under the vendored directory, and verifies the license hash.

- [ ] **Step 5: Add one narrowly scoped upstream patch for project-owned color mapping**

Create this new vendored module:

```ts
// third_party/darkreader/src/inject/dynamic-theme/omarchy-color-hook.ts
import type {RGBA} from "../../utils/color";

export type OmarchyColorKind = "background" | "text" | "border" | "shadow" | "gradient";
export type OmarchyColorHook = (kind: OmarchyColorKind, color: RGBA) => string | null;

let hook: OmarchyColorHook | null = null;

export function setOmarchyColorHook(next: OmarchyColorHook): void {
  hook = next;
}

export function clearOmarchyColorHook(): void {
  hook = null;
}

export function mapWithOmarchyColorHook(kind: OmarchyColorKind, color: RGBA): string | null {
  return hook?.(kind, color) ?? null;
}
```

Patch `modify-colors.ts` to import `mapWithOmarchyColorHook` and consult it before stock behavior in these exact exported functions:

- `modifyBackgroundColor` with `background`;
- `modifyForegroundColor` with `text`;
- `modifyBorderColor` with `border`;
- `modifyShadowColor` with `shadow`;
- `modifyGradientColor` with `gradient`.

For registered background/text/border colors, register the hooked value through upstream `registerColor()` so variable palettes remain coherent. With no hook, behavior remains exactly upstream.

Export `setOmarchyColorHook` and `clearOmarchyColorHook` from vendored `dynamic-theme/index.ts`.

- [ ] **Step 6: Run vendoring and record the exact closure**

```bash
node scripts/vendor-darkreader.mjs --update
node scripts/vendor-darkreader.mjs --check
```

Expected: both exit `0`; `SOURCE-MANIFEST.json` names only reviewed roots, and `UPSTREAM.md` records the five hook points.

- [ ] **Step 7: Define compile-time flags for vendored code**

```ts
// extension/vite.config.ts
export default defineConfig({
  define: {
    __TEST__: "false",
    __CHROMIUM_MV3__: "true",
    __PLUS__: "false",
    __FIREFOX_MV2__: "false",
    __THUNDERBIRD__: "false",
  },
});
```

Ensure every `vite.build()` call in `scripts/build.ts` imports and spreads the same `define` object; do not allow one build entry to compile with different flags.

- [ ] **Step 8: Add package scripts and run verification**

```json
{
  "scripts": {
    "vendor:darkreader": "node scripts/vendor-darkreader.mjs --update",
    "vendor:check": "node scripts/vendor-darkreader.mjs --check"
  }
}
```

```bash
npm run vendor:check
npm run typecheck
npm test -- tests/unit/vendor-darkreader.test.ts
npm run build
```

Expected: PASS.

- [ ] **Step 9: Commit the pinned renderer subset**

```bash
git add extension/scripts extension/third_party extension/package.json extension/package-lock.json extension/vite.config.ts extension/scripts/build.ts extension/tests/unit/vendor-darkreader.test.ts
git commit -m "build: vendor pinned Dark Reader renderer"
```

---

### Task 2: Implement shared perceptual color math and bounded caches

**Files:**
- Create: `extension/src/renderer/types.ts`
- Create: `extension/src/renderer/color.ts`
- Create: `extension/src/renderer/color-cache.ts`
- Create: `extension/tests/vectors/color-vectors.json`
- Create: `extension/tests/unit/color.test.ts`
- Create: `extension/tests/unit/color-cache.test.ts`
- Modify: `native-host/tests/test_color.py`

**Interfaces:**
- Produces: `Rgba`, `Oklch`, `ColorRole`, `SourceMode`, `MappingContext`, and `MappedColor`.
- Produces: `rgbaToOklch()`, `oklchToRgba()`, `relativeLuminance()`, `contrastRatio()`, `mixOklch()`, and `serializeRgba()`.
- Produces: `GenerationColorCache.getOrCompute(key, factory)` with a fixed entry bound.
- Consumes: vendored Dark Reader `RGBA` values and `OmarchyTheme` from PR 1.

- [ ] **Step 1: Add exact cross-language vectors**

```json
[
  {"hex":"#000000","oklch":[0.0,0.0,0.0]},
  {"hex":"#ffffff","oklch":[1.0,0.0,0.0]},
  {"hex":"#ff0000","oklch":[0.627955,0.257683,29.233885]},
  {"hex":"#7aa2f7","oklch":[0.718977,0.132159,264.202157]},
  {"hex":"#1a1b26","oklch":[0.226288,0.021374,280.487102]},
  {"hex":"#a9b1d6","oklch":[0.766586,0.053700,275.492395]},
  {"hex":"#414868","oklch":[0.409437,0.054556,274.273479]}
]
```

Use tolerance `0.00001` for L/C and `0.001` degrees for hue. Treat chroma below `0.000001` as hue `0`.

- [ ] **Step 2: Write failing conversion and cache tests**

```ts
import vectors from "../vectors/color-vectors.json";
import {hexToRgba, rgbaToOklch, serializeRgba} from "../../src/renderer/color";

it.each(vectors)("converts $hex to the shared OKLCH vector", ({hex, oklch}) => {
  const actual = rgbaToOklch(hexToRgba(hex));
  expect(actual.l).toBeCloseTo(oklch[0], 5);
  expect(actual.c).toBeCloseTo(oklch[1], 5);
  if (actual.c >= 0.000001) expect(actual.h).toBeCloseTo(oklch[2], 3);
  expect(serializeRgba(hexToRgba(hex))).toBe(hex);
});
```

Cache test:

```ts
const cache = new GenerationColorCache(2);
cache.set("g1", "a", "#000000");
cache.set("g1", "b", "#111111");
cache.get("g1", "a");
cache.set("g1", "c", "#222222");
expect(cache.get("g1", "b")).toBeUndefined();
cache.retireGeneration("g1");
expect(cache.size).toBe(0);
```

- [ ] **Step 3: Run tests and verify the red state**

```bash
npm test -- tests/unit/color.test.ts tests/unit/color-cache.test.ts
```

Expected: FAIL because renderer color modules do not exist.

- [ ] **Step 4: Implement exact sRGB ↔ OKLab ↔ OKLCH formulas**

Use Björn Ottosson’s published matrices:

```ts
function srgbToLinear(value: number): number {
  const c = value / 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function linearToSrgb(value: number): number {
  const c = value <= 0.0031308 ? 12.92 * value : 1.055 * value ** (1 / 2.4) - 0.055;
  return Math.round(Math.min(1, Math.max(0, c)) * 255);
}
```

Forward LMS and OKLab:

```ts
const l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b;
const m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b;
const s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b;
const lRoot = Math.cbrt(l);
const mRoot = Math.cbrt(m);
const sRoot = Math.cbrt(s);
const L = 0.2104542553 * lRoot + 0.7936177850 * mRoot - 0.0040720468 * sRoot;
const a = 1.9779984951 * lRoot - 2.4285922050 * mRoot + 0.4505937099 * sRoot;
const bLab = 0.0259040371 * lRoot + 0.7827717662 * mRoot - 0.8086757660 * sRoot;
```

Implement the inverse matrices in the same module. Convert `(a,b)` to chroma and hue with `atan2`; normalize hue into `[0,360)`. Preserve alpha unchanged.

- [ ] **Step 5: Implement WCAG relative luminance and contrast**

```ts
export function relativeLuminance(color: Rgba): number {
  const r = srgbToLinear(color.r);
  const g = srgbToLinear(color.g);
  const b = srgbToLinear(color.b);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrastRatio(a: Rgba, b: Rgba): number {
  const lighter = Math.max(relativeLuminance(a), relativeLuminance(b));
  const darker = Math.min(relativeLuminance(a), relativeLuminance(b));
  return (lighter + 0.05) / (darker + 0.05);
}
```

`serializeRgba()` returns lowercase `#rrggbb` for alpha 255 and `#rrggbbaa` otherwise.

- [ ] **Step 6: Implement a bounded per-generation LRU cache**

Use one `Map<string, string>` with composite key `${generation}\u0000${mappingKey}`. Reading moves an entry to the end. Insertion removes the oldest entry until `size <= maxEntries`. `retireGeneration()` removes matching prefixes. Reject `maxEntries < 1`.

- [ ] **Step 7: Verify Python uses the same vectors**

Load `extension/tests/vectors/color-vectors.json` from `native-host/tests/test_color.py` and assert the Python conversion matches the same tolerances. Adjust PR 1’s Python color formulas if needed; do not create separate truth tables.

- [ ] **Step 8: Run both language suites**

```bash
cd extension
npm test -- tests/unit/color.test.ts tests/unit/color-cache.test.ts
cd ../native-host
. .venv/bin/activate
pytest tests/test_color.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit perceptual color primitives**

```bash
git add extension/src/renderer extension/tests/vectors extension/tests/unit/color.test.ts extension/tests/unit/color-cache.test.ts native-host/tests/test_color.py
git commit -m "feat: add perceptual color primitives"
```

---

### Task 3: Build the neutral ramp, semantic mapper, and contrast repair

**Files:**
- Create: `extension/src/renderer/neutral-ramp.ts`
- Create: `extension/src/renderer/contrast.ts`
- Create: `extension/src/renderer/omarchy-mapper.ts`
- Create: `extension/src/renderer/source-mode.ts`
- Test: `extension/tests/unit/neutral-ramp.test.ts`
- Test: `extension/tests/unit/contrast.test.ts`
- Test: `extension/tests/unit/omarchy-mapper.test.ts`
- Test: `extension/tests/unit/source-mode.test.ts`

**Interfaces:**
- Produces: `buildNeutralRamp(theme: OmarchyTheme): NeutralRamp`.
- Produces: `repairContrast(foreground, background, target, family): Rgba`.
- Produces: `OmarchyMapper.map(context: MappingContext): MappedColor`.
- Produces: `inferSourceMode(document: Document): SourceMode` using at most one root/body computed-style read each.
- Consumes: color primitives and `OmarchyTheme`.

- [ ] **Step 1: Define mapping types**

```ts
export type ColorRole = "background" | "text" | "border" | "shadow" | "gradient";
export type SourceMode = "dark" | "light" | "unknown";
export type SemanticHint = "accent" | "danger" | "success" | "warning" | "info" | "brand" | "neutral" | "unknown";

export interface MappingContext {
  generation: string;
  role: ColorRole;
  source: Rgba;
  sourceMode: SourceMode;
  theme: OmarchyTheme;
  semanticHint: SemanticHint;
  effectiveBackground?: Rgba;
}

export interface MappedColor {
  value: string;
  token: string | null;
  repairedContrast: boolean;
  preserved: boolean;
}
```

- [ ] **Step 2: Write failing behavior tests**

Required assertions:

```ts
it("maps a light page canvas to Tokyo Night canvas", () => {
  expect(map({role: "background", source: hex("#ffffff"), sourceMode: "light"})).toMatchObject({
    value: "#1a1b26",
    token: "canvas",
    preserved: false,
  });
});

it("maps dark-site raised neutrals above the Tokyo Night canvas", () => {
  const canvas = rgbaToOklch(hex("#1a1b26")).l;
  const raised = rgbaToOklch(parse(map({role: "background", source: hex("#303030"), sourceMode: "dark"}).value)).l;
  expect(raised).toBeGreaterThan(canvas);
});

it("keeps a high-chroma brand background when no semantic hint exists", () => {
  expect(map({role: "background", source: hex("#ff00ff"), sourceMode: "light", semanticHint: "brand"}).preserved).toBe(true);
});

it("maps semantic red text to the danger family", () => {
  expect(map({role: "text", source: hex("#d93025"), sourceMode: "light", semanticHint: "danger"}).token).toBe("danger");
});
```

Contrast tests must prove normal text reaches `>= 4.5`, large/essential UI target reaches `>= 3.0`, hue drift is below 12 degrees when chroma remains meaningful, and impossible out-of-gamut attempts terminate after a bounded binary search.

Source-mode tests:

- `<meta name="color-scheme" content="dark light">` plus dark root background → dark;
- CSS `color-scheme: light` → light;
- transparent root plus dark body → dark;
- both transparent → unknown;
- no more than two `getComputedStyle()` calls.

- [ ] **Step 3: Run mapper tests and verify the red state**

```bash
npm test -- tests/unit/neutral-ramp.test.ts tests/unit/contrast.test.ts tests/unit/omarchy-mapper.test.ts tests/unit/source-mode.test.ts
```

Expected: FAIL because mapper modules do not exist.

- [ ] **Step 4: Build the target neutral ramp from actual lightness**

Parse these tokens: `surfaceInset`, `canvas`, `surface`, `surfaceRaised`, `border`, `textMuted`, `text`, `textStrong`. Sort same-category candidates by OKLCH lightness but retain named anchors.

For background mapping, define source elevation:

```ts
function sourceElevation(lightness: number, sourceMode: SourceMode): number {
  if (sourceMode === "light") return clamp01(1 - lightness);
  if (sourceMode === "dark") return clamp01(lightness);
  return clamp01(Math.abs(lightness - 0.5) * 0.35);
}
```

Map neutral background elevation through stops:

```text
0.00 canvas
0.28 surface
0.62 surfaceRaised
1.00 mix(surfaceRaised, textMuted, 0.18)
```

Use monotonic OKLCH interpolation and clamp to sRGB. For `unknown`, prefer a conservative canvas/surface range and never produce a near-text background.

Text emphasis is `L` in dark source mode and `1-L` in light source mode. Map:

```text
0.00 textMuted
0.55 text
1.00 textStrong
```

Borders map source emphasis into `mix(canvas,border,0.65)` through `border`.

- [ ] **Step 5: Implement semantic hue classification without class-name guessing**

When `semanticHint` is explicit, honor it. Otherwise classify only sufficiently chromatic colors (`c >= 0.07`) by OKLCH hue:

```text
red/danger:       15°..50° or 345°..360°
yellow/warning:   50°..115°
green/success:    115°..170°
cyan/info:        170°..225°
blue/info/accent: 225°..285°
purple/magenta:   285°..345°
```

Rules:

- ambiguous high-chroma backgrounds with no UI hint are preserved;
- chromatic text/borders map to the corresponding Omarchy family while preserving source alpha;
- `accent` hint always maps to accent;
- `brand` hint always preserves;
- neutral colors use the neutral ramp;
- unsupported/non-finite inputs preserve.

- [ ] **Step 6: Implement deterministic interaction and contrast repair**

`repairContrast()` performs at most 18 binary-search iterations over OKLCH lightness, first toward the direction that increases contrast. Preserve hue, then reduce chroma in 5% steps only if the candidate remains out of sRGB gamut. Prefer exact theme `textStrong` before deriving a new normal-text fallback.

Return `{color, repaired}`; never mutate the theme.

For mapped text with reliable effective background, target `4.5`. For border/focus contexts explicitly marked essential by the caller, target `3.0`. Without a reliable background, return the mapped family without a compliance claim.

- [ ] **Step 7: Implement one-time source-mode inference**

Check, in order:

1. root computed `colorScheme` containing exactly `dark` or `light`;
2. non-transparent root background luminance;
3. non-transparent body background luminance;
4. `unknown`.

Do not inspect text, class names, page titles, or arbitrary nodes.

- [ ] **Step 8: Implement the generation-scoped mapper cache**

Cache key fields, joined with `\u0000`:

```text
generation
role
source rgba
sourceMode
semanticHint
effective-background bucket or none
```

The effective-background bucket rounds OKLCH L and C to two decimals and hue to the nearest five degrees. Default max entries: `4096` per active renderer. Retire the old generation on a successful swap.

- [ ] **Step 9: Run mapper suites**

```bash
npm run typecheck
npm test -- tests/unit/neutral-ramp.test.ts tests/unit/contrast.test.ts tests/unit/omarchy-mapper.test.ts tests/unit/source-mode.test.ts
```

Expected: PASS.

- [ ] **Step 10: Commit semantic mapping**

```bash
git add extension/src/renderer extension/tests/unit/neutral-ramp.test.ts extension/tests/unit/contrast.test.ts extension/tests/unit/omarchy-mapper.test.ts extension/tests/unit/source-mode.test.ts
git commit -m "feat: map website colors to Omarchy semantics"
```

---

### Task 4: Implement preservation and declarative compatibility rules

**Files:**
- Create: `extension/src/content/preservation.ts`
- Create: `extension/src/compat/schema.ts`
- Create: `extension/src/compat/rules.ts`
- Create: `extension/src/compat/sites/generic.ts`
- Test: `extension/tests/unit/preservation.test.ts`
- Test: `extension/tests/unit/compatibility-rules.test.ts`

**Interfaces:**
- Produces: `CompatibilityRule` exactly matching the design spec.
- Produces: `validateCompatibilityRule(value: unknown): CompatibilityRule`.
- Produces: `getCompatibilityRule(hostname: string): CompatibilityRule | null`.
- Produces: `toDynamicThemeFix(rule: CompatibilityRule | null): DynamicThemeFix[]`.
- Produces: `classifyPreservation(element: Element): "preserve" | "theme-ui" | "unknown"`.
- Consumes: vendored `DynamicThemeFix` type and project settings.

- [ ] **Step 1: Write failing schema and preservation tests**

Required schema cases:

- accepts only exact documented fields;
- each selector array contains unique strings of `1..512` characters;
- total selectors per rule are capped at `256`;
- rule ID matches `^[a-z0-9][a-z0-9-]{0,63}$`;
- matches contain exact hostnames or `*.` wildcard hostnames only;
- rejects JavaScript URLs, HTML, and fields such as `script` or `remoteUrl`.

Required preservation cases:

```ts
expect(classifyPreservation(document.createElement("img"))).toBe("preserve");
expect(classifyPreservation(document.createElement("video"))).toBe("preserve");
expect(classifyPreservation(document.createElement("canvas"))).toBe("preserve");
expect(classifyPreservation(document.createElement("button"))).toBe("theme-ui");
```

Also preserve `picture`, `object[type^="image/"]`, external `<svg><image>`, elements with reliable `contenteditable` authored-body boundaries, color swatches (`input[type=color]` and `[role=img][aria-label*="color"]` only when a bundled rule marks them), and CAPTCHA selectors through compatibility rules.

- [ ] **Step 2: Run tests and verify the red state**

```bash
npm test -- tests/unit/preservation.test.ts tests/unit/compatibility-rules.test.ts
```

Expected: FAIL because modules do not exist.

- [ ] **Step 3: Implement the exact compatibility contract**

```ts
export interface CompatibilityRule {
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

Normalize exact hostnames through PR 1’s `normalizeHostname()`. Wildcards match subdomains only: `*.example.com` matches `a.example.com`, not `example.com`.

- [ ] **Step 4: Add the generic preservation rule**

```ts
export const GENERIC_RULE: CompatibilityRule = {
  id: "generic",
  matches: ["*"],
  preserve: [
    "img",
    "picture",
    "video",
    "canvas",
    "object[type^='image/']",
    "embed[type^='image/']",
    "input[type='color']",
    "[data-omarchy-theme-bridge-preserve]",
  ],
  preserveUserContent: [
    "[data-omarchy-theme-bridge-user-content]",
  ],
  preserveInlineSvg: [
    "svg[aria-label][role='img']",
  ],
};
```

Do not infer authored content from generic text content. Rich editors and mail applications receive site-specific rules in PR 4.

- [ ] **Step 5: Translate compatibility rules into engine fixes and project CSS**

Dark Reader fix translation:

```ts
return [{
  url: [hostnamePattern],
  invert: [],
  css: generatedCompatibilityCss,
  ignoreInlineStyle: [...preserve, ...preserveUserContent, ...disableSelector],
  ignoreImageAnalysis: ["*"],
  ignoreCSSUrl: [],
  disableStyleSheetsProxy: false,
  disableCustomElementRegistryProxy: false,
}];
```

`ignoreImageAnalysis: ["*"]` is mandatory because the product never filters or analyzes media pixels. Generate CSS only from validated selectors and fixed property templates; selector strings are data, never executable code.

- [ ] **Step 6: Run preservation tests**

```bash
npm run typecheck
npm test -- tests/unit/preservation.test.ts tests/unit/compatibility-rules.test.ts
```

Expected: PASS.

- [ ] **Step 7: Commit preservation and rule infrastructure**

```bash
git add extension/src/content/preservation.ts extension/src/compat extension/tests/unit/preservation.test.ts extension/tests/unit/compatibility-rules.test.ts
git commit -m "feat: preserve media and validate site rules"
```

---

### Task 5: Implement Adaptive, Accent, Off, and atomic renderer generations

**Files:**
- Create: `extension/src/renderer/darkreader-theme.ts`
- Create: `extension/src/renderer/engine-adapter.ts`
- Create: `extension/src/renderer/generation.ts`
- Create: `extension/src/content/accent-style.ts`
- Create: `extension/src/content/renderer-controller.ts`
- Modify: `extension/src/content/content-script.ts`
- Test: `extension/tests/unit/darkreader-theme.test.ts`
- Test: `extension/tests/unit/generation.test.ts`
- Test: `extension/tests/unit/accent-style.test.ts`
- Test: `extension/tests/integration/renderer-controller.test.ts`

**Interfaces:**
- Produces: `RendererEngine` with `start`, `update`, `stop`, and `getStatus` from the spec.
- Produces: `RendererController.apply(state: ApplyState): Promise<void>` and `dispose(): Promise<void>`.
- Consumes: mapper, compatibility, preservation, source-mode inference, and PR 1 internal state messages.

- [ ] **Step 1: Define exact renderer interfaces**

```ts
export interface RendererStartOptions {
  theme: OmarchyTheme;
  hostname: string | null;
  iframe: boolean;
  signal: AbortSignal;
}

export interface RendererUpdateOptions extends RendererStartOptions {}

export type RendererStatus =
  | {state: "idle"}
  | {state: "preparing"; generation: string}
  | {state: "active"; generation: string; mode: "adaptive" | "accent"; compatibilityRuleId: string | null}
  | {state: "degraded"; retainedGeneration?: string; errorCode: "RENDERER_PREPARE_FAILED" | "RENDERER_COMMIT_FAILED"};

export interface RendererEngine {
  start(options: RendererStartOptions): Promise<void>;
  update(options: RendererUpdateOptions): Promise<void>;
  stop(): Promise<void>;
  getStatus(): RendererStatus;
}
```

- [ ] **Step 2: Write failing translation, generation, and lifecycle tests**

Required assertions:

- dark Omarchy mode maps to Dark Reader `mode: 1`; light maps to `mode: 0`;
- background/text poles use active theme colors and no sepia/grayscale/filter effects;
- `styleSystemControls: true`, selection uses Omarchy selection, scrollbar uses muted/accent-derived value;
- starting generation B aborts preparation for generation A;
- failed B leaves A’s committed style active;
- Off removes bootstrap, Accent style, engine styles, observers, and generation caches;
- Accent CSS contains `:any-link`, `:focus-visible`, form `accent-color`, `::selection`, and `@media print`, but contains no wildcard text/background override;
- repeated application of the same generation/mode is a no-op.

- [ ] **Step 3: Run tests and verify the red state**

```bash
npm test -- tests/unit/darkreader-theme.test.ts tests/unit/generation.test.ts tests/unit/accent-style.test.ts tests/integration/renderer-controller.test.ts
```

Expected: FAIL because renderer lifecycle modules do not exist.

- [ ] **Step 4: Translate Omarchy state to a neutral Dark Reader theme shell**

```ts
export function toDarkReaderTheme(theme: OmarchyTheme): Theme {
  return {
    mode: theme.mode === "dark" ? 1 : 0,
    brightness: 100,
    contrast: 100,
    grayscale: 0,
    sepia: 0,
    useFont: false,
    fontFamily: "",
    textStroke: 0,
    engine: 1,
    stylesheet: "",
    darkSchemeBackgroundColor: theme.colors.canvas,
    darkSchemeTextColor: theme.colors.text,
    lightSchemeBackgroundColor: theme.colors.canvas,
    lightSchemeTextColor: theme.colors.text,
    scrollbarColor: theme.colors.border,
    selectionColor: theme.colors.selection,
    styleSystemControls: true,
    lightColorScheme: "light",
    darkColorScheme: "dark",
    immediateModify: false,
  };
}
```

Use the vendored enum value for Dynamic engine instead of a magic number if the dependency closure exports it.

- [ ] **Step 5: Implement the engine adapter and install the color hook**

On start/update:

1. infer source mode once per navigation;
2. create one `OmarchyMapper` and generation cache;
3. call `setOmarchyColorHook((kind, color) => mapper.map({...}).value)`;
4. convert validated compatibility rules to dynamic fixes;
5. call vendored `createOrUpdateDynamicTheme()`;
6. mark generated Dark Reader styles with `data-omarchy-theme-bridge-generation` after preparation;
7. await one animation frame and verify required generated style containers exist;
8. commit status only when the AbortSignal is current.

On stop:

- call `removeDynamicTheme()` and cleanup cache exports;
- call `clearOmarchyColorHook()`;
- remove project-owned attributes/styles;
- retire generation caches.

Only one engine instance exists per frame.

- [ ] **Step 6: Generate conservative Accent CSS**

Use CSS variables on `:root` and narrow selectors:

```css
:root {
  --otb-accent: var(--generated-accent);
  --otb-selection: var(--generated-selection);
  --otb-border: var(--generated-border);
}
:any-link { color: var(--otb-accent) !important; }
:where(button, [role="button"], input, select, textarea):focus-visible {
  outline: 2px solid var(--otb-accent) !important;
  outline-offset: 2px;
}
:where(input[type="checkbox"], input[type="radio"], input[type="range"], progress) {
  accent-color: var(--otb-accent) !important;
}
::selection { background: var(--otb-selection) !important; }
@media print { :root { --otb-accent: initial; --otb-selection: initial; --otb-border: initial; } }
```

Primary buttons are recolored only through validated compatibility selectors, not every generic `button` background.

- [ ] **Step 7: Implement generation ownership and atomic controller behavior**

`GenerationCoordinator.begin(generation)` aborts the previous pending controller and returns `{signal, isCurrent, commit, fail}`.

Controller transition matrix:

```text
Adaptive → same Adaptive/generation: no-op
Adaptive → newer Adaptive: engine update; commit newest only
Adaptive → Accent: stop engine, then atomically install Accent style
Accent → Adaptive: prepare engine, then remove Accent after engine commit
Any → Off: remove all generated styles and bootstrap
Any → null theme: retain bootstrap only if a valid cached theme exists; otherwise original page
failure with previous active generation: retain previous generation and report degraded
failure without previous generation: remove incomplete output and restore original page
```

Do not leave both full Adaptive and Accent layers active after commit.

- [ ] **Step 8: Wire content messages and bounded renderer status**

`content-script.ts` creates one controller, applies the initial `state.get` response, listens for `state.apply`, and sends:

```ts
{
  type: "renderer.status",
  state: "active" | "idle" | "degraded",
  generation?: string,
  mode?: "adaptive" | "accent",
  errorCode?: "RENDERER_PREPARE_FAILED" | "RENDERER_COMMIT_FAILED",
  compatibilityRuleId?: string,
}
```

No hostname, URL, selector, source CSS, or page text is included.

- [ ] **Step 9: Run lifecycle tests and build**

```bash
npm run vendor:check
npm run typecheck
npm test -- tests/unit/darkreader-theme.test.ts tests/unit/generation.test.ts tests/unit/accent-style.test.ts tests/integration/renderer-controller.test.ts
npm run build
```

Expected: PASS.

- [ ] **Step 10: Commit renderer lifecycle**

```bash
git add extension/src/renderer extension/src/content extension/tests/unit extension/tests/integration
git commit -m "feat: apply Adaptive and Accent website themes"
```

---

### Task 6: Add deterministic fixture pages and extension-driven browser tests

**Files:**
- Create: `extension/tests/fixtures/index.html`
- Create: `extension/tests/fixtures/styles.css`
- Create: `extension/tests/fixtures/app.ts`
- Create: `extension/tests/fixtures/assets/photo.svg`
- Create: `extension/tests/fixtures/assets/avatar.svg`
- Create: `extension/tests/browser/extension-context.ts`
- Create: `extension/tests/browser/adaptive.spec.ts`
- Create: `extension/tests/browser/accent-off.spec.ts`
- Create: `extension/tests/browser/dynamic.spec.ts`
- Modify: `extension/playwright.config.ts`
- Modify: `extension/package.json`

**Interfaces:**
- Produces: local fixture URL with neutral surfaces, chromatic states, media, gradients, inline styles, pseudo-elements, and dynamic insertions.
- Produces: `launchExtensionContext(theme: OmarchyTheme): Promise<ExtensionTestContext>`.
- Consumes: built extension and renderer controller.

- [ ] **Step 1: Build one deterministic fixture that exposes semantic boundaries**

The page must include stable IDs:

```html
<main id="canvas">
  <nav id="surface">Navigation</nav>
  <section id="raised">
    <h1 id="primary-text">Heading</h1>
    <p id="muted-text">Metadata</p>
    <a id="link" href="#target">Link</a>
    <button id="button">Action</button>
    <div id="danger">Error</div>
    <div id="success">Success</div>
    <div id="warning">Warning</div>
    <img id="photo" src="/assets/photo.svg" alt="fixture photo">
    <canvas id="chart" width="40" height="40"></canvas>
    <div id="gradient"></div>
    <div id="pseudo"></div>
    <div id="dynamic-root"></div>
  </section>
</main>
```

Draw exact red, green, and blue pixels on the canvas. The photo SVG contains a fixed multicolor checker pattern. The dynamic app adds a styled card after 100 ms and changes one CSS variable after 200 ms.

- [ ] **Step 2: Create a Playwright extension context helper**

Build the extension, launch a persistent bundled Chromium context with:

```ts
args: [
  `--disable-extensions-except=${extensionPath}`,
  `--load-extension=${extensionPath}`,
]
```

Find the extension service worker, obtain the extension ID from its URL, and seed `chrome.storage.local` from the worker context with:

```ts
{
  "bridge.theme": theme,
  "bridge.settings": DEFAULT_SETTINGS,
  "bridge.schemaVersion": 1,
}
```

Native-host absence is expected in fixture tests; the cached theme remains authoritative.

- [ ] **Step 3: Write failing browser assertions**

Adaptive assertions:

- root background equals theme canvas;
- raised surface differs perceptually from canvas and remains in the theme neutral family;
- primary and muted text differ and both meet intended local contrast;
- link/focus uses accent;
- danger/success/warning remain distinguishable;
- layout bounding boxes match Off mode within one CSS pixel;
- computed `filter` on image/video/canvas is `none`;
- screenshot pixel samples inside the SVG image and canvas are identical between Off and Adaptive.

Dynamic assertions:

- inserted card is themed within 500 ms;
- changed CSS variable is reprocessed;
- no duplicate generated style containers after ten mutations;
- Off removes generated containers and restores original computed colors.

- [ ] **Step 4: Run browser tests and verify the red state**

```bash
npm run build
npm run test:browser -- tests/browser/adaptive.spec.ts tests/browser/accent-off.spec.ts tests/browser/dynamic.spec.ts
```

Expected: tests initially expose missing integration defects; fix only renderer/controller code needed by these deterministic cases.

- [ ] **Step 5: Stabilize screenshots and pixel comparisons**

Use a fixed viewport `1280x800`, bundled fonts only, animations disabled, and `deviceScaleFactor: 1`. Store baseline screenshots only for local fixtures. Compare preserved-media crops with `pixelmatch` at threshold `0`; add `pixelmatch` and `pngjs` as exact dev dependencies.

- [ ] **Step 6: Run full PR 2 verification**

```bash
npm run vendor:check
npm run typecheck
npm test
npm run build
npm run test:browser
```

Expected: PASS.

- [ ] **Step 7: Commit deterministic fixtures**

```bash
git add extension/tests extension/package.json extension/package-lock.json extension/playwright.config.ts
git commit -m "test: verify renderer against deterministic pages"
```

---

### Task 7: Document renderer behavior and open PR 2

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Create: `docs/compatibility.md`
- Create: `docs/renderer.md`
- Create: `scripts/verify-pr2.sh`

**Interfaces:**
- Produces: renderer support matrix, preservation contract, vendoring update procedure, and one PR 2 verification command.
- Consumes: Tasks 1–6.

- [ ] **Step 1: Document exact renderer capabilities and exclusions**

Describe:

- Adaptive, Accent, and Off behavior;
- semantic mapping and contrast repair without a universal WCAG claim;
- preserved media/content list;
- source-mode inference limits;
- open Shadow DOM/adopted stylesheet status as implemented, not aspirational;
- closed Shadow DOM, browser pages, PDF viewer, canvas recoloring, maps, and media recoloring as unsupported;
- conflict detection as best-effort only.

- [ ] **Step 2: Document Dark Reader provenance and update procedure**

`docs/renderer.md` must name:

```text
repository: darkreader/darkreader
tag: v4.9.130
commit: f235365a039183e75fc91d7e22edd724d7b697ec
entry: src/inject/dynamic-theme/index.ts
local modification: five-kind Omarchy color hook
```

Update command:

```bash
cd extension
npm run vendor:darkreader
npm run vendor:check
npm test
npm run build
```

Any upstream change requires reviewing changed dependency closure, hashes, compile-time flags, and hook anchors.

- [ ] **Step 3: Add the PR 2 verification script**

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
./scripts/verify-pr2.sh
```

Expected: exit `0`; retain complete output.

- [ ] **Step 5: Perform scoped manual smoke checks when browsers are available**

With a valid installed native host, test one normal static page and one local fixture in both Chrome and Chromium:

```text
Adaptive applies active Omarchy generation
Accent preserves page foundation
Off restores original page
theme switch updates without reload
image/video/canvas pixels remain unchanged
```

Record each browser separately as PASS, FAIL, or PENDING. Do not claim YouTube/GitHub qualification yet; those belong to PR 4.

- [ ] **Step 6: Commit documentation and verifier**

```bash
git add README.md docs scripts/verify-pr2.sh
git commit -m "docs: document semantic renderer behavior"
```

- [ ] **Step 7: Review and open Draft PR 2**

```bash
git diff --check main...HEAD
git log --oneline main..HEAD
git diff --stat main...HEAD
git push -u origin feat/renderer-semantic-mapper
```

Open a Draft PR to `main` titled:

```text
Renderer: adapt website interfaces to Omarchy themes
```

Include fresh automated results, separate Chrome/Chromium local status, preserved-content evidence, Dark Reader provenance, known limitations, and the next plan path `docs/superpowers/plans/2026-09-04-product-controls.md`.
