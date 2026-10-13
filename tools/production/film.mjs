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
import { miniMaxCredentialsConfigured, prepareMiniMaxRequest, submitMiniMaxGeneration, pollMiniMaxOperation,
  downloadMiniMaxVideo, listMiniMaxTasks, recoverMiniMaxOperation } from '../../mcp/video-generator/dist/clients/minimax.js';
import { runwayCredentialsConfigured, prepareRunwayRequest, submitRunwayGeneration, pollRunwayOperation,
  downloadRunwayVideo, getRunwayAccount, recoverRunwayOperation } from '../../mcp/video-generator/dist/clients/runway.js';
import { loadConfig } from '../../mcp/video-generator/dist/utils/config.js';
import { PROJECT_ROOT } from '../../mcp/video-generator/dist/utils/paths.js';
import { importClip, resolveClip, generationMetadata } from './clip-library.mjs';
import { readGenerationSnapshot, snapshotHash } from './generation-snapshot.mjs';

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
function shotAttempt(root, id) {
  const plan = loadPlan(root);
  const shot = plan.shots.find(s => s.id === id);
  if (!shot) throw new Error('Unknown shot');
  const requestId = shot.requestId ?? `${id}-v1`;
  if (typeof requestId !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$/.test(requestId))
    throw new Error('Shot requires a stable request ID');
  return { plan, shot, requestId };
}
export function shotRequest(root, id) {
  const { plan, shot, requestId } = shotAttempt(root, id);
  if (!shot.request) throw new Error('Shot has no generation request');
  const request = { ...shot.request, requestId, budgetFile: localPath(root, 'budget.json') };
  videoProvider(request);
  if (request.promptFile) {
    request.prompt = fs.readFileSync(localPath(root, request.promptFile), 'utf8'); delete request.promptFile;
  }
  for (const k of ['firstFramePath', 'lastFramePath']) if (request[k]) request[k] = localPath(root, request[k]);
  for (const k of ['referenceImagePaths', 'referenceVideoPaths', 'referenceAudioPaths']) {
    if (request[k] !== undefined) {
      if (!Array.isArray(request[k])) throw new Error('Reference paths must be arrays');
      request[k] = request[k].map(p => localPath(root, p));
    }
  }
  if (request.aspectRatio !== `${plan.width / gcd(plan.width, plan.height)}:${plan.height / gcd(plan.width, plan.height)}`)
    throw new Error('Shot aspect ratio differs from film');
  return { shot, request };
}
export function videoProvider(request) {
  const provider = request.provider ?? 'veo';
  if (!['veo', 'minimax', 'runway'].includes(provider)) throw new Error('Unsupported video provider; choose veo, minimax or runway');
  if (provider === 'veo' && ['referenceImagePaths', 'referenceVideoPaths', 'referenceAudioPaths', 'promptExpansionMode'].some(k => request[k] !== undefined))
    throw new Error('MiniMax controls require provider: minimax');
  return provider;
}
function gcd(a, b) { return b ? gcd(b, a % b) : a; }
/** `--wait` alone waits up to 20 minutes; `--wait=N` bounds it; `--interval=N` sets the cadence (default 20 s, minimum 5). */
export function pollOptions(flags) {
  let waitSeconds = 0, intervalSeconds = 20;
  for (const f of flags) {
    const m = /^--(wait|interval)(?:=(\d+))?$/.exec(f);
    if (!m) throw new Error(`Unknown poll option: ${f}`);
    if (m[1] === 'wait') waitSeconds = m[2] === undefined ? 1200 : Number(m[2]);
    else { if (m[2] === undefined) throw new Error('--interval needs seconds'); intervalSeconds = Math.max(5, Number(m[2])); }
  }
  return { waitSeconds, intervalSeconds };
}

/** `image` takes one or more request files; `--reconcile` reduces each reservation to its saved-usage estimate
 *  right after the image is saved; `--spacing=N` seconds between requests (default 10, minimum 0). */
