from __future__ import annotations

import copy
import hashlib
import math
import struct
from typing import Any, Iterable, Sequence

from mind_core.util import canonical_json, record_binding_hash, sha256_text


CREATED_AT = "2026-01-01T00:00:00.000000Z"
GENERATION_TWO_AT = "2026-01-01T00:10:00.000000Z"
SOURCE_ID = "source:phase2-synthetic"
SOURCE_DIGEST = sha256_text("phase2 synthetic source v1")
PRODUCT_ID = "product:phase2-synthetic"
PROVIDER_ID = "provider:phase2-synthetic"
LEXICAL_PROFILE_ID = "lexical:phase2-synthetic-v1"
EMBEDDING_PROFILE_ID = "embedding:phase2-synthetic-v1"

TASK_VECTOR = (1.0, 0.0, 0.0, 0.0)


def float32_vector(values: Sequence[float]) -> tuple[float, ...]:
    payload = struct.pack(f"<{len(values)}f", *values)
    return tuple(struct.unpack(f"<{len(values)}f", payload))


def cosine_distance(left: Sequence[float], right: Sequence[float]) -> float:
    left32 = float32_vector(left)
    right32 = float32_vector(right)
    dot = math.fsum(a * b for a, b in zip(left32, right32, strict=True))
    left_norm = math.sqrt(math.fsum(value * value for value in left32))
    right_norm = math.sqrt(math.fsum(value * value for value in right32))
    cosine = dot / (left_norm * right_norm)
    return 1.0 - min(1.0, max(-1.0, cosine))


PATTERN_VECTOR = float32_vector((0.98, math.sqrt(1.0 - 0.98**2), 0.0, 0.0))
BOUNDARY_VECTOR = PATTERN_VECTOR
PROFILE_RADIUS = cosine_distance(TASK_VECTOR, PATTERN_VECTOR)
PROFILE_TOLERANCE = 1e-9
OUTER_VECTOR = float32_vector(
    (0.9798, math.sqrt(1.0 - 0.9798**2), 0.0, 0.0)
)

VECTOR_BY_HANDLE: dict[str, tuple[float, ...]] = {
    "signal-weaver": TASK_VECTOR,
    "pattern-lens": PATTERN_VECTOR,
    "bridge-kit": (0.0, -1.0, 0.0, 0.0),
    "boundary-decoy": BOUNDARY_VECTOR,
    "correction-lens": (0.0, 1.0, 0.0, 0.0),
    "private-compass": TASK_VECTOR,
    "outer-marker": OUTER_VECTOR,
}


CARD_SPECS: tuple[dict[str, Any], ...] = (
    {
        "handle": "signal-weaver",
        "name": "Signal Weaver",
        "cluster": "signals",
        "projection": "Maps causal structure into a compact working model.",
        "boundaries": "Requires named evidence for consequential claims.",
        "view_kind": "transformation",
        "content": "Map causal pattern analysis across complex systems.",
        "aliases": ("causal map",),
    },
    {
        "handle": "pattern-lens",
        "name": "Pattern Lens",
        "cluster": "inquiry",
        "projection": "Inspects recurring structure and dependency topology.",
        "boundaries": "Does not turn resemblance into causation.",
        "view_kind": "positive_cue",
        "content": "Inspect causal pattern analysis and dependency topology.",
        "aliases": ("dependency topology lens",),
    },
    {
        "handle": "bridge-kit",
        "name": "Bridge Kit",
        "cluster": "coordination",
        "projection": "Translates an established map into coordinated handoffs.",
        "boundaries": "Needs an upstream model before handoff design.",
        "view_kind": "situation",
        "content": "Use when a stable model must cross an ownership boundary.",
        "aliases": (),
    },
    {
        "handle": "boundary-decoy",
        "name": "Boundary Decoy",
        "cluster": "guardrails",
        "projection": "Flags a nearby form that can mislead by surface resemblance.",
        "boundaries": "Boundary evidence only; do not treat resemblance as support.",
        "view_kind": "positive_cue",
        "content": "A familiar surface pattern can look immediately applicable.",
        "aliases": (),
    },
    {
        "handle": "correction-lens",
        "name": "Correction Lens",
        "cluster": "repair",
        "projection": "Reframes assumptions after contradiction or error.",
        "boundaries": "Preserves supported prior findings while revising the fault.",
        "view_kind": "error_or_correction",
        "content": "Use after a contradiction exposes a broken assumption.",
        "aliases": (),
    },
    {
        "handle": "private-compass",
        "name": "Private Compass",
        "cluster": "orientation",
        "projection": "Recalls private operating constraints for the bound agent.",
        "boundaries": "Visible only through the owning agent session capability.",
        "view_kind": "positive_cue",
        "content": "Recall the bound private compass and its operating constraints.",
        "aliases": (),
        "private_owner": "agent:b",
    },
    {
        "handle": "outer-marker",
        "name": "Outer Marker",
        "cluster": "signals",
        "projection": "Marks a reference just outside the configured semantic field.",
        "boundaries": "Appears only through an independent lexical association.",
        "view_kind": "example",
        "content": "A distant reference outside the configured vector field.",
        "aliases": ("perimeter marker",),
    },
)


