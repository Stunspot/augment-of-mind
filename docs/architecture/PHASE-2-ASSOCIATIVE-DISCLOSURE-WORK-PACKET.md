# MIND Core Phase 2 — Associative Disclosure work packet

Status: implementation complete on `codex/mind-associative-disclosure`; verification evidence is recorded under `artifacts/testforge/phase2/`; not packaged or released.

## Outcome

Phase 2 gives MIND a persona-neutral associative reminder field. A host supplies distinct ephemeral semantic anchors. Core returns every visible capability handle inside the configured vector radius, every approved lexical match, and explicit one-hop bridges or false-friend boundaries. The returned field reminds the model what is nearby; it does not score utility, recommend an action, select a capability, or claim automatic delivery.

This packet corrects the earlier ranking-shaped Phase 2 proposal. Package hierarchy remains a custody and expansion mechanism. Vector geometry supplies the complementary discovery mechanism.

## Authority and source custody

Sam authorized this leg with `Proceed` on 2026-07-31 and clarified that the prior leg's **process**—audit, architecture, bounded work packet, implementation, root-cause-first debugging, TestForge, independent review, reproducible evidence, and local commit—should be repeated.

The implementation is bound to these local authorities as observed after the associative-disclosure correction:

| Authority | SHA-256 |
|---|---|
| Associative Disclosure ADR | `E1398C29B9B48671C90ECD763CEF3B425314ED925BD1E94583D9D449E67E7E46` |
| Foundational architecture design | `A822E655187EDB58964367DCAA049F278FC57F9A50EDC4E83FA06656E0DC7034` |
| Normative architecture contracts | `0CFA61D07E852E9BCAACA8FF90C6D352A06A8B65B77A45936BF4AB0C0C2F3F2D` |
| Phase 1 implementation base | Git commit `86583ec8c3b9ac71ee0d2106db30fce59020a2d9` |

The old `nova_control_plane.py` remains design evidence only. Its embedding transport and vector encoding may inform the work; its reciprocal-rank fusion, top-K recall, global score, collapsed capability status, Nova-specific monolith, action gate, and capsule behavior are not imported.

## Product and host boundary

- MIND Core owns capability identity, authored cards, derived indexes, exact neighborhood membership, field manifests, and deterministic field representations.
- Host adapters own turn observation, ephemeral anchor formation, embedding calls, pre-sampling attachment, context budgeting, and delivery receipts.
- Nova is one consuming persona composition. The Core and protocol do not require or infer Nova.
- Codex Desktop remains cooperative H0 because no verified dynamic pre-turn context-provider hook is exposed. A Core/CLI query is useful but begins after reasoning has already started.
- Exoframe exposes the owned pre-sampling seam used by the delivery portion of H1: after transcript resolution, before context rendering and provider dispatch. A rendered-payload capture proves that local construction boundary only. Full H1 additionally requires durable event ingest, field compilation, turn correlation, and pre-turn delivery evidence.
- TestForge is an independent verifier, not a runtime dependency.

## Phase 2 implementation boundary

### In scope

- one checksum-bound `0002_associative_disclosure.sql` migration in the existing Core database;
- immutable capability-card revisions and independently embeddable semantic views;
- meaningful associative clusters and typed relations;
- named embedding profiles with fixed dimensions, cosine-distance semantics, and calibrated radii;
- versioned exhaustive lexical-membership profiles;
- immutable derived-index snapshots and append-only activation records;
- vectors and FTS rows as rebuildable projections in the same SQLite database;
- exact exhaustive cosine-distance membership through a replaceable adapter;
- distinct multi-anchor neighborhoods joined by set union;
- lexical-only labelled degradation;
- one-hop `bridges_to`, `complements`, `requires`, and `false_friend_of` paths;
- exact agent-private filtering before vector, lexical, relation, count, and error production;
- opaque expiring session capabilities that derive private query scope server-side;
- independent lifecycle annotations without an `active` state;
- deterministic canonical and compact renderings with one shared membership digest;
- administrative index-manifest ingestion;
- query-only `reminder.neighborhood` and `reminder.card` service methods;
- field-bound visibility tokens for progressive card expansion;
- a copy-ready CLI query route for cooperative H0 use;
- a portable delivery contract and a capture-based pre-sampling loopback proof;
- a narrow Exoframe adapter after the portable boundary is verified.

### Out of scope

- a full capability-estate inventory or migration;
- inference from filenames or package paths;
- raw `SKILL.md` or owner-corpus ingestion;
- raw prompt, transcript, correction, or error-text persistence;
- a universal capability-fitness scalar;
- RRF, top-K truncation, ranked suggestions, recommendation state, or action authorization;
- automatic capability selection or activation;
- silent embedding-model substitution or model installation;
- mutation of global Codex instructions or installed plugin caches;
- People, Dunbar, continuity, Obsidian, or private data migration;
- release, push, marketplace update, or publication.

