import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';

test('Meridian all-in budget preserves reserves, rejects over-cap spend and unsupported durations',()=>{
  const result=execFileSync('python3',['-c',`
import importlib.util, tempfile, os, types, contextlib, io
spec=importlib.util.spec_from_file_location('budget','tools/veo-budget.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
b.select_project('meridian-house')
assert b.CAP_USD == 49
with tempfile.TemporaryDirectory(prefix='meridian-budget-test-') as d:
    b.LEDGER=os.path.join(d,'ledger.tsv')
    b.append('adjust',0,'-','-',10,'RESERVE legacy-image')
    b.append('adjust',0,'-','-',1,'RESERVE infrastructure')
    a=types.SimpleNamespace(model='quality',seconds=4,resolution='1080p',audio='yes',note='test')
    with contextlib.redirect_stdout(io.StringIO()):
        b.cmd_preflight(a)
    assert abs(b.read_spent()[0]-12.6)<1e-8
    before=b.read_spent()
    a.seconds=3
    try:
        with contextlib.redirect_stderr(io.StringIO()): b.cmd_preflight(a)
        raise AssertionError('unsupported duration accepted')
    except SystemExit as e: assert e.code==2
    assert b.read_spent()==before
    a.seconds=4
    b.append('adjust',0,'-','-',35.4,'test fill to 48')
    before=b.read_spent()
    try:
        with contextlib.redirect_stderr(io.StringIO()): b.cmd_preflight(a)
        raise AssertionError('overspend accepted')
    except SystemExit as e: assert e.code==3
    assert b.read_spent()==before
print('PASS: no real ledger or external service was touched')
`],{cwd:new URL('../..',import.meta.url),encoding:'utf8'});
  assert.match(result,/PASS/);
});
