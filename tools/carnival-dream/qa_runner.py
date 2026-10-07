#!/usr/bin/env python3
"""Budgeted calls to existing repository QA tools; no automatic retries."""
import argparse,json,subprocess,sys
from pathlib import Path
from api_budget import ROOT,reserve

ap=argparse.ArgumentParser();ap.add_argument('--draft',type=int,choices=[1,2,3],required=True)
ap.add_argument('--id',required=True);ap.add_argument('--tool',choices=['frame-qa','anchor-drift','clip-qa','clone-check'],required=True)
ap.add_argument('--model-id',default='claude-opus-4-7')
ap.add_argument('--reserve',type=float,default=.50);ap.add_argument('arguments',nargs=argparse.REMAINDER)
a=ap.parse_args();extra=a.arguments[1:] if a.arguments[:1]==['--'] else a.arguments
run=ROOT/'data/workspace/carnival-dream'/f'draft-v{a.draft}'
reserve(a.draft,a.id,a.reserve,'anthropic-qa',a.tool+' bounded visual check')
ledger=ROOT/'data/cost-ledger.jsonl'
before=len(ledger.read_text().splitlines()) if ledger.exists() else 0
command=[sys.executable,str(ROOT/'tools'/f'{a.tool}.py'),*extra,'--model-id='+a.model_id,'--retries=0','--json','--fail-on=medium']
with (run/'qa'/f'{a.id}.json').open('w') as out,(run/'operations'/f'{a.id}.log').open('w') as err:
    result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err)
rows=[]
if ledger.exists():
    for line in ledger.read_text().splitlines()[before:]:
        row=json.loads(line)
        target=row.get('target','')
        expected=Path(extra[1] if a.tool=='anchor-drift' else extra[0])
        matches=target==expected.name if a.tool in ['frame-qa','anchor-drift'] else target.startswith(expected.stem+'.')
        if row.get('tool')==a.tool and matches:rows.append(row)
estimate=sum((r.get('input_tokens',0)*5+r.get('output_tokens',0)*25+r.get('cache_creation_input_tokens',0)*6.25+r.get('cache_read_input_tokens',0)*.5)/1e6 for r in rows)
receipt={'id':a.id,'tool':a.tool,'exit_code':result.returncode,'usage_records':rows,'estimated_usd':round(estimate,6),'reserved_usd':a.reserve,'pricing_model':a.model_id+'; USD 5/25 per million input/output tokens','billing_status':'token-based estimate; reservation retained if no usage record'}
(run/'operations'/f'{a.id}.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'id':a.id,'exit_code':result.returncode,'estimated_usd':round(estimate,6),'qa_file':str((run/'qa'/f'{a.id}.json').relative_to(ROOT))}))
sys.exit(result.returncode)
