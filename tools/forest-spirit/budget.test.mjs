import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';

test('Scary Woods episode budgets are separate all-in pots with hard spending gates', () => {
  const result = execFileSync('python3', ['-c', `
import contextlib, importlib.util, io, pathlib, tempfile, types
spec = importlib.util.spec_from_file_location('budget', 'tools/veo-budget.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
expected = {'scary-woods-ep03': 50.0, 'scary-woods-ep04': 30.0}
assert len({b.PROJECTS[name][1] for name in expected}) == 2
with tempfile.TemporaryDirectory(prefix='scary-woods-budget-test-') as directory:
    for name, cap in expected.items():
        assert b.PROJECTS[name][0] == cap
        ledger = pathlib.Path(directory) / (name + '.tsv')
        b.PROJECTS[name] = (cap, str(ledger))
        b.select_project(name)
        b.append('adjust', 0, '-', '-', cap - 1.60, 'RESERVE test allocation')
        status = io.StringIO()
        with contextlib.redirect_stdout(status):
            b.cmd_status()
        assert 'All-in allocation (includes reserves)' in status.getvalue()
        args = types.SimpleNamespace(model='quality', seconds=4, resolution='1080p', audio='yes', note='exact cap')
        with contextlib.redirect_stdout(io.StringIO()):
            assert b.cmd_preflight(args) == 0
        assert round(b.read_spent()[0], 2) == cap
        before = ledger.read_bytes()
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                b.cmd_preflight(args)
            raise AssertionError('overspend accepted')
        except SystemExit as error:
            assert error.code == 3
        assert ledger.read_bytes() == before
print('PASS: isolated episode budgets; no production ledgers or providers touched')
`], {cwd: new URL('../..', import.meta.url), encoding: 'utf8'});
  assert.match(result, /PASS/);
});
