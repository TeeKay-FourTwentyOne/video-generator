/** Frame-addressed local edit + inspectable delivery. Inputs are never overwritten. */
import fs from 'node:fs';
import path from 'node:path';
import { command, probe, hashFile, readJson, localPath, loadPlan } from './film.mjs';
import { atomicJson, readLedger, budgetSummary } from '../../mcp/video-generator/dist/production/ledger.js';

const validVersion = version => {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,39}$/.test(version ?? '')) throw new Error('Specify a new safe edit version, e.g. v1');
};
export function validateEdit(root, edit, plan) {
  if (edit.schemaVersion !== 1 || !Array.isArray(edit.segments) || !edit.segments.length) throw new Error('Invalid edit');
  if (budgetSummary(readLedger(path.join(root, 'budget.json'))).remainingUsd < 0) throw new Error('Budget overrun must be resolved before delivery');
  let total = 0;
  for (const segment of edit.segments) {
    if (!plan.shots.some(s => s.id === segment.shotId)) throw new Error('Edit references an unknown shot');
    const source = localPath(root, segment.source);
    if (hashFile(source) !== segment.sha256) throw new Error(`Source hash changed: ${segment.shotId}`);
    if (!Number.isInteger(segment.inFrame) || segment.inFrame < 0 || !Number.isInteger(segment.frames) || segment.frames < 1)
      throw new Error('Trims require nonnegative integer inFrame and positive frames');
    const decision = readJson(localPath(root, segment.decisionFile));
    if (!['keep', 'edit-around'].includes(decision.decision) || !decision.notes?.trim() || decision.sha256 !== segment.sha256
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
export function assemble(root, version) {
  validVersion(version);
  const plan = loadPlan(root);
  const edit = readJson(localPath(root, `edit/${version}.json`));
  const expected = validateEdit(root, edit, plan);
  const folder = localPath(root, `final/${version}`);
  // Refuse existing version, even if it is incomplete. A crash must not overwrite evidence.
  fs.mkdirSync(folder);
  const files = [];
  for (const [i, segment] of edit.segments.entries()) {
    const filename = `segment-${String(i + 1).padStart(2, '0')}.mp4`;
    const output = path.join(folder, filename);
    const filters = [`trim=start_frame=${segment.inFrame}:end_frame=${segment.inFrame + segment.frames}`,
      'setpts=PTS-STARTPTS', `scale=${plan.width}:${plan.height}:flags=lanczos`, 'setsar=1'];
    command('ffmpeg', ['-v', 'error', '-n', '-i', localPath(root, segment.source), '-an', '-vf', filters.join(','),
      '-frames:v', String(segment.frames), '-r', String(plan.fps), '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
      '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', output]);
    files.push(filename);
  }
  const list = path.join(folder, 'concat.txt');
  fs.writeFileSync(list, files.map(f => `file '${f}'`).join('\n') + '\n', { flag: 'wx' });
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
  for (const segment of edit.segments)
    if (hashFile(localPath(root, segment.source)) !== segment.sha256) throw new Error('Source mutated during rendering');
  const report = { schemaVersion: 1, version, title: plan.title, output: path.relative(root, output), sha256: hashFile(output),
    expected, probe: details, checks: { fullDecode: true, dimensions: true, frameCount: true, sourceHashes: true },
    audioReview: 'Technical verification only; listening review is separate.', budget: budgetSummary(readLedger(path.join(root, 'budget.json'))),
    edit, artisticApproval: false, publication: null };
  atomicJson(path.join(folder, 'delivery.json'), report);
  return { output: report.output, sha256: report.sha256, ...expected, checks: report.checks };
}
const escape = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export function review(root, version) {
  validVersion(version);
  const folder = localPath(root, `final/${version}`);
  const report = readJson(path.join(folder, 'delivery.json'));
  const movie = localPath(root, report.output);
  if (hashFile(movie) !== report.sha256) throw new Error('Delivery hash changed');
  const htmlPath = path.join(folder, 'review.html');
  if (fs.existsSync(htmlPath)) throw new Error('Review exists; use a new edit version');
  const plan = loadPlan(root);
  let frame = 0;
  const cards = report.edit.segments.map((s, i) => {
    const image = `shot-${i + 1}.jpg`;
    command('ffmpeg', ['-v', 'error', '-n', '-ss', String((s.inFrame + s.frames * .5) / plan.fps), '-i', localPath(root, s.source),
      '-vf', 'scale=324:-2', '-frames:v', '1', path.join(folder, image)]);
    const at = frame / plan.fps; frame += s.frames;
    const decision = readJson(localPath(root, s.decisionFile));
    return `<button data-time="${at}"><img src="${image}" alt="${escape(s.shotId)}"><strong>${escape(s.shotId)} · ${at.toFixed(2)}s</strong><span>${escape(plan.shots.find(x => x.id === s.shotId).beat)}</span><small>${escape(decision.notes)}</small></button>`;
  });
  const html = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(plan.title)} — review ${escape(version)}</title>
<style>*{box-sizing:border-box}body{margin:0;background:#101d22;color:#ece6d6;font:16px/1.55 system-ui}main{max-width:1200px;margin:0 auto;padding:30px}header{border-bottom:1px solid #405054;margin-bottom:24px}h1{font:44px Georgia;margin:0}p{color:#bac7c9}section{display:grid;grid-template-columns:minmax(280px,440px) 1fr;gap:28px}video{width:100%;max-height:82vh;background:#000;border:1px solid #405054}aside{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;align-content:start}button{text-align:left;padding:0;background:#1b2b31;color:inherit;border:1px solid #405054;border-radius:5px;overflow:hidden;cursor:pointer}button img{width:100%;display:block}strong,span,small{display:block;margin:8px}small{font-size:11px;color:#afbec0}a{color:#e8c184}footer{margin-top:24px;font-size:13px;color:#afbec0}@media(max-width:760px){section{display:block}aside{margin-top:20px}main{padding:16px}h1{font-size:32px}}</style>
<main><header><h1>${escape(plan.title)}</h1><p>${report.expected.seconds}s · ${plan.width} × ${plan.height} · ${plan.fps} fps · Native review ${escape(version)}</p></header><section><div><video id="film" controls playsinline preload="metadata" src="${escape(path.basename(movie))}"></video><p><a href="${escape(path.basename(movie))}">Open film</a> · <a href="delivery.json">Delivery evidence</a></p></div><aside>${cards.join('')}</aside></section><footer>Committed budget including reserves: $${report.budget.committedUsd.toFixed(2)} / $${report.budget.limitUsd.toFixed(2)}. Technical checks passed; artistic approval and real-time listening remain separate. All images and motion are fictional generated material.</footer></main><script>document.querySelectorAll('[data-time]').forEach(b=>b.addEventListener('click',()=>{const v=document.getElementById('film');v.currentTime=Number(b.dataset.time);v.pause()}));</script></html>`;
  fs.writeFileSync(htmlPath, html, { flag: 'wx' });
  return { review: path.relative(root, htmlPath), shots: cards.length };
}
