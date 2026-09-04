import type {ConnectionErrorCode} from "../shared/errors";
import {parseHostMessage} from "../shared/native-messages";
import type {BridgeStateStore} from "./state-store";

export const NATIVE_HOST_NAME = "com.omarchy.theme_bridge";
export const RECONNECT_ALARM = "native-reconnect";
export const MAX_IMMEDIATE_RETRIES = 2;
export const RECONNECT_DELAY_MINUTES = 0.5;

export type StateChangedHandler = () => void | Promise<void>;

export class NativeConnection {
  private port: chrome.runtime.Port | null = null;
  private connecting: Promise<void> | null = null;
  private disposed = false;
  private immediateRetries = 0;
  private readyPort: chrome.runtime.Port | null = null;
  private suppressReconnectPort: chrome.runtime.Port | null = null;

  constructor(
    private readonly store: BridgeStateStore,
    private readonly extensionVersion: string,
    private readonly onStateChanged: StateChangedHandler = () => undefined,
  ) {}

  start(): void {
    void this.requestReconnect();
  }

  async requestReconnect(): Promise<void> {
    if (this.disposed || this.port) return;
    if (this.connecting) return this.connecting;
    this.connecting = Promise.resolve().then(() => this.openPort()).finally(() => {
      this.connecting = null;
    });
    return this.connecting;
  }

  private openPort(): void {
    if (this.disposed || this.port) return;
    const port = chrome.runtime.connectNative(NATIVE_HOST_NAME);
    this.port = port;
    port.onMessage.addListener((message: unknown) => {
      void this.handleMessage(port, message);
    });
    port.onDisconnect.addListener(() => {
      void this.handleDisconnect(port);
    });
    port.postMessage({
      type: "hello",
      protocolVersion: 1,
      extensionVersion: this.extensionVersion,
    });
  }

  private async handleMessage(port: chrome.runtime.Port, input: unknown): Promise<void> {
    if (this.disposed || this.port !== port) return;
    let message;
    try {
      message = parseHostMessage(input);
    } catch {
      this.suppressReconnectPort = port;
      await this.store.setConnectionError("HOST_MESSAGE_INVALID");
      await this.onStateChanged();
      port.disconnect();
      return;
    }

    if (message.type !== "host.ready" && this.readyPort !== port) {
      this.suppressReconnectPort = port;
      await this.store.setConnectionError("HOST_PROTOCOL_ERROR");
      await this.onStateChanged();
      port.disconnect();
      return;
    }

    if (message.type === "host.ready") {
      this.readyPort = port;
      this.immediateRetries = 0;
      await chrome.alarms.clear(RECONNECT_ALARM);
    }
    await this.store.applyHostMessage(message);
    await this.onStateChanged();
  }

  private async handleDisconnect(port: chrome.runtime.Port): Promise<void> {
    if (this.port !== port) return;
    this.port = null;
    if (this.readyPort === port) this.readyPort = null;
    if (this.disposed) return;

    if (this.suppressReconnectPort === port) {
      this.suppressReconnectPort = null;
      return;
    }

    const error = this.mapDisconnectError(chrome.runtime.lastError?.message);
    await this.store.setConnectionError(error);
    await this.onStateChanged();

    if (this.immediateRetries < MAX_IMMEDIATE_RETRIES) {
      this.immediateRetries += 1;
      await this.requestReconnect();
      return;
    }
    await this.scheduleReconnectAlarm();
  }

  private mapDisconnectError(message: string | undefined): ConnectionErrorCode {
    if (message?.toLowerCase().includes("native messaging host not found")) return "HOST_NOT_FOUND";
    return "HOST_DISCONNECTED";
  }

  private async scheduleReconnectAlarm(): Promise<void> {
    if (await chrome.alarms.get(RECONNECT_ALARM)) return;
    await chrome.alarms.create(RECONNECT_ALARM, {delayInMinutes: RECONNECT_DELAY_MINUTES});
  }

  dispose(): void {
    this.disposed = true;
    const port = this.port;
    this.port = null;
    this.readyPort = null;
    if (port) port.disconnect();
  }
}
