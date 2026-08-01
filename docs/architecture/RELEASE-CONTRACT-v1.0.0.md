# MIND 1.0.0 release contract

Status: accepted release boundary for the standalone public repository.

## Customer object

The release is one installable, skills-only Codex plugin named
`augment-of-mind`, version `1.0.0`. It contains the MIND integrator and fifteen
Faculty skills. Nova is not included or required.

The same archive contains `cd-mind-core` version `0.2.0` as an optional Python
wheel. Core is a persona-neutral metadata and associative-reminder runtime. Its
version does not renumber the plugin, and installing the plugin does not
silently install or start Core.

## Archive

- filename: `augment-of-mind-v1.0.0.zip`
- single top-level directory: `augment-of-mind-v1.0.0/`
- plugin entry point: `.codex-plugin/plugin.json`
- marketplace entry point: `.agents/plugins/marketplace.json`
- optional runtime: `optional-core/cd_mind_core-0.2.0-py3-none-any.whl`
- exact contents: `RELEASE-MANIFEST.json`
- customer verifier: `verify-release.py`

The archive is constructed from an explicit positive allowlist. It excludes
Git history, tests, development evidence, architecture work packets, source
checkout paths, caches, databases, and the unrelated local
`release-v0.2.0/` directory.

## Host claims

- Codex plugin package structure and local marketplace installation are tested
  separately from skill selection and behavior.
- Codex remains cooperative H0 for MIND Core. No automatic pre-turn reminder
  field is claimed.
- The optional Core wheel may answer explicit H0 queries when a caller supplies
  the required metadata, index, session capability, and anchors.
- A generic harness may integrate the portable delivery envelope, but H1 is
  earned only by an observed event-ingest, compilation, correlation, and
  pre-sampling delivery chain.
- Exoframe has a separately tested transient delivery seam. That source is not
  bundled into this public archive.
- No Claude-specific or public-directory distribution is claimed by this
  release.

## Publication gate

The release may be tagged and published only after:

1. the customer documentation journey passes Hesperos authorship and an
   independent accessibility review;
2. the square icon, 16:9 hero, and 4:5 capability card are inspected at their
   original dimensions and used on Pages;
3. the plugin validates and a clean host installs and discovers it;
4. the optional wheel rebuilds deterministically, installs offline, and passes
   `init` and `status` smoke tests;
5. the archive verifier, extracted-tree comparison, link/privacy audit, and
   final TestForge release gate pass;
6. GitHub `main`, Pages, tag, release, asset bytes, and live customer links are
   read back from their authoritative surfaces.