## Schema

`0002_associative_disclosure.sql` adds:

- capability-level `public_safe` or exact-agent-private exposure bindings, inherited exactly by every card revision;
- `capability_cards` — immutable card revisions, compact projections, boundaries, cluster identity, exposure policy, source/card digests, and context cost;
- `capability_card_views` — immutable `transformation`, `situation`, `positive_cue`, `error_or_correction`, `negative_boundary`, and `example` facets;
- `capability_relations` — typed visible edges with source and relation digests;
- `embedding_profiles` — provider/model/dimension/metric/radius/encoding/qualification contracts;
- `lexical_profiles` — normalization, tokenization, and exhaustive cue-membership contracts;
- `associative_index_snapshots` — immutable complete generation identity, source/card/profile digests, and explicit `complete` or `unavailable` vector coverage;
- `associative_view_vectors` — finite fixed-dimension float32 projections bound to one view and snapshot;
- `associative_snapshot_activations` — append-only current-generation transitions;
- `session_query_capabilities` — hashes of opaque expiring capabilities bound to one agent/session/epoch and exposure scope;
- `capability_card_fts` — a derived FTS5 projection over approved compact card views.

Capability and card visibility are either public-safe or bound to one exact agent instance in this phase; the bindings must agree. Shared audiences require a later grant model. A successful host handshake may issue one raw session capability once; Core stores only its digest and derives the agent/session scope from the verified capability on each reminder or estate query. Caller-nominated scope IDs are not accepted by these methods. Private handles and metadata therefore cannot be recovered by guessing another agent or session identifier.

Snapshots and activations are immutable. Each activation strictly advances one globally ordered generation clock and is one complete successor generation, not a partial patch: it carries exactly one card revision for every capability in the immediately prior globally activated generation, including when opening a new embedding-profile chain. Phase 2 admits additions and revisions but does not encode removal; a later phase must add an explicit hash-bound removal manifest before omission can be replayable. A build validates all rows before the activation record enters the same transaction. Querying an inactive or source-mismatched generation returns stale/unavailable rather than laundering it into current association.

## Index manifest

Administrative ingestion accepts exactly `mind-associative-index/v1` with:

- one profile;
- one complete snapshot identity;
- authored cards and facet views tied to existing capability/source identities;
- typed relations whose endpoints are in the visible capability estate;
- an explicit vector-coverage state: `complete` requires one finite, non-zero, exact-dimension vector per indexed view; `unavailable` requires none and permits lexical-only operation;
- declared expected row counts and content digests;
- builder identity and evidence boundary.

The operation is transactional and idempotent for exact replay. A reused stable ID with changed bytes fails as a conflict. The stdio query service exposes no indexing mutation.

## Query contract

`reminder.neighborhood` requires:

- one opaque unexpired session capability bound server-side to the current agent/session/epoch and exposure scope;
- active `snapshot_id`;
- one or more bounded anchors with stable query-local IDs and kinds;
- an optional finite vector of the profile's exact dimensions;
- optional bounded lexical hints.

The anchors remain separate. For each anchor, Core forms its complete scoped radius neighborhood and lexical set. The final direct set is their union. One visible relation hop may then add a bridge, complement, requirement, or boundary member.

Lexical membership is exhaustive under `nfkc-casefold-contiguous-token-v1`: NFKC-normalize, case-fold, tokenize with the declared Unicode grammar, and match only a complete contiguous hint-token sequence in a visible handle, alias, or approved view. Every visible match enters the union. FTS5 may accelerate or diagnose enumeration, but BM25, ties, row order, and limits cannot decide membership.

The response contains:

- field, scoped-estate, snapshot, profile, vector-coverage, and membership-manifest identity, with profile qualification explicitly attributed as a builder-reported claim and its evidence reference/digest rather than treated as independently verified;
- `vector_current`, `hybrid_current`, `lexical_degraded`, or `unavailable` mode;
- stable handle records with exact card ID/revision, typed association paths, independent lifecycle observations, and a scoped visibility token;
- explicit false-friend/boundary treatment;
- canonical and compact model-facing fields with the same membership digest;
- a claim boundary stating that association is not utility, recommendation, selection, activation, fitness, health, or authority.

It contains no score, rank, top-K, RRF, utility, recommendation, or action field. Internal distances are verification mechanics and do not enter the model-facing representation.

`reminder.card` requires the same session capability plus field ID, membership-manifest digest, and the member's opaque visibility token. The token authenticates the exact card revision, snapshot, field, agent, and session. Expansion rejects non-members, token mismatch, expired or changed scope, a superseded active snapshot, and revoked visibility. It never resolves a convenient newer card by name and never opens raw package or owner-corpus material.

