const settingsButton = document.querySelector<HTMLButtonElement>("#settings");
settingsButton?.addEventListener("click", () => {
  void chrome.runtime.openOptionsPage();
});

void chrome.runtime.sendMessage({type: "state.get"}).then((response: unknown) => {
  const status = document.querySelector<HTMLElement>("#status");
  if (status) {
    status.textContent = typeof response === "object" && response !== null
      ? "Bridge status available"
      : "Native host unavailable";
  }
}).catch(() => {
  const status = document.querySelector<HTMLElement>("#status");
  if (status) status.textContent = "Native host unavailable";
});
