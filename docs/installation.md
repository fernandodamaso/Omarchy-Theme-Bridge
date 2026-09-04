# Developer installation

This runbook installs the PR 1 Developer MVP for the current user. It supports Google Chrome and Chromium on Linux.

## 1. Build the extension

```bash
git clone https://github.com/fernandodamaso/Omarchy-Theme-Bridge.git
cd Omarchy-Theme-Bridge
git switch feat/foundation-native-bridge
cd extension
npm ci
npm run verify
```

The unpacked extension is written to `extension/dist`.

## 2. Load the unpacked extension

For Google Chrome, open `chrome://extensions`. For Chromium, open `chromium://extensions`.

1. Enable **Developer mode**.
2. Select **Load unpacked**.
3. Choose the repository's `extension/dist` directory.
4. Confirm that the extension ID is:

```text
lmekdlcaodjnmpoonpjikpfnghhjfong
```

The ID is stable because `manifest.json` contains the committed public development key. No private key is stored in this repository.

## 3. Install the native host

From the repository root:

```bash
./native-host/install/install.sh \
  --extension-id lmekdlcaodjnmpoonpjikpfnghhjfong
```

The installer is user-scoped and writes these project-owned paths:

```text
${XDG_DATA_HOME:-$HOME/.local/share}/omarchy-theme-bridge/host/
$HOME/.config/google-chrome/NativeMessagingHosts/com.omarchy.theme_bridge.json
$HOME/.config/chromium/NativeMessagingHosts/com.omarchy.theme_bridge.json
$HOME/.config/omarchy/hooks/theme-set-omarchy-theme-bridge
```

It does not modify browser profiles, policies, bookmarks, history, or cookies.

## 4. Verify the installation

```bash
./native-host/install/verify.sh
```

Expected final line:

```text
Omarchy Theme Bridge verification passed
```

Then reload the extension from the extensions page. The popup should report that bridge status is available once the Native Messaging handshake succeeds.

## 5. Exercise theme synchronization

PR 1 can prove bridge synchronization and the temporary root-canvas bootstrap only. It does not provide complete Adaptive website recoloring.

1. Open a normal HTTP or HTTPS page.
2. Switch the active Omarchy theme.
3. Observe the extension service worker and native-host status.
4. Confirm that a valid new generation reaches browser storage without reloading the extension.
5. Confirm that malformed theme input retains the previous generation.

Do not treat an untested browser as passing. Record Google Chrome and Chromium separately as `PASS`, `FAIL`, or `PENDING`.

## Nonstandard manifest directories

Developer profiles can override the browser Native Messaging directories:

```bash
./native-host/install/install.sh \
  --extension-id lmekdlcaodjnmpoonpjikpfnghhjfong \
  --chrome-dir /absolute/chrome/NativeMessagingHosts \
  --chromium-dir /absolute/chromium/NativeMessagingHosts
```

Pass the same overrides to `verify.sh` and `uninstall.sh`.

## Remove the native host

```bash
./native-host/install/uninstall.sh
```

The uninstaller validates ownership markers and removes only this project's manifests, unique Omarchy hook, host directory, and known state files. It leaves parent directories and unrelated hooks untouched.

Remove the unpacked extension separately from the browser extensions page.

## Troubleshooting

### Native host not found

Run `verify.sh`, confirm the extension ID, reload the extension, and restart the browser if the manifest was installed while it was running.

### Forbidden caller

The extension ID supplied to `install.sh` does not match the loaded extension. Re-run the installer with the ID shown by the browser.

### Active theme missing or invalid

Check:

```text
$HOME/.local/state/omarchy/current/theme/colors.toml
$HOME/.local/state/omarchy/current/theme.name
```

The host keeps the last valid normalized palette and exposes only a bounded error code.

### Inspecting logs

The host writes framed protocol data to stdout and bounded human-readable status codes to stderr. It intentionally does not log paths, source colors, websites, or page content.
