import {beforeEach, describe, expect, it, vi} from "vitest";
import {installFakeChrome} from "../helpers/fake-chrome";

beforeEach(() => {
  vi.resetModules();
  installFakeChrome();
});

describe("service worker wiring", () => {
  it("registers the reconnect alarm listener at module evaluation", async () => {
    const fake = installFakeChrome();
    await import("../../src/background/service-worker");
    expect(fake.alarms.onAlarm.listeners).toHaveLength(1);
  });

  it("returns current state to a content frame without exposing a URL", async () => {
    const fake = installFakeChrome();
    await import("../../src/background/service-worker");
    await fake.flush();
    const listener = fake.runtime.onMessage.listeners[0];
    expect(listener).toBeDefined();
    const sendResponse = vi.fn();
    const keepChannelOpen = listener?.(
      {type: "content.ready"},
      {
        id: fake.runtime.id,
        url: "https://example.com/frame",
        tab: {id: 7, url: "https://example.com/page"},
      },
      sendResponse,
    );
    expect(keepChannelOpen).toBe(true);
    await fake.flush();
    expect(sendResponse).toHaveBeenCalledOnce();
    const response = sendResponse.mock.calls[0]?.[0];
    expect(response).toMatchObject({
      type: "state.apply",
      enabled: true,
      mode: "adaptive",
      theme: null,
    });
    expect(JSON.stringify(response)).not.toContain("example.com");
  });

  it("rejects privileged reconnect requests from content-script senders", async () => {
    const fake = installFakeChrome();
    await import("../../src/background/service-worker");
    await fake.flush();
    const listener = fake.runtime.onMessage.listeners[0];
    const sendResponse = vi.fn();
    const keepChannelOpen = listener?.(
      {type: "native.reconnect"},
      {id: fake.runtime.id, tab: {id: 7, url: "https://example.com/"}},
      sendResponse,
    );
    expect(keepChannelOpen).toBe(false);
    expect(sendResponse).not.toHaveBeenCalled();
  });
});
