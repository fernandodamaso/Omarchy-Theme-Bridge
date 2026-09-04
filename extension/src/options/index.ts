const reconnectButton = document.querySelector<HTMLButtonElement>("#reconnect");
reconnectButton?.addEventListener("click", async () => {
  const status = document.querySelector<HTMLElement>("#status");
  if (status) status.textContent = "Reconnecting…";
  try {
    await chrome.runtime.sendMessage({type: "native.reconnect"});
    if (status) status.textContent = "Reconnect requested";
  } catch {
    if (status) status.textContent = "Reconnect failed";
  }
});
