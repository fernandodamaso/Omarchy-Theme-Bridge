import {beforeEach, describe, expect, it} from "vitest";
import {installFakeChrome} from "../helpers/fake-chrome";
import {NativeConnection, RECONNECT_ALARM} from "../../src/background/native-connection";
import {BridgeStateStore} from "../../src/background/state-store";
import {TOKYO_THEME} from "../helpers/themes";

beforeEach(() => installFakeChrome());

describe("NativeConnection", () => {
  it("sends hello and accepts ready plus snapshot", async () => {
    const fake = installFakeChrome();
    const store = new BridgeStateStore();
    await store.initialize();
    const connection = new NativeConnection(store, "0.1.0");
    await connection.requestReconnect();
    const port = fake.runtime.latestNativePort();
    expect(port.posted).toEqual([{
      type: "hello",
      protocolVersion: 1,
      extensionVersion: "0.1.0",
    }]);

    port.emitMessage({type: "host.ready", protocolVersion: 1, hostVersion: "0.1.0"});
    port.emitMessage({type: "theme.snapshot", theme: TOKYO_THEME});
    await fake.flush();
    expect((await store.get()).theme?.generation).toBe(TOKYO_THEME.generation);
    expect((await store.get()).connection.connected).toBe(true);
  });

  it("stores invalid messages and disconnects the unsafe port", async () => {
    const fake = installFakeChrome();
    const store = new BridgeStateStore();
    await store.initialize();
    const connection = new NativeConnection(store, "0.1.0");
    await connection.requestReconnect();
    const port = fake.runtime.latestNativePort();
    port.emitMessage({type: "theme.changed", theme: TOKYO_THEME, url: "https://example.com"});
    await fake.flush();
    expect((await store.get()).connection.error).toBe("HOST_MESSAGE_INVALID");
    expect(port.disconnected).toBe(true);
  });

  it("schedules one alarm after bounded immediate disconnect retries", async () => {
    const fake = installFakeChrome();
    const store = new BridgeStateStore();
    await store.initialize();
    const connection = new NativeConnection(store, "0.1.0");
    await connection.requestReconnect();
    fake.runtime.disconnectLatest("Specified native messaging host not found.");
    await fake.flush();
    fake.runtime.disconnectLatest("Specified native messaging host not found.");
    await fake.flush();
    fake.runtime.disconnectLatest("Specified native messaging host not found.");
    await fake.flush();
    expect(fake.alarms.created.filter((alarm) => alarm.name === RECONNECT_ALARM)).toHaveLength(1);
    expect((await store.get()).connection.error).toBe("HOST_NOT_FOUND");
  });

  it("keeps the retry budget bounded when the host repeatedly becomes ready then crashes", async () => {
    const fake = installFakeChrome();
    const store = new BridgeStateStore();
    await store.initialize();
    const connection = new NativeConnection(store, "0.1.0");
    await connection.requestReconnect();

    for (let attempt = 0; attempt < 3; attempt += 1) {
      const port = fake.runtime.latestNativePort();
      port.emitMessage({type: "host.ready", protocolVersion: 1, hostVersion: "0.1.0"});
      await fake.flush();
      fake.runtime.disconnectLatest("Native host exited after handshake.");
      await fake.flush();
    }

    expect(fake.runtime.nativePorts).toHaveLength(3);
    expect(fake.alarms.created.filter((alarm) => alarm.name === RECONNECT_ALARM)).toHaveLength(1);
  });
});
