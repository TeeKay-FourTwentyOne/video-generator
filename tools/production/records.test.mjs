import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { validateRecord, loadRecords, exportRecord, buildViews, syncDescription, validateLocalEvidence, main, REPOSITORY_URL } from './records.mjs';
import { sha256 } from './record-schema.mjs';
import { archiveWorkspace } from './archive.mjs';
import { reconcileAccounting, writeAccounting } from './accounting.mjs';

const json = value => JSON.stringify(value, null, 2) + '\n';
async function fixture(t) {
  const repo = await fs.mkdtemp(path.join(os.tmpdir(), 'production-records-'));
  t.after(() => fs.rm(repo, { recursive: true, force: true }));
  const write = async (file, text) => { await fs.mkdir(path.dirname(path.join(repo, file)), { recursive: true }); await fs.writeFile(path.join(repo, file), text); };
  const description = `User-edited wording.\n\n${REPOSITORY_URL}\n`;
  const r = { schemaVersion: 1, projectId: 'example', title: 'Example', kind: 'film', status: 'review',
    briefPath: 'briefs/example/brief.md', descriptionPath: 'briefs/example/description.md', descriptionSha256: sha256(description),
    workspace: { path: 'data/workspace/example-v1', state: 'active' },
    artifacts: [{ role: 'native-review', version: 'v1', path: 'final/v1/film.mp4', sha256: 'a'.repeat(64),
      width: 16, height: 16, fps: { numerator: 2, denominator: 1 }, frames: 4, durationSeconds: 2, publishedMaster: false,
      descriptionCopyPath: 'final/v1/description.txt', deliveryRecordPath: 'final/v1/delivery.json' }],
    production: { providers: [], credits: [] }, reviewEvents: [],
    legacyPaths: [{ path: 'briefs/example-old.md', target: 'briefs/example/brief.md' }] };
  await write(r.briefPath, '# Intent\n\n[Current record](README.md).\n');
  await write(r.descriptionPath, description);
  await write('briefs/example-old.md', '[Moved](example/brief.md).\n');
  await write('briefs/example/production.json', json(r));
  await buildViews(repo);
  return { repo, r, write, description };
}
function publish(r, processing = false) {
  r.status = processing ? 'delivered' : 'published';
  r.artifacts[0].publishedMaster = !processing;
  r.publication = { platform: 'YouTube', url: 'https://youtu.be/example', evidence: processing ? 'supplied-processing' : 'user-confirmed',
    recordedDate: '2026-10-12', artifactVersion: 'v1' };
  r.reviewEvents.push({ type: 'publication', artifactVersion: 'v1', artifactSha256: r.artifacts[0].sha256,
    recordedDate: '2026-10-12', evidence: 'User supplied the URL.', outcome: r.publication.evidence });
}

test('source-only validation and deterministic views need no workspace, credentials or provider build', async t => {
  const { repo, r, write } = await fixture(t);
  await assert.rejects(fs.stat(path.join(repo, 'data')), { code: 'ENOENT' });
  publish(r);
  await exportRecord(repo, r);
  await buildViews(repo);
  const before = await fs.readFile(path.join(repo, 'briefs/example/production.json'));
  assert.deepEqual((await buildViews(repo, { check: true })).changed, []);
  assert.equal((await exportRecord(repo, r, { check: true })).changed, false);
  assert.deepEqual(await fs.readFile(path.join(repo, 'briefs/example/production.json')), before);
  assert.equal((await loadRecords(repo))[0].status, 'published');
  await write('briefs/example/README.md', 'stale');
  await assert.rejects(buildViews(repo, { check: true }), /drift/);
  assert.equal((await buildViews(repo, { dryRun: true })).changed.length, 1);
  assert.equal(await fs.readFile(path.join(repo, 'briefs/example/README.md'), 'utf8'), 'stale');
});

