import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { main as filmMain } from './film.mjs';
import { projectIdFor, migrate, walk } from './clip-import.mjs';
import { writeProjectIdentity } from './project-identity.mjs';
import { atomicJson, readJson, importClip, readClip, listUses, run, hashFile } from './clip-library.mjs';
import { configureDefault } from './clip-analysis-workflow.mjs';

function fixture(t) {
  fs.mkdirSync('data/workspace', { recursive: true });
  const repo = fs.mkdtempSync(path.resolve('data/workspace/project-identity-test-'));
  t.after(() => fs.rmSync(repo, { recursive: true, force: true }));
  return { repo, root: path.join(repo, 'data/workspace/fixture-v1'), main: args => filmMain(args, { catalogRoot: repo }) };
}
const publicRecord = (repo, root, projectId, name = projectId) => atomicJson(path.join(repo, `briefs/${name}/production.json`),
  { projectId, workspace: { path: path.relative(repo, root).split(path.sep).join('/') } });
const catalogBytes = repo => walk(path.join(repo, 'catalog')).map(file => [path.relative(repo, file), fs.readFileSync(file, 'utf8')]);
const init = (main, root, id) => main(['init', root, '2', 'Synthetic offline allocation', ...(id === undefined ? [] : [`--project-id=${id}`])]);
const request = { provider: 'runway', model: 'gen4.5', prompt: 'A synthetic color card.', durationSeconds: 2,
  aspectRatio: '16:9', resolution: '720p', seed: 0 };
const plan = { schemaVersion: 1, title: 'Identity fixture', width: 160, height: 90, fps: 24,
  shots: [{ id: 'S01', beat: 'A synthetic card', frames: 12, requestId: 'S01-v1', request }] };
