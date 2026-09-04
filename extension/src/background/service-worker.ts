import {parseInternalRequest} from "../shared/internal-messages";
import {NativeConnection, RECONNECT_ALARM} from "./native-connection";
import {BridgeStateStore} from "./state-store";
import {TabCoordinator} from "./tab-coordinator";

const store = new BridgeStateStore();
const coordinator = new TabCoordinator(store);
const connection = new NativeConnection(
  store,
  chrome.runtime.getManifest().version,
  () => coordinator.broadcastState(),
);

async function statusSnapshot(): Promise<unknown> {
  const state = await store.get();
  return {
    type: "status.snapshot",
    connected: state.connection.connected,
    ...(state.connection.error ? {connectionError: state.connection.error} : {}),
    ...(state.themeError ? {themeError: state.themeError} : {}),
    theme: state.theme,
  };
}

chrome.runtime.onInstalled.addListener(() => {
  void store.initialize().then(async () => {
    await connection.requestReconnect();
    await coordinator.recoverExistingTabs();
  });
});

chrome.runtime.onStartup.addListener(() => {
  void store.initialize().then(() => connection.requestReconnect());
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === RECONNECT_ALARM) void connection.requestReconnect();
});

chrome.runtime.onMessage.addListener((input: unknown, sender, sendResponse) => {
  let request;
  try {
    request = parseInternalRequest(input);
  } catch {
    return false;
  }

  if (sender.id !== chrome.runtime.id) return false;

  if (request.type === "content.ready") {
    if (!sender.tab) return false;
    void coordinator.stateForSender(sender).then(sendResponse).catch(() => sendResponse(undefined));
    return true;
  }

  if (request.type === "state.get") {
    const response = sender.tab ? coordinator.stateForSender(sender) : statusSnapshot();
    void response.then(sendResponse).catch(() => sendResponse(undefined));
    return true;
  }

  if (sender.tab) return false;
  void connection.requestReconnect()
    .then(statusSnapshot)
    .then(sendResponse)
    .catch(() => sendResponse(undefined));
  return true;
});

void store.initialize().then(() => connection.start());
