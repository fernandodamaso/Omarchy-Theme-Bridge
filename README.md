# Omarchy Theme Bridge

Omarchy Theme Bridge connects Google Chrome and Chromium to the currently active [Omarchy](https://github.com/omacom/omarchy) color theme.

> **Development status:** PR 1 implements the native theme bridge, browser connection, persisted theme snapshot, and an early page-canvas bootstrap. The Adaptive website renderer arrives in PR 2. This branch does **not** yet claim full website recoloring.

## What PR 1 provides

- A Manifest V3 extension for Chrome and Chromium.
- A Python 3.11+ Native Messaging host with no runtime dependencies outside the standard library.
- Active-theme parsing from `~/.local/state/omarchy/current/theme/colors.toml`.
- Dark and light palette normalization with safe legacy fallbacks.
- Event-driven theme updates through Linux `inotify`; no continuous filesystem polling.
- Last-known-good theme retention when the active theme is temporarily missing or invalid.
- User-scoped install, verify, and uninstall scripts.
- A cached, temporary root-canvas color to reduce page flashes before the future renderer starts.

## Current boundary

PR 1 does **not** transform website styles. It does not recolor cards, text, buttons, borders, SVG controls, or dynamic styles yet. It also does not alter images, video, canvas, charts, maps, or authored content.

## Build

Requirements: Node.js 20+, npm, Python 3.11+, Linux, and either Chrome or Chromium.

```bash
cd extension
npm ci
npm run verify
```

Load `extension/dist` as an unpacked extension. The committed public manifest key produces this development extension ID:

```text
lmekdlcaodjnmpoonpjikpfnghhjfong
```

Install the native host for that ID:

```bash
./native-host/install/install.sh \
  --extension-id lmekdlcaodjnmpoonpjikpfnghhjfong
./native-host/install/verify.sh
```

Detailed steps are in [`docs/installation.md`](docs/installation.md).

## Verification

```bash
./scripts/verify-pr1.sh
```

This command installs development dependencies into project-local directories, type-checks and tests the extension, builds the unpacked bundle, compiles and tests the Python host, and runs installer tests against temporary directories. It does not install anything into the real browser profile.

## Privacy

The native process accepts only a versioned handshake, a reload request, and a bounded ping. It receives no URL, hostname, page text, DOM, CSS source, cookie, token, form value, title, screenshot, browsing history, or profile path. See [`docs/privacy.md`](docs/privacy.md).

## Design and plans

- [Approved Developer MVP design](docs/superpowers/specs/2026-09-04-omarchy-theme-bridge-design.md)
- [Execution index](docs/superpowers/plans/2026-09-04-developer-mvp-execution-index.md)
- [PR 1 implementation plan](docs/superpowers/plans/2026-09-04-foundation-native-bridge.md)

## License

Project licensing will be finalized before a public release. PR 2 will vendor a pinned, attributed MIT-licensed subset of Dark Reader; no Dark Reader source is included in PR 1.
