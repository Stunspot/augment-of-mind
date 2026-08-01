# MIND reminder delivery protocol

`mind-associative-field-delivery/v1` is the portable boundary between MIND Core's associative field compiler and a trusted host's transient pre-sampling context seam.

The envelope carries exactly one already-selected representation:

- `field_id`, `snapshot_id`, and `scoped_estate_digest` bind the compiled scope;
- `membership_manifest_digest` is identical for canonical and compact representations;
- `mode` preserves the vector, hybrid, lexical-degraded, or unavailable evidence boundary;
- `representation` names `canonical` or `compact`;
- `text`, `body_sha256`, and `utf8_bytes` bind the exact model-facing bytes;
- `delivery_digest` binds every preceding envelope field through MIND canonical JSON and SHA-256.

The envelope deliberately omits anchors, vectors, lifecycle evidence, member expansion tokens, raw package content, utility scores, ranks, and action authority. It is transient context, not an instruction to activate any capability. Its hashes prove byte integrity, not MIND origin or provider receipt.

A host validates the whole envelope before attaching `text` as one transient developer message. It preserves the text exactly, appends no wrapper, writes none of it to conversation or event storage, and fails visibly if the selected representation does not fit. Representation selection and context-budget measurement remain host concerns; truncating members is not a valid fallback.

A rendered-payload capture at a local adapter handoff establishes only pre-sampling construction. Full H1 additionally requires observed event ingest, same-turn anchor and field compilation, authenticated correlation, provider delivery evidence, and a hash-only receipt.
