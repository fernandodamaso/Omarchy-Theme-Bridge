import type {ConnectionErrorCode, ThemeErrorCode} from "./errors";
import type {SiteMode} from "./settings";
import {isOmarchyTheme, type OmarchyTheme} from "./theme";
import {hasExactKeys, isRecord} from "./validation";

export type RendererState = "idle" | "bootstrapped" | "off" | "waiting";

export type InternalRequest =
  | {type: "content.ready"}
  | {type: "state.get"}
  | {type: "native.reconnect"};

export interface ApplyState {
  type: "state.apply";
  enabled: boolean;
  mode: SiteMode;
  theme: OmarchyTheme | null;
}

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

export function parseInternalRequest(value: unknown): InternalRequest {
  if (!isRecord(value) || !hasExactKeys(value, ["type"]) || typeof value.type !== "string") {
    throw new Error("Invalid internal request");
  }
  if (value.type === "content.ready" || value.type === "state.get" || value.type === "native.reconnect") {
    return {type: value.type};
  }
  throw new Error("Unsupported internal request");
}

export function isApplyState(value: unknown): value is ApplyState {
  return isRecord(value)
    && hasExactKeys(value, ["type", "enabled", "mode", "theme"])
    && value.type === "state.apply"
    && typeof value.enabled === "boolean"
    && (value.mode === "adaptive" || value.mode === "accent" || value.mode === "off")
    && (value.theme === null || isOmarchyTheme(value.theme));
}