Queries are side-effect free. Raw anchors and rendered field bodies are not written to SQLite. Field IDs and manifests are deterministic in-memory derivatives of snapshot, scope-safe membership, and anchor hashes.

## Field rendering

The canonical field begins:

```text
MIND · ARM'S REACH
Notice the nearby handles; treat proximity as memory, not verdict. Open only the transformation the work actually needs.
```

The canonical representation names every member with its compact projection, association paths, lifecycle summary, and boundary. The compact representation groups the same handle IDs under meaningful associative clusters and elides descriptions, not members. Both bind the same membership-manifest digest.

No runtime path silently truncates membership. If neither representation fits a host's measured budget, delivery stops at `BUDGET_UNSATISFIED`.

## Distance backend and embedding provider

The portable reference adapter first converts stored and query vectors to little-endian float32, rejects non-finite and zero-norm inputs, and computes the dot product and squared norms in stable dimension order with `math.fsum` before float64 division. Distance is `1 - clamp(cosine, -1, 1)`. Membership is `distance <= radius + comparison_tolerance`, with both values fixed by the immutable profile. This is the behavioral oracle and requires no extension. A pinned `sqlite-vec` scalar-distance adapter may later accelerate a widened first pass, but every tolerance-band item is decided by the reference. Qualification includes `nextafter`-adjacent boundary values. A top-K KNN API cannot substitute for the range oracle. An `unavailable` snapshot rejects vector-bearing queries and can answer only labelled lexical fields.

Embedding generation remains a host/index-builder concern. Ollama's `/api/embed` route and `qwen3-embedding:0.6b` are the first intended local qualification profile, but that model was not installed at work-packet time. The implementation will not pull it or substitute another model silently. Deterministic fixed vectors establish geometry and protocol behavior; semantic quality remains a separately named qualification state.

## Root-cause-first failure loop

Every failing check is handled in this order:

1. preserve the full error and reached boundary;
2. classify it as product defect, test defect, environment failure, nondeterminism, expected contract change, tooling failure, or insufficient evidence;
3. identify why the failure happened and why that cause existed;
4. form one discriminating hypothesis;
5. change one hypothesis-bearing thing;
6. rerun the narrow check;
7. keep or revert from evidence before moving to the next failure.

An absent extension, embedding model, build backend, or host hook is an environment or capability fact. It is not repaired by a baroque substitute and is never misreported as product behavior.

## Acceptance probes

The deterministic suite uses several synthetic capability fields rather than canonizing one illustrative user example.

1. exact cosine-radius inclusion and exclusion at the boundary;
2. row-order and equal-distance enumeration invariance;
3. cross-taxonomy union from separate anchors;
4. correction/error/phase anchor addition without task-neighborhood erasure;
5. explicit bridge versus direct-vector provenance;
6. false-friend and negative-boundary presentation precedence, including collision with a direct positive match;
7. independent lifecycle truth for a nearby canonical-only capability;
8. agent-private non-disclosure through vector, FTS, relation, counts, errors, diagnostics, guessed scope IDs, and another agent's session capability;
9. lexical-only degradation with no semantic claim;
10. source/card revision invalidation of an old snapshot;
11. malformed, non-finite, zero, and wrong-dimension vector rejection;
12. exact idempotent replay and conflicting stable-ID rejection;
13. no raw-anchor or rendered-field persistence after query;
14. canonical/compact membership conservation;
15. field-bound card expansion accepts an exact current member and rejects non-members, stale snapshots, altered tokens, scope changes, and newer-by-name substitutions;
16. query responses and field text contain no forbidden recommendation vocabulary or fields;
17. H0 evidence stops at query/offered;
18. loopback capture observes the field in the rendered payload before adapter dispatch and reports only pre-sampling construction, not H1;
19. baseline Phase 1 identity, lifecycle, mount, receipt, isolation, and migration invariants remain green.
20. one producer-generated portable envelope vector is regenerated by MIND, consumed unchanged by Exoframe, and byte-bound across both repositories.

## Evidence and completion gate

The leg completes only when:

- narrow and full repository checks pass with raw reproducible output;
- the TestForge manifest and traceability validate;
- failure classifications and fixes are preserved;
- an independent verification reviewer either passes or names visible residual risk;
- a target snapshot excludes the pre-existing untracked `release-v0.2.0/` directory;
- the exact diff is locally committed;
- Codex is described as H0; an Exoframe rendered-payload proof is not called H1 until the complete event-ingest, compilation, correlation, and delivery chain exists;
- no push, release, installation, or publication occurs.