test('unfinished, multiple-version and processing records never infer publication or artistic approval', async t => {
  const { repo, r } = await fixture(t);
  r.artifacts.push({ ...r.artifacts[0], version: 'v2', path: 'final/v2/film.mp4',
    descriptionCopyPath: 'final/v2/description.txt', deliveryRecordPath: 'final/v2/delivery.json' });
  publish(r, true);
  assert.equal((await validateRecord(repo, r)).status, 'delivered');
  r.status = 'published'; r.artifacts[0].publishedMaster = true;
  await assert.rejects(validateRecord(repo, r), /processing/);
  r.status = 'review'; r.artifacts[0].publishedMaster = false; delete r.publication; r.reviewEvents = [];
  r.reviewEvents.push({ type: 'technical-check', artifactVersion: 'v1', artifactSha256: r.artifacts[0].sha256,
    recordedDate: '2026-10-12', evidence: 'Decode completed.', outcome: 'approved' });
  await assert.rejects(validateRecord(repo, r), /type and outcome/);
  r.reviewEvents[0].outcome = 'passed';
  const result = await validateRecord(repo, r);
  assert.equal(result.status, 'review'); assert.equal(result.publication, undefined);
  assert.equal(result.reviewEvents.some(e => e.type === 'artistic-approval'), false);
  r.artifacts = []; r.reviewEvents = []; delete r.workspace;
  delete r.descriptionPath; delete r.descriptionSha256; r.status = 'planned';
  assert.equal((await validateRecord(repo, r)).status, 'planned');
});

test('export fails closed on nested runtime fields, financial data, unsafe paths and inconsistent timing', async t => {
  const { repo, r } = await fixture(t);
  for (const edit of [v => { v.operation = { token: 'private-value' }; }, v => { v.artifacts[0].taskId = 'private-value'; },
    v => { v.cost = { total: 1 }; }, v => { v.workspace.path = '../outside'; }, v => { v.artifacts[0].path = 'C:\\outside'; },
    v => { v.briefPath = '/outside'; }, v => { v.artifacts[0].path = 'final/../source.mp4'; },
    v => { v.artifacts[0].durationSeconds = 3; }, v => { v.title = 'Budget: $' + '12'; },
    v => { v.artifacts[0].descriptionCopyPath = v.artifacts[0].path; },
    v => { v.artifacts[0].deliveryRecordPath = 'budget.json'; }]) {
    const value = structuredClone(r); edit(value);
    await assert.rejects(exportRecord(repo, value), e => !e.message.includes('private-value'));
  }
  const value = structuredClone(r); publish(value); value.publication.recordedDate = '2026-02-30';
  await assert.rejects(validateRecord(repo, value), /date/);
  assert.equal((await loadRecords(repo))[0].status, 'review');
});

test('new projects export before generated views exist and accept ordinary watch URLs', async t => {
  const { repo, r } = await fixture(t);
  await fs.unlink(path.join(repo, 'briefs/example/production.json'));
  await fs.unlink(path.join(repo, 'briefs/example/README.md'));
  publish(r); r.publication.url = 'https://www.youtube.com/watch?v=example';
  await exportRecord(repo, r);
  await buildViews(repo);
  assert.equal((await loadRecords(repo)).length, 1);
  r.publication.url += '&token=hidden';
  await assert.rejects(validateRecord(repo, r), /public-url/);
});

test('canonical hashes, source links, aliases and symlinked paths are checked', async t => {
  const { repo, r, write, description } = await fixture(t);
  await write(r.descriptionPath, description + '\n');
  await assert.rejects(validateRecord(repo, r), /hash mismatch/);
  await write(r.descriptionPath, description);
  await write(r.briefPath, '[Missing](missing.md)');
  await assert.rejects(validateRecord(repo, r), /broken link/);
  await write(r.briefPath, '# Intent\n');
  await write('briefs/example-old.md', '[Wrong](example/description.md)');
  await assert.rejects(validateRecord(repo, r), /forward/);
  await write('briefs/example-old.md', '[Moved](example/brief.md)');
  await fs.rename(path.join(repo, r.descriptionPath), path.join(repo, 'actual.md'));
  await fs.symlink(path.join(repo, 'actual.md'), path.join(repo, r.descriptionPath));
  await assert.rejects(validateRecord(repo, r), /Unsafe link/);
});

