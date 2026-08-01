# Maintainer guide

## Release identities

- Plugin: `augment-of-mind` `1.0.0` in `.codex-plugin/plugin.json`.
- Optional Python component: `cd-mind-core` `0.2.0` in `pyproject.toml`.
- Customer archive: `augment-of-mind-v1.0.0.zip` with one same-named root.

Change these independently and document their relationship. Do not bump the
plugin merely to invalidate a local cache; use the supported cachebuster flow
during local development.

## Canonical sources

- plugin and Faculties: `.codex-plugin/` and `skills/`;
- Core: `mind_core/`, migrations, and `pyproject.toml`;
- customer documentation: the files declared in
  `documentation-manifest.json`;
- Pages: `docs/index.html`, `docs/style.css`, and `docs/assets/`;
- customer artwork: `assets/` with matching Pages copies;
- release policy: `docs/architecture/RELEASE-CONTRACT-v1.0.0.md`;
- verification evidence: `artifacts/testforge/` and `verification/`.

## Required release cycle

1. Reconcile versions, claims, links, rights, and visual dimensions.
2. Run the full Hesperos authoring, accessibility lint, and independent review.
3. Run plugin validation and representative behavioral evaluation.
4. Use a qualified Python 3.11+ environment with setuptools `69.2` or newer.
   Build the wheel twice with a fixed source date and require identical bytes.
5. Build the allowlisted archive twice from the same selected source bytes,
   require identical ZIP bytes, extract it cleanly, verify its manifest, and
   compare trees.
6. Perform fresh-host plugin install/discovery/behavior and offline Core
   install/`init`/`status` checks.
7. Run final TestForge over the exact release candidate.
8. Publish only the reviewed bytes; then read back `main`, Pages, tag, release,
   assets, links, images, and first-success behavior.

## Documentation change triggers

Review the customer set whenever a version, install command, host surface,
Faculty promise, Core schema or command, data behavior, permission boundary,
support route, legal link, or release asset changes. Record untested surfaces
as limits rather than laundering a file diff into behavior evidence.
