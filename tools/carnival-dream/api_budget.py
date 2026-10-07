#!/usr/bin/env python3
"""Separate all-API $30 gates for the three explicitly authorized drafts."""
import argparse
import datetime
import fcntl
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]

def reserve(draft, ident, usd, category, note):
    run=ROOT/'data/workspace/carnival-dream'/f'draft-v{draft}'
    path=run/'budget.json'
    with (run/'budget.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        budget=json.loads(path.read_text())
        records=budget.setdefault('allocations',[])
        if any(r['id']==ident for r in records):raise RuntimeError('Attempt already allocated; inspect its outcome, never silently retry')
        total=sum(r['reserved_usd'] for r in records)
        if usd<=0 or total+usd>30+1e-8:raise RuntimeError('Draft budget limit; external call is not authorized')
        rec={'id':ident,'category':category,'reserved_usd':usd,'note':note,'status':'reserved-before-call','time':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        records.append(rec);budget['reserved_total_usd']=round(total+usd,6)
        tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(budget,indent=2)+'\n');os.replace(tmp,path)
    return rec

def veo_preflight(draft,seconds,note):
    # Invoke the repository's existing Veo hard-stop without editing the shared
    # tool or another film's project registry. The all-API gate above is stricter.
    sp=importlib.util.spec_from_file_location('repo_veo_budget',ROOT/'tools/veo-budget.py')
    mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
    mod.CAP_USD=30
    mod.LEDGER=str(ROOT/'data/workspace/carnival-dream'/f'draft-v{draft}'/'veo-budget.tsv')
    return mod.cmd_preflight(SimpleNamespace(model='quality',seconds=seconds,resolution='1080p',audio='no',note=note))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--draft',type=int,choices=[1,2,3],required=True)
    ap.add_argument('--id',required=True);ap.add_argument('--usd',type=float,required=True)
    ap.add_argument('--category',required=True);ap.add_argument('--note',required=True)
    ap.add_argument('--veo-seconds',type=int,choices=[4,6,8])
    a=ap.parse_args();r=reserve(a.draft,a.id,a.usd,a.category,a.note)
    if a.veo_seconds:veo_preflight(a.draft,a.veo_seconds,a.note)
    print(json.dumps({'id':r['id'],'reserved_usd':r['reserved_usd'],'draft':a.draft}))
