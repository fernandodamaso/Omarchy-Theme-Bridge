import {hasAllowedKeys, hasExactKeys, isBoundedString, isCanonicalColor, isRecord} from "./validation";

export type ThemeMode = "dark" | "light";
export type CanonicalColor = `#${string}`;
export type ThemeGeneration = `sha256:${string}`;

export const SEMANTIC_COLOR_KEYS = [
  "canvas",
  "surface",
  "surfaceRaised",
  "surfaceInset",
  "text",
  "textStrong",
  "textMuted",
  "border",
  "accent",
  "selection",
  "danger",
  "success",
  "warning",
  "info",
  "magenta",
  "cyan",
] as const;

export const SOURCE_REQUIRED_KEYS = ["background", "foreground"] as const;
export const SOURCE_OPTIONAL_KEYS = [
  "darkBackground",
  "darkerBackground",
  "lighterBackground",
  "darkForeground",
  "lightForeground",
  "brightForeground",
] as const;

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

export function isThemeGeneration(value: unknown): value is ThemeGeneration {
  return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value);
}

export function isOmarchyTheme(value: unknown): value is OmarchyTheme {
  if (!isRecord(value) || !hasExactKeys(value, [
    "schemaVersion",
    "generation",
    "name",
    "mode",
    "colors",
    "source",
  ])) {
    return false;
  }

  if (value.schemaVersion !== 1
    || !isThemeGeneration(value.generation)
    || !isBoundedString(value.name)
    || (value.mode !== "dark" && value.mode !== "light")
    || !isRecord(value.colors)
    || !isRecord(value.source)) {
    return false;
  }

  if (!hasExactKeys(value.colors, SEMANTIC_COLOR_KEYS)) {
    return false;
  }
  if (!Object.values(value.colors).every(isCanonicalColor)) {
    return false;
  }
  if (!hasAllowedKeys(value.source, SOURCE_REQUIRED_KEYS, SOURCE_OPTIONAL_KEYS)) {
    return false;
  }
  return Object.values(value.source).every(isCanonicalColor);
}
