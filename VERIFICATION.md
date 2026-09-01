# Verification

MIND `2.1.7` is built from committed tracked source by `scripts/build_release.py` and checked by `scripts/verify_release.py`.

The release builder:

- validates the plugin and Core version graph;
- rejects bundled MCP registration and the removed MCP runtime paths;
- selects customer files through a positive allowlist;
- builds the Core wheel twice under a fixed source date and requires byte identity;
- writes an exact release manifest, component checksums, archive checksum, and build receipt;
- safely extracts the resulting ZIP;
- compares the staged and extracted trees byte-for-byte;
- runs the offline customer release verifier against both trees.

The permanent GitHub verification workflow runs the repository tests and deterministic release builder on Linux, Windows, and macOS for each pull request and each push to `main`. The separate line-ending workflow runs only once per pull request and once after merge; ordinary branch pushes do not duplicate it.

## Current public release

- Product: **MIND by Collaborative Dynamics 2.1.7**
- Core: **0.2.0**
- Included TestForge roles: **1.1.6**
- Public release tag: **v2.1.7**
- Archive: `augment-of-mind-v2.1.7.zip`
- Archive SHA-256: recorded in `augment-of-mind-v2.1.7.zip.sha256`, the build receipt, and the GitHub release asset metadata
- Source file count: `306`
- Source-material SHA-256: `88c4e7ab6ca0ee7597d07c75915e1fd45eb03989fc3b3fef3d2fd7617a827771`
- Staged/extracted tree SHA-256: `336169c9802a52d5753d8b5add4530c11de620237f40b1a5748da1e3ca671a4f`
- Core wheel SHA-256: `0f9d1d2787a161bfd58113e735cacbbdcdb11844e2072c9f206c36cbda9fb779`

## Evidence boundary

The repository suite contains 20 deterministic tests. It locks the embedded TestForge operator and reviewer tree digests to the copies taken from published TestForge `v1.1.6` commit `93120abaa39c26a6f0ec494bdff0c7e6f92344cf`, including the metered-capacity authority boundary. The build independently proves repeatable wheel and archive bytes, positive-allowlist packaging, staged/extracted parity, offline verification, and package cleanliness.

The GitHub release carries the ZIP, checksum, and build receipt. Release assets are compared with the local deterministic build after publication.

This establishes source custody and deterministic package integrity. Installation, Codex discovery, hook trust, Ollama reachability, reminder delivery, semantic retrieval quality, and model use remain separate runtime claims.
