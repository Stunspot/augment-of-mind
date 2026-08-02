from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MODEL = "qwen35:latest"
URL = "http://127.0.0.1:11434/api/generate"


def section(path: str) -> str:
    source = ROOT / path
    return f"\n\n===== {path} =====\n{source.read_text(encoding='utf-8')}"


manifest = json.loads((ROOT / "documentation-manifest.json").read_text(encoding="utf-8"))
customer_docs = "".join(section(path) for path in manifest["customer_docs"])
reality_paths = [
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    "skills/augment-of-mind/SKILL.md",
    "skills/augment-of-mind/references/faculty-runtime/faculty-registry.json",
    "scripts/query_associative_field.py",
    "scripts/build_release.py",
    "scripts/verify_release.py",
    "verification/associative-retrieval/live-results.json",
    "verification/hesperos-authoring/evidence-packet.md",
    "verification/hesperos-authoring/source-ledger.md",
]
reality = "".join(section(path) for path in reality_paths)

prompt = f"""You are an independent documentation and accessibility reviewer. Review the complete MIND customer documentation against the supplied implementation and evidence excerpts. This is a content review, not a punctuation or consistency exercise.

Your job:
1. Judge whether a new Codex user can orient, install, get first value, use, recover, remove, and seek support without hidden prerequisite knowledge.
2. Check every capability, privacy, security, package, host-support, version, Agentic Eros, and associative-reminder claim against the supplied reality packet.
3. Check that association is described as serendipitous contextual reminding, never a top-K tool recommendation, universal scalar, selection, activation, health, or authority.
4. Check that Agentic Eros is one of sixteen Faculties, remains persona-neutral, preserves non-erotic defaults, and does not gain durable intimate memory or direct participation without the documented authority/invitation boundaries.
5. Check evidence verbs: static/package, local behavior, install/discovery, public release, and deployed Pages must remain distinct.
6. Review the Pages text as a reader-facing public product surface as well as the repository guides. Identify missing or misleading transitions, not merely inconsistent strings.
7. Review accessibility at the source-content level: headings, link purpose, alt text, readable instructions, error recovery, and cognitive load. Do not claim assistive-technology or live-browser results from source alone.

Do not recommend redesign for taste. Report only material or useful findings supported by exact file and claim references. If no material finding remains, say so. A later gate will separately test the archive, fresh install, public release, and live Pages deployment.

Return one JSON object with exactly these keys:
- disposition: REVIEW_PASS or REVIEW_CHANGES_REQUIRED
- summary: concise string
- findings: array of objects with severity (material or useful), file, claim, reality, and correction
- passed_areas: array of concise strings
- evidence_boundary: concise string

DOCUMENTATION SURFACE:{customer_docs}

IMPLEMENTATION AND EVIDENCE PACKET:{reality}
"""

request_body = json.dumps(
    {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "think": False,
        "options": {"temperature": 0.1, "num_ctx": 65536, "num_predict": 8192},
    }
).encode("utf-8")
request = urllib.request.Request(URL, data=request_body, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(request, timeout=900) as response:
    envelope = json.load(response)
(HERE / "content-review-provider-envelope.json").write_text(
    json.dumps(envelope, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
    newline="\n",
)
raw_review = envelope.get("response")
if not isinstance(raw_review, str) or not raw_review.strip():
    raise RuntimeError(
        "review provider returned no response text; "
        f"done_reason={envelope.get('done_reason')!r}, "
        f"eval_count={envelope.get('eval_count')!r}, "
        f"thinking_bytes={len(str(envelope.get('thinking', '')).encode('utf-8'))}"
    )
review = json.loads(raw_review)
receipt = {
    "format": "cd-hesperos-independent-content-review/v1",
    "model": MODEL,
    "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    "prompt_bytes": len(prompt.encode("utf-8")),
    "done_reason": envelope.get("done_reason"),
    "eval_count": envelope.get("eval_count"),
    "review": review,
}
(HERE / "content-review-response.json").write_text(
    json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
    newline="\n",
)
print(json.dumps(review, indent=2, ensure_ascii=False))
