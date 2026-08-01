# Package reference

The release ZIP contains one root: `augment-of-mind-v1.0.0/`.

| Path | Purpose |
|---|---|
| `.codex-plugin/plugin.json` | Codex plugin identity and presentation metadata. |
| `.agents/plugins/marketplace.json` | Local or Git-backed marketplace catalog entry. |
| `skills/` | MIND integrator, fifteen Faculties, references, templates, schemas, examples, and runtime helpers. Development evals and nested tests are excluded. |
| `assets/` | Product icon, hero, and capability-card artwork. |
| `optional-core/*.whl` | Offline-installable `cd-mind-core` 0.2.0 wheel. |
| `START-HERE.md` | Reader entry and task routing. |
| `INSTALL-CODEX.md` | Online and offline Codex installation. |
| `OPTIONAL-CORE.md` | Core installation, commands, and removal. |
| `CAPABILITIES-AND-LIMITS.md` | Product promise and boundaries. |
| `DATA-AND-PRIVACY.md` | Data handling and network behavior. |
| `SECURITY.md` | Security boundary and reporting path. |
| `TROUBLESHOOTING.md` | Symptom-first diagnosis and recovery. |
| `SUPPORT.md` | Support and escalation routes. |
| `LICENSE.md`, `NOTICE.md`, `TERMS-OF-USE.md` | Rights, provenance, and terms. |
| `RELEASE-MANIFEST.json` | Exact member paths, sizes, SHA-256 values, and tree digest. |
| `COMPONENT-SHA256SUMS.txt` | Hash for the optional wheel inside the archive. The ZIP's own hash is published in the adjacent `.zip.sha256` sidecar. |
| `verify-release.py` | Offline archive-tree verifier. |

The release is built from a positive allowlist. Development tests, Core source,
Git history, TestForge artifacts, local paths, databases, caches, and
architecture work packets are not customer payload.
