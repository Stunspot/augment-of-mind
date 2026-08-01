# Verification report

## Decision

**Status:** READY_WITH_RESIDUAL_RISK
**Target:** MIND Core Phase 1 read-only truth substrate
**Revision:** base:b23e866789bd9554fc848cef4d090ec18b123cb0+phase1-sha256:41d0d9550b2cd1d5dbcfb6c9b4336fba51df6f7d15019dcc13fadb2bf26a0116
**Reviewer:** REVIEW_PASS_WITH_CONDITIONS

### Basis

- The captured 34-test suite passed in the declared Windows/Python/SQLite environment.
- All critical and high risks have covered scenarios, executable tests, and captured passing evidence.
- TestForge manifest and traceability validation passed without warnings.
- The independent reviewer returned REVIEW_PASS_WITH_CONDITIONS after reproducing the prior blocker and re-testing the corrected revision.
- The reviewed source tree is bound to the reproducible target snapshot receipt.
- The remaining blocked package-build check is medium severity and explicitly outside this source/runtime development-packet claim.

## Scope

### Included

- persona-neutral Core bootstrap and status
- SQLite schema, migration checksum, startup integrity, restart persistence, and writer lease
- agent-instance and host-session identity and freshness
- capability/provider/distribution/lifecycle metadata
- mount registration, grant, availability, and freshness metadata
- receipt idempotency, scope, ancestry, and append-only behavior
- bounded query-only H0 stdio framing and method dispatch

### Excluded

- plugin prompt or Faculty behavior changes
- live host H1, H2, or H3 integration
- automatic capability recruitment or activation
- owner-store reads, writes, or legacy data migration
- embeddings, vectors, corpus content, people records, and continuity records
- capsule transfer, Obsidian integration, external Mnemosyne integration, and TestForge runtime dependency
- release, publication, merge, and fresh-host qualification

## Critical invariants

- I-SCOPE: Mutable operational facts and their evidence remain inside one exact agent/session scope.
- I-NO-ACTIVE: Capability identity, provider, distribution, lifecycle, invocation, fitness, and health remain distinct; no active bit is derived.
- I-RECEIPT: Receipts and receipt edges are append-only, scope-compatible, acyclic, idempotent within scope, and bound to the exact typed record they evidence.
- I-FRESHNESS: A child observation cannot outlive its host session, and an expired session makes its dependent facts stale.
- I-WRITER: Exactly one process owns the Core writer lease for a database at a time.
- I-H0: Phase 1 records metadata and answers queries without claiming automatic delivery, activation, interception, or dispatch control.
- I-EMPTY: AUTHORITATIVE_EMPTY requires a successful authoritative read through an open, valid owner runtime.

## Risk register

| ID | Severity | Disposition | Risk |
|---|---|---|---|
| R-001 | critical | covered | When scoped records cite or expose another agent's receipts, authority and operational truth can leak across agents. |
| R-002 | high | covered | When names or global lifecycle facts collapse providers and operational axes, a caller can infer a capability is active without evidence. |
| R-003 | critical | covered | When receipts replay, mutate, form cross-scope ancestry, or evidence an unrelated same-scope record, evidence can duplicate, diverge, disclose provenance, or support false operational truth. |
| R-004 | high | covered | When child facts outlive their host session, expired catalog, permission, authentication, and health claims can appear current. |
| R-005 | critical | covered | When migration integrity or writer exclusion fails, the sole Core metadata authority can corrupt or fork. |
| R-006 | high | covered | When framed input is ambiguous or query dispatch is open-ended, malformed data or a mutation route can cross the H0 boundary. |
| R-007 | high | covered | When availability enum membership is accepted without semantic guards, an unreadable owner store can be reported as authoritatively empty. |
| R-008 | high | covered | When Core boot requires Nova or optional providers, MIND ceases to be a persona-neutral portable base. |
| R-009 | medium | blocked | When the declared build backend is unavailable, source behavior may be verified while the distributable package remains unproved. |

## Execution evidence

| ID | Status | Exit | Command | Raw evidence |
|---|---|---:|---|---|
| E-001 | passed | 0 | `python -B -X utf8 -m unittest discover -s tests -v` | artifacts/testforge/unittest-execution.json |
| E-002 | failed | 1 | `python -B -X utf8 -c import setuptools; print(setuptools.__version__)` | artifacts/testforge/build-backend-probe.json |

## Findings

- F-001 [PRODUCT_DEFECT/high]: Initial receipt consumers checked evidence existence but not scope compatibility, permitting cross-agent provenance. — resolved
- F-002 [PRODUCT_DEFECT/high]: Initial repeat handshakes regenerated immutable agent creation time and rejected every later session for the same agent. — resolved
- F-003 [TEST_DEFECT/low]: The first EGDOD oracle matched forbidden words inside an explicit non-claim boundary instead of inspecting typed lifecycle states. — resolved
- F-004 [TOOLING_FAILURE/informational]: The heuristic smell scan flagged the identifier catalog_snapshot as a snapshot assertion in helper data and a freshness assertion. — resolved
- F-005 [PRODUCT_DEFECT/high]: The first reviewed revision enforced receipt scope but allowed an unrelated same-scope receipt to evidence lifecycle and mount truth. — resolved
- F-006 [PRODUCT_DEFECT/low]: The first reviewed revision treated a short read from a complete BinaryIO frame as truncation. — resolved
- F-007 [ENVIRONMENT_FAILURE/medium]: The local Python environment lacks setuptools, so a PEP 517 wheel build was not executed. — blocked
- F-008 [TOOLING_FAILURE/high]: The first recorded aggregate target digest omitted its path set and byte-framing contract; the first repair then hashed checkout-dependent working-tree bytes instead of canonical Git blobs. — resolved

## Residual risk

- RR-001: Python 3.11-3.13 and POSIX locking paths were not executed. — Run the same suite in a cross-platform Python version matrix before package release or fresh-host qualification.
- RR-002: No live host adapter proved H1, H2, or H3 event coverage. — Keep every Phase 1 API and document capped at H0; require later host-specific conformance packets.
- RR-003: Schema v1 has no predecessor migration or rollback path to exercise against representative legacy Core data. — Treat v1 as fresh bootstrap only; require forward, coexistence, and recovery tests before schema v2 or legacy import.
- RR-004: The source/runtime packet is exercised, but its PEP 517 wheel is not built in the current environment. — Keep package build and release out of the present readiness claim; execute the build in a provisioned isolated environment later.

## Authority still required

- Provision and run the declared build backend before package-build or fresh-host qualification
- Sam retains merge, release, publication, and later-phase authority
