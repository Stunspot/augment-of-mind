# Verification

MIND `2.1.1` is built from committed tracked source by `scripts/build_release.py` and checked by `scripts/verify_release.py`.

The release builder:

- validates the plugin and Core version graph;
- rejects bundled MCP registration and the removed MCP runtime paths;
- selects customer files through a positive allowlist;
- builds the Core wheel twice under a fixed source date and requires byte identity;
- writes an exact release manifest, component checksums, archive checksum, and build receipt;
- safely extracts the resulting ZIP;
- compares the staged and extracted trees byte-for-byte;
- runs the offline customer release verifier against the extracted archive.

The standalone repository synchronization computed SHA-256 inventories and required exact byte parity with `plugins/augment-of-mind` from the verified flagship repository, excluding only repository-owned GitHub workflows, Pages content, verification record, and line-ending/editor policy files.

## Current public release

- Product: **MIND by Collaborative Dynamics 2.1.1**
- Core: **0.2.0**
- Public release tag: **v2.1.1**
- Archive: `augment-of-mind-v2.1.1.zip`
- Archive SHA-256: `d836c69d3e72866682e263aea03650ba0accdafaf96e4df995d334719d8d9867`
- Source file count: `298`
- Source SHA-256: `65da25f2539c4a7e90ae79ffb854084a6de9345ac0adb65009166bb65901dae5`
- Staged/extracted tree SHA-256: `f00ab317f46336abe3543c9f8561fdcbf6f0c45de2b7bc56412233fa2d686e96`
- Core wheel SHA-256: `a10e88d4c6a85acf6d4c31a46e0ec9454dac5acfe6c95ac5d265d1f8822ecb60`

## Evidence

The final synchronization run passed source parity, deterministic build, extracted-tree comparison, offline release verification, branch publication, and artifact upload.

- Synchronization workflow run: `30967446614`
- Synchronization job: `92183133601`
- Publication workflow run: `30967675155`
- Publication job: `92185068716`

The publication job rebuilt and verified the archive from synchronized `main`, published the ZIP, checksum, and build receipt to GitHub Release `v2.1.1`, and uploaded the same evidence as an Actions artifact.

This establishes source parity and deterministic package integrity. Host discovery, hook trust, reminder delivery, and model use remain separate runtime claims.

## Post-publication cleanup

After synchronization, verification, and publication completed, the version-specific sync-and-release workflow was removed from `main`. The run and job identifiers above preserve the authoritative evidence without leaving a served one-release trigger active in the public repository.
