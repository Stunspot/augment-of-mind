# Verification report

## Decision

**Status:** READY_WITH_RESIDUAL_RISK
**Target:** MIND Phase 2 associative disclosure plus Exoframe cooperative delivery seam
**Revision:** mind-base:86583ec8c3b9ac71ee0d2106db30fce59020a2d9+exoframe-base:e4bdb2ca91ca007aeee03498f8035c5e6447609c+phase2-sha256:4028d8399bff4444208415a94d1c4c063ecb5afcbab9c2fb6b48a4dc35340a58
**Reviewer:** REVIEW_PASS

### Basis

- Implementation, captured execution evidence, cross-repository contract vector, manifest, traceability, and exact target snapshot are complete for the bounded local development packet.
- Independent target-fidelity re-review recomputed all 29 staged Git blobs to aggregate SHA-256 4028d8399bff4444208415a94d1c4c063ecb5afcbab9c2fb6b48a4dc35340a58 and passed without a decision-changing finding.

## Scope

### Included

- persona-neutral MIND capability cards, semantic views, clusters, relations, profiles, immutable complete index generations, and scoped query capabilities
- exact cosine-radius union, exhaustive lexical membership, one-hop bridges, false-friend boundaries, and canonical or compact membership-conserving rendering
- privacy filtering, generation replay, activation ordering, currentness, field-bound card expansion, and query-only H0 service behavior
- portable MIND delivery-envelope integrity
- Exoframe validated transient developer-context construction before adapter dispatch, exact renderer preservation, and safe-mode denial before state mutation
- regression behavior in the two repository source trees

### Excluded

- live Codex Desktop event interception or dynamic pre-turn context-provider integration
- observed event ingestion, live embedding generation, authenticated provider dispatch, provider receipt, and complete H1 correlation
- utility ranking, top-K recommendation, automatic tool activation, action authorization, or result interception
- real corpus ingestion, owner-store migration, people data, continuity data, or Obsidian integration
- embedding-model qualification on this host
- wheel construction, fresh-host installation, release, push, publication, and public-distribution readiness
- the pre-existing untracked release-v0.2.0 directory

## Critical invariants

- I-PRIVACY-FIRST: Visibility filtering precedes comparison, currentness, errors, counts, and diagnostics on every query and expansion route.
- I-GLOBAL-GENERATION: Every activation strictly advances one complete global successor generation across embedding profiles and commits atomically.
- I-REMINDER-NOT-RANKING: Membership is an unordered union of exact-radius, exhaustive lexical, and explicit one-hop association paths; no utility score, top-K, fusion rank, recommendation, or action authority is emitted.
- I-MEMBERSHIP-CONSERVATION: Canonical and compact forms carry every same handle and bind one membership-manifest digest.
- I-DELIVERY-BINDING: One portable envelope binds exact field bytes, field, snapshot, scoped estate, membership, mode, and representation.
- I-TRANSIENT-HOST: A validated field is appended exactly once after transcript loading, before rendering and dispatch, and is absent from persistent messages, turns, events, and later continuations.
- I-EVIDENCE-CEILING: MIND service responses remain H0 and local adapter capture is described only as pre-sampling construction, not live H1.

## Risk register

| ID | Severity | Disposition | Risk |
|---|---|---|---|
| R-001 | critical | covered | Private capability existence leaks through comparison, diagnostics, counts, stale status, or card expansion. |
| R-002 | critical | covered | An alternate profile, equal or backdated activation, stale revision, replay, or concurrent writer forks or partially mutates the global generation. |
| R-003 | high | covered | Ranking-shaped retrieval, boundary instability, or row-order dependence changes reminder membership or hides relevant handles. |
| R-004 | high | covered | Canonical and compact forms, expansion tokens, or the delivery envelope accept mismatched membership or altered bytes. |
| R-005 | critical | covered | Exoframe persists, duplicates, resurrects, or safe-mode-mutates around transient reminder material. |
| R-006 | high | covered | Development evidence is generalized into an automatic H1, provider, fresh-host, package, or release claim. |
| R-007 | medium | covered | A sandbox-only Windows Credential Manager failure is misclassified as a product regression or silently ignored. |

## Execution evidence

| ID | Status | Exit | Command | Raw evidence |
|---|---|---:|---|---|
| E-001 | passed | 0 | `python -B -X utf8 -m unittest discover -s tests -v` | artifacts/testforge/phase2/E-001-mind-full-unittest.json |
| E-002 | failed | 1 | `python-3.12-venv -B -X utf8 -m pytest -p no:cacheprovider -q` | artifacts/testforge/phase2/E-002-exoframe-full-pytest.json |
| E-003 | passed | 0 | `python-3.12-venv -B -X utf8 -m pytest -p no:cacheprovider -q --junitxml=E-003.xml two exact Credential Manager node IDs` | artifacts/testforge/phase2/E-003-exoframe-windows-vault-host.json |
| E-004 | passed | 0 | `python-3.12-venv -B -X utf8 -m pytest -p no:cacheprovider -q --junitxml=E-004.xml --deselect=two exact Credential Manager node IDs` | artifacts/testforge/phase2/E-004-exoframe-hermetic-pytest.json |
| E-005 | passed | 0 | `powershell.exe -NoProfile -NonInteractive -Command compare exact fixture lengths and SHA-256 values` | artifacts/testforge/phase2/E-005-contract-vector-byte-identity.json |

## Findings

- F-001 [PRODUCT_DEFECT/critical]: Earlier activation logic allowed profile-local or partial successor generations to bypass a globally complete capability baseline. — resolved
- F-002 [ENVIRONMENT_LIMITATION/medium]: The sandboxed Exoframe test process had no usable Windows Credential Manager logon session and returned Win32 error 1312. — resolved
- F-003 [TOOLING_LIMITATION/low]: TestForge's heuristic smell scanner treats the domain word snapshot as a snapshot-assertion smell and emits 112 low-severity false positives. — open
- F-004 [TOOLING_LIMITATION/low]: Command-record normalization preserves exit status but does not parse unittest or pytest output into per-case counts. — open
- F-005 [TEST_DEFECT/medium]: The first portable contract vector captured a field ID derived from a randomly issued session capability, so the supposedly stable vector changed on every construction. — resolved

## Residual risk

- RR-001: No live H1 event-ingest, same-turn compilation, authenticated provider delivery, correlation, or receipt chain has been observed. — Keep MIND at H0 and Exoframe at local pre-sampling construction until a separately authorized live acceptance.
- RR-002: No production embedding model or calibrated profile was qualified on this host. — Use explicit lexical degradation or qualify an immutable embedding profile before vector-backed runtime use.
- RR-003: Wheel construction, fresh-host installation, and public distribution remain unexecuted. — Run separate packaging, fresh-host, documentation, and release gates before distribution.
- RR-004: TestForge smell and command-record normalization heuristics produced known low-severity evidence noise. — Preserve the raw receipts and keep the tooling fixes in a separate bounded TestForge change.

## Authority still required

- None recorded
