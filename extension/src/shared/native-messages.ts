import {THEME_ERROR_CODES, type ThemeErrorCode} from "./errors";
import {isOmarchyTheme, isThemeGeneration, type OmarchyTheme} from "./theme";
import {hasAllowedKeys, hasExactKeys, isBoundedString, isRecord} from "./validation";

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

export function parseExtensionMessage(value: unknown): ExtensionToHost {
  if (!isRecord(value) || typeof value.type !== "string") {
    throw new Error("Invalid extension message");
  }
  switch (value.type) {
    case "hello":
      if (!hasExactKeys(value, ["type", "protocolVersion", "extensionVersion"])
        || value.protocolVersion !== 1
        || !isBoundedString(value.extensionVersion)) {
        throw new Error("Invalid hello message");
      }
      return value as ExtensionToHost;
    case "theme.reload":
      if (!hasExactKeys(value, ["type"])) throw new Error("Invalid reload message");
      return {type: "theme.reload"};
    case "ping":
      if (!hasExactKeys(value, ["type", "requestId"])
        || !isBoundedString(value.requestId)) {
        throw new Error("Invalid ping message");
      }
      return value as ExtensionToHost;
    default:
      throw new Error("Unsupported extension message");
  }
}

export function parseHostMessage(value: unknown): HostToExtension {
  if (!isRecord(value) || typeof value.type !== "string") {
    throw new Error("Invalid host message");
  }
  switch (value.type) {
    case "host.ready":
      if (!hasExactKeys(value, ["type", "protocolVersion", "hostVersion"])
        || value.protocolVersion !== 1
        || !isBoundedString(value.hostVersion)) {
        throw new Error("Invalid ready message");
      }
      return value as HostToExtension;
    case "theme.snapshot":
    case "theme.changed":
      if (!hasExactKeys(value, ["type", "theme"]) || !isOmarchyTheme(value.theme)) {
        throw new Error("Invalid theme message");
      }
      return value as HostToExtension;
    case "theme.error": {
      if (!hasAllowedKeys(value, ["type", "code"], ["retainedGeneration"])
        || !THEME_ERROR_CODES.includes(value.code as ThemeErrorCode)
        || (value.retainedGeneration !== undefined && !isThemeGeneration(value.retainedGeneration))) {
        throw new Error("Invalid theme error message");
      }
      return value as HostToExtension;
    }
    case "pong":
      if (!hasExactKeys(value, ["type", "requestId"]) || !isBoundedString(value.requestId)) {
        throw new Error("Invalid pong message");
      }
      return value as HostToExtension;
    default:
      throw new Error("Unsupported host message");
  }
}
