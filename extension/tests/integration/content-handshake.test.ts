import {beforeEach, describe, expect, it, vi} from "vitest";
import {installFakeChrome} from "../helpers/fake-chrome";
import {TOKYO_THEME} from "../helpers/themes";
import {STORAGE_KEYS} from "../../src/background/state-store";

beforeEach(() => {
  vi.resetModules();
  document.documentElement.innerHTML = "<head></head><body></body>";
  delete (globalThis as typeof globalThis & Record<string, unknown>).__omarchyThemeBridgeContentV1;
});

describe("content bootstrap handshake", () => {
  it("applies the cached canvas without sending hostname data", async () => {
    const fake = installFakeChrome();
    await fake.storage.local.set({
      [STORAGE_KEYS.theme]: TOKYO_THEME,
      [STORAGE_KEYS.settings]: {
        schemaVersion: 1,
        enabled: true,
        defaultMode: "adaptive",
        hostnameOverrides: {},
      },
    });
    fake.runtime.sendMessageResponse = {
      type: "state.apply",
      enabled: true,
      mode: "adaptive",
      theme: TOKYO_THEME,
    };

    await import("../../src/content/content-script");
    await fake.flush();

    expect(document.getElementById("omarchy-theme-bridge-bootstrap")).not.toBeNull();
    expect(fake.runtime.sentMessages).toEqual([{type: "content.ready"}]);
    expect(JSON.stringify(fake.runtime.sentMessages)).not.toContain("hostname");
    expect(JSON.stringify(fake.runtime.sentMessages)).not.toContain("http");
  });
});
