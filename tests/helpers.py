from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from mind_core import MindCore
from mind_core.constants import PROTOCOL_VERSION
from mind_core.util import record_binding_hash, timestamp


FIXTURES = Path(__file__).parent / "fixtures"


def stamp(seconds: int = 0) -> str:
    return timestamp(datetime.now(timezone.utc) + timedelta(seconds=seconds))


def handshake_record(
    agent_instance_id: str,
    host_session_id: str,
    *,
    session_epoch: int = 1,
    external_session_id: str | None = None,
    persona_id: str | None = None,
    profile_id: str | None = None,
    declared_conformance_level: str = "H0",
    protocol_version: str = PROTOCOL_VERSION,
    observed_offset: int = -120,
    expires_offset: int = 3600,
    catalog_expires_offset: int = 1800,
) -> dict[str, Any]:
    return {
        "agent_instance_id": agent_instance_id,
        "host_session_id": host_session_id,
        "host_id": "host:test",
        "external_session_id": external_session_id or host_session_id,
        "session_epoch": session_epoch,
        "persona_id": persona_id,
        "profile_id": profile_id,
        "adapter_id": "adapter:test",
        "adapter_version": "0.1.0",
        "protocol_version": protocol_version,
        "declared_conformance_level": declared_conformance_level,
        "catalog_snapshot_hash": "a" * 64,
        "catalog_snapshot_expires_at": stamp(catalog_expires_offset),
        "permission_observation_hash": "b" * 64,
        "authentication_observation_hash": "c" * 64,
        "observed_at": stamp(observed_offset),
        "expires_at": stamp(expires_offset),
    }


def scoped_receipt(
    core: MindCore,
    agent_instance_id: str,
    host_session_id: str,
    *,
    receipt_id: str,
    idempotency_key: str,
    subject_id: str = "subject:test",
    observed_offset: int = -30,
    expires_offset: int = 600,
) -> dict[str, Any]:
    return core.receipts.append(
        {
            "receipt_id": receipt_id,
            "idempotency_key": idempotency_key,
            "receipt_type": "test.observation",
            "subject_kind": "test_subject",
            "subject_id": subject_id,
            "agent_instance_id": agent_instance_id,
            "host_session_id": host_session_id,
            "evidence_state": "observed",
            "claimed_boundary": "A deterministic test observation was recorded.",
            "observed_at": stamp(observed_offset),
            "expires_at": stamp(expires_offset),
            "redaction_class": "metadata_only",
            "payload_hash": "d" * 64,
        }
    )


def bound_receipt(
    core: MindCore,
    record: dict[str, Any],
    *,
    receipt_id: str,
    idempotency_key: str,
    receipt_type: str,
    subject_kind: str,
    subject_id: str,
    agent_instance_id: str | None,
    host_session_id: str | None,
    evidence_state: str = "observed",
) -> dict[str, Any]:
    envelope: dict[str, Any] = {
        "receipt_id": receipt_id,
        "idempotency_key": idempotency_key,
        "receipt_type": receipt_type,
        "subject_kind": subject_kind,
        "subject_id": subject_id,
        "agent_instance_id": agent_instance_id,
        "host_session_id": host_session_id,
        "evidence_state": evidence_state,
        "claimed_boundary": "The receipt is bound to the canonical test record payload.",
        "observed_at": record["observed_at"],
        "redaction_class": "metadata_only",
        "payload_hash": record_binding_hash(record),
    }
    if record.get("expires_at") is not None:
        envelope["expires_at"] = record["expires_at"]
    return core.receipts.append(envelope)


def global_receipt(
    core: MindCore,
    *,
    receipt_id: str,
    idempotency_key: str,
    subject_id: str = "subject:global",
) -> dict[str, Any]:
    return core.receipts.append(
        {
            "receipt_id": receipt_id,
            "idempotency_key": idempotency_key,
            "receipt_type": "test.global",
            "subject_kind": "test_subject",
            "subject_id": subject_id,
            "evidence_state": "reported",
            "claimed_boundary": "A global metadata premise was recorded.",
            "observed_at": stamp(-30),
            "redaction_class": "metadata_only",
            "payload_hash": "e" * 64,
        }
    )


def bootstrap_fixture() -> dict[str, Any]:
    return json.loads(
        (FIXTURES / "phase1_bootstrap.json").read_text(encoding="utf-8")
    )
