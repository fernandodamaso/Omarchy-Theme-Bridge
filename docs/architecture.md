# PR 1 architecture

```text
Omarchy theme activation
        │
        ├── active directory replacement / colors.toml update
        └── unique theme-set hook signal
                        │
                        ▼
Python Native Messaging host
  - validates caller origin
  - parses and normalizes colors.toml
  - retains last known good generation
  - waits on stdin + Linux inotify
                        │
                        ▼
Manifest V3 service worker
  - validates native messages
  - persists theme and connection state
  - reconnects with chrome.alarms
  - updates eligible tabs visible-first
                        │
                        ▼
Isolated content script in permitted frames
  - reads safe cached state
  - applies/removes temporary root canvas
  - sends only {type: "content.ready"}
```

## Native boundary

The host is named `com.omarchy.theme_bridge`. Chrome launches it over stdin/stdout using native-endian 32-bit length-prefixed UTF-8 JSON. Application messages are capped at 65,536 bytes.

Browser-to-host messages are limited to:

```text
hello          protocol and extension version
ping           bounded request ID
theme.reload   no payload
```

Host-to-browser messages are limited to:

```text
host.ready      protocol and host version
theme.snapshot  complete normalized theme
theme.changed   complete normalized theme
theme.error     bounded code and optional retained generation
pong            bounded request ID
```

Unexpected fields are rejected. Exception text and filesystem paths never cross the protocol boundary.

## Omarchy observation

Current Omarchy replaces the active theme directory. Watching only the previous `colors.toml` inode would stop after a switch, so the host watches:

- `~/.local/state/omarchy/current` for `theme` replacement and `theme.name` changes;
- the active `theme` directory for palette and light-mode changes;
- the project-owned hook signal directory.

The unique hook is a low-latency hint. The parent-directory watch remains authoritative fallback coverage. Event bursts are coalesced for 75 ms; there is no periodic scan.

## Browser state

The service worker treats process memory as disposable. It stores only the current normalized theme, extension settings, bounded connection state, and safe error codes in `chrome.storage.local`.

Delayed native reconnection uses a named `chrome.alarms` alarm rather than a long timer that Manifest V3 suspension could discard.

## Page bootstrap

The PR 1 content script runs at `document_start` in an isolated world. When a valid cached theme is available, it temporarily sets only the root canvas background and `color-scheme`. It removes this style when disabled or when no valid state exists. Print styles restore the normal page background.

The bootstrap is intentionally not the Adaptive renderer. Dynamic stylesheet transformation, semantic mapping, media preservation, and site compatibility rules are PR 2 work.
