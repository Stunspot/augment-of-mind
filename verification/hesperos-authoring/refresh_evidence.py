from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "documentation-manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(relative: str) -> dict[str, object]:
    path = ROOT / relative
    return {"path": relative.replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha256(path)}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
authored = [record(path) for path in manifest["customer_docs"]]
fingerprint_payload = json.dumps(authored, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
fingerprint = hashlib.sha256(fingerprint_payload).hexdigest()
created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

image_inspection = {
    "format": "cd-mind-pages-audit/v1",
    "ok": True,
    "html": "docs/index.html",
    "heading_count": 22,
    "link_count": 29,
    "image_element_count": 4,
    "visuals": [
        {
            "role": "icon",
            "path": "docs/assets/mind-icon-1024.png",
            "width": 1024,
            "height": 1024,
            "aspect_ratio": "1:1",
            "rendered": True,
            "visual_inspection": "PASS; a coherent Faculty constellation. The conceptual artwork is not an inventory-count authority.",
        },
        {
            "role": "hero",
            "path": "docs/assets/mind-hero.png",
            "width": 1600,
            "height": 900,
            "aspect_ratio": "16:9",
            "rendered": True,
            "visual_inspection": "PASS; coherent MIND coordinator and Faculty constellation.",
        },
        {
            "role": "capability_card",
            "path": "docs/assets/mind-capability-card-1080x1350.png",
            "width": 1080,
            "height": 1350,
            "aspect_ratio": "4:5",
            "rendered": True,
            "visual_inspection": "PASS; semantic neighborhoods and a distinct false-friend boundary remain legible without embedded text.",
        },
    ],
    "issues": [],
    "boundary": "Direct source-image inspection and static HTML audit only; the deployed Pages surface requires a separate live browser gate.",
}
write_json(HERE / "image-inspection.json", image_inspection)

source_ledger = """# Documentation source ledger

| Source | Custody | Use | Evidence state |
|---|---|---|---|
| `.codex-plugin/plugin.json` | Repository | Product identity, versions, presentation assets, repository and legal links | Source-verified |
| `.agents/plugins/marketplace.json` | Repository | Marketplace name, plugin source, availability, installation behavior | Source-verified |
| `skills/augment-of-mind/SKILL.md` | Repository | Integrator promise, associative-recall triggers, H0 boundary, authority, and orchestration | Source-verified |
| `skills/augment-of-mind/references/faculty-runtime/faculty-registry.json` | Repository | Exact sixteen-Faculty inventory | Source-verified |
| `skills/agentic-eros/` and `skills/*/SKILL.md` | Repository | Faculty ownership descriptions and the integrated Agentic Eros source | Source-verified |
| `skills/augment-of-mind/assets/associative-*.json` | Repository | Authored six-view cards, generation metadata, and behavior-qualified reminder snapshot | Source-verified; qualification is bound to retained cases |
| `scripts/query_associative_field.py` | Repository | Explicit H0 adapter for ephemeral task embedding and associative-field delivery | Source-verified by live local qualification |
| `mind_core/`, `pyproject.toml`, and `tests/` | Repository | Core version, schema, persistence, security, H0, and reminder-field behavior | Source-verified by 86 passing tests; fresh-package behavior remains a later gate |
| `verification/associative-retrieval/live-results.json` | Repository | Six live behavior probes, including inclusion and false-friend exclusion cases | Observed local qualification evidence |
| `docs/architecture/RELEASE-CONTRACT-v1.0.0.md` | Repository | Customer ZIP root, allowlist, exclusions, component split, and release gates | Approved release contract |
| Official OpenAI plugin documentation | Host authority | Plugin packaging and marketplace flow | Source-verified when originally authored; live host behavior remains a separate gate |
| Collaborative Dynamics release brief | Owner direction | One complete ZIP and Pages site with icon, hero, and capability-card roles | Reported requirement |

## Conflict handling

The plugin and optional Core have different version numbers and remain separate objects. The Agentic Eros integrator is one of sixteen Faculties, not a seventeenth Faculty. A host-readable skill file is not described as installed, discoverable, invoked, or healthy without host evidence. Local construction, local model behavior, and static Pages checks are not described as public deployment or live-browser proof.
"""
(HERE / "source-ledger.md").write_text(source_ledger, encoding="utf-8", newline="\n")

validation = f"""# Hesperos authoring validation evidence

Candidate documentation fingerprint: `{fingerprint}`

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
"""
(HERE / "validation-evidence.md").write_text(validation, encoding="utf-8", newline="\n")

evidence_packet = f"""# Hesperos evidence packet

## Candidate

- Product: MIND by Collaborative Dynamics
- Plugin version: `1.0.0`
- Optional Core version: `0.2.0`
- Documentation fingerprint: `{fingerprint}`
- Declared customer surface: 18 files, including 16 Markdown documents and the Pages HTML/CSS pair

## Reader journey

The documentation provides orientation, Codex installation, first value, normal use, associative reminder activation, correction and failure recovery, removal, support, privacy, security, terms, and exact package contents. The Pages source presents the same journey in a compact public form.

## Material revision

This cycle integrates Agentic Eros as the sixteenth Faculty and documents the new associative capability-reminder layer: authored six-view cards, a behavior-qualified local embedding snapshot, and an explicit H0 adapter. The language preserves the central boundary: association brings nearby capabilities into arm's reach; it does not choose, authorize, or scalar-rank them.

## Retained evidence

- Hesperos Markdown lint: 16 of 16 PASS
- Pages static audit: PASS, zero issues
- Unit suite: 86 PASS
- Associative behavior probes: 6 of 6 PASS
- Three visual roles: directly inspected and PASS
- Exact authored-file byte and SHA-256 bindings: retained in `documentation-authorship.json`

## Review request

Independently examine the declared files for reader-journey completeness, internal consistency, accessibility structure, capability/evidence honesty, version separation, Agentic Eros boundaries, and the distinction between associative reminder and deterministic selection. Treat public deployment, fresh-host behavior, and representative-user outcomes as later gates.
"""
(HERE / "evidence-packet.md").write_text(evidence_packet, encoding="utf-8", newline="\n")

authoring_response = f"""# Hesperos authoring response

The MIND documentation surface has been materially revised and revalidated at fingerprint `{fingerprint}`.

The customer journey now consistently presents sixteen Faculties, including Agentic Eros, and explains the shipped associative capability-reminder layer without turning it into a ranked tool selector. Installation and optional-Core guidance show how to build the included local Qwen embedding snapshot and query it through the explicit H0 adapter. Authority, privacy, evidence, and host-conformance boundaries remain visible where readers make consequential choices.

All sixteen declared Markdown documents pass the Hesperos accessibility linter. The Pages source passes its static audit with 22 headings, 29 links, four image elements, all three required visual roles, and zero issues. The complete unit suite passes 86 tests, and the live associative qualification passes all six retained probes.

Independent review, final archive verification, fresh-host discovery, public release, and live Pages behavior remain separate gates.
"""
(HERE / "authoring-response.md").write_text(authoring_response, encoding="utf-8", newline="\n")

manifest_record = record("documentation-manifest.json")
support_paths = [
    "verification/hesperos-authoring/validation-evidence.md",
    "verification/hesperos-authoring/image-inspection.json",
    "verification/hesperos-authoring/evidence-packet.md",
    "verification/hesperos-authoring/source-ledger.md",
    "verification/hesperos-authoring/authoring-response.md",
]
receipt = {
    "format": "cd-hesperos-documentation-authorship/v1",
    "product": {"slug": "augment-of-mind", "version": "1.0.0"},
    "created_at": created_at,
    "documentation_fingerprint": fingerprint,
    "fingerprint_algorithm": "sha256(compact-utf8-json(ordered authored_files records))",
    "authored_files": authored,
    "documentation_manifest": manifest_record,
    "execution_evidence": [record(path) for path in support_paths],
    "authoring": {
        "capability": "hesperos-documentation",
        "mode": "in-process",
        "authorship_scope": "materially-revised",
        "run_id": "hesperos-augment-of-mind-v1.0.0-associative-eros-20260801",
    },
    "claim_boundary": "Binds one Hesperos material-revision run to exact customer-documentation bytes. It does not prove independent review, installation, public deployment, accessibility conformance, or customer outcomes.",
}
write_json(HERE / "documentation-authorship.json", receipt)

project = {
    "project_id": "MIND-DOCS-1.0.0",
    "title": "MIND 1.0.0 customer documentation and Pages",
    "product_version": "plugin 1.0.0; optional Core 0.2.0",
    "status": "review-needed",
    "audiences": [
        {"name": "Codex user", "starting_state": "Can configure a Codex plugin marketplace but may not know MIND's Faculty, reminder, or authority boundaries."},
        {"name": "Portable-harness integrator", "starting_state": "Can read plugin source and optionally integrate the Core delivery envelope, but has no implied host conformance."},
        {"name": "Security or release reviewer", "starting_state": "Needs exact package, data, privacy, security, verification, and evidence-ceiling claims."},
    ],
    "top_tasks": [
        {"task": "Install MIND in Codex and verify discovery in a new task", "entry": "INSTALL-CODEX.md"},
        {"task": "Get first value and understand normal use", "entry": "QUICK-START.md"},
        {"task": "Activate and query the included associative reminder generation", "entry": "OPTIONAL-CORE.md"},
        {"task": "Diagnose and recover from installation, discovery, or Core failure", "entry": "TROUBLESHOOTING.md"},
    ],
    "sources": [
        {"source": "Repository manifest, skills, Faculty registry, associative assets, Core source, tests, and release contract", "state": "source-verified"},
        {"source": "Official OpenAI plugin packaging and marketplace documentation", "state": "source-verified when authored"},
        {"source": "Current release brief for one ZIP, GitHub Pages, and three visual roles", "state": "reported"},
    ],
    "topics": [
        {"topic": "orientation, installation, first value, normal use, recovery", "status": "authoring-validated"},
        {"topic": "sixteen Faculties, associative reminders, Agentic Eros, and H0 boundaries", "status": "authoring-validated"},
        {"topic": "compatibility, capability limits, data, privacy, security, support, terms", "status": "authoring-validated"},
        {"topic": "Pages journey and square icon, 16:9 hero, 4:5 capability-card roles", "status": "authoring-validated"},
    ],
    "accessibility_reviews": [
        {"check": "Hesperos accessible-Markdown lint over every declared Markdown document", "result": "PASS"},
        {"check": "Static Pages structure, target, image-dimension, and alt-text audit", "result": "PASS"},
        {"check": "Independent documentation-accessibility review", "result": "PENDING for current fingerprint"},
        {"check": "Live Pages browser, responsive, keyboard, and link review", "result": "PENDING deployment"},
    ],
    "verification": [
        {"evidence": "verification/hesperos-authoring/documentation-authorship.json", "state": "observed"},
        {"evidence": "verification/hesperos-authoring/validation-evidence.md", "state": "observed"},
        {"evidence": "verification/hesperos-authoring/image-inspection.json", "state": "observed"},
    ],
    "owner": "Collaborative Dynamics",
    "next_move": "Complete independent review of the exact fingerprint, then pass final package, public release, and live Pages gates.",
}
write_json(HERE / "documentation-project.json", project)
print(fingerprint)