export function imageOptions(args) {
  let reconcile = false, spacingSeconds = 10;
  const files = [];
  for (const a of args) {
    if (a === '--reconcile') reconcile = true;
    else if (/^--spacing=\d+$/.test(a)) spacingSeconds = Number(a.slice(10));
    else if (a.startsWith('--')) throw new Error(`Unknown image option: ${a}`);
    else files.push(a);
  }
  if (!files.length) throw new Error('Specify at least one image request file');
  return { files, reconcile, spacingSeconds };
}
export async function main(argv, { catalogRoot = PROJECT_ROOT } = {}) {
  const [verb, location, ...args] = argv;
  if (!verb || verb === 'help') return { commands: [
    'doctor', 'init WORKSPACE LIMIT_USD AUTHORIZATION', 'status WORKSPACE', 'plan WORKSPACE',
    'minimax-tasks [PAGE]', 'recover-minimax WORKSPACE SHOT_ID TASK_ID EVIDENCE',
    'runway-account', 'recover-runway WORKSPACE SHOT_ID TASK_ID EVIDENCE', 'reconcile-runway WORKSPACE SHOT_ID',
    'submit WORKSPACE SHOT_ID', 'poll WORKSPACE SHOT_ID [--wait[=SECONDS]] [--interval=SECONDS]',
    'reserve WORKSPACE ID USD CATEGORY PURPOSE', 'reconcile WORKSPACE ID USD EVIDENCE',
    'image WORKSPACE REQUEST_JSON [MORE_JSON...] [--reconcile] [--spacing=SECONDS]', 'reconcile-image WORKSPACE IMAGE_ID',
    'join-anchor WORKSPACE SOURCE FRAME OUTPUT.png',
    'assemble WORKSPACE VERSION', 'review WORKSPACE VERSION [--overlay]', 'clips search|show|resolve|analytics [QUERY_OR_ID]'
  ], note: 'Only submit/image perform generation. Poll retrieves an existing operation; it never submits. Several image requests run in order, spaced apart; --reconcile (or reconcile-image) reduces an image reservation to its saved-usage list-price estimate.' };
  if (verb === 'clips') {
    if (!['search', 'show', 'resolve', 'analytics'].includes(location)) throw new Error('Use npm run clips for catalog mutations');
    return (await import('./clips.mjs')).main([location, ...args], catalogRoot);
  }
  if (verb === 'doctor') {
    const config = loadConfig();
    return { node: process.version, ffmpeg: command('ffmpeg', ['-version']).split('\n')[0],
      ffprobe: !!command('ffprobe', ['-version']), googleCredentialsConfigured: !!config.veoServiceAccountPath,
      minimaxCredentialsConfigured: miniMaxCredentialsConfigured(),
      runwayCredentialsConfigured: runwayCredentialsConfigured(),
      note: 'Read-only local checks; no installation or provider requests performed.' };
  }
  if (verb === 'minimax-tasks') {
    const result = await listMiniMaxTasks(location === undefined ? 1 : Number(location));
    return { ...result, tasks: result.tasks.map(({ video, ...task }) => task),
      note: 'Read-only provider query covering the last 7 days. Task IDs require manual matching before recovery.' };
  }
  if (verb === 'runway-account') return { ...await getRunwayAccount(), note: 'Read-only API balance and model limits; no generation.' };
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
      quote: s.request ? (() => {
        const { request } = shotRequest(root, s.id);
        const provider = videoProvider(request);
        return provider === 'minimax' ? prepareMiniMaxRequest(request).quote
          : provider === 'runway' ? prepareRunwayRequest(request).quote : qualifyVeo(request);
      })() : null }));
    return { title: plan.title, width: plan.width, height: plan.height, fps: plan.fps,
      seconds: plan.shots.reduce((n, s) => n + s.frames, 0) / plan.fps,
      videoQuoteUsd: shots.reduce((n, s) => n + (s.quote?.estimatedUsd ?? 0), 0), shots,
      budget: budgetSummary(readLedger(budget)), note: 'Dry run. No reservations or API calls.' };
  }
  if (verb === 'submit') {
    const { request } = shotRequest(root, args[0]);
    const provider = videoProvider(request);
    // Resolve before the client writes its journal; this also rejects symlinked operation directories.
    localPath(root, `operations/${request.requestId}.json`);
    localPath(root, `operations/${request.requestId}.request.json`);
    const result = provider === 'minimax' ? await submitMiniMaxGeneration(request)
      : provider === 'runway' ? await submitRunwayGeneration(request) : await submitVeoGeneration(request);
    return { shot: args[0], requestId: request.requestId, status: 'submitted', model: result.model };
  }
  if (verb === 'recover-minimax') {
    const { request } = shotRequest(root, args[0]);
    if (videoProvider(request) !== 'minimax') throw new Error('Recovery command requires a MiniMax shot');
    localPath(root, `operations/${request.requestId}.json`);
    const result = await recoverMiniMaxOperation(request, args[1], args.slice(2).join(' '));
    return { shot: args[0], requestId: request.requestId, status: 'recovered', model: result.model };
  }
  if (verb === 'recover-runway') {
    const { request } = shotRequest(root, args[0]);
    if (videoProvider(request) !== 'runway') throw new Error('Recovery command requires a Runway shot');
    localPath(root, `operations/${request.requestId}.json`);
    const result = await recoverRunwayOperation(request, args[1], args.slice(2).join(' '));
    return { shot: args[0], requestId: request.requestId, status: 'recovered', model: result.model };
  }
  if (verb === 'reconcile-runway') {
    const { requestId } = shotAttempt(root, args[0]);
    const entry = readLedger(budget).entries.find(e => e.id === requestId);
    const result = readJson(localPath(root, `operations/${requestId}.poll.json`));
    if (entry?.category !== 'runway' || !entry.operationName
      || !result.done || result.operationName !== entry.operationName || !Number.isSafeInteger(result.costCredits) || result.costCredits < 0)
      throw new Error('Reconciliation requires a matching terminal Runway task with nonnegative reported cost');
    const usd = result.costCredits / 100;
    return { shot: args[0], usd, entry: reconcileSpend(budget, requestId, usd,
      `Runway terminal task reports cost.credits=${result.costCredits}; USD 0.01/credit; saved in operations/${requestId}.poll.json. Excludes tax.`) };
  }
  if (verb === 'poll') {
    const { requestId } = shotAttempt(root, args[0]);
    const entry = readLedger(budget).entries.find(e => e.id === requestId);
    if (!entry?.operationName) throw new Error('No known operation to poll; do not resubmit');
    const record = localPath(root, `operations/${requestId}.asset.json`);
    const operationFile = localPath(root, `operations/${requestId}.json`);
    const operation = fs.existsSync(operationFile) ? readJson(operationFile) : {};
    if (operation.operationName && operation.operationName !== entry.operationName)
      throw new Error('Operation record differs from the reserved operation');
    localPath(root, `operations/${requestId}.request.json`);
    const snapshot = readGenerationSnapshot(budget, requestId, { provider: entry.category,
      fingerprint: entry.fingerprint, model: entry.model, snapshotSha256: operation.snapshotSha256 });
    // New attempts never reread mutable prompts/references or fill defaults from a later plan.
    const request = snapshot ? null : shotRequest(root, args[0]).request;
    const provider = snapshot?.provider ?? videoProvider(request);
    if (!['veo', 'minimax', 'runway'].includes(provider) || entry.category !== provider)
      throw new Error('Provider differs from the existing reservation');
    if (!snapshot && provider === 'runway' && prepareRunwayRequest(request).fingerprint !== entry.fingerprint)
      throw new Error('Runway request changed after submission; restore its original plan before polling');
    const generationSource = operation.prompt ? 'saved-operation-request' : 'film-plan';
    const generationRequest = snapshot ?? { ...(operation.prompt ? operation.quote ?? {} : request),
      ...operation.parameters, prompt: operation.prompt ?? request.prompt,
      provider, model: entry.model, seed: entry.seed, createdAt: operation.createdAt };
    const metadata = { kind: 'source', collections: [path.basename(root)], generationSnapshot: snapshot,
      generations: snapshot ? [] : [generationMetadata(generationRequest, generationSource)] };
    if (fs.existsSync(record)) {
      let asset = readJson(record);
      const source = asset.clipId ? resolveClip(asset.clipId, catalogRoot) : localPath(root, asset.path);
      if (hashFile(source) !== asset.sha256) throw new Error('Downloaded source changed');
      if (!asset.clipId || snapshot) {
        const clip = importClip(source, metadata, catalogRoot);
        asset = { ...asset, ...(!asset.clipId ? { legacyPath: asset.path } : {}), path: clip.path, clipId: clip.id,
          ...(snapshot ? { snapshotSha256: snapshotHash(snapshot) } : {}) };
        atomicJson(record, asset);
      }
      if (!['complete', 'reconciled'].includes(entry.status))
        updateSpend(budget, entry.id, { status: 'complete', evidence: `Recovered downloaded SHA256 ${asset.sha256}` });
      return { shot: args[0], status: 'complete', path: asset.path, clipId: asset.clipId, sha256: asset.sha256 };
    }
    // --wait keeps polling the SAME operation at a bounded cadence; it never submits.
    const { waitSeconds, intervalSeconds } = pollOptions(args.slice(1));
    const started = Date.now();
    const poll = async () => {
      const result = provider === 'minimax' ? await pollMiniMaxOperation(entry.operationName, entry.model)
        : provider === 'runway' ? await pollRunwayOperation(entry.operationName, entry.model)
        : await pollVeoOperation(entry.operationName, entry.model);
      // Veo inline media is already preserved as the master; do not duplicate base64 in the journal.
      atomicJson(localPath(root, `operations/${requestId}.poll.json`), provider === 'veo'
        ? { ...result, video: result.video ? { uri: result.video.gcsUri ?? result.video.uri, inline: !!result.video.bytesBase64Encoded } : undefined } : result);
      return result;
    };
    let result = await poll();
    while (!result.done && waitSeconds > 0 && (Date.now() - started) / 1000 < waitSeconds) {
      await new Promise(r => setTimeout(r, Math.min(Math.max(provider === 'minimax' ? 10 : 5, intervalSeconds) * 1000,
        Math.max(0, waitSeconds * 1000 - (Date.now() - started)))));
      if (Date.now() - started >= waitSeconds * 1000) break;
      result = await poll();
    }
    if (!result.done) return { shot: args[0], status: 'processing', waitedSeconds: Math.round((Date.now() - started) / 1000) };
    if (result.error) {
      updateSpend(budget, entry.id, { status: 'failed', evidence: result.error });
      throw new Error(result.error);
    }
    const incoming = path.join(catalogRoot, 'data/clips/.incoming');
    fs.mkdirSync(incoming, { recursive: true });
    const output = path.join(incoming, `${createHash('sha256').update(root + requestId + entry.operationName).digest('hex')}.mp4`);
    let clip;
    if (provider === 'veo') {
      const video = await downloadVeoVideo(result, { request: generationRequest, generationSource, generationSnapshot: snapshot,
        collections: metadata.collections, catalogRoot });
      clip = { id: video.clipId, sha256: video.sha256, path: video.path };
    } else {
      // Resume a completed download after interruption; never generate again to repair ingestion.
      if (!fs.existsSync(output)) {
        if (provider === 'minimax') await downloadMiniMaxVideo(result, output);
        else await downloadRunwayVideo(result, output);
      }
      clip = importClip(output, metadata, catalogRoot);
    }
    const asset = { clipId: clip.id, path: clip.path, sha256: clip.sha256, probe: probe(resolveClip(clip.id, catalogRoot)),
      ...(snapshot ? { snapshotSha256: snapshotHash(snapshot) } : {}) };
    if (provider !== 'veo' && !asset.probe.streams?.some(s => s.codec_type === 'video' && s.width > 0 && s.height > 0))
      throw new Error('Provider output has no usable video stream; preserved for inspection');
    atomicJson(record, asset);
    if (fs.existsSync(output)) fs.unlinkSync(output);
    updateSpend(budget, entry.id, { status: 'complete', evidence: `Downloaded SHA256 ${asset.sha256}` });
    return { shot: args[0], status: 'complete', path: asset.path, clipId: asset.clipId, sha256: asset.sha256 };
  }
  if (verb === 'image') {
    const { generateAnchor } = await import('./google-image.mjs');
    const { imageUsageCost } = await import('./image-rates.mjs');
    const { files, reconcile, spacingSeconds } = imageOptions(args);
    const results = [];
    for (const [i, file] of files.entries()) {
      // The endpoint answers HTTP 429 to rapid batches; space sequential requests, never retry one.
      if (i) await new Promise(r => setTimeout(r, spacingSeconds * 1000));
      const request = readJson(localPath(root, file));
      let result;
      try { result = await generateAnchor(root, request); }
      catch (e) { throw new Error(`${e.message}${results.length ? ` (completed before the failure: ${results.map(r => r.output).join(', ')})` : ''}`); }
      if (reconcile) {
        // Same evidence as reconcile-image: the usage record this request just saved.
        const cost = imageUsageCost(readJson(localPath(root, `operations/${request.id}.usage.json`)));
        result.reconciled = { usd: cost.usd, evidence: cost.evidence, entry: reconcileSpend(budget, request.id, cost.usd, cost.evidence) };
      }
      results.push(result);
    }
    return files.length === 1 ? results[0] : results;
  }
  if (verb === 'reconcile-image') {
    // Evidence-based only: the saved usage record written by the image route is the input; no network.
    const { imageUsageCost } = await import('./image-rates.mjs');
    const cost = imageUsageCost(readJson(localPath(root, `operations/${args[0]}.usage.json`)));
    return { ...cost, entry: reconcileSpend(budget, args[0], cost.usd, cost.evidence) };
  }
  if (verb === 'join-anchor') {
    if (args.length !== 3) throw new Error('join-anchor needs SOURCE FRAME OUTPUT.png');
    const { joinAnchor } = await import('./join-anchor.mjs');
    return joinAnchor(root, args[0], Number(args[1]), args[2], { catalogRoot });
  }
  if (verb === 'assemble' || verb === 'review') {
    const { assemble, review } = await import('./edit.mjs');
    if (verb === 'assemble') return assemble(root, args[0], { catalogRoot });
    const flags = args.slice(1);
    for (const f of flags) if (f !== '--overlay') throw new Error(`Unknown review option: ${f}`);
    return review(root, args[0], { overlay: flags.includes('--overlay'), catalogRoot });
  }
  throw new Error(`Unknown command: ${verb}`);
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).then(result => process.stdout.write(JSON.stringify(result, null, 2) + '\n')).catch(e => {
    process.stderr.write(JSON.stringify({ error: e.message }) + '\n'); process.exitCode = 1;
  });
}
