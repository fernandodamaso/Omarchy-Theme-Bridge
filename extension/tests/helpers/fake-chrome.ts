import {vi} from "vitest";

class FakeEvent<T extends (...args: any[]) => any> {
  readonly listeners: T[] = [];

  addListener = (listener: T): void => {
    this.listeners.push(listener);
  };

  removeListener = (listener: T): void => {
    const index = this.listeners.indexOf(listener);
    if (index >= 0) this.listeners.splice(index, 1);
  };

  hasListener = (listener: T): boolean => this.listeners.includes(listener);

  emit(...args: Parameters<T>): void {
    for (const listener of [...this.listeners]) listener(...args);
  }
}

export class FakeNativePort {
  readonly posted: unknown[] = [];
  readonly onMessage = new FakeEvent<(...args: any[]) => any>();
  readonly onDisconnect = new FakeEvent<(...args: any[]) => any>();
  disconnected = false;
  name = "com.omarchy.theme_bridge";
  sender = undefined;

  postMessage = (message: unknown): void => {
    this.posted.push(message);
  };

  disconnect = (): void => {
    if (this.disconnected) return;
    this.disconnected = true;
    this.onDisconnect.emit(this as never);
  };

  emitMessage(message: unknown): void {
    this.onMessage.emit(message as never, this as never);
  }

  emitDisconnect(): void {
    if (this.disconnected) return;
    this.disconnected = true;
    this.onDisconnect.emit(this as never);
  }
}

class FakeStorageArea {
  readonly values = new Map<string, unknown>();
  readonly setCalls: Array<Record<string, unknown>> = [];

  async get(keys?: string | string[] | Record<string, unknown> | null): Promise<Record<string, unknown>> {
    if (keys == null) return Object.fromEntries(this.values);
    const names = typeof keys === "string"
      ? [keys]
      : Array.isArray(keys)
        ? keys
        : Object.keys(keys);
    const result: Record<string, unknown> = {};
    for (const name of names) {
      if (this.values.has(name)) result[name] = this.values.get(name);
      else if (keys && !Array.isArray(keys) && typeof keys === "object") result[name] = keys[name];
    }
    return result;
  }

  async set(items: Record<string, unknown>): Promise<void> {
    this.setCalls.push(structuredClone(items));
    for (const [key, value] of Object.entries(items)) this.values.set(key, structuredClone(value));
  }

  async remove(keys: string | string[]): Promise<void> {
    for (const key of typeof keys === "string" ? [keys] : keys) this.values.delete(key);
  }

  async clear(): Promise<void> {
    this.values.clear();
  }
}

export interface FakeTab {
  id?: number;
  url?: string;
  active?: boolean;
  discarded?: boolean;
  windowId?: number;
}

export interface FakeChrome {
  runtime: {
    id: string;
    lastError?: {message: string};
    onInstalled: FakeEvent<(...args: any[]) => any>;
    onStartup: FakeEvent<(...args: any[]) => any>;
    onMessage: FakeEvent<(...args: any[]) => any>;
    nativePorts: FakeNativePort[];
    sentMessages: unknown[];
    sendMessageResponse: unknown;
    connectNative: (name: string) => FakeNativePort;
    latestNativePort: () => FakeNativePort;
    disconnectLatest: (message: string) => void;
    sendMessage: (message: unknown) => Promise<unknown>;
    getManifest: () => {version: string};
    openOptionsPage: () => Promise<void>;
  };
  storage: {
    local: FakeStorageArea;
    session: FakeStorageArea;
  };
  alarms: {
    onAlarm: FakeEvent<(...args: any[]) => any>;
    created: Array<{name: string; alarmInfo: {delayInMinutes?: number}}> ;
    current: Map<string, {name: string; scheduledTime: number}>;
    create: (name: string, alarmInfo: {delayInMinutes?: number}) => Promise<void>;
    clear: (name: string) => Promise<boolean>;
    get: (name: string) => Promise<{name: string; scheduledTime: number} | undefined>;
  };
  tabs: {
    items: FakeTab[];
    sent: Array<{tabId: number; message: unknown}>;
    failNextSendFor: Set<number>;
    query: (queryInfo: Record<string, unknown>) => Promise<FakeTab[]>;
    sendMessage: (tabId: number, message: unknown) => Promise<unknown>;
    onRemoved: FakeEvent<(...args: any[]) => any>;
  };
  scripting: {
    executions: Array<{target: {tabId: number; allFrames?: boolean}; files?: string[]}>;
    executeScript: (injection: {target: {tabId: number; allFrames?: boolean}; files?: string[]}) => Promise<unknown[]>;
  };
  flush: () => Promise<void>;
}

