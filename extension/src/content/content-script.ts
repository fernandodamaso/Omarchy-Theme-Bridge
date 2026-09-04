import {isApplyState, type ApplyState} from "../shared/internal-messages";
import {isExtensionSettings, resolveSiteMode} from "../shared/settings";
import {isOmarchyTheme} from "../shared/theme";
import {STORAGE_KEYS} from "../background/state-store";
import {applyBootstrap, removeBootstrap} from "./bootstrap";

const CONTENT_GUARD = "__omarchyThemeBridgeContentV1";
const globalScope = globalThis as typeof globalThis & Record<string, unknown>;

function applyState(state: ApplyState): void {
  if (!state.enabled || state.mode === "off" || !state.theme) {
    removeBootstrap();
    return;
  }
  applyBootstrap(state.theme);
}

async function cachedState(): Promise<ApplyState | null> {
  const stored = await chrome.storage.local.get([STORAGE_KEYS.theme, STORAGE_KEYS.settings]);
  const theme = stored[STORAGE_KEYS.theme];
  const settings = stored[STORAGE_KEYS.settings];
  if (!isOmarchyTheme(theme) || !isExtensionSettings(settings)) return null;
  if (location.protocol !== "http:" && location.protocol !== "https:") return null;
  return {
    type: "state.apply",
    enabled: settings.enabled,
    mode: resolveSiteMode(settings, location.hostname),
    theme,
  };
}

async function initialize(): Promise<void> {
  try {
    const cached = await cachedState();
    if (cached) applyState(cached);
  } catch {
    removeBootstrap();
  }

  chrome.runtime.onMessage.addListener((message: unknown) => {
    if (isApplyState(message)) applyState(message);
  });

  try {
    const response: unknown = await chrome.runtime.sendMessage({type: "content.ready"});
    if (isApplyState(response)) applyState(response);
  } catch {
    // Cached state remains useful while the service worker restarts.
  }
}

if (!globalScope[CONTENT_GUARD]) {
  globalScope[CONTENT_GUARD] = true;
  void initialize();
}
