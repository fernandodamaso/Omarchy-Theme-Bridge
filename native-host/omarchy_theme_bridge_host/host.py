from __future__ import annotations

import os
import selectors
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import BinaryIO

from . import PROTOCOL_VERSION, __version__
from .config import HostConfig
from .errors import ThemeErrorCode, ThemeLoadError
from .last_good import LastGoodStore
from .protocol import FramingError, HelloMessage, PingMessage, ProtocolError, ReloadMessage, parse_extension_message, read_message, write_message
from .theme_loader import ThemePaths
from .theme_normalizer import NormalizedTheme, load_and_normalize
from .watcher import InotifyWatcher

RELOAD_DEBOUNCE_SECONDS = 0.075


class NativeHost:
    def __init__(
        self,
        *,
        config: HostConfig,
        paths: ThemePaths,
        signal_file: Path,
        last_good: LastGoodStore,
        watcher: InotifyWatcher,
    ) -> None:
        self.config = config
        self.paths = paths
        self.signal_file = signal_file
        self.last_good = last_good
        self.watcher = watcher
        self.current_theme = last_good.load()
        self._last_error_signature: tuple[str, str | None] | None = None

    @classmethod
    def from_environment(
        cls,
        *,
        config: HostConfig,
        home: Path,
        environ: Mapping[str, str],
    ) -> "NativeHost":
        paths = ThemePaths.resolve(home, environ.get("OMARCHY_THEME_BRIDGE_THEME_DIR"))
        state_home = Path(environ.get("XDG_STATE_HOME", str(home / ".local" / "state")))
        state_dir = state_home / "omarchy-theme-bridge"
        state_dir.mkdir(parents=True, exist_ok=True)
        signal_file = state_dir / "theme-set.signal"
        return cls(
            config=config,
            paths=paths,
            signal_file=signal_file,
            last_good=LastGoodStore(state_dir / "last-good-theme.json"),
            watcher=InotifyWatcher(paths, signal_file),
        )

    def _safe_diagnostic(self, code: str) -> None:
        print(f"omarchy-theme-bridge-host: {code}", file=sys.stderr, flush=True)

    def _send_error(self, stdout: BinaryIO, code: str) -> None:
        retained = None
        if self.current_theme is not None:
            retained_value = self.current_theme.get("generation")
            retained = retained_value if isinstance(retained_value, str) else None
        signature = (code, retained)
        if signature == self._last_error_signature:
            return
        message: dict[str, object] = {"type": "theme.error", "code": code}
        if retained:
            message["retainedGeneration"] = retained
        write_message(stdout, message)
        self._last_error_signature = signature
        self._safe_diagnostic(code)

    def _read_active_theme(self) -> NormalizedTheme:
        return load_and_normalize(self.paths)

    def _persist_last_good(self, theme: NormalizedTheme) -> None:
        try:
            self.last_good.save(theme)
        except OSError:
            self._safe_diagnostic("LAST_GOOD_WRITE_FAILED")

    def _publish_initial(self, stdout: BinaryIO) -> None:
        try:
            theme = self._read_active_theme()
        except ThemeLoadError as error:
            self._send_error(stdout, error.code)
            return
        self.current_theme = theme
        self._persist_last_good(theme)
        self._last_error_signature = None
        write_message(stdout, {"type": "theme.snapshot", "theme": theme})

    def _publish_change(self, stdout: BinaryIO) -> None:
        try:
            theme = self._read_active_theme()
        except ThemeLoadError as error:
            self._send_error(stdout, error.code)
            return
        self._last_error_signature = None
        previous_generation = self.current_theme.get("generation") if self.current_theme else None
        self.current_theme = theme
        self._persist_last_good(theme)
        if theme.get("generation") != previous_generation:
            write_message(stdout, {"type": "theme.changed", "theme": theme})

    def run(self, stdin: BinaryIO, stdout: BinaryIO) -> int:
        selector = selectors.DefaultSelector()
        selector.register(stdin, selectors.EVENT_READ, "stdin")
        selector.register(self.watcher.fileno(), selectors.EVENT_READ, "watcher")
        handshake_complete = False
        reload_deadline: float | None = None
        rearm_before_reload = False

        def rearm_watcher() -> None:
            old_fd = self.watcher.fileno()
            selector.unregister(old_fd)
            try:
                self.watcher.rearm()
            except BaseException:
                selector.register(old_fd, selectors.EVENT_READ, "watcher")
                raise
            selector.register(self.watcher.fileno(), selectors.EVENT_READ, "watcher")

        try:
            while True:
                timeout = None if reload_deadline is None else max(0.0, reload_deadline - time.monotonic())
                events = selector.select(timeout)

                if reload_deadline is not None and time.monotonic() >= reload_deadline:
                    reload_deadline = None
                    if rearm_before_reload:
                        rearm_watcher()
                        rearm_before_reload = False
                    if handshake_complete:
                        self._publish_change(stdout)

                for key, _mask in events:
                    if key.data == "stdin":
                        try:
                            raw = read_message(stdin)
                        except FramingError:
                            self._send_error(stdout, ThemeErrorCode.PROTOCOL_MISMATCH)
                            return 5
                        except ProtocolError:
                            self._send_error(stdout, ThemeErrorCode.PROTOCOL_MISMATCH)
                            continue
                        if raw is None:
                            return 0
                        try:
                            message = parse_extension_message(raw)
                        except ProtocolError:
                            self._send_error(stdout, ThemeErrorCode.PROTOCOL_MISMATCH)
                            continue

                        if not handshake_complete:
                            if not isinstance(message, HelloMessage):
                                self._send_error(stdout, ThemeErrorCode.PROTOCOL_MISMATCH)
                                continue
                            handshake_complete = True
                            write_message(stdout, {
                                "type": "host.ready",
                                "protocolVersion": PROTOCOL_VERSION,
                                "hostVersion": __version__,
                            })
                            self._publish_initial(stdout)
                            continue

                        if isinstance(message, HelloMessage):
                            self._send_error(stdout, ThemeErrorCode.PROTOCOL_MISMATCH)
                        elif isinstance(message, ReloadMessage):
                            self._publish_change(stdout)
                        elif isinstance(message, PingMessage):
                            write_message(stdout, {"type": "pong", "requestId": message.request_id})
                    else:
                        batch = self.watcher.read_events()
                        if batch.rearm_requested:
                            rearm_watcher()
                            rearm_before_reload = True
                        if batch.reload_requested:
                            reload_deadline = time.monotonic() + RELOAD_DEBOUNCE_SECONDS
        finally:
            selector.close()
            self.watcher.close()
