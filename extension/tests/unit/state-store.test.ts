import {beforeEach, describe, expect, it} from "vitest";
import {installFakeChrome} from "../helpers/fake-chrome";
import {BridgeStateStore, STORAGE_KEYS} from "../../src/background/state-store";
import {TOKYO_THEME} from "../helpers/themes";

beforeEach(() => installFakeChrome());

describe("BridgeStateStore", () => {
  it("creates safe defaults when storage is empty", async () => {
    const state = await new BridgeStateStore().initialize();
    expect(state.settings).toEqual({
      schemaVersion: 1,
      enabled: true,
      defaultMode: "adaptive",
      hostnameOverrides: {},
    });
    expect(state.theme).toBeNull();
    expect(state.connection.connected).toBe(false);
  });

  it("retains the current theme after a safe theme error", async () => {
    const store = new BridgeStateStore();
    await store.initialize();
    await store.applyHostMessage({type: "theme.snapshot", theme: TOKYO_THEME});
    const state = await store.applyHostMessage({
      type: "theme.error",
      code: "THEME_INVALID",
      retainedGeneration: TOKYO_THEME.generation,
    });
    expect(state.theme).toEqual(TOKYO_THEME);
    expect(state.themeError).toBe("THEME_INVALID");
  });

  it("does not rewrite storage for a duplicate generation", async () => {
    const fake = installFakeChrome();
    const store = new BridgeStateStore();
    await store.initialize();
    await store.applyHostMessage({type: "theme.snapshot", theme: TOKYO_THEME});
    const writes = fake.storage.local.setCalls.length;
    await store.applyHostMessage({type: "theme.changed", theme: TOKYO_THEME});
    expect(fake.storage.local.setCalls).toHaveLength(writes);
    expect(await fake.storage.local.get(STORAGE_KEYS.theme)).toMatchObject({
      [STORAGE_KEYS.theme]: TOKYO_THEME,
    });
  });
});
