#!/usr/bin/env node
/** Small agent-facing CLI. JSON on stdout, errors on stderr. No implicit paid work. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { createLedger, readLedger, reserveSpend, reconcileSpend, updateSpend, budgetSummary, atomicJson } from '../../mcp/video-generator/dist/production/ledger.js';
import { qualifyVeo } from '../../mcp/video-generator/dist/production/veo-spec.js';
import { submitVeoGeneration, pollVeoOperation, downloadVeoVideo } from '../../mcp/video-generator/dist/clients/veo.js';
import { PROJECT_ROOT, VIDEO_DIR } from '../../mcp/video-generator/dist/utils/paths.js';

export const hashFile = p => createHash('sha256').update(fs.readFileSync(p)).digest('hex');
export const readJson = p => JSON.parse(fs.readFileSync(p, 'utf8'));
function rejectSymlinks(base, target) {
  // Existing ancestors matter even when the final output does not exist yet.
  for (let p = target; p !== base; p = path.dirname(p)) {
    let stat;
    try { stat = fs.lstatSync(p); } catch (e) { if (e.code !== 'ENOENT') throw e; }
    if (stat?.isSymbolicLink()) throw new Error('Symlink artifact paths are not supported');
    if (path.dirname(p) === p) throw new Error('Artifact escapes workspace');
  }
}
export function workspace(input) {
  if (!input) throw new Error('Specify a workspace under data/workspace/<slug>');
  const p = path.resolve(input);
  const base = path.join(PROJECT_ROOT, 'data', 'workspace');
  if (!p.startsWith(base + path.sep)) throw new Error('New production state must live under data/workspace/<slug>');
  rejectSymlinks(PROJECT_ROOT, p);
  return p;
}
export function localPath(root, relative) {
  if (typeof relative !== 'string' || !relative || path.isAbsolute(relative)) throw new Error('Artifact path must be workspace-relative');
  const p = path.resolve(root, relative);
  if (!p.startsWith(root + path.sep)) throw new Error('Artifact escapes workspace');
  rejectSymlinks(root, p);
  return p;
}
export function command(binary, args) {
  const p = spawnSync(binary, args, { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
  if (p.error || p.status !== 0) throw new Error(`${binary} failed: ${p.error?.message || p.stderr.slice(-1800)}`);
  return p.stdout;
}
export function probe(p) {
  return JSON.parse(command('ffprobe', ['-v', 'error', '-show_format', '-show_streams', '-of', 'json', p]));
}
export function loadPlan(root) {
  const plan = readJson(localPath(root, 'film.json'));
  if (plan.schemaVersion !== 1 || !plan.title || !Array.isArray(plan.shots) || !plan.shots.length
      || ![24, 25, 30].includes(plan.fps) || !Number.isInteger(plan.width) || !Number.isInteger(plan.height)
      || plan.width < 16 || plan.height < 16 || plan.width % 2 || plan.height % 2)
    throw new Error('Invalid film plan');
  if (new Set(plan.shots.map(s => s.id)).size !== plan.shots.length) throw new Error('Duplicate shot IDs');
  for (const s of plan.shots) {
    if (typeof s.id !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(s.id) || !s.beat || !Number.isInteger(s.frames) || s.frames <= 0)
      throw new Error('Each shot needs a stable ID, story beat and positive frame count');
  }
  return plan;
}
export function shotRequest(root, id) {
  const plan = loadPlan(root);
  const shot = plan.shots.find(s => s.id === id);
  if (!shot?.request) throw new Error('Shot has no generation request');
  const request = { ...shot.request, requestId: shot.requestId ?? `${id}-v1`, budgetFile: localPath(root, 'budget.json') };
  if (request.promptFile) {
    request.prompt = fs.readFileSync(localPath(root, request.promptFile), 'utf8'); delete request.promptFile;
  }
  for (const k of ['firstFramePath', 'lastFramePath']) if (request[k]) request[k] = localPath(root, request[k]);
  if (request.aspectRatio !== `${plan.width / gcd(plan.width, plan.height)}:${plan.height / gcd(plan.width, plan.height)}`)
    throw new Error('Shot aspect ratio differs from film');
  return { shot, request };
}
function gcd(a, b) { return b ? gcd(b, a % b) : a; }

export async function main(argv) {
  const [verb, location, ...args] = argv;
  if (!verb || verb === 'help') return { commands: [
    'doctor', 'init WORKSPACE LIMIT_USD AUTHORIZATION', 'status WORKSPACE', 'plan WORKSPACE',
    'submit WORKSPACE SHOT_ID', 'poll WORKSPACE SHOT_ID',
    'reserve WORKSPACE ID USD CATEGORY PURPOSE', 'reconcile WORKSPACE ID USD EVIDENCE',
    'image WORKSPACE REQUEST_JSON', 'assemble WORKSPACE VERSION', 'review WORKSPACE VERSION'
  ], note: 'Only submit/image perform generation. Poll retrieves an existing operation; it never submits.' };
  if (verb === 'doctor') {
    const config = readJson(path.join(PROJECT_ROOT, 'data/config.json'));
    return { node: process.version, ffmpeg: command('ffmpeg', ['-version']).split('\n')[0],
      ffprobe: !!command('ffprobe', ['-version']), googleCredentialsConfigured: !!config.veoServiceAccountPath,
      note: 'Read-only local checks; no installation or provider requests performed.' };
  }
  const root = workspace(location);
  const budget = localPath(root, 'budget.json');
  if (verb === 'init') {
    createLedger(budget, Number(args[0]), args.slice(1).join(' '));
    for (const d of ['refs', 'prompts', 'clips', 'qa', 'edit', 'final', 'operations']) fs.mkdirSync(localPath(root, d), { recursive: true });
    return { workspace: path.relative(PROJECT_ROOT, root), ...budgetSummary(readLedger(budget)) };
  }
  if (verb === 'status') return { ...budgetSummary(readLedger(budget)), reservations: readLedger(budget).entries.map(({ id, category, status, reservedMicros }) => ({ id, category, status, usd: reservedMicros / 1e6 })) };
  if (verb === 'reserve') return reserveSpend(budget, { id: args[0], usd: Number(args[1]), category: args[2], note: args.slice(3).join(' '), fingerprint: createHash('sha256').update(args.join('\n')).digest('hex') });
  if (verb === 'reconcile') return reconcileSpend(budget, args[0], Number(args[1]), args.slice(2).join(' '));
  if (verb === 'plan') {
    const plan = loadPlan(root);
    const shots = plan.shots.map(s => ({ id: s.id, beat: s.beat, frames: s.frames,
      quote: s.request ? qualifyVeo(shotRequest(root, s.id).request) : null }));
    return { title: plan.title, width: plan.width, height: plan.height, fps: plan.fps,
      seconds: plan.shots.reduce((n, s) => n + s.frames, 0) / plan.fps,
      videoQuoteUsd: shots.reduce((n, s) => n + (s.quote?.estimatedUsd ?? 0), 0), shots,
      budget: budgetSummary(readLedger(budget)), note: 'Dry run. No reservations or API calls.' };
  }
  if (verb === 'submit') {
    const { request } = shotRequest(root, args[0]);
    const result = await submitVeoGeneration(request);
    atomicJson(localPath(root, `operations/${request.requestId}.json`), result);
    return { shot: args[0], requestId: request.requestId, status: 'submitted', model: result.model };
  }
  if (verb === 'poll') {
    const { request } = shotRequest(root, args[0]);
    const entry = readLedger(budget).entries.find(e => e.id === request.requestId);
    if (!entry?.operationName) throw new Error('No known operation to poll; do not resubmit');
    const record = localPath(root, `operations/${request.requestId}.asset.json`);
    if (fs.existsSync(record)) {
      const asset = readJson(record);
      if (hashFile(localPath(root, asset.path)) !== asset.sha256) throw new Error('Downloaded source changed');
      return { shot: args[0], status: 'complete', path: asset.path, sha256: asset.sha256 };
    }
    const result = await pollVeoOperation(entry.operationName, entry.model);
    if (!result.done) return { shot: args[0], status: 'processing' };
    if (result.error) {
      updateSpend(budget, entry.id, { status: 'failed', evidence: result.error });
      throw new Error(result.error);
    }
    const output = localPath(root, `clips/${request.requestId}.mp4`);
    if (fs.existsSync(output)) throw new Error('Unrecorded output exists; inspect it before recovery');
    const video = await downloadVeoVideo(result);
    fs.copyFileSync(path.join(VIDEO_DIR, video.filename), output, fs.constants.COPYFILE_EXCL);
    const asset = { path: path.relative(root, output), sha256: hashFile(output), probe: probe(output) };
    atomicJson(record, asset);
    updateSpend(budget, entry.id, { status: 'complete', evidence: `Downloaded SHA256 ${asset.sha256}` });
    return { shot: args[0], status: 'complete', path: asset.path, sha256: asset.sha256 };
  }
  if (verb === 'image') {
    const { generateAnchor } = await import('./google-image.mjs');
    return generateAnchor(root, readJson(localPath(root, args[0])));
  }
  if (verb === 'assemble' || verb === 'review') {
    const { assemble, review } = await import('./edit.mjs');
    return verb === 'assemble' ? assemble(root, args[0]) : review(root, args[0]);
  }
  throw new Error(`Unknown command: ${verb}`);
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).then(result => process.stdout.write(JSON.stringify(result, null, 2) + '\n')).catch(e => {
    process.stderr.write(JSON.stringify({ error: e.message }) + '\n'); process.exitCode = 1;
  });
}
