import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {execFileSync, spawnSync} from 'node:child_process';
import {audit, scanFile, scanText} from './privacy-check.mjs';

const privateEmail = () => ['private-person','mailbox.io'].join('@');
const token = () => 'sk-' + 'Q'.repeat(40);
const has = (text, rule) => scanText(text).some(f => f.rule === rule);
const publicIdentity = ['12345+review-bot','users.noreply.github.com'].join('@');

test('detects personal identifiers without returning their values', () => {
  const cases = [
    [privateEmail(),'personal-email'],
    [['','Users','private-person','project'].join('/'),'personal-home-path'],
    [['C:','Users','private-person','project'].join('\\'),'personal-home-path'],
    [['415','867','5309'].join('-'),'phone-like'],
    [['123','45','6789'].join('-'),'ssn-like'],
    ['12' + ' Private Street','street-address-like'],
    [['10','24','13','8'].join('.'),'private-network-address'],
  ];
  for (const [value, rule] of cases) {
    assert.ok(has(value,rule),rule);
    assert.ok(!JSON.stringify(scanText(value)).includes(value));
  }
});

test('detects provider tokens, key material, credentials and cloud identifiers', () => {
  for (const [value, rule] of [
    [token(),'provider-token'],
    ['-----BEGIN ' + 'PRIVATE KEY-----','private-key'],
    ['password="' + 'not-a-real-test-secret' + '"','literal-credential'],
    ['https://' + 'person:credential' + '@host.invalid','credential-in-url'],
    ['{"type":' + '"service_account"}','service-account'],
    ['gs://' + 'private-production-bucket/input.png','cloud-bucket-id'],
  ]) assert.ok(has(value,rule),rule);
});

test('allows public no-reply identities, reserved examples and portable paths', () => {
  const examples = [publicIdentity, 'name@example.com', 'name@sample.test',
    'data/workspace/meridian-house', '/home/user/project', 'http://127.0.0.1:4317',
    '2026-09-12', 'model=2.0.0', 'const apiKey = process.env.API_KEY;',
    'api_key="YOUR_API_KEY"', 'gs://example-bucket/frame.png'];
  for (const text of examples) assert.deepEqual(scanText(text),[],text);
});

test('fails closed on runtime paths, binary files and oversized blobs', () => {
  for (const path of ['data/config.json','.env','generated-images/a.png','.claude/plans/private.md'])
    assert.ok(scanFile(path,Buffer.from('{}')).some(f => f.rule === 'private-or-runtime-file'));
  assert.ok(scanFile('picture.png',Buffer.from('stub')).length);
  assert.ok(scanFile('unknown',Buffer.from([1,0,2])).length);
  assert.ok(scanFile('large.txt',Buffer.alloc(2*1024*1024+1,65)).some(f=>f.rule==='oversized-file-requires-review'));
});

function repository(t) {
  const cwd = mkdtempSync(join(tmpdir(),'privacy-check-test-'));
  t.after(()=>rmSync(cwd,{recursive:true,force:true}));
  const git = (...args) => execFileSync('git',args,{cwd,stdio:['ignore','pipe','pipe']}).toString().trim();
  git('init','-q'); git('config','user.name','review-bot'); git('config','user.email',publicIdentity);
  writeFileSync(join(cwd,'source.txt'),'safe initial content\n'); git('add','source.txt'); git('commit','-qm','initial');
  return {cwd,git,base:git('rev-parse','HEAD')};
}

test('scans the actual staged snapshot, not a subsequently cleaned worktree', t => {
  const {cwd,git} = repository(t);
  writeFileSync(join(cwd,'source.txt'),token()); git('add','source.txt');
  writeFileSync(join(cwd,'source.txt'),'clean but not staged');
  assert.ok(audit({cwd,mode:'--staged'}).findings.some(f=>f.rule==='provider-token'));
  git('add','source.txt');
  assert.deepEqual(audit({cwd,mode:'--staged'}).findings,[]);
});

test('detects personal commit email before committing', t => {
  const {cwd,git} = repository(t);
  git('config','user.email',privateEmail());
  assert.ok(audit({cwd,mode:'--staged'}).findings.some(f=>f.rule==='non-noreply-commit-email'));
});

test('outgoing scan catches sensitive content in an earlier, later-cleaned commit', t => {
  const {cwd,git,base} = repository(t);
  writeFileSync(join(cwd,'source.txt'),token()); git('add','source.txt'); git('commit','-qm','add test fixture');
  writeFileSync(join(cwd,'source.txt'),'clean again'); git('add','source.txt'); git('commit','-qm','remove test fixture');
  const result = audit({cwd,mode:'--outgoing',base});
  assert.equal(result.commitCount,2);
  assert.ok(result.findings.some(f=>f.rule==='provider-token'));
  assert.ok(!JSON.stringify(result).includes(token()));
});

test('outgoing scan includes commit messages and metadata', t => {
  const {cwd,git,base} = repository(t);
  git('config','user.email',privateEmail());
  git('commit','--allow-empty','-qm','contact ' + privateEmail());
  const result = audit({cwd,mode:'--outgoing',base});
  assert.ok(result.findings.some(f=>f.rule==='non-noreply-commit-email'));
  assert.ok(result.findings.some(f=>f.path==='[commit message]' && f.rule==='personal-email'));
});

test('pre-push inspects updates and new branches, and safely skips deletions', t => {
  const {cwd,git,base} = repository(t);
  git('update-ref','refs/remotes/origin/main',base);
  writeFileSync(join(cwd,'source.txt'),token()); git('add','source.txt'); git('commit','-qm','fixture');
  const head=git('rev-parse','HEAD'),zero='0'.repeat(40);
  for (const remoteSha of [base,zero]) {
    const result=audit({cwd,mode:'--pre-push',input:`refs/heads/main ${head} refs/heads/main ${remoteSha}\n`,remote:'origin'});
    assert.equal(result.commitCount,1);
    assert.ok(result.findings.some(f=>f.rule==='provider-token'));
  }
  assert.equal(audit({cwd,mode:'--pre-push',input:`(delete) ${zero} refs/heads/old ${head}\n`}).commitCount,0);
  assert.throws(()=>audit({cwd,mode:'--pre-push',input:'invalid input'}),/Malformed/);
});

test('redacted CLI output does not echo the detected value', t => {
  const {cwd,git} = repository(t);
  writeFileSync(join(cwd,'source.txt'),privateEmail()); git('add','source.txt');
  const result=spawnSync(process.execPath,[resolve('tools/privacy-check.mjs'),'--staged'],{cwd,encoding:'utf8'});
  assert.equal(result.status,1);
  assert.match(result.stderr,/value redacted/);
  assert.ok(!result.stderr.includes(privateEmail()));
});

test('hook installer refuses to replace existing custom hooks', t => {
  const {cwd,git} = repository(t);
  const script=resolve('tools/privacy-check.mjs');
  git('config','core.hooksPath','existing-hooks');
  const result=spawnSync(process.execPath,[script,'--install-hooks'],{cwd,encoding:'utf8'});
  assert.equal(result.status,1);
  assert.equal(git('config','core.hooksPath'),'existing-hooks');
});
