# MIND Core Phase 1 work packet

Status: implemented on a development branch; locally verified; not released.

This packet implements the first authorized slice of the accepted foundational architecture: a persona-neutral, local MIND Core truth substrate. It records capability identity, independent lifecycle observations, host/session metadata, mount metadata, and append-only evidence receipts. Its service surface is query-only and its strongest host claim is H0.

## Authorization and source custody

Sam authorized the first implementation packet with `Begin` on 2026-07-31. The implementation is bound to these accepted local authorities, whose SHA-256 digests were re-observed before this packet was documented:

| Authority | SHA-256 |
|---|---|
| Foundational architecture design | `A405A302F6B562CD3C53BC03876DFE8E43C9B3B84F520BF5F20AA02CA0D1AFFC` |
| Normative architecture contracts | `DC9E15B154797C7FC2E80149595FB3B69352F01019FE612A13A2F307C4A011B4` |
| Architecture case | `7CA21DAC6FEBF0C2050AC65E629C9EED13CDC05BA0F0368B9FC68BF51119F1FB` |
| Evidence index | `83841E4C7E9B9605D151D93F69EA7A9ECEE4ADC47D54978C13D777B129AFE450` |

The earlier `nova_control_plane.py`, host-boundary, and capsule/vector prototypes were inspected as design evidence but were not imported into this package. Their task-scoped, Nova-specific, and later-phase behaviors would violate the Phase 1 boundary.

## Implemented boundary

- One Core-owned SQLite metadata database with WAL, foreign keys, checksum-bound migrations, startup integrity checks, and a process writer lease.
- Explicit agent-instance and host-session identity. Persona and profile are optional, never inferred, and immutable within an agent instance.
- Host handshakes with exact protocol version, session epoch, adapter declaration, expiring catalog/authentication/permission observations, and H0 evidence capping.
- Capability, product, provider, source, distribution, alias, and entrypoint identities without name-based provider collapse.
- Independent custody, distribution, host-presence, runtime-use, fitness, and governance observations. No derived `active` state exists.
- Federated mount descriptors, grants, and availability observations without opening or absorbing owner stores.
- Append-only, redacted receipt envelopes and provenance edges with idempotency and scope enforcement.
- A length-prefixed, bounded UTF-8 query service with explicit protocol, schema, scope, and H0 claim metadata.
- An explicit local administrative CLI for schema initialization and idempotent metadata bootstrap.

## Enforced invariants

1. Global lifecycle facts are limited to custody, distribution, and governance. Host presence, runtime use, and fitness require one exact agent/session scope.
2. A scoped receipt cannot be read from another agent/session. Scoped idempotency keys are isolated by that same scope.
3. Every lifecycle observation, mount grant, and mount observation requires a receipt bound to its exact receipt type, subject kind, target ID, and SHA-256 of the canonical logical record. The hash excludes only the self-referential `evidence_receipt_id`. A global authority premise may support a scoped binding receipt as a parent; it cannot substitute for that binding receipt.
4. Receipt ancestry may use a global parent or an exact same-scope parent. A global receipt cannot parent scoped evidence, and receipt cycles are rejected.
5. Session-scoped observations cannot predate or outlive their host session. Expired sessions invalidate their catalog, permission, authentication, lifecycle, grant, and mount freshness.
6. A path-visible but runtime-unopenable owner store is `BACKEND_UNAVAILABLE`, not absent, empty, or corrupt.
7. `AUTHORITATIVE_EMPTY` requires an open runtime, valid schema, valid integrity, a successful authoritative owner read, and a bound receipt stronger than `reported`.
8. Adapter-supplied authentication, permission, catalog, and coverage claims remain `reported`. Durable recording does not upgrade the underlying claim.
9. A declared H1-H3 adapter level cannot raise Phase 1 evidence above H0.

## Deliberate exclusions

Phase 1 contains no corpus text, raw prompts, people records, continuity records, embeddings, vectors, semantic retrieval, context compiler, automatic event delivery, automatic capability activation, result interception, action admission, dispatch gate, owner-store read/write path, legacy migration, capsule transfer, Obsidian dependency, TestForge dependency, or external Mnemosyne dependency.

The bootstrap fixture is a public-safe acceptance exemplar, not a live inventory or migration. It represents:

- EGDOD as canonical-constructed and distribution-not-generated, with no installation, invocation, qualification, or health claim;
- the personal MIND `0.2.0` and Build Week MIND `1.0.0` distributions as separate provider records;
- registered and known-unregistered mount metadata without asserting runtime availability.

## Query methods

The stdio surface accepts only:

- `core.status`
- `core.schema`
- `host.session`
- `coverage.get`
- `estate.resolve`
- `estate.capability`
- `mount.catalog`
- `mount.observation`
- `receipt.get`

Requests use a four-byte unsigned big-endian payload length followed by one UTF-8 JSON object. Frames are capped at 1 MiB, tolerate ordinary short reads, reject duplicate keys and non-standard numeric constants, and preserve strict UTF-8. Responses use a JSON-RPC-like envelope and always declare the H0 claim boundary. Mutation-like method names are rejected rather than routed dynamically.

## Local verification receipt

Observed on 2026-07-31 from the repository root:

```text
python -B -X utf8 -m unittest discover -s tests -v
Ran 34 tests in 1.553s
OK
```

The suite covers persona-free boot, optional-provider absence, idempotent bootstrap, EGDOD lifecycle truth, duplicate-provider separation, registered/unregistered mounts, forbidden Phase 1 schema terms, repeat handshakes, immutable persona/profile binding, protocol rejection, H0 evidence capping, cross-agent isolation, same-scope receipt relevance, exact lifecycle/mount/grant receipt binding, global-runtime rejection, stale-session invalidation, availability semantics, reported-only empty-claim rejection, short-read and strict-JSON framing, query-only dispatch, receipt replay/ancestry/immutability, migration checksum tampering, corrupt-database rejection, clean restart persistence, same-process writer exclusion, and cross-process writer exclusion.

This is local implementation evidence, not a release, fresh-host qualification, host integration, or independent verification receipt.
