from __future__ import annotations

import ctypes
import errno
import os
import select
import struct
from dataclasses import dataclass
from pathlib import Path

from .theme_loader import ThemePaths

_EVENT = struct.Struct("iIII")
IN_ATTRIB = 0x00000004
IN_CLOSE_WRITE = 0x00000008
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_DELETE_SELF = 0x00000400
IN_MOVE_SELF = 0x00000800
IN_IGNORED = 0x00008000
WATCH_MASK = (
    IN_ATTRIB
    | IN_CLOSE_WRITE
    | IN_MOVED_FROM
    | IN_MOVED_TO
    | IN_CREATE
    | IN_DELETE
    | IN_DELETE_SELF
    | IN_MOVE_SELF
)


@dataclass(frozen=True, slots=True)
class WatchBatch:
    reload_requested: bool = False
    rearm_requested: bool = False

    def merged(self, other: "WatchBatch") -> "WatchBatch":
        return WatchBatch(
            reload_requested=self.reload_requested or other.reload_requested,
            rearm_requested=self.rearm_requested or other.rearm_requested,
        )


class InotifyWatcher:
    """Event-driven watcher for Omarchy's replace-in-place active theme."""

    def __init__(self, paths: ThemePaths, signal_file: Path) -> None:
        if not sys_platform_linux():
            raise OSError(errno.ENOSYS, "Linux inotify is required")
        self.paths = paths
        self.signal_file = signal_file
        self._libc = ctypes.CDLL(None, use_errno=True)
        self._libc.inotify_init1.argtypes = [ctypes.c_int]
        self._libc.inotify_init1.restype = ctypes.c_int
        self._libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        self._libc.inotify_add_watch.restype = ctypes.c_int
        self._libc.inotify_rm_watch.argtypes = [ctypes.c_int, ctypes.c_int]
        self._libc.inotify_rm_watch.restype = ctypes.c_int
        self._fd = -1
        self._watches: dict[int, str] = {}
        self.rearm()

    def fileno(self) -> int:
        return self._fd

    def _new_fd(self) -> int:
        fd = self._libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        if fd == -1:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        return fd

    def _add_watch(self, fd: int, watches: dict[int, str], path: Path, kind: str) -> None:
        if not path.is_dir():
            return
        wd = self._libc.inotify_add_watch(fd, os.fsencode(path), WATCH_MASK)
        if wd == -1:
            error = ctypes.get_errno()
            if error in {errno.ENOENT, errno.ENOTDIR}:
                return
            raise OSError(error, os.strerror(error))
        watches[wd] = kind

    def rearm(self) -> None:
        """Replace the inotify instance so stale IN_IGNORED events cannot loop."""
        new_fd = self._new_fd()
        new_watches: dict[int, str] = {}
        try:
            self._add_watch(new_fd, new_watches, self.paths.theme_dir.parent, "current")
            self._add_watch(new_fd, new_watches, self.paths.theme_dir, "theme")
            self._add_watch(new_fd, new_watches, self.signal_file.parent, "signal")
        except BaseException:
            os.close(new_fd)
            raise

        old_fd = self._fd
        self._fd = new_fd
        self._watches = new_watches
        if old_fd >= 0:
            os.close(old_fd)

    def read_events(self) -> WatchBatch:
        batch = WatchBatch()
        while True:
            try:
                data = os.read(self._fd, 64 * 1024)
            except BlockingIOError:
                break
            if not data:
                break
            offset = 0
            while offset + _EVENT.size <= len(data):
                wd, mask, _cookie, name_length = _EVENT.unpack_from(data, offset)
                offset += _EVENT.size
                raw_name = data[offset:offset + name_length]
                offset += name_length
                name = raw_name.split(b"\0", 1)[0].decode("utf-8", "ignore")
                kind = self._watches.get(wd)
                reload_requested = False
                rearm_requested = bool(mask & IN_IGNORED)

                if kind == "current":
                    if name in {"theme", "theme.name"}:
                        reload_requested = True
                    if name == "theme" and mask & (IN_CREATE | IN_DELETE | IN_MOVED_FROM | IN_MOVED_TO):
                        rearm_requested = True
                elif kind == "theme":
                    if name in {"colors.toml", "light.mode", "theme.name"} or mask & (IN_DELETE_SELF | IN_MOVE_SELF):
                        reload_requested = True
                    if mask & (IN_DELETE_SELF | IN_MOVE_SELF | IN_IGNORED):
                        rearm_requested = True
                elif kind == "signal" and name == self.signal_file.name:
                    reload_requested = True

                batch = batch.merged(WatchBatch(reload_requested, rearm_requested))
        return batch

    def wait_for_events(self, timeout: float) -> WatchBatch:
        ready, _, _ = select.select([self._fd], [], [], timeout)
        return self.read_events() if ready else WatchBatch()

    def close(self) -> None:
        if self._fd >= 0:
            os.close(self._fd)
            self._fd = -1
            self._watches.clear()

    def __enter__(self) -> "InotifyWatcher":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def sys_platform_linux() -> bool:
    return os.uname().sysname == "Linux" if hasattr(os, "uname") else False
