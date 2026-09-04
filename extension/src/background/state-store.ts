import type {ConnectionErrorCode, ThemeErrorCode} from "../shared/errors";
import {parseHostMessage, type HostToExtension} from "../shared/native-messages";
import {DEFAULT_SETTINGS, isExtensionSettings, type ExtensionSettings} from "../shared/settings";
import {isOmarchyTheme, type OmarchyTheme} from "../shared/theme";
import {isRecord} from "../shared/validation";

export const STORAGE_KEYS = {
  schemaVersion: "bridge.schemaVersion",
  theme: "bridge.theme",
  settings: "bridge.settings",
  connection: "bridge.connection",
  themeError: "bridge.themeError",
} as const;

export interface ConnectionState {
  connected: boolean;
  hostVersion?: string;
  error?: ConnectionErrorCode;
  changedAt: number;
}

export interface BridgeState {
  schemaVersion: 1;
  theme: OmarchyTheme | null;
  settings: ExtensionSettings;
  connection: ConnectionState;
  themeError?: ThemeErrorCode;
}

function cloneSettings(settings: ExtensionSettings): ExtensionSettings {
  return {
    schemaVersion: 1,
    enabled: settings.enabled,
    defaultMode: "adaptive",
    hostnameOverrides: {...settings.hostnameOverrides},
  };
}

function cloneState(state: BridgeState): BridgeState {
  const result: BridgeState = {
    schemaVersion: 1,
    theme: state.theme ? structuredClone(state.theme) : null,
    settings: cloneSettings(state.settings),
    connection: {...state.connection},
  };
  if (state.themeError) result.themeError = state.themeError;
  return result;
}

function isConnectionState(value: unknown): value is ConnectionState {
  if (!isRecord(value) || typeof value.connected !== "boolean" || typeof value.changedAt !== "number") {
    return false;
  }
  if (value.hostVersion !== undefined && typeof value.hostVersion !== "string") return false;
  if (value.error !== undefined && ![
    "HOST_NOT_FOUND",
    "HOST_DISCONNECTED",
    "HOST_PROTOCOL_ERROR",
    "HOST_MESSAGE_INVALID",
  ].includes(value.error as string)) return false;
  return Object.keys(value).every((key) => ["connected", "hostVersion", "error", "changedAt"].includes(key));
}

export class BridgeStateStore {
  private initialization: Promise<BridgeState> | null = null;
  private state: BridgeState | null = null;

  initialize(): Promise<BridgeState> {
    if (!this.initialization) this.initialization = this.load();
    return this.initialization.then(cloneState);
  }

  private async load(): Promise<BridgeState> {
    const stored = await chrome.storage.local.get(Object.values(STORAGE_KEYS));
    const storedSettings = stored[STORAGE_KEYS.settings];
    const storedTheme = stored[STORAGE_KEYS.theme];
    const storedConnection = stored[STORAGE_KEYS.connection];
    const settings = isExtensionSettings(storedSettings)
      ? cloneSettings(storedSettings)
      : cloneSettings(DEFAULT_SETTINGS);
    const theme = isOmarchyTheme(storedTheme)
      ? structuredClone(storedTheme)
      : null;
    const connection: ConnectionState = isConnectionState(storedConnection)
      ? {...storedConnection}
      : {connected: false, changedAt: 0};
    const state: BridgeState = {
      schemaVersion: 1,
      theme,
      settings,
      connection,
    };
    const themeError = stored[STORAGE_KEYS.themeError];
    if (typeof themeError === "string" && [
      "THEME_NOT_FOUND",
      "THEME_INVALID",
      "THEME_UNSUPPORTED_COLOR",
      "CALLER_FORBIDDEN",
      "PROTOCOL_MISMATCH",
    ].includes(themeError)) {
      state.themeError = themeError as ThemeErrorCode;
    }
    this.state = state;
    await chrome.storage.local.set({
      [STORAGE_KEYS.schemaVersion]: 1,
      [STORAGE_KEYS.settings]: settings,
      [STORAGE_KEYS.connection]: connection,
      ...(theme ? {[STORAGE_KEYS.theme]: theme} : {}),
      ...(state.themeError ? {[STORAGE_KEYS.themeError]: state.themeError} : {}),
    });
    return state;
  }

  async get(): Promise<BridgeState> {
    await this.initialize();
    if (!this.state) throw new Error("Bridge state failed to initialize");
    return cloneState(this.state);
  }

  async applyHostMessage(input: HostToExtension | unknown): Promise<BridgeState> {
    const message = parseHostMessage(input);
    await this.initialize();
    if (!this.state) throw new Error("Bridge state failed to initialize");

    if (message.type === "pong") return cloneState(this.state);

    if (message.type === "host.ready") {
      const connection: ConnectionState = {
        connected: true,
        hostVersion: message.hostVersion,
        changedAt: Date.now(),
      };
      this.state = {...this.state, connection};
      await chrome.storage.local.set({[STORAGE_KEYS.connection]: connection});
      return cloneState(this.state);
    }

    if (message.type === "theme.snapshot" || message.type === "theme.changed") {
      const sameGeneration = this.state.theme?.generation === message.theme.generation;
      const alreadyHealthy = this.state.connection.connected && !this.state.themeError;
      if (sameGeneration && alreadyHealthy) return cloneState(this.state);
      const connection: ConnectionState = {
        ...this.state.connection,
        connected: true,
        changedAt: Date.now(),
      };
      delete connection.error;
      this.state = {
        ...this.state,
        theme: structuredClone(message.theme),
        connection,
      };
      delete this.state.themeError;
      await chrome.storage.local.set({
        [STORAGE_KEYS.theme]: message.theme,
        [STORAGE_KEYS.connection]: connection,
      });
      await chrome.storage.local.remove(STORAGE_KEYS.themeError);
      return cloneState(this.state);
    }

    this.state = {...this.state, themeError: message.code};
    await chrome.storage.local.set({[STORAGE_KEYS.themeError]: message.code});
    return cloneState(this.state);
  }

  async setConnectionError(error: ConnectionErrorCode): Promise<BridgeState> {
    await this.initialize();
    if (!this.state) throw new Error("Bridge state failed to initialize");
    const connection: ConnectionState = {
      connected: false,
      error,
      changedAt: Date.now(),
    };
    this.state = {...this.state, connection};
    await chrome.storage.local.set({[STORAGE_KEYS.connection]: connection});
    return cloneState(this.state);
  }

  async updateSettings(settings: ExtensionSettings): Promise<BridgeState> {
    if (!isExtensionSettings(settings)) throw new Error("Invalid settings");
    await this.initialize();
    if (!this.state) throw new Error("Bridge state failed to initialize");
    const next = cloneSettings(settings);
    this.state = {...this.state, settings: next};
    await chrome.storage.local.set({[STORAGE_KEYS.settings]: next});
    return cloneState(this.state);
  }
}
