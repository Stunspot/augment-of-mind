# Verification

MIND `2.1.1` is built from committed tracked source by `scripts/build_release.py` and checked by `scripts/verify_release.py`.

The release builder:

- validates the plugin and Core version graph;
- rejects bundled MCP registration and removed MCP runtime paths;
- selects customer files through a positive allowlist;
- builds the Core wheel twice under a fixed source date and requires byte identity;
- writes an exact release manifest, component checksums, archive checksum, and build receipt;
- safely extracts the resulting ZIP;
- compares the staged and extracted trees byte-for-byte;
- runs the offline customer release verifier against the extracted archive.

The standalone repository synchronization also computes SHA-256 inventories and requires exact byte parity with `plugins/augment-of-mind` from the verified flagship repository, excluding only repository-owned GitHub workflows, Pages content, and line-ending/editor policy files.

The final synchronization run passed source parity, deterministic build, extracted-tree comparison, offline release verification, branch publication, and artifact upload. The workflow run was `30967036604`; the successful synchronization job was `92183133601`.

This evidence establishes source parity and deterministic package integrity. Host discovery, hook trust, reminder delivery, and model use remain separate runtime claims.