function media(repo, color) {
  const file = path.join(repo, `${color}.mp4`);
  run('ffmpeg', ['-v', 'error', '-n', '-f', 'lavfi', '-i', `color=c=${color}:size=160x90:rate=24:duration=2`,
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', file]);
  return file;
}
function network(t, sources = []) {
  const previous = process.env.RUNWAYML_API_SECRET;
  process.env.RUNWAYML_API_SECRET = 'EXAMPLE_IDENTITY_FIXTURE';
  t.after(() => {
    if (previous === undefined) delete process.env.RUNWAYML_API_SECRET; else process.env.RUNWAYML_API_SECRET = previous;
  });
  let submitted = 0;
  return t.mock.method(globalThis, 'fetch', async (url, options) => {
    if (url === 'https://api.dev.runwayml.com/v1/text_to_video' && options.method === 'POST')
      return Response.json({ id: `00000000-0000-4000-8000-${String(++submitted).padStart(12, '0')}` });
    const task = /^https:\/\/api\.dev\.runwayml\.com\/v1\/tasks\/(00000000-0000-4000-8000-\d{12})$/.exec(url);
    if (task) return Response.json({ id: task[1], status: 'SUCCEEDED', createdAt: '2026-10-12T12:00:00.000Z',
      output: [`https://fixture.cloudfront.net/${Number(task[1].slice(-12))}.mp4`] });
    const download = /^https:\/\/fixture\.cloudfront\.net\/(\d+)\.mp4$/.exec(url);
    if (download && sources[Number(download[1]) - 1]) return new Response(fs.readFileSync(sources[Number(download[1]) - 1]));
    throw new Error('Unexpected network request in offline identity fixture');
  });
}

test('initialization persists explicit identity separately and refuses identity or budget replacement', async t => {
  const { repo, root, main } = fixture(t);
  const result = await main(['init', root, '2', 'Synthetic offline allocation', '--project-id', 'stable-film']);
  assert.equal(result.projectId, 'stable-film');
  assert.deepEqual(readJson(path.join(root, 'workspace.json')), { schemaVersion: 1, projectId: 'stable-film' });
  const budget = fs.readFileSync(path.join(root, 'budget.json'), 'utf8');
  assert.equal(JSON.parse(budget).authorization, 'Synthetic offline allocation');
  assert.equal(JSON.parse(budget).projectId, undefined);
  const metadata = fs.readFileSync(path.join(root, 'workspace.json'), 'utf8');
  await assert.rejects(init(main, root, 'different-film'), /identity conflict/);
  await assert.rejects(init(main, root, 'stable-film'), /Budget already exists/);
  assert.equal(fs.readFileSync(path.join(root, 'workspace.json'), 'utf8'), metadata);
  assert.equal(fs.readFileSync(path.join(root, 'budget.json'), 'utf8'), budget);
  assert.equal(projectIdFor(root, repo), 'stable-film');
  assert.equal(fs.existsSync(path.join(repo, 'catalog')), false);
});

test('invalid IDs and init options fail before creating state', async t => {
  const { repo, root, main } = fixture(t);
  for (const id of ['', 'Upper-case', 'two--hyphens', 'has_underscore', '../escape', ' leading', 'a'.repeat(101)]) {
    await assert.rejects(init(main, root, id), /Invalid project ID/);
    assert.equal(fs.existsSync(root), false);
  }
  for (const flags of [['--project-id'], ['--project-id=valid', '--project-id=second'], ['--project-idd=valid']]) {
    await assert.rejects(main(['init', root, '2', 'Synthetic offline allocation', ...flags]));
    assert.equal(fs.existsSync(root), false);
  }
  await assert.rejects(main(['init', root, 'NaN', 'Synthetic offline allocation', '--project-id=valid']), /finite/);
  await assert.rejects(main(['init', root, '2', '--project-id=valid']), /authorization/);
  assert.equal(fs.existsSync(root), false);
  publicRecord(repo, root, 'different-film');
  await assert.rejects(init(main, root, 'stable-film'), /identity conflict/);
  assert.equal(fs.existsSync(root), false);
});

test('legacy initialization keeps record and basename fallbacks without retrofitting metadata or ledgers', async t => {
  const { repo, root, main } = fixture(t);
  assert.equal((await init(main, root)).projectId, 'fixture-v1');
  const budget = fs.readFileSync(path.join(root, 'budget.json'), 'utf8');
  assert.equal(fs.existsSync(path.join(root, 'workspace.json')), false);
  publicRecord(repo, root, 'stable-film');
  assert.equal(projectIdFor(root, repo), 'stable-film');
  await assert.rejects(init(main, root, 'stable-film'), /Budget already exists/);
  assert.equal(fs.existsSync(path.join(root, 'workspace.json')), false);
  assert.equal(fs.readFileSync(path.join(root, 'budget.json'), 'utf8'), budget);
  const next = path.join(repo, 'data/workspace/fixture-v2');
  publicRecord(repo, next, 'record-first-film');
  assert.equal((await init(main, next)).projectId, 'record-first-film');
  assert.equal(fs.existsSync(path.join(next, 'workspace.json')), false);
});

test('an interrupted init resumes the saved identity without replacing it', async t => {
  const { root, main } = fixture(t);
  writeProjectIdentity(root, 'stable-film');
  const file = path.join(root, 'workspace.json'), before = fs.statSync(file);
  await assert.rejects(init(main, root, 'different-film'), /identity conflict/);
  assert.equal(fs.existsSync(path.join(root, 'budget.json')), false);
  await init(main, root, 'stable-film');
  assert.equal(fs.statSync(file).ino, before.ino);
  assert.equal(fs.statSync(file).mtimeMs, before.mtimeMs);
});

test('two initialized workspace versions share identity before records exist and preserve polling evidence', async t => {
  const { repo, root, main } = fixture(t), other = path.join(repo, 'data/workspace/fixture-v2');
  atomicJson(path.join(repo, 'data/profile.json'), { limits: { minFreeBytes: 1024 * 1024, timeoutSeconds: 60 } });
  configureDefault('data/profile.json', repo);
  const sources = [media(repo, 'red'), media(repo, 'yellow')], fetch = network(t, sources);
  const original = importClip(media(repo, 'blue'), { collections: ['original-collection'] }, repo);
  const roots = [root, other];
  for (const [index, current] of roots.entries()) {
    const version = `v${index + 1}`;
    await init(main, current, 'stable-film');
    atomicJson(path.join(current, 'film.json'), plan);
    atomicJson(path.join(current, 'qa/keep.json'), { decision: 'keep', notes: 'Synthetic reviewed card',
      sha256: original.sha256, startFrame: 0, endFrameExclusive: 48 });
    // Exercise both existing clip references and imports of legacy local source paths.
    if (index) fs.copyFileSync(path.join(repo, original.path), path.join(current, 'clips/source.mp4'));
    atomicJson(path.join(current, `edit/${version}.json`), { schemaVersion: 1, segments: [{ shotId: 'S01',
      ...(index ? { source: 'clips/source.mp4', sha256: original.sha256 } : { clipId: original.id }),
      inFrame: 0, frames: 12, decisionFile: 'qa/keep.json' }] });
    assert.equal(fs.existsSync(path.join(repo, 'briefs')), false);
    if (!index) {
      const policyFile = path.join(repo, 'data/clips/analysis/workflow.json'), policy = fs.readFileSync(policyFile);
      fs.unlinkSync(policyFile);
      await assert.rejects(main(['assemble', current, version]), /No default analysis profile/);
      assert.equal(fs.existsSync(path.join(current, 'final', version)), false, 'Missing analysis profile must block before rendering');
      fs.writeFileSync(policyFile, policy);
    }
    const delivery = await main(['assemble', current, version]);
    assert.equal(delivery.frames, 12); assert.equal(delivery.analysis.status, 'complete');
    assert.equal(delivery.analysis.clips, index + 1, 'Analysis also covers previously generated unused project takes');
    if (!index) {
      const review = await main(['review', current, version]);
      assert.equal(review.shots, 1); assert.equal(review.analysis.status, 'complete');
    }
    await main(['submit', current, 'S01']);
    const snapshotFile = path.join(current, 'operations/S01-v1.request.json');
    const snapshot = fs.readFileSync(snapshotFile), snapshotStat = fs.statSync(snapshotFile);
    const result = await main(['poll', current, 'S01']);
    assert.equal(result.sha256, hashFile(sources[index]));
    assert.deepEqual(readClip(result.clipId, repo).collections, ['stable-film']);
    const generation = readClip(result.clipId, repo).generations[0];
    const savedSnapshot = path.join(repo, 'data/clips', result.clipId, 'generations', `${generation.snapshotSha256}.json`);
    assert.deepEqual(fs.readFileSync(savedSnapshot), snapshot);
    const calls = fetch.mock.callCount(), catalog = catalogBytes(repo);
    const ledger = fs.readFileSync(path.join(current, 'budget.json'));
    for (let repeat = 0; repeat < 2; repeat++) assert.deepEqual(await main(['poll', current, 'S01']), result);
    assert.equal(fetch.mock.callCount(), calls);
    assert.deepEqual(catalogBytes(repo), catalog);
    assert.deepEqual(fs.readFileSync(path.join(current, 'budget.json')), ledger);
    assert.deepEqual(fs.readFileSync(snapshotFile), snapshot);
    assert.deepEqual(fs.readFileSync(savedSnapshot), snapshot);
    assert.equal(fs.statSync(snapshotFile).mtimeMs, snapshotStat.mtimeMs);
  }
  const uses = listUses(repo);
  assert.equal(uses.length, 2);
  assert.deepEqual(uses.map(use => use.projectId), ['stable-film', 'stable-film']);
  assert.deepEqual(uses.map(use => use.editVersion).sort(), ['edit/v1', 'edit/v2']);
  assert.deepEqual(readClip(original.id, repo).collections, ['original-collection', 'stable-film']);
  const catalog = catalogBytes(repo);
  publicRecord(repo, other, 'stable-film');
  for (const current of roots) {
    assert.equal(projectIdFor(current, repo), 'stable-film');
    await main(['poll', current, 'S01']);
  }
  assert.deepEqual(catalogBytes(repo), catalog, 'adding the public record must not change use IDs or completed clips');
});

test('conflicting public identities fail before assembly, polling or migration mutates the catalog', async t => {
  const { repo, root, main } = fixture(t);
  await init(main, root, 'stable-film');
  atomicJson(path.join(root, 'film.json'), plan);
  const fetch = network(t);
  await main(['submit', root, 'S01']);
  const snapshot = fs.readFileSync(path.join(root, 'operations/S01-v1.request.json'));
  const ledger = fs.readFileSync(path.join(root, 'budget.json'));
  const clip = importClip(media(repo, 'blue'), { collections: ['historical-label'] }, repo);
  const catalog = catalogBytes(repo);
  // A valid source outside the conflicting workspace would otherwise be imported first.
  fs.mkdirSync(path.join(repo, 'data/a-video'));
  fs.copyFileSync(media(repo, 'red'), path.join(repo, 'data/a-video/new.mp4'));
  publicRecord(repo, root, 'different-film');
  await assert.rejects(main(['assemble', root, 'v1']), /identity conflict/);
  await assert.rejects(main(['poll', root, 'S01']), /identity conflict/);
  assert.throws(() => migrate(repo), /identity conflict/);
  assert.deepEqual(catalogBytes(repo), catalog);
  assert.equal(hashFile(path.join(repo, clip.path)), clip.sha256);
  assert.equal(fs.existsSync(path.join(root, 'final/v1')), false);
  assert.equal(fetch.mock.callCount(), 1, 'only the stubbed submission should have run');
  assert.deepEqual(fs.readFileSync(path.join(root, 'operations/S01-v1.request.json')), snapshot);
  assert.deepEqual(fs.readFileSync(path.join(root, 'budget.json')), ledger);
  fs.unlinkSync(path.join(root, 'workspace.json'));
  publicRecord(repo, root, 'another-film');
  assert.throws(() => projectIdFor(root, repo), /identity conflict/, 'two matching public records must not depend on walk order');
});

test('completed legacy polling preserves collection labels after a public record is added', async t => {
  const { repo, root, main } = fixture(t);
  const fetch = network(t, [media(repo, 'red')]);
  await init(main, root);
  atomicJson(path.join(root, 'film.json'), plan);
  await main(['submit', root, 'S01']);
  const result = await main(['poll', root, 'S01']);
  assert.deepEqual(readClip(result.clipId, repo).collections, ['fixture-v1']);
  const snapshot = fs.readFileSync(path.join(root, 'operations/S01-v1.request.json'));
  const catalog = catalogBytes(repo), calls = fetch.mock.callCount();
  publicRecord(repo, root, 'stable-film');
  assert.equal(projectIdFor(root, repo), 'stable-film');
  assert.deepEqual(await main(['poll', root, 'S01']), result);
  assert.deepEqual(catalogBytes(repo), catalog);
  assert.deepEqual(fs.readFileSync(path.join(root, 'operations/S01-v1.request.json')), snapshot);
  assert.equal(fetch.mock.callCount(), calls);
});

test('invalid or symlinked workspace metadata cannot silently fall back to a public record', async t => {
  const { repo, root, main } = fixture(t);
  publicRecord(repo, root, 'stable-film');
  const file = path.join(root, 'workspace.json');
  for (const metadata of [null, [], {}, { schemaVersion: 2, projectId: 'stable-film' },
    { schemaVersion: 1, projectId: 'Bad-ID' }, { schemaVersion: 1, projectId: 'stable-film', budget: 2 }]) {
    atomicJson(file, metadata);
    await assert.rejects(main(['assemble', root, 'v1']), /Invalid/);
    await assert.rejects(main(['poll', root, 'S01']), /Invalid/);
  }
  fs.writeFileSync(file, '{broken');
  assert.throws(() => projectIdFor(root, repo), /Unreadable workspace.json/);
  fs.unlinkSync(file);
  fs.symlinkSync(path.join(repo, 'missing-identity.json'), file);
  await assert.rejects(init(main, root, 'stable-film'), /Symlink/);
  assert.equal(fs.existsSync(path.join(repo, 'catalog')), false);
  assert.equal(fs.existsSync(path.join(root, 'budget.json')), false);
});
