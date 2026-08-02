# Hesperos authoring validation evidence

Candidate documentation fingerprint: `b91874a17296f6aa8837d5417174bfca10e8360b07a643d49937ac15ee023b1c`

The fingerprint is SHA-256 over the UTF-8 compact JSON serialization of the ordered `authored_files` records (`path`, `bytes`, `sha256`).

## Observed checks

| Check | Observed result |
|---|---|
| Hesperos accessible-Markdown linter over all 16 declared Markdown documents | PASS for every file |
| `python -B -X utf8 scripts/audit_pages.py` | PASS; 22 headings, 29 links, 4 image elements, all three required visual roles rendered, zero issues |
| Full `unittest` discovery | PASS; 86 tests |
| Live associative-retrieval qualification | PASS; 6 of 6 probes, including Agentic Eros inclusion and false-friend exclusions |
| `git diff --check` | PASS; line-ending conversion warnings only |
| Direct visual inspection of square icon, 16:9 hero, and 4:5 capability card | PASS; all three roles are coherent and usable |

## Root-cause records

The prior documentation evidence described fifteen Faculties because it preceded Agentic Eros integration. Those receipts were invalidated by the source change and regenerated only after the customer documentation, runtime registry, tests, and Pages source consistently described sixteen Faculties.

The native Codex sandbox helper could not launch because `codex-windows-sandbox-setup.exe` is missing from the installed application. That failure occurred before repository commands dispatched. The work used the already-established guarded PowerShell execution channel; it is not evidence of a repository permission defect.

The image viewer used by the app shares the same missing-helper failure. Each source image was therefore decoded and visually inspected through an in-memory PowerShell/.NET thumbnail path. The resulting image assessment is direct source inspection, while live rendered Pages remains a separate gate.

The first associative index build exposed four distinct reproducibility defects: repository import resolution, timestamp precision, card-view digest ordering, and an over-broad profile name. Each premise was corrected before rebuilding. The active snapshot now uses a behavior-qualified profile bound to the six retained live probes; it is not described as universally optimal retrieval.

## Evidence ceiling

These checks establish exact source-level documentation readiness, local visual-source inspection, and local behavior qualification for the documented H0 adapter. They do not establish the final archive, fresh-host discovery, public release, deployed Pages behavior, assistive-technology behavior, representative-user outcomes, or production behavior. Those are separate gates.
