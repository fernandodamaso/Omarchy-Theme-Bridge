import io
import json
import struct

import pytest

from omarchy_theme_bridge_host.protocol import MessageTooLarge, ProtocolError, parse_extension_message, read_message, write_message


def test_round_trip_native_message() -> None:
    stream = io.BytesIO()
    write_message(stream, {"type": "ping", "requestId": "abc"})
    stream.seek(0)
    assert read_message(stream) == {"type": "ping", "requestId": "abc"}


def test_read_rejects_message_over_application_limit() -> None:
    stream = io.BytesIO(struct.pack("=I", 65_537) + b"{}")
    with pytest.raises(MessageTooLarge):
        read_message(stream)


def test_write_uses_compact_utf8_json() -> None:
    stream = io.BytesIO()
    write_message(stream, {"type": "theme.reload"})
    payload = stream.getvalue()[4:]
    assert payload == json.dumps({"type": "theme.reload"}, separators=(",", ":")).encode()


def test_rejects_extra_extension_fields() -> None:
    with pytest.raises(ProtocolError):
        parse_extension_message({"type": "theme.reload", "url": "https://example.com"})


def test_rejects_truncated_payload() -> None:
    stream = io.BytesIO(struct.pack("=I", 4) + b"{}")
    with pytest.raises(ProtocolError, match="Unexpected EOF"):
        read_message(stream)
