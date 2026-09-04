from __future__ import annotations

import json
import struct
from collections.abc import Mapping
from dataclasses import dataclass
from typing import BinaryIO, TypeAlias

from . import MAX_MESSAGE_BYTES, PROTOCOL_VERSION

JsonObject: TypeAlias = dict[str, object]


class ProtocolError(RuntimeError):
    """A native message is malformed or unsupported."""


class FramingError(ProtocolError):
    """A native message cannot be safely resynchronized on the current stream."""


class MessageTooLarge(FramingError):
    """A message exceeded the application-level 64 KiB limit."""


@dataclass(frozen=True, slots=True)
class HelloMessage:
    protocol_version: int
    extension_version: str


@dataclass(frozen=True, slots=True)
class ReloadMessage:
    pass


@dataclass(frozen=True, slots=True)
class PingMessage:
    request_id: str


ExtensionMessage: TypeAlias = HelloMessage | ReloadMessage | PingMessage


def _read_exact(stream: BinaryIO, length: int) -> bytes:
    chunks: list[bytes] = []
    remaining = length
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            raise FramingError("Unexpected EOF")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_message(stream: BinaryIO) -> JsonObject | None:
    header = stream.read(4)
    if header == b"":
        return None
    if len(header) != 4:
        raise FramingError("Truncated message header")
    (length,) = struct.unpack("=I", header)
    if length > MAX_MESSAGE_BYTES:
        raise MessageTooLarge("Message exceeds 64 KiB limit")
    payload = _read_exact(stream, length)
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("Invalid UTF-8 JSON") from exc
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ProtocolError("Message must be a JSON object")
    return value


def write_message(stream: BinaryIO, message: Mapping[str, object]) -> None:
    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_MESSAGE_BYTES:
        raise MessageTooLarge("Message exceeds 64 KiB limit")
    stream.write(struct.pack("=I", len(payload)))
    stream.write(payload)
    stream.flush()


def _bounded_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        raise ProtocolError(f"Invalid {field}")
    return value


def parse_extension_message(value: object) -> ExtensionMessage:
    if not isinstance(value, dict) or not isinstance(value.get("type"), str):
        raise ProtocolError("Message must have a type")

    message_type = value["type"]
    if message_type == "hello":
        if set(value) != {"type", "protocolVersion", "extensionVersion"}:
            raise ProtocolError("Invalid hello message")
        if value["protocolVersion"] != PROTOCOL_VERSION:
            raise ProtocolError("Protocol version mismatch")
        return HelloMessage(
            protocol_version=PROTOCOL_VERSION,
            extension_version=_bounded_string(value["extensionVersion"], "extensionVersion"),
        )
    if message_type == "theme.reload":
        if set(value) != {"type"}:
            raise ProtocolError("Invalid reload message")
        return ReloadMessage()
    if message_type == "ping":
        if set(value) != {"type", "requestId"}:
            raise ProtocolError("Invalid ping message")
        return PingMessage(request_id=_bounded_string(value["requestId"], "requestId"))
    raise ProtocolError("Unsupported message")
