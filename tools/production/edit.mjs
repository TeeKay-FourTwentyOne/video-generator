/** Frame-addressed local edit + inspectable delivery. Inputs are never overwritten. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { command, probe, hashFile, readJson, localPath, loadPlan } from './film.mjs';
import { PROJECT_ROOT } from '../../mcp/video-generator/dist/utils/paths.js';
import { atomicJson, readLedger, budgetSummary } from '../../mcp/video-generator/dist/production/ledger.js';
import { importClip, resolveClip, readClip, recordUse } from './clip-library.mjs';
import { projectIdFor } from './clip-import.mjs';

export function segmentSource(root, segment, catalogRoot = PROJECT_ROOT) {
  if (segment.clipId) {
    if (segment.source !== undefined) throw new Error('Use either clipId or a legacy source path, not both');
    return resolveClip(segment.clipId, catalogRoot);
  }
  return localPath(root, segment.source);
}
const segmentHash = segment => segment.sha256 ?? segment.clipId?.slice(5);

const validVersion = version => {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,39}$/.test(version ?? '')) throw new Error('Specify a new safe edit version, e.g. v1');
};
function concatList(files, segments, fps) {
  let frames = 0, previousUs = 0;
  return files.map((file, i) => {
    frames += segments[i].frames;
    // MP4 duration metadata is rounded to milliseconds. Specify frame-derived
    // durations instead, rounding cumulative boundaries so many short cuts do
    // not accumulate even the microsecond rounding of concat's duration syntax.
    const endUs = Math.round(frames * 1000000 / fps), durationUs = endUs - previousUs;
    previousUs = endUs;
    return `file '${file}'\nduration ${(durationUs / 1000000).toFixed(6)}`;
  }).join('\n') + '\n';
}
export function validateEdit(root, edit, plan, { catalogRoot = PROJECT_ROOT } = {}) {
  if (edit.schemaVersion !== 1 || !Array.isArray(edit.segments) || !edit.segments.length) throw new Error('Invalid edit');
  if (budgetSummary(readLedger(path.join(root, 'budget.json'))).remainingUsd < 0) throw new Error('Budget overrun must be resolved before delivery');
  let total = 0;
  for (const segment of edit.segments) {
    if (!plan.shots.some(s => s.id === segment.shotId)) throw new Error('Edit references an unknown shot');
    const source = segmentSource(root, segment, catalogRoot);
    if (hashFile(source) !== segmentHash(segment)) throw new Error(`Source hash changed: ${segment.shotId}`);
    if (!Number.isInteger(segment.inFrame) || segment.inFrame < 0 || !Number.isInteger(segment.frames) || segment.frames < 1)
      throw new Error('Trims require nonnegative integer inFrame and positive frames');
    const fadeIn = segment.fadeInFrames ?? 0, fadeOut = segment.fadeOutFrames ?? 0;
    if (![fadeIn, fadeOut].every(n => Number.isInteger(n) && n >= 0) || fadeIn + fadeOut >= segment.frames)
      throw new Error('Fades are nonnegative integer frame counts that fit inside the segment');
    const decision = readJson(localPath(root, segment.decisionFile));
    if (!['keep', 'edit-around'].includes(decision.decision) || !decision.notes?.trim() || decision.sha256 !== segmentHash(segment)
        || !Number.isInteger(decision.startFrame) || !Number.isInteger(decision.endFrameExclusive)
        || decision.startFrame < 0 || decision.endFrameExclusive <= decision.startFrame)
      throw new Error(`Missing source-specific acceptance decision: ${segment.shotId}`);
    if (segment.inFrame < decision.startFrame || segment.inFrame + segment.frames > decision.endFrameExclusive)
      throw new Error(`Edit exceeds the reviewed clean range: ${segment.shotId}`);
    const video = probe(source).streams.find(s => s.codec_type === 'video');
    const [num, den] = video.avg_frame_rate.split('/').map(Number);
    if (Math.abs(num / den - plan.fps) > .001 || video.width * plan.height !== video.height * plan.width)
      throw new Error('Source fps/aspect differs; normalize explicitly and review that source first');
    const available = Number(video.nb_frames);
    if (!Number.isFinite(available) || segment.inFrame + segment.frames > available) throw new Error('Trim exceeds source frames');
    total += segment.frames;
  }
  if (edit.audio) {
    const audioPath = localPath(root, edit.audio.path);
    if (hashFile(audioPath) !== edit.audio.sha256) throw new Error('Audio source hash changed');
    if (Number(probe(audioPath).format.duration) + .001 < total / plan.fps) throw new Error('Audio is shorter than picture');
  }
  return { frames: total, seconds: total / plan.fps };
}
/** Register reused and local edit inputs before the maintained CLI analysis checkpoint. */
export function registerEditClips(root, version, { catalogRoot = PROJECT_ROOT, delivered = false } = {}) {
  validVersion(version);
  const projectId = projectIdFor(root, catalogRoot);
  if (!delivered && fs.existsSync(localPath(root, `final/${version}`))) throw new Error('EEXIST: edit version already exists');
  const edit = delivered ? readJson(localPath(root, `final/${version}/delivery.json`)).edit
    : readJson(localPath(root, `edit/${version}.json`));
  validateEdit(root, edit, loadPlan(root), { catalogRoot });
  return { projectId, clipIds: edit.segments.map(segment => importClip(segmentSource(root, segment, catalogRoot),
    { collections: [projectId] }, catalogRoot).id) };
}
export function assemble(root, version, { catalogRoot = PROJECT_ROOT } = {}) {
  validVersion(version);
  const projectId = projectIdFor(root, catalogRoot);
  const plan = loadPlan(root);
  const originalEdit = readJson(localPath(root, `edit/${version}.json`));
  const expected = validateEdit(root, originalEdit, plan, { catalogRoot });
  const folder = localPath(root, `final/${version}`);
  // Refuse existing version, even if it is incomplete. A crash must not overwrite evidence.
  fs.mkdirSync(folder);
  const edit = { ...originalEdit, segments: originalEdit.segments.map(segment => {
    const clip = segment.clipId ? { id: segment.clipId, sha256: segmentHash(segment) }
      : importClip(localPath(root, segment.source), { collections: [projectId] }, catalogRoot);
    const { source, ...rest } = segment;
    return { ...rest, clipId: clip.id, sha256: clip.sha256 };
  }) };
  const files = [];
  for (const [i, segment] of edit.segments.entries()) {
    const filename = `segment-${String(i + 1).padStart(2, '0')}.mp4`;
    const output = path.join(folder, filename);
    const filters = [`trim=start_frame=${segment.inFrame}:end_frame=${segment.inFrame + segment.frames}`,
      'setpts=PTS-STARTPTS', `scale=${plan.width}:${plan.height}:flags=lanczos`, 'setsar=1'];
    // Optional black fades are frame-addressed on the trimmed segment; they never change its length.
    // FFmpeg ramps from the frame after `s`, so the first N frames rise from black and the last N frames end on black.
    if (segment.fadeInFrames) filters.push(`fade=t=in:s=0:n=${segment.fadeInFrames}`);
    if (segment.fadeOutFrames) filters.push(`fade=t=out:s=${segment.frames - segment.fadeOutFrames - 1}:n=${segment.fadeOutFrames}`);
    command('ffmpeg', ['-v', 'error', '-n', '-i', segmentSource(root, segment, catalogRoot), '-an', '-vf', filters.join(','),
      '-frames:v', String(segment.frames), '-r', String(plan.fps), '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
      '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', output]);
    files.push(filename);
  }
  const list = path.join(folder, 'concat.txt');
  fs.writeFileSync(list, concatList(files, edit.segments, plan.fps), { flag: 'wx' });
  const output = path.join(folder, 'film.mp4');
  const args = ['-v', 'error', '-n', '-f', 'concat', '-safe', '1', '-i', list];
  if (edit.audio) args.push('-i', localPath(root, edit.audio.path), '-map', '0:v:0', '-map', '1:a:0', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000');
  else args.push('-map', '0:v:0', '-an');
  args.push('-c:v', 'copy', '-t', String(expected.seconds), '-movflags', '+faststart', output);
  command('ffmpeg', args);
  command('ffmpeg', ['-v', 'error', '-i', output, '-f', 'null', '-']);
  const details = JSON.parse(command('ffprobe', ['-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', output]));
  const video = details.streams.find(s => s.codec_type === 'video');
  if (Number(video.nb_read_frames) !== expected.frames || video.width !== plan.width || video.height !== plan.height)
    throw new Error('Rendered delivery does not match the edit contract');
  for (const segment of originalEdit.segments)
    if (hashFile(segmentSource(root, segment, catalogRoot)) !== segmentHash(segment)) throw new Error('Source mutated during rendering');
  const report = { schemaVersion: 1, version, title: plan.title, output: path.relative(root, output), sha256: hashFile(output),
    expected, probe: details, checks: { fullDecode: true, dimensions: true, frameCount: true, sourceHashes: true },
    audioReview: 'Technical verification only; listening review is separate.', budget: budgetSummary(readLedger(path.join(root, 'budget.json'))),
    edit, artisticApproval: false, publication: null };
  atomicJson(path.join(folder, 'delivery.json'), report);
  let atFrame = 0;
  for (const [index, segment] of edit.segments.entries()) {
    recordUse({ clipId: segment.clipId, projectId, editVersion: `edit/${version}`, segmentIndex: index,
      shotId: segment.shotId, status: 'rendered', evidence: 'saved-frame-edit',
      range: { unit: 'frames', start: segment.inFrame, length: segment.frames, fps: plan.fps },
      timelineStartFrame: atFrame, outputSha256: report.sha256 }, catalogRoot);
    atFrame += segment.frames;
  }
  return { output: report.output, sha256: report.sha256, ...expected, checks: report.checks };
}
const escape = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
/** `--overlay` also burns a frame/timecode copy (`film_debug.mp4`) with the existing local overlay tool. */
export function review(root, version, options = {}) {
  validVersion(version);
  const folder = localPath(root, `final/${version}`);
  const report = readJson(path.join(folder, 'delivery.json'));
  const movie = localPath(root, report.output);
  if (hashFile(movie) !== report.sha256) throw new Error('Delivery hash changed');
  const htmlPath = path.join(folder, 'review.html');
  if (fs.existsSync(htmlPath)) throw new Error('Review exists; use a new edit version');
  const plan = loadPlan(root);
  const width = report.finishing?.width ?? plan.width, height = report.finishing?.height ?? plan.height;
  let frame = 0;
  const cards = report.edit.segments.map((s, i) => {
    const image = `shot-${i + 1}.jpg`;
    command('ffmpeg', ['-v', 'error', '-n', '-ss', String((s.inFrame + s.frames * .5) / plan.fps), '-i', segmentSource(root, s, options.catalogRoot),
      '-vf', 'scale=324:-2', '-frames:v', '1', path.join(folder, image)]);
    const at = frame / plan.fps; frame += s.frames;
    const decision = readJson(localPath(root, s.decisionFile));
    return `<button data-time="${at}"><img src="${image}" alt="${escape(s.shotId)}"><strong>${escape(s.shotId)} · ${at.toFixed(2)}s</strong><span>${escape(plan.shots.find(x => x.id === s.shotId).beat)}</span><small>${escape(decision.notes)}</small></button>`;
  });
  const html = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(plan.title)} — review ${escape(version)}</title>
<style>*{box-sizing:border-box}body{margin:0;background:#101d22;color:#ece6d6;font:16px/1.55 system-ui}main{max-width:1200px;margin:0 auto;padding:30px}header{border-bottom:1px solid #405054;margin-bottom:24px}h1{font:44px Georgia;margin:0}p{color:#bac7c9}#tc{font:14px ui-monospace,monospace;color:#e8c184;margin:8px 0 0}section{display:grid;grid-template-columns:minmax(280px,440px) 1fr;gap:28px}video{width:100%;max-height:82vh;background:#000;border:1px solid #405054}aside{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;align-content:start}button{text-align:left;padding:0;background:#1b2b31;color:inherit;border:1px solid #405054;border-radius:5px;overflow:hidden;cursor:pointer}button img{width:100%;display:block}strong,span,small{display:block;margin:8px}small{font-size:11px;color:#afbec0}a{color:#e8c184}footer{margin-top:24px;font-size:13px;color:#afbec0}@media(max-width:760px){section{display:block}aside{margin-top:20px}main{padding:16px}h1{font-size:32px}}</style>
<main><header><h1>${escape(plan.title)}</h1><p>${report.expected.seconds.toFixed(2)}s · ${width} × ${height} · ${plan.fps} fps · ${report.finishing ? 'Finishing master' : 'Native review'} ${escape(version)}</p></header><section><div><video id="film" controls playsinline preload="metadata" src="${escape(path.basename(movie))}"></video><p id="tc">0.000 s · frame 0</p><p><a href="${escape(path.basename(movie))}">Open film</a> · <a href="delivery.json">Delivery evidence</a></p></div><aside>${cards.join('')}</aside></section><footer>Committed budget including reserves: $${report.budget.committedUsd.toFixed(2)} / $${report.budget.limitUsd.toFixed(2)}. Technical checks passed; artistic approval and real-time listening remain separate. All images and motion are fictional generated material.</footer></main><script>const fps=${plan.fps};const v=document.getElementById('film');const tc=document.getElementById('tc');const show=()=>{tc.textContent=v.currentTime.toFixed(3)+' s · frame '+Math.round(v.currentTime*fps)};v.addEventListener('timeupdate',show);v.addEventListener('seeked',show);document.querySelectorAll('[data-time]').forEach(b=>b.addEventListener('click',()=>{v.currentTime=Number(b.dataset.time);v.pause();show()}));</script></html>`;
  fs.writeFileSync(htmlPath, html, { flag: 'wx' });
  const result = { review: path.relative(root, htmlPath), shots: cards.length };
  if (options.overlay) {
    const debug = path.join(folder, 'film_debug.mp4');
    if (fs.existsSync(debug)) throw new Error('Overlay copy exists; use a new edit version');
    command('python3', [path.join(PROJECT_ROOT, 'tools/add-timestamp.py'), movie, debug, '--frame']);
    result.overlay = path.relative(root, debug);
  }
  return result;
}
/** Digest of one audio stream two ways: the coded packets (stream copy) and the decoded PCM. Streams, never buffers. */
async function audioDigests(file) {
  const digestOf = args => new Promise((resolve, reject) => {
    const hash = createHash('sha256');
    const p = spawn('ffmpeg', ['-v', 'error', '-nostdin', '-i', file, '-map', '0:a:0', ...args, '-'], { stdio: ['ignore', 'pipe', 'pipe'] });
    let stderr = '';
    p.stdout.on('data', chunk => hash.update(chunk));
    p.stderr.on('data', chunk => { stderr += chunk; });
    p.on('error', reject);
    p.on('close', code => code === 0 ? resolve(hash.digest('hex')) : reject(new Error(`ffmpeg failed: ${stderr.slice(-1800)}`)));
  });
  return { packets: await digestOf(['-c:a', 'copy', '-f', 'data']), pcm: await digestOf(['-f', 's16le', '-ac', '2', '-ar', '48000']) };
}
function frameCount(file) {
  const video = probe(file).streams.find(s => s.codec_type === 'video');
  if (!video) throw new Error('Counterpart has no video stream');
  const frames = Number(video.nb_frames);
  if (Number.isSafeInteger(frames) && frames > 0) return { video, frames };
  const counted = JSON.parse(command('ffprobe', ['-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'json', file]));
  return { video, frames: Number(counted.streams[0].nb_read_frames) };
}
/** Read a verified base delivery and the counterpart map for a finish; no rendering, no writes. */
export function validateFinish(root, baseVersion, newVersion, sourcesFile, { catalogRoot = PROJECT_ROOT } = {}) {
  validVersion(baseVersion); validVersion(newVersion);
  if (baseVersion === newVersion) throw new Error('The finishing version must differ from its base');
  const plan = loadPlan(root);
  const baseFolder = localPath(root, `final/${baseVersion}`);
  const base = readJson(path.join(baseFolder, 'delivery.json'));
  if (base.schemaVersion !== 1 || !Array.isArray(base.edit?.segments) || !base.edit.segments.length) throw new Error('Invalid base delivery');
  if (!Object.values(base.checks ?? {}).every(Boolean)) throw new Error('Base delivery did not pass its own checks');
  const baseMovie = localPath(root, base.output);
  if (hashFile(baseMovie) !== base.sha256) throw new Error('Base delivery hash changed');
  if (fs.existsSync(localPath(root, `final/${newVersion}`))) throw new Error('EEXIST: edit version already exists');
  const map = readJson(localPath(root, sourcesFile));
  if (map.schemaVersion !== 1 || !map.counterparts || typeof map.counterparts !== 'object' || Array.isArray(map.counterparts))
    throw new Error('Sources map needs schemaVersion 1 and a counterparts object keyed by base clip ID');
  const counterparts = new Map();
  let size = null, total = 0;
  for (const segment of base.edit.segments) {
    const clipId = segment.clipId ?? (segment.sha256 ? `clip_${segment.sha256}` : null);
    if (!clipId) throw new Error('Base segments must identify their source by clip ID');
    const target = map.counterparts[clipId];
    if (typeof target !== 'string' || !target) throw new Error(`Missing counterpart for ${segment.shotId} (${clipId})`);
    if (!counterparts.has(clipId)) {
      const file = target.startsWith('clip_') ? resolveClip(target, catalogRoot) : localPath(root, target);
      const { video, frames } = frameCount(file);
      const baseFrames = resolveCounterpartBaseFrames(root, segment, clipId, catalogRoot);
      if (frames !== baseFrames) throw new Error(`Counterpart frame count differs for ${segment.shotId}: ${frames} vs ${baseFrames}`);
      const [num, den] = video.avg_frame_rate.split('/').map(Number);
      if (Math.abs(num / den - plan.fps) > .001) throw new Error(`Counterpart frame rate differs for ${segment.shotId}`);
      if (video.width * plan.height !== video.height * plan.width) throw new Error(`Counterpart aspect ratio differs for ${segment.shotId}`);
      if (video.width < plan.width || video.height < plan.height) throw new Error(`Counterpart is smaller than the base for ${segment.shotId}`);
      if (size && (size.width !== video.width || size.height !== video.height)) throw new Error('Counterparts must share one frame size');
      size ??= { width: video.width, height: video.height };
      counterparts.set(clipId, { file, sha256: hashFile(file), frames, reference: target });
    }
    if (segment.inFrame + segment.frames > counterparts.get(clipId).frames) throw new Error('Trim exceeds counterpart frames');
    total += segment.frames;
  }
  if (Number(base.expected?.frames) !== total) throw new Error('Base delivery frame total disagrees with its segments');
  return { plan, base, baseFolder, baseMovie, counterparts, size, expected: { frames: total, seconds: total / plan.fps } };
}
function resolveCounterpartBaseFrames(root, segment, clipId, catalogRoot) {
  // The catalog record is enough; the base source bytes need not be local for a finish.
  const recorded = readClip(clipId, catalogRoot).technical?.frameCount;
  if (Number.isSafeInteger(recorded) && recorded > 0) return recorded;
  return frameCount(segmentSource(root, { ...segment, clipId, source: undefined }, catalogRoot)).frames;
}
/** Import the counterparts into the project collection before the analysis checkpoint, like registerEditClips. */
export function registerFinishClips(root, baseVersion, newVersion, sourcesFile, { catalogRoot = PROJECT_ROOT } = {}) {
  const projectId = projectIdFor(root, catalogRoot);
  const { counterparts } = validateFinish(root, baseVersion, newVersion, sourcesFile, { catalogRoot });
  return { projectId, clipIds: [...counterparts.values()].map(c => importClip(c.file, { kind: 'derived', collections: [projectId] }, catalogRoot).id) };
}
/** Finish an approved edit: the same integer frame ranges cut from higher-resolution counterparts, the base soundtrack copied unchanged. */
export async function finish(root, baseVersion, newVersion, sourcesFile, { catalogRoot = PROJECT_ROOT } = {}) {
  const projectId = projectIdFor(root, catalogRoot);
  const { plan, base, baseFolder, baseMovie, counterparts, size, expected } = validateFinish(root, baseVersion, newVersion, sourcesFile, { catalogRoot });
  const folder = localPath(root, `final/${newVersion}`);
  fs.mkdirSync(folder);
  const files = [];
  for (const [i, segment] of base.edit.segments.entries()) {
    const counterpart = counterparts.get(segment.clipId ?? `clip_${segment.sha256}`);
    const filename = `segment-${String(i + 1).padStart(2, '0')}.mp4`;
    const filters = [`trim=start_frame=${segment.inFrame}:end_frame=${segment.inFrame + segment.frames}`, 'setpts=PTS-STARTPTS',
      `scale=${size.width}:${size.height}:flags=lanczos`, 'setsar=1'];
    if (segment.fadeInFrames) filters.push(`fade=t=in:s=0:n=${segment.fadeInFrames}`);
    if (segment.fadeOutFrames) filters.push(`fade=t=out:s=${segment.frames - segment.fadeOutFrames - 1}:n=${segment.fadeOutFrames}`);
    command('ffmpeg', ['-v', 'error', '-n', '-i', counterpart.file, '-an', '-vf', filters.join(','), '-frames:v', String(segment.frames),
      '-r', String(plan.fps), '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
      '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', path.join(folder, filename)]);
    files.push(filename);
  }
  const list = path.join(folder, 'concat.txt');
  fs.writeFileSync(list, concatList(files, base.edit.segments, plan.fps), { flag: 'wx' });
  const output = path.join(folder, 'film.mp4');
  const hasAudio = probe(baseMovie).streams.some(s => s.codec_type === 'audio');
  const args = ['-v', 'error', '-n', '-f', 'concat', '-safe', '1', '-i', list];
  // The soundtrack is the approved one: packets are copied, never re-encoded or trimmed.
  if (hasAudio) args.push('-i', baseMovie, '-map', '0:v:0', '-map', '1:a:0', '-c:a', 'copy');
  else args.push('-map', '0:v:0', '-an');
  // Concat can omit primaries/transfer tags even when every encoded segment has them.
  // Complete both H.264 VUI and container tags without re-encoding picture or sound.
  args.push('-c:v', 'copy', '-bsf:v', 'h264_metadata=video_full_range_flag=0:colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1',
    '-color_range', 'tv', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', output);
  command('ffmpeg', args);
  command('ffmpeg', ['-v', 'error', '-i', output, '-f', 'null', '-']);
  const details = JSON.parse(command('ffprobe', ['-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', output]));
  const video = details.streams.find(s => s.codec_type === 'video');
  if (Number(video.nb_read_frames) !== expected.frames || video.width !== size.width || video.height !== size.height)
    throw new Error('Rendered finish does not match the base edit contract');
  if (video.color_range !== 'tv' || video.color_space !== 'bt709' || video.color_primaries !== 'bt709' || video.color_transfer !== 'bt709')
    throw new Error('Rendered finish is missing its BT.709 color tags');
  const audio = hasAudio ? { base: await audioDigests(baseMovie), output: await audioDigests(output) } : null;
  if (audio && (audio.base.packets !== audio.output.packets || audio.base.pcm !== audio.output.pcm)) throw new Error('Finished soundtrack differs from the base delivery');
  if (!hasAudio && details.streams.some(s => s.codec_type === 'audio')) throw new Error('Finish gained an audio stream the base does not have');
  for (const c of counterparts.values()) if (hashFile(c.file) !== c.sha256) throw new Error('Counterpart mutated during rendering');
  if (hashFile(baseMovie) !== base.sha256) throw new Error('Base delivery mutated during rendering');
  const registered = new Map([...counterparts].map(([clipId, c]) => [clipId, importClip(c.file, { kind: 'derived', collections: [projectId] }, catalogRoot)]));
  const segments = base.edit.segments.map((segment, index) => {
    const baseClipId = segment.clipId ?? `clip_${segment.sha256}`, clip = registered.get(baseClipId);
    return { index, shotId: segment.shotId, baseClipId, clipId: clip.id, sha256: clip.sha256, counterpart: counterparts.get(baseClipId).reference,
      inFrame: segment.inFrame, frames: segment.frames };
  });
  let description = null;
  if (base.description?.path) {
    // The publication text travels with every master; sync-description then finds this copy by the record's artifact entry.
    const copy = fs.readFileSync(localPath(root, base.description.path));
    if (hashFile(localPath(root, base.description.path)) !== base.description.sha256) throw new Error('Base description copy hash changed; run sync-description first');
    fs.writeFileSync(path.join(folder, 'description.txt'), copy, { flag: 'wx' });
    description = { ...base.description, path: `final/${newVersion}/description.txt` };
  }
  const report = { schemaVersion: 1, version: newVersion, title: plan.title, output: path.relative(root, output), sha256: hashFile(output),
    expected, probe: details,
    checks: { fullDecode: true, dimensions: true, frameCount: true, colorTags: true, baseHash: true, counterpartHashes: true,
      audioPackets: hasAudio ? true : null, audioPcm: hasAudio ? true : null },
    audioReview: 'Technical verification only; listening review is separate.', budget: budgetSummary(readLedger(path.join(root, 'budget.json'))),
    edit: base.edit,
    finishing: { role: 'finishing-master', baseVersion, baseOutput: base.output, baseSha256: base.sha256, width: size.width, height: size.height,
      segments, audio: hasAudio ? { streamCopied: true, packetsSha256: { base: audio.base.packets, output: audio.output.packets },
        pcmSha256: { base: audio.base.pcm, output: audio.output.pcm } } : null,
      method: 'Integer frame ranges cut from prepared counterparts by the maintained editor; no neural upscaling inside the command.' },
    artisticApproval: false, publication: null, ...(description ? { description } : {}) };
  atomicJson(path.join(folder, 'delivery.json'), report);
  let atFrame = 0;
  for (const segment of segments) {
    recordUse({ clipId: segment.clipId, projectId, editVersion: `finish/${newVersion}`, segmentIndex: segment.index,
      shotId: segment.shotId, status: 'rendered', evidence: 'saved-finishing-master',
      range: { unit: 'frames', start: segment.inFrame, length: segment.frames, fps: plan.fps },
      timelineStartFrame: atFrame, outputSha256: report.sha256 }, catalogRoot);
    atFrame += segment.frames;
  }
  importClip(output, { kind: 'delivery', collections: [projectId] }, catalogRoot);
  return { output: report.output, sha256: report.sha256, ...expected, width: size.width, height: size.height, checks: report.checks,
    base: { version: baseVersion, sha256: base.sha256 }, counterparts: [...registered.values()].map(c => c.id), description: description?.path ?? null };
}
