# Privacy and security boundary

Omarchy Theme Bridge performs theme synchronization locally. PR 1 has no telemetry, account, cloud synchronization, analytics endpoint, or remote configuration.

## Data the native host receives

Only these validated messages can reach the Python process:

- protocol/version handshake;
- a payload-free theme reload request;
- a bounded opaque ping request ID.

## Data the native host never receives

- URLs or hostnames;
- page titles or text;
- DOM or stylesheet source;
- cookies, authentication tokens, or form values;
- screenshots or media;
- browsing history;
- browser profile paths.

Content scripts cannot send arbitrary data to the host. They can announce readiness and request their already-resolved safe state from the service worker. Privileged reconnect actions are accepted only from extension pages, not tab senders.

## Files read and written

The host reads Omarchy's active palette and theme name:

```text
$HOME/.local/state/omarchy/current/theme/colors.toml
$HOME/.local/state/omarchy/current/theme.name
```

It may write a normalized last-known-good palette and a hook signal under:

```text
${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-theme-bridge/
```

The snapshot contains theme name, mode, generation hash, and normalized colors only. It contains no source path or browser data and is written with mode `0600`.

## Permissions

The extension requests:

```text
alarms            suspension-safe native reconnect
nativeMessaging   communicate with the local theme host
scripting         recover the packaged content controller in existing tabs
storage           persist safe theme and settings state
http://*/*        run on ordinary web pages
https://*/*       run on ordinary web pages
```

It does not request history, bookmarks, cookies, downloads, identity, clipboard, file URL, or browsing-data permissions. Chrome internal pages, extension pages, the Web Store, and the built-in PDF viewer remain unavailable.

## Diagnostics

Protocol errors are bounded enum values such as `THEME_INVALID`, `HOST_NOT_FOUND`, and `PROTOCOL_MISMATCH`. Human-readable stderr logs use the same safe status style. Raw exceptions, palette source text, and local paths are not transmitted.
