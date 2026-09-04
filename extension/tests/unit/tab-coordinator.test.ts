import {beforeEach, describe, expect, it} from "vitest";
import {installFakeChrome} from "../helpers/fake-chrome";
import {BridgeStateStore} from "../../src/background/state-store";
import {TabCoordinator} from "../../src/background/tab-coordinator";
import {TOKYO_THEME} from "../helpers/themes";

beforeEach(() => installFakeChrome());

describe("TabCoordinator", () => {
  it("recovers eligible visible tabs before inactive tabs and skips protected pages", async () => {
    const fake = installFakeChrome();
    fake.tabs.items = [
      {id: 1, url: "https://inactive.example/", active: false, discarded: false},
      {id: 2, url: "chrome://settings", active: true, discarded: false},
      {id: 3, url: "https://active.example/", active: true, discarded: false},
      {id: 4, url: "https://discarded.example/", active: false, discarded: true},
    ];
    fake.tabs.failNextSendFor.add(3);
    const store = new BridgeStateStore();
    await store.initialize();
    await store.applyHostMessage({type: "theme.snapshot", theme: TOKYO_THEME});
    const coordinator = new TabCoordinator(store);
    await coordinator.recoverExistingTabs();

    expect(fake.scripting.executions[0]?.target).toEqual({tabId: 3, allFrames: true});
    expect(fake.tabs.sent.map((entry) => entry.tabId)).toEqual([3, 3, 1]);
    expect(fake.tabs.sent.some((entry) => entry.tabId === 2 || entry.tabId === 4)).toBe(false);
  });
});