test('description sync preserves previous copies and hashes, supports dry run and refuses seals', async t => {
  const { repo, r, write, description } = await fixture(t);
  const root = r.workspace.path;
  await write(`${root}/final/v1/description.txt`, 'previous wording');
  await write(`${root}/final/v1/delivery.json`, json({ untouched: true, description: { sha256: 'old' } }));
  assert.equal((await syncDescription(repo, r, { dryRun: true })).changed.length, 2);
  assert.equal(await fs.readFile(path.join(repo, root, 'final/v1/description.txt'), 'utf8'), 'previous wording');
  const result = await syncDescription(repo, r);
  assert.equal(await fs.readFile(path.join(repo, root, 'final/v1/description.txt'), 'utf8'), description);
  assert.equal(await fs.readFile(path.join(repo, result.snapshot, 'before', root, 'final/v1/description.txt'), 'utf8'), 'previous wording');
  const delivery = JSON.parse(await fs.readFile(path.join(repo, root, 'final/v1/delivery.json')));
  assert.equal(delivery.untouched, true); assert.equal(delivery.description.sha256, sha256(description));
  await syncDescription(repo, r, { check: true });
  const revised = `Revised exact text.\n\n${REPOSITORY_URL}\n`;
  await write(r.descriptionPath, revised);
  const synced = await syncDescription(repo, r);
  assert.equal(synced.changed.length, 3);
  const updated = JSON.parse(await fs.readFile(path.join(repo, 'briefs/example/production.json')));
  assert.equal(updated.descriptionSha256, sha256(revised));
  await syncDescription(repo, updated, { check: true });
  await write(r.descriptionPath, `Later wording.\n\n${REPOSITORY_URL}\n`);
  await write(`${root}/workspace-archive-manifest.json`, '{}');
  await assert.rejects(syncDescription(repo, updated), /Sealed/);
  assert.equal(await fs.readFile(path.join(repo, root, 'final/v1/description.txt'), 'utf8'), revised);
});

test('local evidence checks actual hashes, dimensions, rational fps, frames and intact archive', async t => {
  const { repo, r, write, description } = await fixture(t);
  const root = r.workspace.path;
  await write(`${root}/final/v1/description.txt`, description);
  await write(`${root}/final/v1/delivery.json`, json({ description: { path: r.artifacts[0].descriptionCopyPath,
    repositorySource: r.descriptionPath, sha256: r.descriptionSha256 } }));
  const file = path.join(repo, root, r.artifacts[0].path);
  const generated = spawnSync('ffmpeg', ['-v', 'error', '-f', 'lavfi', '-i', 'color=black:s=16x16:r=2:d=2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', file]);
  assert.equal(generated.status, 0, generated.stderr?.toString());
  r.artifacts[0].sha256 = sha256(await fs.readFile(file));
  assert.equal((await validateLocalEvidence(repo, r)).artifacts, 1);
  const incorrect = structuredClone(r); incorrect.artifacts[0].width = 32;
  await assert.rejects(validateLocalEvidence(repo, incorrect), /dimensions/);
  const archived = await archiveWorkspace(repo, 'example-v1');
  r.workspace = { path: archived.destination, state: 'archived-verified' };
  r.archive = { manifestPath: `${archived.destination}/workspace-archive-manifest.json`, inventorySha256: archived.inventorySha256, verifiedDate: '2026-10-12' };
  assert.equal((await validateLocalEvidence(repo, r)).archiveVerified, true);
  await write(r.descriptionPath, `New wording.\n\n${REPOSITORY_URL}\n`);
  await assert.rejects(syncDescription(repo, r), /archives stay sealed/);
  await write(r.descriptionPath, description);
  await write(`${archived.destination}/added`, 'changed');
  await assert.rejects(validateLocalEvidence(repo, r), /inventory mismatch/);
});

test('filters and command checks do not mutate publication state', async t => {
  const { repo } = await fixture(t);
  assert.equal((await main(['list', '--status=review', '--title=amp'], repo)).length, 1);
  assert.equal((await main(['list', '--series=absent'], repo)).length, 0);
  await assert.rejects(main(['build', '--force'], repo), /option/);
  await assert.rejects(main(['validate', 'missing'], repo), /Unknown project/);
  assert.equal((await main(['validate'], repo)).mode, 'source-only');
});

