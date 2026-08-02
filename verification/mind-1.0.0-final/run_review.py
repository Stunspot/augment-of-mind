from __future__ import annotations
import hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
ART=ROOT/'artifacts/testforge/mind-1.0.0-final'
MODEL='qwen2.5-coder:14b'
def text(path): return path.read_text(encoding='utf-8-sig')
manifest=text(HERE/'verification-manifest.json')
snapshot=json.loads(text(ART/'target-snapshot.json'))
snapshot_summary=json.dumps({k:v for k,v in snapshot.items() if k!='files'},indent=2)
raw=[]
for p in sorted((ART/'raw').glob('E-00[1-8]-*.json')):
 if 'attempt1' not in p.name and 'results' not in p.name:
  raw.append('\n===== '+p.relative_to(ROOT).as_posix()+' =====\n'+text(p))
packet='\n'.join(raw)
for p in [ART/'manifest-validation.json',ART/'traceability-validation.json',ART/'test-smells.json',ART/'raw/E-009-failed-invocation-control-flow.json',ART/'raw/E-010-smell-triage.json',ROOT/'verification/hesperos-review/review-receipt.json',ROOT/'verification/associative-retrieval/live-results.json']:
 packet+='\n===== '+p.relative_to(ROOT).as_posix()+' =====\n'+text(p)
prompt='''You are the independent TestForge verification reviewer. Try to make the bounded source-readiness claim fail. Review the exact manifest, target binding, validators, raw execution receipts, heuristic smells, Hesperos review, and live associative evidence below.

Challenge this chain: scope -> impact -> risk -> invariant -> scenario -> test -> evidence -> status. Check target fidelity, catastrophic omissions, oracle strength, boundary realism, evidence custody, traceability, authority, and decision fit. A green suite is only one source. The 149 smell hits are heuristic uses of the word snapshot; determine whether they are decision-changing rather than counting them as defects. The failed first E-004 receipt is a preserved harness invocation failure; check that it never dispatched product behavior and that the corrected receipt changes the premise.

Adjudicate three challenged questions from first principles: whether a source-ready decision may precede the explicitly later archive/install/publication gates; whether E-009 proves the missing-argument attempt stopped before any product behavior; and whether E-010 demonstrates lexical domain-term false positives rather than golden-snapshot testing. Cite the actual evidence either way. The proposed status is READY_WITH_RESIDUAL_RISK only for committing this source and entering package/install/publication gates. It is not a claim that archive, fresh installation, GitHub release, or deployed Pages already passed. Do not fail the bounded source decision merely because those explicitly later gates remain, but do fail it if the source evidence cannot safely justify entering them.

Return one JSON object with exactly: disposition (REVIEW_PASS, REVIEW_PASS_WITH_CONDITIONS, or REVIEW_FAIL), summary, findings (array with severity, challenged_claim, evidence, why_support_fails, discriminating_check, required_revision, status_consequence), conditions (array), passed_lenses (array), evidence_boundary.

TARGET SNAPSHOT SUMMARY:
'''+snapshot_summary+'\n\nMANIFEST:\n'+manifest+'\n\nEVIDENCE:\n'+packet
schema={'type':'object','properties':{'disposition':{'type':'string','enum':['REVIEW_PASS','REVIEW_PASS_WITH_CONDITIONS','REVIEW_FAIL']},'summary':{'type':'string'},'findings':{'type':'array','items':{'type':'object','properties':{'severity':{'type':'string'},'challenged_claim':{'type':'string'},'evidence':{'type':'array','items':{'type':'string'}},'why_support_fails':{'type':'string'},'discriminating_check':{'type':'string'},'required_revision':{'type':'string'},'status_consequence':{'type':'string'}},'required':['severity','challenged_claim','evidence','why_support_fails','discriminating_check','required_revision','status_consequence']}},'conditions':{'type':'array','items':{'type':'string'}},'passed_lenses':{'type':'array','items':{'type':'string'}},'evidence_boundary':{'type':'string'}},'required':['disposition','summary','findings','conditions','passed_lenses','evidence_boundary']}
body=json.dumps({'model':MODEL,'prompt':prompt,'stream':False,'format':schema,'think':False,'options':{'temperature':0.1,'num_ctx':32768,'num_predict':4096}}).encode('utf-8')
request=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=body,headers={'Content-Type':'application/json'})
with urllib.request.urlopen(request,timeout=900) as response: envelope=json.load(response)
(HERE/'review-provider-envelope.json').write_text(json.dumps(envelope,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
raw_review=envelope.get('response')
if not isinstance(raw_review,str) or not raw_review.strip(): raise RuntimeError('empty review response: '+repr({k:envelope.get(k) for k in ('done_reason','eval_count')}))
review=json.loads(raw_review)
receipt={'format':'cd-testforge-independent-review/v1','model':MODEL,'prompt_sha256':hashlib.sha256(prompt.encode('utf-8')).hexdigest(),'prompt_bytes':len(prompt.encode('utf-8')),'target_aggregate_sha256':snapshot['aggregate_sha256'],'done_reason':envelope.get('done_reason'),'eval_count':envelope.get('eval_count'),'review':review}
(HERE/'review-response.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(review,indent=2,ensure_ascii=False))