let installed: FakeChrome | null = null;

export function installFakeChrome(): FakeChrome {
  const local = new FakeStorageArea();
  const session = new FakeStorageArea();
  const nativePorts: FakeNativePort[] = [];
  const onInstalled = new FakeEvent<(...args: any[]) => any>();
  const onStartup = new FakeEvent<(...args: any[]) => any>();
  const onMessage = new FakeEvent<(...args: any[]) => any>();
  const alarmsEvent = new FakeEvent<(...args: any[]) => any>();
  const tabsRemoved = new FakeEvent<(...args: any[]) => any>();

  const fake: FakeChrome = {
    runtime: {
      id: "abcdefghijklmnopabcdefghijklmnop",
      onInstalled,
      onStartup,
      onMessage,
      nativePorts,
      sentMessages: [],
      sendMessageResponse: undefined,
      connectNative: (_name: string) => {
        const port = new FakeNativePort();
        nativePorts.push(port);
        return port;
      },
      latestNativePort: () => {
        const port = nativePorts.at(-1);
        if (!port) throw new Error("No native port was created");
        return port;
      },
      disconnectLatest: (message: string) => {
        fake.runtime.lastError = {message};
        fake.runtime.latestNativePort().emitDisconnect();
        delete fake.runtime.lastError;
      },
      sendMessage: async (message: unknown) => {
        fake.runtime.sentMessages.push(structuredClone(message));
        return structuredClone(fake.runtime.sendMessageResponse);
      },
      getManifest: () => ({version: "0.1.0"}),
      openOptionsPage: vi.fn(async () => undefined),
    },
    storage: {local, session},
    alarms: {
      onAlarm: alarmsEvent,
      created: [],
      current: new Map(),
      create: async (name, alarmInfo) => {
        fake.alarms.created.push({name, alarmInfo});
        fake.alarms.current.set(name, {name, scheduledTime: Date.now() + 30_000});
      },
      clear: async (name) => fake.alarms.current.delete(name),
      get: async (name) => fake.alarms.current.get(name),
    },
    tabs: {
      items: [],
      sent: [],
      failNextSendFor: new Set(),
      query: async () => structuredClone(fake.tabs.items),
      sendMessage: async (tabId, message) => {
        fake.tabs.sent.push({tabId, message: structuredClone(message)});
        if (fake.tabs.failNextSendFor.delete(tabId)) {
          throw new Error("Could not establish connection. Receiving end does not exist.");
        }
        return undefined;
      },
      onRemoved: tabsRemoved,
    },
    scripting: {
      executions: [],
      executeScript: async (injection) => {
        fake.scripting.executions.push(structuredClone(injection));
        return [];
      },
    },
    flush: async () => {
      await Promise.resolve();
      await Promise.resolve();
      await new Promise((resolve) => setTimeout(resolve, 0));
      await Promise.resolve();
    },
  };

  installed = fake;
  Object.defineProperty(globalThis, "chrome", {
    value: fake,
    writable: true,
    configurable: true,
  });
  delete (globalThis as Record<string, unknown>).__omarchyThemeBridgeContentV1;
  return fake;
}

export function getFakeChrome(): FakeChrome {
  if (!installed) throw new Error("Fake Chrome is not installed");
  return installed;
}
