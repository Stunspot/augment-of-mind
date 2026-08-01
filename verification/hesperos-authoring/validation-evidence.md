# Hesperos authoring validation evidence

Candidate documentation fingerprint:
`b7dcf63ef6244b4df4f1ef869f8d7b5fb9a224a5eb667fcf4a651a88d0c903c9`

## Observed checks

| Check | Observed result |
|---|---|
| Hesperos accessible-Markdown linter over all 16 declared Markdown documents | PASS for every file |
| `python -X utf8 scripts/audit_pages.py` | PASS; 22 headings, 29 links, 4 image elements, required visual roles rendered, zero issues |
| True 390 CSS-pixel Chrome CDP regression plus focused original-detail visual review | PASS; 390px document width, three 342px installation cards, 295px scrollable code block, no container clipping; screenshot SHA-256 `34ff8908e590487b1f1a4658db286d064da91829c33c1a9639ae19fbb3325b7a` |
| Full `unittest` discovery under qualified Python 3.12 after the responsive repair | PASS; 83 tests |
| `git diff --check` | PASS; line-ending conversion warnings only |
| UTF-8 mojibake-codepoint scan of customer Markdown and Pages source | PASS; no suspect codepoints found |
| `python -X utf8 -m mind_core init` followed by `status` against a new temporary database | PASS on Windows; same Core instance, schema 2, runtime 0.2.0, H0 mode, SQLite integrity `ok` |

## Root-cause records

The first documentation lint invocation used `--help`, but the linter is a
single-path script without an argument parser and treated that token as a file
name. No product file changed. The command model was corrected before running
the linter once per declared Markdown path.

An initial `git diff --check` found an extra blank line at the end of
`.gitignore`. That exact whitespace defect was removed and the check then
passed.

The in-app browser rejected the local `file://` Pages URL under its URL policy.
That is a browser-admission boundary, not a page failure. No localhost disguise,
alternate browser, or raw browser route was attempted. Rendered, responsive,
keyboard, and link behavior remains pending until the authoritative Pages URL
exists.

The first independent Hesperos review blocked the former fingerprint
`a686dd4cfebd521eb8c13f68d674229c973386928dd56b053823664fb716aa58`.
It found that the Core procedure named macOS and Linux but used Windows-only
console-script paths, and that the offline plugin path made the Python verifier
look mandatory without declaring Python. The repair uses `python -m mind_core`
with explicit Windows and POSIX environment paths, limits release qualification
to the observed Windows run, and separates required archive-hash verification
from the optional stronger Python tree verifier. The candidate was
refingerprinted after those changes; independent rereview is required.

A later release-tooling audit found that `PACKAGE-REFERENCE.md` described the
internal component checksum file as covering both the wheel and the containing
ZIP. An archive cannot contain its own stable digest. The corrected reference
states that `COMPONENT-SHA256SUMS.txt` covers the wheel and that the archive
digest is the adjacent `.zip.sha256` sidecar. It also removes development evals
and nested tests from the customer `skills/` description. The Hesperos-authored
manifest now explicitly scopes itself to guidance and Pages while listing the
separately governed license outside the authorship claim. Independent rereview
passed after those changes.

The staged-byte check then exposed one trailing blank line at EOF in eleven
customer documents. Removing only those blank lines produced the final
fingerprint recorded here. The independent reviewer observed each diff as zero
additions and one blank-line deletion, repeated the static checks, and returned
REVIEW_PASS for this exact fingerprint.

Host-state inspection then found that CanopyOps already owned marketplace ID
`collaborative-dynamics`. Codex identifies and caches marketplaces by name, so
publishing another standalone repository under that ID would create a sibling
product collision. MIND now uses the portable unique marketplace ID
`collaborative-dynamics-mind`, with the display title `Collaborative Dynamics:
MIND`. Installation, upgrade, removal, troubleshooting, and customer-visible
marketplace-selection instructions were updated together. The first rereview
caught two installer references and one Pages reference that still displayed
the parent brand instead of the exact marketplace title; those three references
were corrected before this fingerprint was issued. This semantic repair
produced the current fingerprint and requires exact independent rereview.

The release verifier now binds both the machine ID and the exact display title.
A focused regression test rejects the former shared ID and the parent-brand-only
display label. The narrow release-tooling suite passes 6 tests, and full
discovery passes 83 tests on both Python 3.14 and Python 3.12. This closes the
recurrence path at the release-package boundary.

The prepublication live-visual cycle then found a mobile clipping report in a
390-pixel PNG. Root-cause isolation showed that the first Windows headless
Chrome invocation had silently laid out the page at its 500-CSS-pixel minimum
and cropped the PNG to 390 pixels, so that image could not diagnose the site.
A direct DevTools emulation at a true 390 CSS pixels then exposed a separate
real defect: the mobile `.steps > li { grid-template-columns: 1fr; }` rule let
the long marketplace command impose a roughly 661-pixel min-content width,
while `main { overflow: hidden; }` concealed document overflow. The repair
uses zero-minimum grid tracks and zero-minimum step children. The corrected
browser receipt observes a 390-pixel document, three 342-pixel step cards, a
295-pixel `pre` with `overflow-x: auto` and a 613-pixel scroll width, and no
container clipping. Independent original-detail visual rereview passed the
focused 390-pixel installation capture. Public Pages deployment remains a
separate post-merge gate.

## Evidence ceiling

These checks establish source-level documentation readiness, exact authored
bytes, and a local true-390px responsive regression closure. They do not
establish independent review of this fingerprint, the rebuilt release archive,
fresh-public plugin behavior, corrected GitHub Pages deployment, assistive-
technology behavior, or production outcomes. Those are separate gates.
