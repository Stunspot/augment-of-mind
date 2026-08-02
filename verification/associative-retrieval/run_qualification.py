"""Run live semantic acceptance probes against a fresh MIND Core database."""

from __future__ import annotations

import argparse, json, tempfile
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from mind_core import MindCore
from mind_core.util import canonical_json, sha256_text
from scripts.query_associative_field import embed
from tests.helpers import handshake_record

CASES=[
 {"id":"HAFR-010","text":"There is charged chemistry and teasing between two adults, but first determine whether the attraction is mutual before escalating.","include":["agentic-eros"],"exclude":[]},
 {"id":"HAFR-011","text":"My sister is grieving. Help me offer warm family comfort and practical support without making it awkward.","include":[],"exclude":["agentic-eros"]},
 {"id":"HAFR-012","text":"Two consenting adults explicitly invite direct erotic participation; respond with desire while preserving pacing, consent, tone, and relational context.","include":["agentic-eros","kairos"],"exclude":[]},
 {"id":"MIND-ASSOC-001","text":"GitHub authentication failed even though this connector should always work. Determine why before choosing a workaround.","include":["sensemaking","epistemic-regulation"],"exclude":[]},
 {"id":"MIND-ASSOC-002","text":"The task crashed halfway through a long release. Recover prior decisions and unfinished verification, then keep striving to completion.","include":["cognitive-continuity","agent-striving","executive-function"],"exclude":[]},
 {"id":"MIND-ASSOC-003","text":"The page is technically usable but visually generic and tonally incoherent. Give it a stronger symbolic visual language.","include":["aesthetic-intelligence"],"exclude":["agentic-eros"]},
]

def main()->int:
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--output",type=Path,required=True)
 p.add_argument("--bootstrap",type=Path,default=ROOT/"skills/augment-of-mind/assets/associative-bootstrap.json")
 p.add_argument("--index",type=Path,default=ROOT/"skills/augment-of-mind/assets/associative-index-qwen3-embedding-0.6b.json")
 p.add_argument("--model",default="qwen3-embedding:0.6b")
 args=p.parse_args()
 bootstrap=json.loads(args.bootstrap.read_text(encoding="utf-8"))
 manifest=json.loads(args.index.read_text(encoding="utf-8"))
 results=[]
 with tempfile.TemporaryDirectory() as directory:
  with MindCore(Path(directory)/"mind.sqlite3") as core:
   core.hosts.handshake(handshake_record("agent:qualification","session:qualification"))
   core.bootstrap(bootstrap)
   status=core.reminders.ingest_index(manifest)
   token=core.reminders.issue_session_capability("agent:qualification","session:qualification")["session_capability"]
   for case in CASES:
    vector=embed(case["text"],args.model,"http://127.0.0.1:11434")
    field=core.reminders.neighborhood(token,status["associative_index_snapshot_id"],
      [{"anchor_id":"anchor:"+case["id"].lower(),"anchor_kind":"acceptance_probe","vector":vector}])
    handles=sorted(x["handle"] for x in field["members"])
    missing=sorted(set(case["include"])-set(handles))
    forbidden=sorted(set(case["exclude"])&set(handles))
    results.append({**case,"observed_handles":handles,"missing_required":missing,"present_forbidden":forbidden,
      "passed":not missing and not forbidden,"field_body_sha256":field["representations"]["canonical"]["body_sha256"],
      "membership_manifest_digest":field["membership_manifest_digest"]})
 profile=manifest["embedding_profile"]
 subject={"model":profile["model_id"],"dimensions":profile["dimensions"],"metric":profile["metric"],
  "radius":profile["radius"],"comparison_tolerance":profile["comparison_tolerance"],"vector_encoding":profile["vector_encoding"],
  "lexical_profile_digest":manifest["lexical_profile"]["profile_digest"],
  "cards":sorted((x["capability_card_id"],x["card_digest"]) for x in manifest["cards"]),
  "relations":sorted((x["capability_relation_id"],x["relation_digest"]) for x in manifest["relations"]),
  "vectors":sorted((x["capability_card_view_id"],x["vector_digest"]) for x in manifest["vectors"])}
 report={"format":"mind-associative-qualification/v2","model":args.model,
  "qualification_subject_digest":sha256_text(canonical_json(subject)),"radius":profile["radius"],
  "cases":results,"summary":{"passed":sum(x["passed"] for x in results),"total":len(results),
  "verdict":"PASS" if all(x["passed"] for x in results) else "FAIL"},
  "evidence_boundary":"Observed live Ollama embeddings and MIND Core H0 neighborhood membership in a fresh local SQLite database. This does not establish automatic host pre-sampling delivery."}
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")
 print(json.dumps(report["summary"],indent=2))
 return 0 if report["summary"]["verdict"]=="PASS" else 1

if __name__=="__main__":
 raise SystemExit(main())
