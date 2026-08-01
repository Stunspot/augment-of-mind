from __future__ import annotations

import copy
import math
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Any, Iterator

from mind_core import MindCore
from mind_core.errors import ConflictError, NotFoundError, ValidationError
from mind_core.service import QueryService
from mind_core.util import canonical_json, parse_timestamp, sha256_text

from tests.helpers import handshake_record, stamp
from tests.phase2_helpers import (
    BOUNDARY_VECTOR,
    CREATED_AT,
    GENERATION_TWO_AT,
    OUTER_VECTOR,
    PATTERN_VECTOR,
    PROFILE_RADIUS,
    PROFILE_TOLERANCE,
    SOURCE_DIGEST,
    SOURCE_ID,
    TASK_VECTOR,
    associative_index_manifest,
    cosine_distance,
    handles,
    member_by_handle,
    phase2_bootstrap_fixture,
    rebind_card_digest,
    rebind_manifest_snapshot,
    rebind_record_digest,
    without_visibility,
)


SNAPSHOT_ONE = "snapshot:phase2-synthetic:r1"
SNAPSHOT_TWO = "snapshot:phase2-synthetic:r2"


def _all_keys(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _all_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _all_keys(nested)


def _private_only_change_generation_two(
    *, source_id: str | None = None, source_digest: str | None = None
) -> dict[str, Any]:
    manifest = associative_index_manifest(1)
    newer = associative_index_manifest(2)
    private_card = next(
        card
        for card in newer["cards"]
        if card["capability_id"] == "capability:private-compass"
    )
    if source_id is not None and source_digest is not None:
        private_card["source_id"] = source_id
        private_card["source_digest"] = source_digest
        rebind_card_digest(private_card)
    manifest["cards"] = [
        private_card
        if card["capability_id"] == "capability:private-compass"
        else card
        for card in manifest["cards"]
    ]
    private_relation = {
        "capability_relation_id": "relation:signal-private:mixed-r2",
        "from_capability_card_id": "card:signal-weaver:r1",
        "to_capability_card_id": private_card["capability_card_id"],
        "relation_kind": "complements",
        "source_id": SOURCE_ID,
        "source_digest": SOURCE_DIGEST,
        "created_at": GENERATION_TWO_AT,
    }
    rebind_record_digest(private_relation, "relation_digest")
    manifest["relations"] = [
        private_relation
        if relation["capability_relation_id"] == "relation:signal-private:r1"
        else relation
        for relation in manifest["relations"]
    ]
    private_view_ids = {view["capability_card_view_id"] for view in private_card["views"]}
    newer_private_vectors = [
        vector
        for vector in newer["vectors"]
        if vector["capability_card_view_id"] in private_view_ids
    ]
    manifest["vectors"] = [
        vector
        for vector in manifest["vectors"]
        if vector["capability_card_view_id"] != "view:private-compass:r1"
    ] + newer_private_vectors
    manifest["snapshot"]["associative_index_snapshot_id"] = SNAPSHOT_TWO
    manifest["snapshot"]["created_at"] = GENERATION_TWO_AT
    manifest["activation"] = copy.deepcopy(newer["activation"])
    rebind_manifest_snapshot(manifest)
    return manifest


class AssociativeDisclosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.core = MindCore(Path(self.temp.name) / "mind-core.sqlite3")
        self.addCleanup(self.core.close)
        self._prepare_core(self.core)
        self.manifest = associative_index_manifest()
        self.core.reminders.ingest_index(self.manifest)
        self.token_a = self.core.reminders.issue_session_capability(
            "agent:a",
            "session:a",
            exposure_scope="public_and_agent_private",
        )["session_capability"]
        self.token_b = self.core.reminders.issue_session_capability(
            "agent:b",
            "session:b",
            exposure_scope="public_and_agent_private",
        )["session_capability"]

    @staticmethod
    def _prepare_core(core: MindCore) -> None:
        core.hosts.handshake(handshake_record("agent:a", "session:a"))
        core.hosts.handshake(handshake_record("agent:b", "session:b"))
        core.bootstrap(phase2_bootstrap_fixture())

    @staticmethod
    def _vector_anchor(
        anchor_id: str, kind: str, vector: list[float] | tuple[float, ...]
    ) -> dict[str, Any]:
        return {
            "anchor_id": anchor_id,
            "anchor_kind": kind,
            "vector": list(vector),
        }

    def _task_field(self, *, token: str | None = None) -> dict[str, Any]:
        return self.core.reminders.neighborhood(
            token or self.token_a,
            SNAPSHOT_ONE,
            [self._vector_anchor("task", "task", TASK_VECTOR)],
        )

    def test_exact_radius_union_bridge_and_false_friend_precedence(self) -> None:
        self.assertEqual(cosine_distance(TASK_VECTOR, PATTERN_VECTOR), PROFILE_RADIUS)
        self.assertLessEqual(
            cosine_distance(TASK_VECTOR, PATTERN_VECTOR),
            PROFILE_RADIUS + PROFILE_TOLERANCE,
        )
        self.assertGreater(
            cosine_distance(TASK_VECTOR, OUTER_VECTOR),
            PROFILE_RADIUS + PROFILE_TOLERANCE,
        )
        self.assertEqual(
            cosine_distance(TASK_VECTOR, PATTERN_VECTOR),
            cosine_distance(TASK_VECTOR, BOUNDARY_VECTOR),
        )

        field = self._task_field()
        self.assertEqual(field["mode"], "vector_current")
        self.assertEqual(
            handles(field),
            {"signal-weaver", "pattern-lens", "bridge-kit", "boundary-decoy"},
        )
        pattern = member_by_handle(field, "pattern-lens")
        self.assertTrue(
            any(path["basis"] == "vector" for path in pattern["associations"])
        )
        bridge = member_by_handle(field, "bridge-kit")
        self.assertEqual(
            {path["basis"] for path in bridge["associations"]}, {"relation"}
        )
        self.assertEqual(
            {path["relation_kind"] for path in bridge["associations"]},
            {"bridges_to"},
        )
        boundary = member_by_handle(field, "boundary-decoy")
        self.assertEqual(boundary["presentation"], "boundary_only")
        self.assertIn("vector", {path["basis"] for path in boundary["associations"]})
        self.assertIn(
            "false_friend_of",
            {
                path.get("relation_kind")
                for path in boundary["associations"]
                if path["basis"] == "relation"
            },
        )
        forbidden_fields = {
            "score",
            "rank",
            "top_k",
            "rrf",
            "utility",
            "recommendation",
            "authorization",
            "action",
            "distance",
        }
        self.assertTrue(forbidden_fields.isdisjoint(_all_keys(field)))
        model_fields = "\n".join(
            representation["text"].casefold()
            for representation in field["representations"].values()
        )
        for term in ("score", "rank", "top-k", "rrf", "utility", "recommendation"):
            self.assertNotIn(term, model_fields)

    def test_boundary_render_hides_positive_path_but_keeps_audit_provenance(self) -> None:
        field = self._task_field()
        boundary = member_by_handle(field, "boundary-decoy")
        self.assertTrue(
            any(path["basis"] == "vector" for path in boundary["associations"])
        )
        canonical = field["representations"]["canonical"]["text"]
        line = next(
            line for line in canonical.splitlines() if "boundary-decoy" in line
        )
        self.assertIn("false_friend_of", line)
        self.assertNotIn("task:vector", line)

    def test_multi_anchor_union_adds_correction_without_erasing_task_field(self) -> None:
        task = self._task_field()
        combined = self.core.reminders.neighborhood(
            self.token_a,
            SNAPSHOT_ONE,
            [
                self._vector_anchor("task", "task", TASK_VECTOR),
                self._vector_anchor(
                    "correction", "correction", (0.0, 1.0, 0.0, 0.0)
                ),
            ],
        )
        self.assertTrue(handles(task).issubset(handles(combined)))
        self.assertIn("correction-lens", handles(combined))
        correction = member_by_handle(combined, "correction-lens")
        self.assertTrue(
            any(
                path["anchor_id"] == "correction" and path["basis"] == "vector"
                for path in correction["associations"]
            )
        )

    def test_lexical_degradation_is_exhaustive_and_can_reach_aliases(self) -> None:
        field = self.core.reminders.neighborhood(
            self.token_a,
            SNAPSHOT_ONE,
            [
                {
                    "anchor_id": "lexical",
                    "anchor_kind": "task",
                    "lexical_hints": ["causal pattern analysis"],
                }
            ],
        )
        self.assertEqual(field["mode"], "lexical_degraded")
        for handle in ("signal-weaver", "pattern-lens"):
            member = member_by_handle(field, handle)
            self.assertTrue(
                any(path["basis"] == "lexical" for path in member["associations"])
            )

        alias_field = self.core.reminders.neighborhood(
            self.token_a,
            SNAPSHOT_ONE,
            [
                {
                    "anchor_id": "alias",
                    "anchor_kind": "task",
                    "lexical_hints": ["perimeter marker"],
                }
            ],
        )
        self.assertEqual(handles(alias_field), {"outer-marker"})
        outer = member_by_handle(alias_field, "outer-marker")
        self.assertIn(
            "alias", {path.get("lexical_surface") for path in outer["associations"]}
        )

    def test_private_scope_is_server_bound_before_every_disclosure_path(self) -> None:
        field_a = self._task_field(token=self.token_a)
        field_b = self._task_field(token=self.token_b)
        self.assertNotIn("private-compass", handles(field_a))
        self.assertIn("private-compass", handles(field_b))

        token_b_public = self.core.reminders.issue_session_capability(
            "agent:b", "session:b", exposure_scope="public_only"
        )["session_capability"]
        field_b_public = self._task_field(token=token_b_public)
        self.assertNotIn("private-compass", handles(field_b_public))

        private_hint = {
            "anchor_id": "private-clue",
            "anchor_kind": "task",
            "lexical_hints": ["bound private compass"],
        }
        private_a = self.core.reminders.neighborhood(
            self.token_a, SNAPSHOT_ONE, [private_hint]
        )
        private_b = self.core.reminders.neighborhood(
            self.token_b, SNAPSHOT_ONE, [private_hint]
        )
        self.assertEqual(private_a["members"], [])
        self.assertNotIn("private-compass", str(private_a))
        self.assertEqual(handles(private_b), {"private-compass"})

        private_member = member_by_handle(field_b, "private-compass")
        with self.assertRaises(NotFoundError):
            self.core.reminders.card(
                self.token_a,
                field_b["field_id"],
                field_b["membership_manifest_digest"],
                private_member["visibility_token"],
            )

        guessed = QueryService(self.core).handle(
            {
                "jsonrpc": "2.0",
                "id": "guess",
                "method": "reminder.neighborhood",
                "params": {
                    "session_capability": self.token_a,
                    "snapshot_id": SNAPSHOT_ONE,
                    "anchors": [self._vector_anchor("task", "task", TASK_VECTOR)],
                    "agent_instance_id": "agent:b",
                    "host_session_id": "session:b",
                },
            }
        )
        self.assertEqual(guessed["error"]["code"], -32602)

    def test_least_privilege_is_the_default_session_exposure(self) -> None:
        issued = self.core.reminders.issue_session_capability(
            "agent:b", "session:b"
        )
        self.assertEqual(issued["exposure_scope"], "public_only")
        field = self._task_field(token=issued["session_capability"])
        self.assertNotIn("private-compass", handles(field))

    def test_estate_identity_lookup_uses_opaque_scope_and_hides_private_handles(self) -> None:
        service = QueryService(self.core)
        public = service.handle(
            {
                "jsonrpc": "2.0",
                "id": "public",
                "method": "estate.resolve",
                "params": {"handle_or_alias": "signal-weaver"},
            }
        )
        self.assertEqual(public["result"][0]["handle"], "signal-weaver")

        hidden = service.handle(
            {
                "jsonrpc": "2.0",
                "id": "hidden",
                "method": "estate.resolve",
                "params": {
                    "handle_or_alias": "private-compass",
                    "session_capability": self.token_a,
                },
            }
        )
        self.assertEqual(hidden["result"], [])
        owner = service.handle(
            {
                "jsonrpc": "2.0",
                "id": "owner",
                "method": "estate.resolve",
                "params": {
                    "handle_or_alias": "private-compass",
                    "session_capability": self.token_b,
                },
            }
        )
        self.assertEqual(owner["result"][0]["handle"], "private-compass")

        hidden_by_id = service.handle(
            {
                "jsonrpc": "2.0",
                "id": "hidden-id",
                "method": "estate.capability",
                "params": {
                    "capability_id": "capability:private-compass",
                    "session_capability": self.token_a,
                },
            }
        )
        self.assertEqual(hidden_by_id["error"]["code"], -32004)
        owner_by_id = service.handle(
            {
                "jsonrpc": "2.0",
                "id": "owner-id",
                "method": "estate.capability",
                "params": {
                    "capability_id": "capability:private-compass",
                    "session_capability": self.token_b,
                },
            }
        )
        self.assertEqual(owner_by_id["result"]["handle"], "private-compass")

        nominated = service.handle(
            {
                "jsonrpc": "2.0",
                "id": "nominated",
                "method": "estate.resolve",
                "params": {
                    "handle_or_alias": "private-compass",
                    "agent_instance_id": "agent:b",
                    "host_session_id": "session:b",
                },
            }
        )
        self.assertEqual(nominated["error"]["code"], -32602)

    def test_past_session_capability_expiry_fails_cleanly_without_a_row(self) -> None:
        before = self.core.store.connection.execute(
            "SELECT COUNT(*) FROM session_query_capabilities"
        ).fetchone()[0]
        with self.assertRaises(ValidationError):
            self.core.reminders.issue_session_capability(
                "agent:a", "session:a", expires_at=stamp(-30)
            )
        after = self.core.store.connection.execute(
            "SELECT COUNT(*) FROM session_query_capabilities"
        ).fetchone()[0]
        self.assertEqual(after, before)

    def test_field_bound_card_expansion_rejects_tamper_scope_and_nonmember(self) -> None:
        field = self._task_field()
        signal = member_by_handle(field, "signal-weaver")
        expanded = self.core.reminders.card(
            self.token_a,
            field["field_id"],
            field["membership_manifest_digest"],
            signal["visibility_token"],
        )
        self.assertEqual(expanded["card"]["card_id"], signal["card_id"])
        self.assertEqual(expanded["card"]["card_revision"], 1)

        body, signature = signal["visibility_token"].split(".", 1)
        replacement = "A" if signature[0] != "A" else "B"
        tampered = body + "." + replacement + signature[1:]
        with self.assertRaises(NotFoundError):
            self.core.reminders.card(
                self.token_a,
                field["field_id"],
                field["membership_manifest_digest"],
                tampered,
            )
        with self.assertRaises(NotFoundError):
            self.core.reminders.card(
                self.token_a,
                field["field_id"],
                "0" * 64,
                signal["visibility_token"],
            )

        outer_field = self.core.reminders.neighborhood(
            self.token_a,
            SNAPSHOT_ONE,
            [
                {
                    "anchor_id": "outer",
                    "anchor_kind": "task",
                    "lexical_hints": ["perimeter marker"],
                }
            ],
        )
        outer = member_by_handle(outer_field, "outer-marker")
        with self.assertRaises(NotFoundError):
            self.core.reminders.card(
                self.token_a,
                field["field_id"],
                field["membership_manifest_digest"],
                outer["visibility_token"],
            )

    def test_visibility_token_rejects_noncanonical_base64url_spelling(self) -> None:
        field = self._task_field()
        signal = member_by_handle(field, "signal-weaver")
        body, signature = signal["visibility_token"].split(".", 1)
        malleated = body[:1] + "!!!!" + body[1:] + "." + signature
        with self.assertRaises(NotFoundError):
            self.core.reminders.card(
                self.token_a,
                field["field_id"],
                field["membership_manifest_digest"],
                malleated,
            )

    def test_new_generation_invalidates_old_queries_and_card_tokens(self) -> None:
        old_field = self._task_field()
        old_signal = member_by_handle(old_field, "signal-weaver")
        self.core.reminders.ingest_index(associative_index_manifest(2))
        with self.assertRaises(ConflictError):
            self.core.reminders.neighborhood(
                self.token_a,
                SNAPSHOT_ONE,
                [self._vector_anchor("task", "task", TASK_VECTOR)],
            )
        with self.assertRaises(ConflictError):
            self.core.reminders.card(
                self.token_a,
                old_field["field_id"],
                old_field["membership_manifest_digest"],
                old_signal["visibility_token"],
            )

        current = self.core.reminders.neighborhood(
            self.token_a,
            SNAPSHOT_TWO,
            [self._vector_anchor("task", "task", TASK_VECTOR)],
        )
        current_signal = member_by_handle(current, "signal-weaver")
        self.assertEqual(current_signal["card_revision"], 2)
        expanded = self.core.reminders.card(
            self.token_a,
            current["field_id"],
            current["membership_manifest_digest"],
            current_signal["visibility_token"],
        )
        self.assertEqual(expanded["card"]["card_revision"], 2)

    def test_query_is_side_effect_free_and_persists_no_raw_anchor_or_field(self) -> None:
        unique_raw_hint = "ephemeral-needle-7e42a19c"
        before = "\n".join(self.core.store.connection.iterdump())
        field = self.core.reminders.neighborhood(
            self.token_a,
            SNAPSHOT_ONE,
            [
                {
                    "anchor_id": "ephemeral",
                    "anchor_kind": "correction",
                    "lexical_hints": [unique_raw_hint],
                }
            ],
        )
        after = "\n".join(self.core.store.connection.iterdump())
        self.assertEqual(before, after)
        self.assertNotIn(unique_raw_hint, after)
        self.assertNotIn(field["field_id"], after)
        self.assertNotIn(field["representations"]["canonical"]["text"], after)
        self.assertNotIn(self.token_a, after)

    def test_exact_replay_is_idempotent_and_any_changed_manifest_conflicts(self) -> None:
        before = self.core.status()["counts"]
        replay = self.core.reminders.ingest_index(copy.deepcopy(self.manifest))
        self.assertTrue(replay["current"])
        self.assertEqual(self.core.status()["counts"], before)

        changed_card = associative_index_manifest(
            projection_overrides={
                "signal-weaver": "A changed projection under the same stable identities."
            }
        )
        with self.assertRaises(ConflictError):
            self.core.reminders.ingest_index(changed_card)

        changed_activation = copy.deepcopy(self.manifest)
        changed_activation["activation"]["activated_at"] = (
            "2026-01-01T00:00:01.000000Z"
        )
        with self.assertRaises(ConflictError):
            self.core.reminders.ingest_index(changed_activation)

    def test_index_requires_one_vector_for_every_approved_view(self) -> None:
        incomplete = associative_index_manifest(2)
        incomplete["vectors"] = incomplete["vectors"][:-1]
        rebind_manifest_snapshot(incomplete)
        with self.assertRaises(ValidationError):
            self.core.reminders.ingest_index(incomplete)

    def test_unavailable_vector_snapshot_degrades_explicitly_to_lexical_only(self) -> None:
        unavailable = associative_index_manifest(2)
        unavailable["snapshot"]["vector_coverage_state"] = "unavailable"
        unavailable["vectors"] = []
        rebind_manifest_snapshot(unavailable)
        status = self.core.reminders.ingest_index(unavailable)
        self.assertEqual(status["vector_coverage_state"], "unavailable")
        self.assertEqual(status["counts"]["vectors"], 0)

        with self.assertRaises(ValidationError):
            self.core.reminders.neighborhood(
                self.token_a,
                SNAPSHOT_TWO,
                [self._vector_anchor("task", "task", TASK_VECTOR)],
            )
        lexical = self.core.reminders.neighborhood(
            self.token_a,
            SNAPSHOT_TWO,
            [
                {
                    "anchor_id": "lexical-only",
                    "anchor_kind": "task",
                    "lexical_hints": ["causal pattern analysis"],
                }
            ],
        )
        self.assertEqual(lexical["mode"], "lexical_degraded")
        self.assertIn("signal-weaver", handles(lexical))
        self.assertIn("pattern-lens", handles(lexical))
        self.assertTrue(
            all(
                path["basis"] != "vector"
                for member in lexical["members"]
                for path in member["associations"]
            )
        )

    def test_malformed_query_vectors_are_rejected_by_the_float32_oracle(self) -> None:
        malformed = (
            [float("nan"), 0.0, 0.0, 0.0],
            [math.inf, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        )
        for index, vector in enumerate(malformed):
            with self.subTest(index=index), self.assertRaises(ValidationError):
                self.core.reminders.neighborhood(
                    self.token_a,
                    SNAPSHOT_ONE,
                    [self._vector_anchor(f"bad-{index}", "task", vector)],
                )

    def test_malformed_index_vectors_are_rejected_before_commit(self) -> None:
        malformed = (
            [float("nan"), 0.0, 0.0, 0.0],
            [math.inf, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        )
        before = self.core.status()["counts"]
        for index, vector in enumerate(malformed):
            manifest = associative_index_manifest(2)
            manifest["vectors"][0]["values"] = vector
            with self.subTest(index=index), self.assertRaises(ValidationError):
                self.core.reminders.ingest_index(manifest)
        self.assertEqual(self.core.status()["counts"], before)

    def test_canonical_and_compact_fields_conserve_membership(self) -> None:
        field = self._task_field()
        canonical = field["representations"]["canonical"]
        compact = field["representations"]["compact"]
        self.assertEqual(
            canonical["membership_manifest_digest"],
            field["membership_manifest_digest"],
        )
        self.assertEqual(
            compact["membership_manifest_digest"],
            field["membership_manifest_digest"],
        )
        for handle in handles(field):
            self.assertIn(handle, canonical["text"])
            self.assertIn(handle, compact["text"])

    def test_row_order_does_not_change_membership_or_rendering(self) -> None:
        first = self._task_field()
        with tempfile.TemporaryDirectory() as directory:
            other = MindCore(Path(directory) / "mind-core.sqlite3")
            try:
                self._prepare_core(other)
                other.reminders.ingest_index(
                    associative_index_manifest(reverse_rows=True)
                )
                token = other.reminders.issue_session_capability(
                    "agent:a",
                    "session:a",
                    exposure_scope="public_and_agent_private",
                )["session_capability"]
                second = other.reminders.neighborhood(
                    token,
                    SNAPSHOT_ONE,
                    [self._vector_anchor("task", "task", TASK_VECTOR)],
                )
            finally:
                other.close()
        self.assertEqual(
            first["membership_manifest_digest"],
            second["membership_manifest_digest"],
        )
        self.assertEqual(first["representations"], second["representations"])
        self.assertEqual(
            without_visibility(first["members"]),
            without_visibility(second["members"]),
        )

    def test_lifecycle_axes_remain_independent_and_do_not_imply_active(self) -> None:
        field = self._task_field()
        signal = member_by_handle(field, "signal-weaver")
        observed = {
            (item["axis"], item["state"])
            for item in signal["lifecycle_observations"]
        }
        self.assertEqual(
            observed,
            {
                ("custody", "canonical-constructed"),
                ("distribution", "not-generated"),
            },
        )
        capability = self.core.estate.capability("capability:signal-weaver")
        self.assertIsNone(capability["derived_active_state"])
        states = {item["state"] for item in capability["lifecycle_observations"]}
        self.assertTrue(states.isdisjoint({"installed", "invoked", "healthy"}))

    def test_service_is_query_only_and_claims_h0_no_further(self) -> None:
        service = QueryService(self.core)
        response = service.handle(
            {
                "jsonrpc": "2.0",
                "id": "field",
                "method": "reminder.neighborhood",
                "params": {
                    "session_capability": self.token_a,
                    "snapshot_id": SNAPSHOT_ONE,
                    "anchors": [self._vector_anchor("task", "task", TASK_VECTOR)],
                },
            }
        )
        self.assertEqual(response["meta"]["maximum_host_conformance"], "H0")
        self.assertIn("H0 query result only", response["meta"]["claim_boundary"])
        self.assertNotIn("delivery_receipt", response["result"])
        for method in (
            "admin.associative_index",
            "reminder.issue_session_capability",
            "reminder.revoke_session_capability",
        ):
            rejected = service.handle(
                {"jsonrpc": "2.0", "id": method, "method": method, "params": {}}
            )
            self.assertEqual(rejected["error"]["code"], -32601)

    def test_unscoped_h0_status_exposes_no_private_sensitive_phase2_counts(self) -> None:
        response = QueryService(self.core).handle(
            {"jsonrpc": "2.0", "id": "status", "method": "core.status", "params": {}}
        )
        sensitive = {
            "capability_cards",
            "capability_card_views",
            "capability_relations",
            "associative_index_snapshots",
            "associative_view_vectors",
            "associative_snapshot_activations",
            "session_query_capabilities",
        }
        self.assertTrue(
            sensitive.isdisjoint(response["result"].get("counts", {}))
        )

    def test_scoped_field_does_not_expose_global_estate_digest(self) -> None:
        self.assertNotIn("estate_digest", self._task_field())

    def test_lexical_profile_must_describe_the_executed_predicate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core = MindCore(Path(directory) / "mind-core.sqlite3")
            try:
                self._prepare_core(core)
                manifest = associative_index_manifest()
                manifest["lexical_profile"]["unicode_token_grammar"] = (
                    "split on ASCII spaces only"
                )
                manifest["lexical_profile"]["cue_membership_contract"] = (
                    "Return only the first arbitrary match."
                )
                rebind_record_digest(manifest["lexical_profile"], "profile_digest")
                rebind_manifest_snapshot(manifest)
                with self.assertRaises(ValidationError):
                    core.reminders.ingest_index(manifest)
            finally:
                core.close()

    def test_activation_time_must_advance_monotonically(self) -> None:
        generation_two = associative_index_manifest(2)
        generation_two["snapshot"]["created_at"] = CREATED_AT
        generation_two["activation"]["activated_at"] = CREATED_AT
        rebind_manifest_snapshot(generation_two)
        with self.assertRaises((ConflictError, ValidationError)):
            self.core.reminders.ingest_index(generation_two)

    def test_snapshot_digest_binds_cluster_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core = MindCore(Path(directory) / "mind-core.sqlite3")
            try:
                self._prepare_core(core)
                manifest = associative_index_manifest()
                manifest["clusters"][0]["description"] = (
                    "Changed cluster semantics under the same snapshot digest."
                )
                rebind_record_digest(manifest["clusters"][0], "cluster_digest")
                with self.assertRaises(ValidationError):
                    core.reminders.ingest_index(manifest)
            finally:
                core.close()

    def test_activation_seals_snapshot_projections_and_capability_visibility(self) -> None:
        connection = self.core.store.connection
        seal_probes = (
            (
                "INSERT INTO associative_snapshot_cards "
                "SELECT associative_index_snapshot_id,capability_card_id,source_digest,card_digest "
                "FROM associative_snapshot_cards WHERE associative_index_snapshot_id=? LIMIT 1",
                (SNAPSHOT_ONE,),
                "activated snapshot membership is immutable",
            ),
            (
                "INSERT INTO associative_snapshot_relations "
                "SELECT associative_index_snapshot_id,capability_relation_id,relation_digest "
                "FROM associative_snapshot_relations WHERE associative_index_snapshot_id=? LIMIT 1",
                (SNAPSHOT_ONE,),
                "activated snapshot relations are immutable",
            ),
            (
                "INSERT INTO associative_view_vectors "
                "SELECT associative_index_snapshot_id,capability_card_view_id,dimensions,"
                "vector_float32_le,vector_digest FROM associative_view_vectors "
                "WHERE associative_index_snapshot_id=? LIMIT 1",
                (SNAPSHOT_ONE,),
                "activated snapshot vectors are immutable",
            ),
            (
                "INSERT INTO capability_card_views("
                "capability_card_view_id,capability_card_id,view_kind,content,content_digest,created_at"
                ") VALUES (?,?,?,?,?,?)",
                (
                    "view:late-insert:r1",
                    "card:signal-weaver:r1",
                    "example",
                    "A post-activation view must not enter the sealed field.",
                    sha256_text(
                        "A post-activation view must not enter the sealed field."
                    ),
                    CREATED_AT,
                ),
                "activated card views are immutable",
            ),
            (
                "UPDATE capabilities SET handle=? WHERE capability_id=?",
                ("signal-weaver-mutated", "capability:signal-weaver"),
                "activated capability visibility is immutable",
            ),
            (
                "INSERT INTO capability_aliases("
                "capability_id,namespace,normalized_alias,display_alias"
                ") VALUES (?,?,?,?)",
                (
                    "capability:signal-weaver",
                    "global",
                    "late alias",
                    "Late Alias",
                ),
                "activated capability aliases are immutable",
            ),
            (
                "UPDATE capability_aliases SET display_alias=? "
                "WHERE capability_id=? AND namespace=? AND normalized_alias=?",
                (
                    "Changed Causal Map",
                    "capability:signal-weaver",
                    "global",
                    "causal map",
                ),
                "activated capability aliases are immutable",
            ),
        )
        for statement, params, expected_message in seal_probes:
            with self.subTest(expected_message=expected_message):
                with self.assertRaises(sqlite3.IntegrityError) as caught:
                    connection.execute(statement, params)
                self.assertIn(expected_message, str(caught.exception))

        activation = connection.execute(
            "SELECT * FROM associative_snapshot_activations "
            "WHERE associative_index_snapshot_id=?",
            (SNAPSHOT_ONE,),
        ).fetchone()
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO associative_snapshot_activations("
                "associative_snapshot_activation_id,associative_index_snapshot_id,"
                "prior_associative_index_snapshot_id,activated_at,activation_receipt_id"
                ") VALUES (?,?,?,?,?)",
                (
                    "activation:duplicate:r1",
                    SNAPSHOT_ONE,
                    activation["prior_associative_index_snapshot_id"],
                    activation["activated_at"],
                    activation["activation_receipt_id"],
                ),
            )

    def test_newer_revision_under_another_embedding_profile_invalidates_old_field(self) -> None:
        old_field = self._task_field()
        old_signal = member_by_handle(old_field, "signal-weaver")
        generation_two = associative_index_manifest(2)
        embedding = generation_two["embedding_profile"]
        embedding["embedding_profile_id"] = "embedding:phase2-synthetic-v2"
        embedding["name"] = "Phase 2 alternate deterministic oracle"
        embedding["model_id"] = "synthetic-fixed-v2"
        rebind_record_digest(embedding, "profile_digest")
        generation_two["snapshot"]["embedding_profile_id"] = embedding[
            "embedding_profile_id"
        ]
        generation_two["activation"]["prior_associative_index_snapshot_id"] = None
        rebind_manifest_snapshot(generation_two)

        new_status = self.core.reminders.ingest_index(generation_two)
        self.assertTrue(new_status["current"])
        old_status = self.core.reminders._snapshot_status(SNAPSHOT_ONE)
        self.assertTrue(old_status["activation_current"])
        self.assertFalse(old_status["card_revisions_current"])
        self.assertFalse(old_status["current"])
        with self.assertRaises(ConflictError):
            self.core.reminders.neighborhood(
                self.token_a,
                SNAPSHOT_ONE,
                [self._vector_anchor("task", "task", TASK_VECTOR)],
            )
        with self.assertRaises(ConflictError):
            self.core.reminders.card(
                self.token_a,
                old_field["field_id"],
                old_field["membership_manifest_digest"],
                old_signal["visibility_token"],
            )

    def test_current_source_binding_drift_marks_snapshot_noncurrent(self) -> None:
        old_field = self._task_field()
        self.core.store.connection.execute(
            "UPDATE sources SET digest=? WHERE source_id=?",
            ("f" * 64, "source:phase2-synthetic"),
        )
        status = self.core.reminders._snapshot_status(SNAPSHOT_ONE)
        self.assertTrue(status["activation_current"])
        self.assertFalse(status["source_current"])
        self.assertFalse(status["current"])
        with self.assertRaises(ConflictError):
            self.core.reminders.neighborhood(
                self.token_a,
                SNAPSHOT_ONE,
                [self._vector_anchor("task", "task", TASK_VECTOR)],
            )
        signal = member_by_handle(old_field, "signal-weaver")
        with self.assertRaises(ConflictError):
            self.core.reminders.card(
                self.token_a,
                old_field["field_id"],
                old_field["membership_manifest_digest"],
                signal["visibility_token"],
            )

    def test_exact_replay_detects_extra_derived_fts_projection(self) -> None:
        self.core.store.connection.execute(
            "INSERT INTO capability_card_fts("
            "associative_index_snapshot_id,capability_card_view_id,capability_id,handle,content"
            ") VALUES (?,?,?,?,?)",
            (
                SNAPSHOT_ONE,
                "view:extra-derived:r1",
                "capability:signal-weaver",
                "signal-weaver",
                "An extra rebuildable projection row.",
            ),
        )
        with self.assertRaises(ConflictError):
            self.core.reminders.ingest_index(copy.deepcopy(self.manifest))

    def test_future_activation_rolls_back_and_receipt_uses_server_observation_time(
        self,
    ) -> None:
        future = associative_index_manifest(2)
        future["activation"]["activated_at"] = "2999-01-01T00:00:00.000000Z"
        before_rejection = "\n".join(self.core.store.connection.iterdump())

        with self.assertRaisesRegex(
            ValidationError, "activation cannot be later than Core observation"
        ):
            self.core.reminders.ingest_index(future)

        self.assertEqual(
            "\n".join(self.core.store.connection.iterdump()), before_rejection
        )

        valid = associative_index_manifest(2)
        observed_lower_bound = stamp(-1)
        status = self.core.reminders.ingest_index(valid)
        observed_upper_bound = stamp(1)
        self.assertTrue(status["current"])
        activation = self.core.store.connection.execute(
            "SELECT activated_at,activation_receipt_id "
            "FROM associative_snapshot_activations "
            "WHERE associative_index_snapshot_id=?",
            (SNAPSHOT_TWO,),
        ).fetchone()
        receipt = self.core.store.connection.execute(
            "SELECT observed_at,receipt_type,subject_id FROM receipts WHERE receipt_id=?",
            (activation["activation_receipt_id"],),
        ).fetchone()
        self.assertEqual(activation["activated_at"], valid["activation"]["activated_at"])
        self.assertEqual(receipt["receipt_type"], "reminder.snapshot_activation")
        self.assertEqual(receipt["subject_id"], SNAPSHOT_TWO)
        self.assertNotEqual(receipt["observed_at"], activation["activated_at"])
        self.assertGreaterEqual(
            parse_timestamp(receipt["observed_at"], "receipt.observed_at"),
            parse_timestamp(observed_lower_bound, "observed lower bound"),
        )
        self.assertLessEqual(
            parse_timestamp(receipt["observed_at"], "receipt.observed_at"),
            parse_timestamp(observed_upper_bound, "observed upper bound"),
        )

    def test_database_dependent_validation_holds_begin_immediate_against_second_writer(
        self,
    ) -> None:
        generation_two = associative_index_manifest(2)
        source_before = self.core.store.connection.execute(
            "SELECT digest FROM sources WHERE source_id=?", (SOURCE_ID,)
        ).fetchone()["digest"]
        original_validation = self.core.reminders._validate_generation_bindings
        probe_reached = False

        def validation_with_second_writer_probe(**kwargs: Any) -> None:
            nonlocal probe_reached
            probe_reached = True
            second_writer = sqlite3.connect(
                self.core.store.path, isolation_level=None, timeout=0.0
            )
            try:
                second_writer.execute("PRAGMA busy_timeout=0")
                with self.assertRaises(sqlite3.OperationalError) as caught:
                    second_writer.execute(
                        "UPDATE sources SET digest=? WHERE source_id=?",
                        ("e" * 64, SOURCE_ID),
                    )
                self.assertIn("locked", str(caught.exception).casefold())
            finally:
                second_writer.close()
            original_validation(**kwargs)

        self.core.reminders._validate_generation_bindings = (
            validation_with_second_writer_probe
        )
        try:
            status = self.core.reminders.ingest_index(generation_two)
        finally:
            self.core.reminders._validate_generation_bindings = original_validation

        self.assertTrue(probe_reached)
        self.assertTrue(status["current"])
        source_after = self.core.store.connection.execute(
            "SELECT digest FROM sources WHERE source_id=?", (SOURCE_ID,)
        ).fetchone()["digest"]
        self.assertEqual(source_after, source_before)

    def test_normalized_alias_remains_exhaustive_when_display_alias_differs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core = MindCore(Path(directory) / "mind-core.sqlite3")
            try:
                core.hosts.handshake(handshake_record("agent:a", "session:a"))
                core.hosts.handshake(handshake_record("agent:b", "session:b"))
                fixture = phase2_bootstrap_fixture()
                outer = next(
                    capability
                    for capability in fixture["capabilities"]
                    if capability["capability_id"] == "capability:outer-marker"
                )
                outer["aliases"][0] = {
                    "namespace": "global",
                    "alias": "normalized perimeter cue",
                    "display_alias": "Readable Boundary Label",
                }
                core.bootstrap(fixture)
                manifest = associative_index_manifest()
                capability_ids = [
                    card["capability_id"] for card in manifest["cards"]
                ]
                rebind_manifest_snapshot(
                    manifest,
                    estate_surface_manifest=core.reminders._capability_surface_manifest(
                        capability_ids
                    ),
                )
                core.reminders.ingest_index(manifest)
                token = core.reminders.issue_session_capability(
                    "agent:a", "session:a", exposure_scope="public_only"
                )["session_capability"]

                alias = core.store.connection.execute(
                    "SELECT normalized_alias,display_alias FROM capability_aliases "
                    "WHERE capability_id=?",
                    ("capability:outer-marker",),
                ).fetchone()
                self.assertEqual(alias["normalized_alias"], "normalized perimeter cue")
                self.assertEqual(alias["display_alias"], "Readable Boundary Label")
                field = core.reminders.neighborhood(
                    token,
                    SNAPSHOT_ONE,
                    [
                        {
                            "anchor_id": "normalized-alias",
                            "anchor_kind": "task",
                            "lexical_hints": ["normalized perimeter cue"],
                        }
                    ],
                )
                self.assertEqual(handles(field), {"outer-marker"})
                self.assertIn(
                    "alias",
                    {
                        path.get("lexical_surface")
                        for path in member_by_handle(
                            field, "outer-marker"
                        )["associations"]
                    },
                )
            finally:
                core.close()

    def test_manifest_binds_handle_and_alias_surfaces_across_twin_databases(
        self,
    ) -> None:
        for changed_surface in ("handle", "alias"):
            with self.subTest(changed_surface=changed_surface), tempfile.TemporaryDirectory() as directory:
                core = MindCore(Path(directory) / "mind-core.sqlite3")
                try:
                    core.hosts.handshake(handshake_record("agent:a", "session:a"))
                    core.hosts.handshake(handshake_record("agent:b", "session:b"))
                    fixture = phase2_bootstrap_fixture()
                    if changed_surface == "handle":
                        signal = next(
                            capability
                            for capability in fixture["capabilities"]
                            if capability["capability_id"]
                            == "capability:signal-weaver"
                        )
                        signal["handle"] = "signal-weaver-renamed"
                    else:
                        outer = next(
                            capability
                            for capability in fixture["capabilities"]
                            if capability["capability_id"]
                            == "capability:outer-marker"
                        )
                        outer["aliases"][0]["display_alias"] = (
                            "Changed Perimeter Label"
                        )
                    core.bootstrap(fixture)

                    with self.assertRaisesRegex(
                        ValidationError, "estate_digest does not bind"
                    ):
                        core.reminders.ingest_index(
                            copy.deepcopy(associative_index_manifest())
                        )
                    count = core.store.connection.execute(
                        "SELECT COUNT(*) FROM associative_index_snapshots"
                    ).fetchone()[0]
                    self.assertEqual(count, 0)
                finally:
                    core.close()

    def test_public_field_survives_private_only_newer_revision_and_source_drift(
        self,
    ) -> None:
        public_token = self.core.reminders.issue_session_capability(
            "agent:a", "session:a", exposure_scope="public_only"
        )["session_capability"]
        before = canonical_json(self._task_field(token=public_token))
        private_source_id = "source:phase2-private-only"
        private_source_digest = sha256_text("phase2 private-only source v1")
        self.core.bootstrap(
            {
                "format": "mind-core-bootstrap/v1",
                "sources": [
                    {
                        "source_id": private_source_id,
                        "locator": "fixture://phase2/private-only",
                        "digest": private_source_digest,
                        "custody_state": "canonical-constructed",
                        "authority_ref": "Private-only scope isolation fixture.",
                        "observed_at": CREATED_AT,
                    }
                ],
                "products": [],
                "providers": [],
                "capabilities": [],
                "distributions": [],
                "receipts": [],
                "lifecycle_observations": [],
                "mounts": [],
            }
        )
        private_generation = _private_only_change_generation_two(
            source_id=private_source_id, source_digest=private_source_digest
        )
        status = self.core.reminders.ingest_index(private_generation)
        self.assertTrue(status["current"])

        after_private_activation = canonical_json(
            self._task_field(token=public_token)
        )
        self.assertEqual(after_private_activation, before)

        self.core.store.connection.execute(
            "UPDATE sources SET digest=? WHERE source_id=?",
            ("d" * 64, private_source_id),
        )
        self.assertFalse(
            self.core.reminders._snapshot_status(SNAPSHOT_TWO)["source_current"]
        )
        after_private_source_drift = canonical_json(
            self._task_field(token=public_token)
        )
        self.assertEqual(after_private_source_drift, before)

    def test_query_status_coarsens_foreign_key_diagnostics(self) -> None:
        connection = self.core.store.connection
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute(
            "INSERT INTO capability_aliases("
            "capability_id,namespace,normalized_alias,display_alias"
            ") VALUES (?,?,?,?)",
            (
                "capability:missing-for-diagnostic-probe",
                "global",
                "missing diagnostic alias",
                "Missing Diagnostic Alias",
            ),
        )
        connection.execute("PRAGMA foreign_keys=ON")
        self.assertTrue(self.core.store.integrity()["foreign_key_failures"])

        response = QueryService(self.core).handle(
            {"jsonrpc": "2.0", "id": "coarse-status", "method": "core.status", "params": {}}
        )
        diagnostics = response["result"]["sqlite"]
        self.assertEqual(
            set(diagnostics),
            {
                "integrity_ok",
                "foreign_key_ok",
                "foreign_keys_enabled",
                "journal_mode",
            },
        )
        self.assertFalse(diagnostics["foreign_key_ok"])
        self.assertTrue(diagnostics["foreign_keys_enabled"])
        serialized = canonical_json(response)
        self.assertNotIn("foreign_key_failures", serialized)
        self.assertNotIn("capability_aliases", serialized)
        self.assertNotIn("capability:missing-for-diagnostic-probe", serialized)

    def test_older_card_revision_activation_rolls_back_after_newer_revision(
        self,
    ) -> None:
        self.core.reminders.ingest_index(associative_index_manifest(2))
        rollback = copy.deepcopy(self.manifest)
        rollback["snapshot"]["associative_index_snapshot_id"] = (
            "snapshot:phase2-synthetic:rollback"
        )
        rollback["snapshot"]["created_at"] = "2026-01-01T00:20:00.000000Z"
        rollback["activation"] = {
            "associative_snapshot_activation_id": "activation:phase2-synthetic:rollback",
            "prior_associative_index_snapshot_id": SNAPSHOT_TWO,
            "activated_at": "2026-01-01T00:20:00.000000Z",
        }
        rebind_manifest_snapshot(rollback)
        before = "\n".join(self.core.store.connection.iterdump())

        with self.assertRaisesRegex(
            ConflictError, "stale capability-card revision"
        ):
            self.core.reminders.ingest_index(rollback)

        self.assertEqual("\n".join(self.core.store.connection.iterdump()), before)

    def test_card_created_after_snapshot_is_rejected_before_commit(self) -> None:
        manifest = associative_index_manifest(2)
        card = next(
            item
            for item in manifest["cards"]
            if item["capability_id"] == "capability:signal-weaver"
        )
        card["created_at"] = "2026-01-01T00:11:00.000000Z"
        card["views"][0]["created_at"] = "2026-01-01T00:11:00.000000Z"
        rebind_card_digest(card)
        rebind_manifest_snapshot(manifest)
        before = "\n".join(self.core.store.connection.iterdump())

        with self.assertRaisesRegex(
            ValidationError, "card creation cannot be later than its snapshot"
        ):
            self.core.reminders.ingest_index(manifest)

        self.assertEqual("\n".join(self.core.store.connection.iterdump()), before)

    def test_card_view_cannot_predate_its_card_revision(self) -> None:
        manifest = associative_index_manifest(2)
        card = next(
            item
            for item in manifest["cards"]
            if item["capability_id"] == "capability:signal-weaver"
        )
        self.assertEqual(card["created_at"], GENERATION_TWO_AT)
        card["views"][0]["created_at"] = CREATED_AT
        rebind_card_digest(card)
        rebind_manifest_snapshot(manifest)
        before = "\n".join(self.core.store.connection.iterdump())

        with self.assertRaisesRegex(
            ValidationError, "card-view creation predates its card revision"
        ):
            self.core.reminders.ingest_index(manifest)

        self.assertEqual("\n".join(self.core.store.connection.iterdump()), before)

    def test_new_profile_cannot_bypass_global_generation_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core = MindCore(Path(directory) / "mind-core.sqlite3")
            try:
                self._prepare_core(core)

                def profile_manifest(
                    suffix: str,
                    *,
                    include_late_capability: bool,
                    activated_at: str,
                ) -> dict[str, Any]:
                    manifest = associative_index_manifest(1)
                    if not include_late_capability:
                        omitted_cards = {
                            card["capability_card_id"]
                            for card in manifest["cards"]
                            if card["capability_id"] == "capability:outer-marker"
                        }
                        omitted_views = {
                            view["capability_card_view_id"]
                            for card in manifest["cards"]
                            if card["capability_card_id"] in omitted_cards
                            for view in card["views"]
                        }
                        manifest["cards"] = [
                            card
                            for card in manifest["cards"]
                            if card["capability_card_id"] not in omitted_cards
                        ]
                        manifest["relations"] = [
                            relation
                            for relation in manifest["relations"]
                            if relation["from_capability_card_id"]
                            not in omitted_cards
                            and relation["to_capability_card_id"]
                            not in omitted_cards
                        ]
                        manifest["vectors"] = [
                            vector
                            for vector in manifest["vectors"]
                            if vector["capability_card_view_id"] not in omitted_views
                        ]

                    profile_id = f"embedding:three-profile:{suffix}"
                    embedding_profile = manifest["embedding_profile"]
                    embedding_profile["embedding_profile_id"] = profile_id
                    embedding_profile["name"] = (
                        f"Three-profile generation oracle {suffix}"
                    )
                    embedding_profile["model_id"] = f"synthetic-three-profile-{suffix}"
                    rebind_record_digest(embedding_profile, "profile_digest")

                    snapshot_id = f"snapshot:three-profile:{suffix}"
                    manifest["snapshot"]["associative_index_snapshot_id"] = snapshot_id
                    manifest["snapshot"]["embedding_profile_id"] = profile_id
                    manifest["activation"] = {
                        "associative_snapshot_activation_id": (
                            f"activation:three-profile:{suffix}"
                        ),
                        "prior_associative_index_snapshot_id": None,
                        "activated_at": activated_at,
                    }
                    rebind_manifest_snapshot(manifest)
                    return manifest

                profile_a = profile_manifest(
                    "a",
                    include_late_capability=False,
                    activated_at=CREATED_AT,
                )
                profile_b = profile_manifest(
                    "b",
                    include_late_capability=True,
                    activated_at="2026-01-01T00:10:00.000000Z",
                )
                profile_a_capabilities = {
                    card["capability_id"] for card in profile_a["cards"]
                }
                profile_b_capabilities = {
                    card["capability_id"] for card in profile_b["cards"]
                }
                self.assertEqual(
                    profile_b_capabilities - profile_a_capabilities,
                    {"capability:outer-marker"},
                )
                core.reminders.ingest_index(profile_a)
                core.reminders.ingest_index(profile_b)

                for suffix, activated_at in (
                    ("c-equal", "2026-01-01T00:10:00.000000Z"),
                    ("c-backdated", "2026-01-01T00:09:00.000000Z"),
                ):
                    with self.subTest(activated_at=activated_at):
                        candidate = profile_manifest(
                            suffix,
                            include_late_capability=False,
                            activated_at=activated_at,
                        )
                        self.assertNotIn(
                            "capability:outer-marker",
                            {
                                card["capability_id"]
                                for card in candidate["cards"]
                            },
                        )
                        before = "\n".join(core.store.connection.iterdump())

                        with self.assertRaisesRegex(
                            ConflictError,
                            "global generation chain",
                        ):
                            core.reminders.ingest_index(candidate)

                        self.assertEqual(
                            "\n".join(core.store.connection.iterdump()), before
                        )
            finally:
                core.close()


if __name__ == "__main__":
    unittest.main()
