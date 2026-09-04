import type {ApplyState} from "../shared/internal-messages";
import {resolveSiteMode} from "../shared/settings";
import type {BridgeStateStore} from "./state-store";

const CONTENT_SCRIPT_FILE = "content/content-script.js";
const INACTIVE_CONCURRENCY = 4;

export function isEligibleUrl(url: string | undefined): boolean {
  if (!url) return false;
  try {
    const protocol = new URL(url).protocol;
    return protocol === "http:" || protocol === "https:";
  } catch {
    return false;
  }
}

function isMissingReceiver(error: unknown): boolean {
  return error instanceof Error && error.message.includes("Receiving end does not exist");
}

export class TabCoordinator {
  constructor(private readonly store: BridgeStateStore) {}

  async stateForUrl(url: string | undefined): Promise<ApplyState> {
    const state = await this.store.get();
    let mode: ApplyState["mode"] = "off";
    if (isEligibleUrl(url)) {
      mode = resolveSiteMode(state.settings, new URL(url as string).hostname);
    }
    return {
      type: "state.apply",
      enabled: state.settings.enabled,
      mode,
      theme: state.theme,
    };
  }

  async stateForSender(sender: chrome.runtime.MessageSender): Promise<ApplyState> {
    const ownUrl = sender.url;
    const fallback = sender.tab?.url;
    return this.stateForUrl(isEligibleUrl(ownUrl) ? ownUrl : fallback);
  }

  private async sendToTab(tab: chrome.tabs.Tab, recover: boolean): Promise<void> {
    if (tab.id == null || !isEligibleUrl(tab.url) || tab.discarded) return;
    const message = await this.stateForUrl(tab.url);
    try {
      await chrome.tabs.sendMessage(tab.id, message);
    } catch (error) {
      if (!recover || !isMissingReceiver(error)) return;
      try {
        await chrome.scripting.executeScript({
          target: {tabId: tab.id, allFrames: true},
          files: [CONTENT_SCRIPT_FILE],
        });
        await chrome.tabs.sendMessage(tab.id, message);
      } catch {
        // Protected frames and permission races are expected bounded failures.
      }
    }
  }

  async recoverExistingTabs(): Promise<void> {
    const tabs = (await chrome.tabs.query({})).filter((tab) => (
      tab.id != null && !tab.discarded && isEligibleUrl(tab.url)
    ));
    const active = tabs.filter((tab) => tab.active);
    const inactive = tabs.filter((tab) => !tab.active);
    for (const tab of active) await this.sendToTab(tab, true);
    await this.runBounded(inactive, INACTIVE_CONCURRENCY, (tab) => this.sendToTab(tab, true));
  }

  async broadcastState(): Promise<void> {
    const tabs = (await chrome.tabs.query({})).filter((tab) => (
      tab.id != null && !tab.discarded && isEligibleUrl(tab.url)
    ));
    const active = tabs.filter((tab) => tab.active);
    const inactive = tabs.filter((tab) => !tab.active);
    for (const tab of active) await this.sendToTab(tab, false);
    await this.runBounded(inactive, INACTIVE_CONCURRENCY, (tab) => this.sendToTab(tab, false));
  }

  private async runBounded<T>(items: T[], concurrency: number, worker: (item: T) => Promise<void>): Promise<void> {
    let index = 0;
    const runners = Array.from({length: Math.min(concurrency, items.length)}, async () => {
      while (index < items.length) {
        const item = items[index];
        index += 1;
        if (item !== undefined) await worker(item);
      }
    });
    await Promise.all(runners);
  }
}
