#!/usr/bin/env python3
"""Reconcile per-operation estimates while retaining conservative reservations."""
import argparse,json
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);a=ap.parse_args()
run=a.run;path=run/'budget.json';budget=json.loads(path.read_text());estimates={};unknown=[]
for p in (run/'operations').glob('*.receipt.json'):
    d=json.loads(p.read_text())
    if d['usage_records']:estimates[d['id']]=d['estimated_usd']
    else:unknown.append(d['id'])
for p in (run/'operations').glob('*-video.result.json'):
    d=json.loads(p.read_text());ident=p.name.removesuffix('.result.json')
    if d.get('status')=='downloaded':estimates[ident]=d['estimatedUSD']
for row in budget.get('allocations',[]):
    ident=row['id']
    if ident in estimates:row['estimated_usd']=estimates[ident];row['status']='usage-estimated'
    else:row['estimated_usd']=row['reserved_usd'];row['status']='conservative-reservation-pending-billing'
budget['external_spend_estimate_usd']=round(sum(r['estimated_usd'] for r in budget.get('allocations',[])),6)
budget['reserved_total_usd']=round(sum(r['reserved_usd'] for r in budget.get('allocations',[])),6)
assert budget['reserved_total_usd']<=30 and budget['external_spend_estimate_usd']<=30
budget['billing_note']='Token usage and published video rates give estimates, not an invoice. Calls without usage evidence retain their full reservation. No unused reservation is silently recycled.'
path.write_text(json.dumps(budget,indent=2)+'\n')
print(json.dumps({k:budget[k] for k in ['external_spend_estimate_usd','reserved_total_usd','ceiling_usd']}))