CLUSTER_SPECS: tuple[tuple[str, str, str], ...] = (
    ("signals", "Signals", "Causal and structural orientation."),
    ("inquiry", "Inquiry", "Pattern inspection and discriminating questions."),
    ("coordination", "Coordination", "Ownership boundaries and handoffs."),
    ("guardrails", "Guardrails", "Nearby traps and explicit negative boundaries."),
    ("repair", "Repair", "Correction after contradiction or error."),
    ("orientation", "Orientation", "Scoped operating context."),
)


def _estate_surface_manifest(cards: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    capability_ids = {card["capability_id"] for card in cards}
    return [
        {
            "capability_id": f"capability:{spec['handle']}",
            "handle": spec["handle"],
            "exposure_policy": (
                "agent_private" if spec.get("private_owner") else "public_safe"
            ),
            "owner_agent_instance_id": spec.get("private_owner"),
            "aliases": [
                {
                    "namespace": "global",
                    "normalized_alias": alias.casefold(),
                    "display_alias": alias,
                }
                for alias in spec["aliases"]
            ],
        }
        for spec in sorted(CARD_SPECS, key=lambda item: item["handle"])
        if f"capability:{spec['handle']}" in capability_ids
    ]


def _record_digest(record: dict[str, Any], digest_field: str) -> str:
    return sha256_text(
        canonical_json(
            {key: value for key, value in record.items() if key != digest_field}
        )
    )


def rebind_record_digest(record: dict[str, Any], digest_field: str) -> None:
    record[digest_field] = _record_digest(record, digest_field)


def rebind_card_digest(card: dict[str, Any]) -> None:
    """Rebind a wire-format card using Core's parent-bound view material."""

    material = {
        key: value
        for key, value in card.items()
        if key not in {"card_digest", "views"}
    }
    material["views"] = sorted(
        (
            {
                **view,
                "capability_card_id": card["capability_card_id"],
            }
            for view in card["views"]
        ),
        key=lambda view: view["capability_card_view_id"],
    )
    card["card_digest"] = _record_digest(material, "card_digest")


def _lifecycle_pair(handle: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    observations: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for axis, state in (
        ("custody", "canonical-constructed"),
        ("distribution", "not-generated"),
    ):
        observation_id = f"lifecycle:{handle}:{axis}"
        receipt_id = f"receipt:{handle}:{axis}"
        observation = {
            "observation_id": observation_id,
            "capability_id": f"capability:{handle}",
            "distribution_id": None,
            "axis": axis,
            "state": state,
            "agent_instance_id": None,
            "host_session_id": None,
            "observed_at": CREATED_AT,
            "expires_at": None,
            "evidence_receipt_id": receipt_id,
            "source_reference": "Synthetic fixture evidence only.",
        }
        receipts.append(
            {
                "receipt_id": receipt_id,
                "idempotency_key": f"lifecycle:{handle}:{axis}",
                "receipt_type": "lifecycle.observation",
                "subject_kind": "lifecycle_observation",
                "subject_id": observation_id,
                "evidence_state": "observed",
                "claimed_boundary": "The synthetic lifecycle record is fixture evidence only.",
                "observed_at": CREATED_AT,
                "redaction_class": "metadata_only",
                "payload_hash": record_binding_hash(observation),
            }
        )
        observations.append(observation)
    return observations, receipts


def phase2_bootstrap_fixture() -> dict[str, Any]:
    capabilities: list[dict[str, Any]] = []
    for spec in CARD_SPECS:
        capabilities.append(
            {
                "capability_id": f"capability:{spec['handle']}",
                "handle": spec["handle"],
                "name": spec["name"],
                "product_id": PRODUCT_ID,
                "canonical_source_id": SOURCE_ID,
                "promise": spec["projection"],
                "negative_space": spec["boundaries"],
                "created_at": CREATED_AT,
                "superseded_by": None,
                "aliases": [
                    {
                        "namespace": "global",
                        "alias": alias,
                        "display_alias": alias,
                    }
                    for alias in spec["aliases"]
                ],
                "entrypoints": [],
                **(
                    {
                        "exposure_policy": "agent_private",
                        "owner_agent_instance_id": spec["private_owner"],
                    }
                    if spec.get("private_owner")
                    else {}
                ),
            }
        )

    lifecycle, receipts = _lifecycle_pair("signal-weaver")
    return {
        "format": "mind-core-bootstrap/v1",
        "sources": [
            {
                "source_id": SOURCE_ID,
                "locator": "fixture://phase2/domain-neutral",
                "digest": SOURCE_DIGEST,
                "custody_state": "canonical-constructed",
                "authority_ref": "Phase 2 deterministic acceptance fixture.",
                "observed_at": CREATED_AT,
            }
        ],
        "products": [
            {
                "product_id": PRODUCT_ID,
                "name": "Phase 2 Synthetic Estate",
                "owner": "MIND acceptance tests",
                "canonical_uri": None,
                "created_at": CREATED_AT,
            }
        ],
        "providers": [
            {
                "provider_id": PROVIDER_ID,
                "name": "Deterministic Float Fixture",
                "owner": "MIND acceptance tests",
                "provider_kind": "test_fixture",
                "canonical_uri": None,
                "created_at": CREATED_AT,
            }
        ],
        "capabilities": capabilities,
        "distributions": [],
        "receipts": receipts,
        "lifecycle_observations": lifecycle,
        "mounts": [],
    }


def _lexical_profile() -> dict[str, Any]:
    record = {
        "lexical_profile_id": LEXICAL_PROFILE_ID,
        "name": "Phase 2 deterministic lexical oracle",
        "normalization_contract": "nfkc-casefold-contiguous-token-v1",
        "unicode_token_grammar": r"\w+(?:[.:/-]\w+)* under Python Unicode semantics",
        "cue_membership_contract": "Complete contiguous hint-token sequence; exhaustive over visible approved surfaces.",
        "created_at": CREATED_AT,
    }
    record["profile_digest"] = _record_digest(record, "profile_digest")
    return record


def _embedding_profile() -> dict[str, Any]:
    record = {
        "embedding_profile_id": EMBEDDING_PROFILE_ID,
        "name": "Phase 2 deterministic four-dimensional oracle",
        "provider_id": PROVIDER_ID,
        "model_id": "synthetic-fixed-v1",
        "dimensions": 4,
        "metric": "cosine_distance",
        "radius": PROFILE_RADIUS,
        "comparison_tolerance": PROFILE_TOLERANCE,
        "vector_encoding": "float32_le",
        "qualification_state": "test_only",
        "qualification_evidence_ref": "Deterministic fixture geometry only.",
        "qualification_digest": sha256_text("phase2 deterministic geometry v1"),
        "created_at": CREATED_AT,
    }
    record["profile_digest"] = _record_digest(record, "profile_digest")
    return record


def _clusters() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for handle, name, description in CLUSTER_SPECS:
        record = {
            "cluster_id": f"cluster:{handle}",
            "handle": handle,
            "name": name,
            "description": description,
            "source_id": SOURCE_ID,
            "source_digest": SOURCE_DIGEST,
            "created_at": CREATED_AT,
        }
        record["cluster_digest"] = _record_digest(record, "cluster_digest")
        result.append(record)
    return result


def _cards(
    generation: int, projection_overrides: dict[str, str] | None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    created_at = CREATED_AT if generation == 1 else GENERATION_TWO_AT
    manifest_cards: list[dict[str, Any]] = []
    validated_views: list[dict[str, Any]] = []
    overrides = projection_overrides or {}
    for spec in CARD_SPECS:
        handle = spec["handle"]
        card_id = f"card:{handle}:r{generation}"
        view = {
            "capability_card_view_id": f"view:{handle}:r{generation}",
            "capability_card_id": card_id,
            "view_kind": spec["view_kind"],
            "content": spec["content"],
            "content_digest": sha256_text(spec["content"]),
            "created_at": created_at,
        }
        card = {
            "capability_card_id": card_id,
            "capability_id": f"capability:{handle}",
            "revision": generation,
            "compact_projection": overrides.get(handle, spec["projection"]),
            "boundaries": spec["boundaries"],
            "cluster_id": f"cluster:{spec['cluster']}",
            "exposure_policy": (
                "agent_private" if spec.get("private_owner") else "public_safe"
            ),
            "owner_agent_instance_id": spec.get("private_owner"),
            "source_id": SOURCE_ID,
            "source_digest": SOURCE_DIGEST,
            "context_cost": 64,
            "created_at": created_at,
        }
        card_material = {**card, "views": [view]}
        card["card_digest"] = _record_digest(card_material, "card_digest")
        manifest_cards.append(
            {
                **card,
                "views": [
                    {
                        key: value
                        for key, value in view.items()
                        if key != "capability_card_id"
                    }
                ],
            }
        )
        validated_views.append(view)
    return manifest_cards, validated_views


def _relations(generation: int) -> list[dict[str, Any]]:
    created_at = CREATED_AT if generation == 1 else GENERATION_TWO_AT
    relation_specs = (
        ("signal-bridge", "signal-weaver", "bridge-kit", "bridges_to"),
        ("signal-boundary", "signal-weaver", "boundary-decoy", "false_friend_of"),
        ("signal-private", "signal-weaver", "private-compass", "complements"),
    )
    result: list[dict[str, Any]] = []
    for suffix, source, target, kind in relation_specs:
        record = {
            "capability_relation_id": f"relation:{suffix}:r{generation}",
            "from_capability_card_id": f"card:{source}:r{generation}",
            "to_capability_card_id": f"card:{target}:r{generation}",
            "relation_kind": kind,
            "source_id": SOURCE_ID,
            "source_digest": SOURCE_DIGEST,
            "created_at": created_at,
        }
        record["relation_digest"] = _record_digest(record, "relation_digest")
        result.append(record)
    return result


def _vectors(generation: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for spec in CARD_SPECS:
        handle = spec["handle"]
        values = float32_vector(VECTOR_BY_HANDLE[handle])
        payload = struct.pack("<4f", *values)
        result.append(
            {
                "capability_card_view_id": f"view:{handle}:r{generation}",
                "values": list(values),
                "vector_digest": hashlib.sha256(payload).hexdigest(),
            }
        )
    return result


def associative_index_manifest(
    generation: int = 1,
    *,
    reverse_rows: bool = False,
    projection_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    if generation not in (1, 2):
        raise ValueError("the acceptance fixture defines exactly two generations")
    lexical_profile = _lexical_profile()
    embedding_profile = _embedding_profile()
    clusters = _clusters()
    cards, _ = _cards(generation, projection_overrides)
    relations = _relations(generation)
    vectors = _vectors(generation)
    created_at = CREATED_AT if generation == 1 else GENERATION_TWO_AT

    estate_digest = sha256_text(canonical_json(_estate_surface_manifest(cards)))
    source_digest = sha256_text(
        canonical_json(
            sorted(
                {
                    (record["source_id"], record["source_digest"])
                    for record in [*clusters, *cards, *relations]
                }
            )
        )
    )
    card_digest = sha256_text(
        canonical_json(sorted(card["card_digest"] for card in cards))
    )
    profile_digest = sha256_text(
        canonical_json(
            [lexical_profile["profile_digest"], embedding_profile["profile_digest"]]
        )
    )
    snapshot = {
        "associative_index_snapshot_id": f"snapshot:phase2-synthetic:r{generation}",
        "embedding_profile_id": EMBEDDING_PROFILE_ID,
        "lexical_profile_id": LEXICAL_PROFILE_ID,
        "vector_coverage_state": "complete",
        "estate_digest": estate_digest,
        "source_digest": source_digest,
        "card_digest": card_digest,
        "profile_digest": profile_digest,
        "builder_identity": "phase2 deterministic acceptance fixture",
        "evidence_boundary": "Synthetic geometry proves protocol behavior, not semantic quality.",
        "created_at": created_at,
        "expected_card_count": len(cards),
        "expected_relation_count": len(relations),
        "expected_vector_count": len(vectors),
    }
    snapshot_material = dict(snapshot)
    for field in (
        "expected_card_count",
        "expected_relation_count",
        "expected_vector_count",
    ):
        snapshot_material.pop(field)
    snapshot_material.update(
        {
            "cards": sorted(
                (card["capability_card_id"], card["card_digest"])
                for card in cards
            ),
            "clusters": sorted(
                (cluster["cluster_id"], cluster["cluster_digest"])
                for cluster in clusters
            ),
            "relations": sorted(
                (relation["capability_relation_id"], relation["relation_digest"])
                for relation in relations
            ),
            "vectors": sorted(
                (vector["capability_card_view_id"], vector["vector_digest"])
                for vector in vectors
            ),
        }
    )
    snapshot["snapshot_digest"] = sha256_text(canonical_json(snapshot_material))

    manifest = {
        "format": "mind-associative-index/v1",
        "lexical_profile": lexical_profile,
        "embedding_profile": embedding_profile,
        "clusters": clusters,
        "cards": cards,
        "relations": relations,
        "snapshot": snapshot,
        "vectors": vectors,
        "activation": {
            "associative_snapshot_activation_id": f"activation:phase2-synthetic:r{generation}",
            "prior_associative_index_snapshot_id": (
                None if generation == 1 else "snapshot:phase2-synthetic:r1"
            ),
            "activated_at": created_at,
        },
    }
    if reverse_rows:
        manifest = copy.deepcopy(manifest)
        for field in ("clusters", "cards", "relations", "vectors"):
            manifest[field].reverse()
        for card in manifest["cards"]:
            card["views"].reverse()
    return manifest


def rebind_manifest_snapshot(
    manifest: dict[str, Any],
    *,
    bind_clusters: bool = True,
    estate_surface_manifest: Sequence[dict[str, Any]] | None = None,
) -> None:
    """Recompute the current snapshot contract after a discriminating mutation.

    ``bind_clusters`` defaults to the complete-generation contract. It remains
    optional only so a negative test can construct a deliberately stale digest.
    ``estate_surface_manifest`` lets a test bind the same generation to an
    intentionally different, already-bootstrapped capability surface.
    """

    lexical_profile = manifest["lexical_profile"]
    embedding_profile = manifest["embedding_profile"]
    clusters = manifest["clusters"]
    cards = manifest["cards"]
    relations = manifest["relations"]
    vectors = manifest["vectors"]
    snapshot = manifest["snapshot"]
    snapshot["estate_digest"] = sha256_text(
        canonical_json(
            list(estate_surface_manifest)
            if estate_surface_manifest is not None
            else _estate_surface_manifest(cards)
        )
    )
    snapshot["source_digest"] = sha256_text(
        canonical_json(
            sorted(
                {
                    (record["source_id"], record["source_digest"])
                    for record in [*clusters, *cards, *relations]
                }
            )
        )
    )
    snapshot["card_digest"] = sha256_text(
        canonical_json(sorted(card["card_digest"] for card in cards))
    )
    snapshot["profile_digest"] = sha256_text(
        canonical_json(
            [lexical_profile["profile_digest"], embedding_profile["profile_digest"]]
        )
    )
    snapshot["expected_card_count"] = len(cards)
    snapshot["expected_relation_count"] = len(relations)
    snapshot["expected_vector_count"] = len(vectors)
    snapshot_material = {
        key: value
        for key, value in snapshot.items()
        if key
        not in {
            "snapshot_digest",
            "expected_card_count",
            "expected_relation_count",
            "expected_vector_count",
        }
    }
    snapshot_material.update(
        {
            "cards": sorted(
                (card["capability_card_id"], card["card_digest"])
                for card in cards
            ),
            "relations": sorted(
                (relation["capability_relation_id"], relation["relation_digest"])
                for relation in relations
            ),
            "vectors": sorted(
                (vector["capability_card_view_id"], vector["vector_digest"])
                for vector in vectors
            ),
        }
    )
    if bind_clusters:
        snapshot_material["clusters"] = sorted(
            (cluster["cluster_id"], cluster["cluster_digest"])
            for cluster in clusters
        )
    snapshot["snapshot_digest"] = sha256_text(canonical_json(snapshot_material))


def member_by_handle(field: dict[str, Any], handle: str) -> dict[str, Any]:
    return next(member for member in field["members"] if member["handle"] == handle)


def handles(field: dict[str, Any]) -> set[str]:
    return {member["handle"] for member in field["members"]}


def without_visibility(members: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in member.items() if key != "visibility_token"}
        for member in members
    ]
