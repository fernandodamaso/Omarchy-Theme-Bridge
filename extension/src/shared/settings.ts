import {hasExactKeys, isRecord} from "./validation";

export type SiteMode = "adaptive" | "accent" | "off";

export interface ExtensionSettings {
  schemaVersion: 1;
  enabled: boolean;
  defaultMode: "adaptive";
  hostnameOverrides: Record<string, SiteMode>;
}

export const DEFAULT_SETTINGS: ExtensionSettings = Object.freeze({
  schemaVersion: 1,
  enabled: true,
  defaultMode: "adaptive",
  hostnameOverrides: Object.freeze({}),
});

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

export function isSiteMode(value: unknown): value is SiteMode {
  return value === "adaptive" || value === "accent" || value === "off";
}

export function isExtensionSettings(value: unknown): value is ExtensionSettings {
  if (!isRecord(value) || !hasExactKeys(value, [
    "schemaVersion",
    "enabled",
    "defaultMode",
    "hostnameOverrides",
  ])) {
    return false;
  }
  if (value.schemaVersion !== 1
    || typeof value.enabled !== "boolean"
    || value.defaultMode !== "adaptive"
    || !isRecord(value.hostnameOverrides)) {
    return false;
  }

  try {
    return Object.entries(value.hostnameOverrides).every(([hostname, mode]) => (
      normalizeHostname(hostname) === hostname && isSiteMode(mode)
    ));
  } catch {
    return false;
  }
}

export function resolveSiteMode(settings: ExtensionSettings, hostname: string): SiteMode {
  if (!settings.enabled) return "off";
  return settings.hostnameOverrides[normalizeHostname(hostname)] ?? settings.defaultMode;
}
