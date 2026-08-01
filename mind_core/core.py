"""Persona-neutral MIND Core façade."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .constants import (
    MAX_CONFORMANCE_LEVEL,
    PROTOCOL_VERSION,
    RUNTIME_VERSION,
    SCHEMA_VERSION,
)
from .errors import ValidationError
from .estate import CapabilityEstate
from .handshake import HostRegistry
from .mounts import MountCatalog
from .receipts import ReceiptLedger
from .reminders import AssociativeReminders
from .store import CoreStore
from .util import new_id, require_identifier, timestamp


class MindCore:
    """One local metadata authority; never a model, persona, or owner-store."""

    def __init__(self, database: str | Path):
        self.store = CoreStore(database)
        self.receipts = ReceiptLedger(self.store)
        self.hosts = HostRegistry(self.store, self.receipts)
        self.estate = CapabilityEstate(self.store, self.receipts, self.hosts)
        self.mounts = MountCatalog(self.store, self.receipts, self.hosts)
        with self.store.transaction() as connection:
            row = connection.execute(
                "SELECT value FROM core_meta WHERE key='core_instance_id'"
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO core_meta(key,value,updated_at) VALUES (?,?,?)",
                    ("core_instance_id", new_id("core"), timestamp()),
                )
        self.reminders = AssociativeReminders(
            self.store, self.receipts, self.hosts, self.estate
        )

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> "MindCore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def status(self) -> dict[str, Any]:
        connection = self.store.connection
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "agent_instances",
                "host_sessions",
                "capabilities",
                "distributions",
                "lifecycle_observations",
                "mounts",
                "mount_observations",
                "capability_cards",
                "capability_card_views",
                "capability_relations",
                "associative_index_snapshots",
                "associative_view_vectors",
                "associative_snapshot_activations",
                "session_query_capabilities",
                "receipts",
            )
        }
        core_id = connection.execute(
            "SELECT value FROM core_meta WHERE key='core_instance_id'"
        ).fetchone()[0]
        return {
            "runtime_version": RUNTIME_VERSION,
            "schema_version": SCHEMA_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "core_instance_id": core_id,
            "maximum_host_conformance": MAX_CONFORMANCE_LEVEL,
            "persona_required": False,
            "persona_inference": False,
            "mode": "phase2_associative_disclosure_h0",
            "implemented": [
                "agent_instance_isolation",
                "host_handshake_metadata",
                "event_coverage_metadata",
                "capability_estate_metadata",
                "mount_catalog_metadata",
                "append_only_receipts",
                "stdio_protocol_skeleton",
                "versioned_capability_cards",
                "exact_vector_radius_neighborhoods",
                "exhaustive_lexical_membership",
                "typed_associative_relations",
                "field_bound_card_expansion",
                "canonical_and_compact_reminder_fields",
            ],
            "not_implemented": [
                "event_delivery",
                "automatic_activation",
                "automatic_pre_sampling_reminder_delivery",
                "embedding_generation_or_model_installation",
                "vector_acceleration_extension",
                "owner_store_reads_or_writes",
                "legacy_data_migration",
                "action_admission_or_dispatch_gate",
                "capsule_export_or_import",
            ],
            "counts": counts,
            "sqlite": self.store.integrity(),
        }

    def query_status(self) -> dict[str, Any]:
        """Return H0 runtime identity without unscoped private-sensitive counts."""

        result = self.status()
        result.pop("counts", None)
        sqlite_status = result["sqlite"]
        result["sqlite"] = {
            "integrity_ok": sqlite_status["integrity_check"] == "ok",
            "foreign_key_ok": not sqlite_status["foreign_key_failures"],
            "foreign_keys_enabled": sqlite_status["foreign_keys_enabled"],
            "journal_mode": sqlite_status["journal_mode"],
        }
        return result

    def bootstrap(self, manifest: dict[str, Any]) -> dict[str, Any]:
        if manifest.get("format") != "mind-core-bootstrap/v1":
            raise ValidationError("unsupported bootstrap manifest format")
        allowed = {
            "format",
            "sources",
            "products",
            "providers",
            "capabilities",
            "distributions",
            "receipts",
            "lifecycle_observations",
            "mounts",
        }
        unknown = sorted(set(manifest) - allowed)
        if unknown:
            raise ValidationError(f"unsupported bootstrap fields: {','.join(unknown)}")
        with self.store.transaction() as connection:
            self.estate.ingest_sources(manifest.get("sources", []), connection)
            self.estate.ingest_products(manifest.get("products", []), connection)
            self.estate.ingest_providers(manifest.get("providers", []), connection)
            self.estate.ingest_capabilities(manifest.get("capabilities", []), connection)
            self.estate.ingest_distributions(manifest.get("distributions", []), connection)
            for item in manifest.get("receipts", []):
                self.receipts.append(
                    item,
                    parents=item.get("parents", []),
                    connection=connection,
                )
            self.estate.ingest_lifecycle_observations(
                manifest.get("lifecycle_observations", []), connection
            )
            self.mounts.ingest_mounts(manifest.get("mounts", []), connection)
        return self.status()

    def schema_tables(self) -> list[str]:
        return [
            row["name"]
            for row in self.store.connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            ).fetchall()
        ]