test('accounting retains uncertain and failed reservations, distinguishes allowances and preserves report history', async t => {
  const { repo, write } = await fixture(t);
  const config = { schemaVersion: 1, projectId: 'example', asOf: '2026-10-12', sources: [{ path: 'data/ledger.json', kind: 'budget-v1', basisByEntry: { one: 'reported-usage' } }, { path: 'data/legacy.json', kind: 'episode-allowances-v1' }] };
  const ledger = { schemaVersion: 1, currency: 'USD', entries: [
    { id: 'one', category: 'motion', reservedMicros: 100, status: 'reconciled', evidence: 'Usage recorded.' },
    { id: 'two', category: 'motion', reservedMicros: 200, status: 'uncertain' },
    { id: 'three', category: 'motion', reservedMicros: 300, status: 'failed' }] };
  await write('data/ledger.json', json(ledger));
  await write('data/legacy.json', json({ allocationIsNotBilling: true, allocations: { imagery: 1 }, imageCalls: [
    { asset: 'plate', method: 'built-in imagery', billedUSD: null, allowanceUSD: 1 }], paidCalls: [] }));
  const report = await reconcileAccounting(repo, config);
  assert.equal(report.entries.length, 4); assert.equal(report.totals.confirmedMicros, 100);
  assert.equal(report.totals.knownReservedMicros, 500); assert.equal(report.totals.unresolvedEntries, 3);
  assert.equal(report.totals.confirmedTotalIsComplete, false); assert.equal(report.totals.reservationTotalIsComplete, false);
  assert.equal(report.totals.allocatedMicros, 1000000);
  const first = await writeAccounting(repo, config);
  assert.equal(first.path, 'data/accounting/example/summary.json');
  await writeAccounting(repo, config, { check: true });
  ledger.entries[1].status = 'reconciled'; ledger.entries[1].evidence = 'Usage recorded.';
  await write('data/ledger.json', json(ledger));
  await assert.rejects(writeAccounting(repo, config, { check: true }), /drift/);
  await writeAccounting(repo, config);
  assert.equal((await fs.readdir(path.join(repo, 'data/accounting/example/history'))).length, 1);
  assert.deepEqual(JSON.parse(await fs.readFile(path.join(repo, 'data/ledger.json'))), ledger);
  config.sources.push(config.sources[0]);
  await assert.rejects(reconcileAccounting(repo, config), /duplicate/);
});

test('reconciliation alone cannot turn an estimate into a confirmed charge', async t => {
  const { repo, write } = await fixture(t);
  const config = { schemaVersion: 1, projectId: 'example', asOf: '2026-10-12', sources: [{ path: 'data/ledger.json', kind: 'budget-v1' }] };
  await write('data/ledger.json', json({ schemaVersion: 1, currency: 'USD', entries: [
    { id: 'image', category: 'images', status: 'reconciled', reservedMicros: 123, evidence: 'Token estimate from saved usage.' }] }));
  let report = await reconcileAccounting(repo, config);
  assert.equal(report.totals.confirmedMicros, 0); assert.equal(report.totals.unclassifiedMicros, 123);
  config.sources[0].basisByEntry = { image: 'estimate' };
  report = await reconcileAccounting(repo, config);
  assert.equal(report.totals.confirmedMicros, 0); assert.equal(report.totals.estimatedMicros, 123);
  assert.equal(report.totals.confirmedTotalIsComplete, false);
  config.sources[0].basisByEntry.missing = 'invoiced';
  await assert.rejects(reconcileAccounting(repo, config), /basis/);
});

test('accounting rejects duplicate provider operations even across different ledgers', async t => {
  const { repo, write } = await fixture(t);
  const entry = { id: 'take', category: 'motion', status: 'submitted', reservedMicros: 100, operationName: 'fixture-operation' };
  await write('data/first.json', json({ schemaVersion: 1, currency: 'USD', entries: [entry] }));
  await write('data/copy.json', json({ schemaVersion: 1, currency: 'USD', entries: [{ ...entry, id: 'different-id' }] }));
  await assert.rejects(reconcileAccounting(repo, { schemaVersion: 1, projectId: 'example', asOf: '2026-10-12',
    sources: [{ path: 'data/first.json', kind: 'budget-v1' }, { path: 'data/copy.json', kind: 'budget-v1' }] }), /multiple accounting sources/);
});

test('migrated public records validate in a source-only copy with no ignored data', async t => {
  const { repo } = await fixture(t);
  const source = fileURLToPath(new URL('../../briefs/', import.meta.url));
  await fs.rm(path.join(repo, 'briefs'), { recursive: true });
  await fs.cp(source, path.join(repo, 'briefs'), { recursive: true });
  // Pilot briefs link existing public documentation; copy source docs, not media.
  await fs.cp(fileURLToPath(new URL('../../docs/', import.meta.url)), path.join(repo, 'docs'), { recursive: true });
  const records = await loadRecords(repo);
  assert.equal(records.find(r => r.projectId === 'verify').status, 'published');
  assert.equal(records.find(r => r.projectId === 'scary-woods-episode-05').status, 'review');
  await buildViews(repo, { check: true });
  await assert.rejects(fs.stat(path.join(repo, 'data')), { code: 'ENOENT' });
});
