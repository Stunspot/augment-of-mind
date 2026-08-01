from __future__ import annotations

import io
import struct
import tempfile
import unittest
from pathlib import Path

from mind_core import MindCore
from mind_core.errors import ProtocolError
from mind_core.protocol import MAX_FRAME_BYTES, encode_frame, read_frame
from mind_core.service import QueryService, serve

from tests.helpers import handshake_record


class _OneByteReader(io.BytesIO):
    def read(self, size: int = -1) -> bytes:
        return super().read(1 if size < 0 else min(size, 1))


class ProtocolServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.core = MindCore(Path(self.temp.name) / "mind-core.sqlite3")

    def tearDown(self) -> None:
        self.core.close()
        self.temp.cleanup()

    def test_frame_round_trip_preserves_unicode(self) -> None:
        request = {
            "jsonrpc": "2.0",
            "id": "unicode",
            "method": "core.status",
            "params": {"note": "Mnemosyne — optional"},
        }
        self.assertEqual(read_frame(io.BytesIO(encode_frame(request))), request)
        self.assertEqual(read_frame(_OneByteReader(encode_frame(request))), request)

    def test_frame_rejects_truncation_oversize_and_duplicate_keys(self) -> None:
        with self.assertRaises(ProtocolError):
            read_frame(io.BytesIO(b"\x00\x00"))
        with self.assertRaises(ProtocolError):
            read_frame(io.BytesIO(struct.pack(">I", MAX_FRAME_BYTES + 1)))
        duplicate = b'{"jsonrpc":"2.0","id":1,"id":2}'
        with self.assertRaises(ProtocolError):
            read_frame(io.BytesIO(struct.pack(">I", len(duplicate)) + duplicate))
        nonstandard = b'{"value":NaN}'
        with self.assertRaises(ProtocolError):
            read_frame(
                io.BytesIO(struct.pack(">I", len(nonstandard)) + nonstandard)
            )
        with self.assertRaises(ProtocolError):
            encode_frame({"value": float("nan")})

    def test_query_response_is_explicitly_h0(self) -> None:
        response = QueryService(self.core).handle(
            {"jsonrpc": "2.0", "id": 1, "method": "core.status", "params": {}}
        )
        self.assertEqual(response["meta"]["maximum_host_conformance"], "H0")
        self.assertIn("H0 query result only", response["meta"]["claim_boundary"])
        self.assertEqual(response["result"]["maximum_host_conformance"], "H0")

    def test_stdio_surface_rejects_mutating_methods(self) -> None:
        response = QueryService(self.core).handle(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "admin.bootstrap",
                "params": {},
            }
        )
        self.assertEqual(response["error"]["code"], -32601)

    def test_query_param_type_confusion_is_rejected(self) -> None:
        self.core.hosts.handshake(handshake_record("agent:a", "session:a"))
        response = QueryService(self.core).handle(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "host.session",
                "params": {
                    "host_session_id": "session:a",
                    "agent_instance_id": "agent:a",
                    "require_fresh": "false"
                },
            }
        )
        self.assertEqual(response["error"]["code"], -32602)

    def test_service_handles_multiple_complete_frames(self) -> None:
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "core.status", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "core.schema", "params": {}},
        ]
        reader = io.BytesIO(b"".join(encode_frame(item) for item in requests))
        writer = io.BytesIO()
        self.assertEqual(serve(self.core, reader, writer), 0)
        writer.seek(0)
        first = read_frame(writer)
        second = read_frame(writer)
        self.assertEqual(first["id"], 1)
        self.assertEqual(second["id"], 2)
        self.assertIsNone(read_frame(writer))


if __name__ == "__main__":
    unittest.main()
