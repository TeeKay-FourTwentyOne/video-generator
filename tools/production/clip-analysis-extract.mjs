import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { readJson, safePath, verifyClipSnapshots, hashFile } from './clip-library.mjs';
import { privateJson, assert, now, sha, verifyFile, fileIdentity } from './clip-analysis-store.mjs';
import { execute, GzipLines, readLines, compact, seconds } from './clip-analysis-process.mjs';

const json = (c, name, value) => privateJson(path.join(c.dir, name), value);
const input = c => ['-protocol_whitelist', 'file,pipe', '-threads', String(c.config.threads), '-i', c.source];
const ff = c => ['-hide_banner', '-nostdin', '-v', 'warning', '-xerror', '-err_detect', 'explode', '-filter_threads', '1', '-filter_complex_threads', '1'];
const get = (c, step, name) => readJson(path.join(c.runDir, 'steps', step, name));
const result = (coverage, extra = {}) => ({ state: 'complete', coverage, ...extra });
export function frameSelection(indices) {
  assert(indices.length > 0 && indices.every(n => Number.isSafeInteger(n) && n >= 0), 'Invalid selected frame indices');
  // FFmpeg's expression parser has a recursion limit. A long left-associative
  // sum fails on cut-heavy clips; a balanced tree keeps depth logarithmic.
  const tree = values => values.length === 1 ? `eq(n\\,${values[0]})`
    : `(${tree(values.slice(0, Math.floor(values.length / 2)))}+${tree(values.slice(Math.floor(values.length / 2)))})`;
  return tree(indices);
}

export async function evidence(c) {
  verifyClipSnapshots(c.clip, c.repo);
  const historical = { schemaVersion: 1, evidenceType: 'historical-catalog-evidence', capturedAt: now(), sourceSha256: c.clip.sha256,
    catalogSha256: sha(c.clip), generations: c.clip.generations, analysis: c.clip.analysis, characters: c.clip.characters,
    warning: 'Retained attribution, not newly observed content or reconstructed creation evidence.' };
  json(c, 'historical.json', historical);
  const retained = [];
  for (const entry of c.config.evidence.filter(e => e.clipId === c.clip.id)) {
    const source = safePath(c.repo, entry.path); verifyFile(source, { ...fileIdentity(source), sha256: entry.sha256 });
    const name = `adjacent/${entry.sha256}${path.extname(entry.path)}`;
    fs.mkdirSync(path.dirname(path.join(c.dir, name)), { recursive: true, mode: 0o700 });
    if (!fs.existsSync(path.join(c.dir, name))) fs.copyFileSync(source, path.join(c.dir, name), fs.constants.COPYFILE_EXCL);
    assert(hashFile(path.join(c.dir, name)) === entry.sha256 && hashFile(source) === entry.sha256, 'Adjacent evidence changed during capture');
    retained.push({ ...entry, artifact: name, evidenceType: 'historical-evidence' });
  }
  json(c, 'adjacent.json', { schemaVersion: 1, retained, scope: 'Explicit allowlist only; completeness requires a dependency audit.' });
  return result({ historicalRecords: c.clip.analysis.length, adjacentFiles: retained.length });
}
export async function probe(c) {
  await execute(c.tools.ffprobe.binary, ['-v', 'error', ...input(c), '-show_streams', '-show_format', '-show_chapters', '-show_programs', '-of', 'json'], c, { stdoutFile: path.join(c.dir, 'technical.json') });
  const p = readJson(path.join(c.dir, 'technical.json'));
  assert(p.streams?.some(s => s.codec_type === 'video'), 'Input has no video stream');
  for (const s of p.streams.filter(s => ['video', 'audio'].includes(s.codec_type))) assert(/^\d+\/[1-9]\d*$/.test(s.time_base), 'Stream has no exact time base');
  return result({ streams: p.streams.length, rawContainerTags: 'private', generationTime: 'not inferred' });
}
export async function decode(c) {
  await execute(c.tools.ffmpeg.binary, [...ff(c), ...input(c), '-map', '0:v?', '-map', '0:a?', '-sn', '-dn', '-f', 'null', '-'], c);
  json(c, 'decode.json', { sourceSha256: c.clip.sha256, fullDecode: true, policy: 'All audio/video streams; fatal decoder errors fail the pass', warnings: 'See retained decoder diagnostics' });
  return result({ allAudioVideoStreams: true, fullDecode: true });
}
export async function timing(c) {
  const p = get(c, 'probe', 'technical.json'), streams = new Map(p.streams.map(s => [s.index, { streamIndex: s.index, type: s.codec_type,
    timeBase: s.time_base, frames: 0, keyframes: 0, firstPts: null, lastPts: null, lastDuration: null, timestampGaps: false, deltas: new Set() }]));
  const frames = new GzipLines(path.join(c.dir, 'frames.jsonl.gz'));
  let total = 0, issues = [];
  try {
    await execute(c.tools.ffprobe.binary, ['-v', 'error', ...input(c), '-show_frames', '-show_entries',
      'frame=media_type,stream_index,key_frame,pts,pkt_dts,best_effort_timestamp,duration,pkt_duration,pict_type,nb_samples:frame_side_data=', '-of', 'compact=p=0:nk=0'], c, { onLine: line => {
      const row = compact(line); if (!row.media_type) return;
      const s = streams.get(Number(row.stream_index)); assert(s, 'Unknown frame stream');
      assert(++total <= c.config.limits.maxFrames, 'Analysis frame limit exceeded');
      const pts = row.pts ?? row.best_effort_timestamp;
      if (!/^-?\d+$/.test(pts ?? '')) { issues.push('A decoded frame lacks a presentation timestamp'); s.timestampGaps = true; }
      else {
        if (s.lastPts !== null) { const delta = BigInt(pts) - BigInt(s.lastPts); if (delta <= 0n) { s.timestampGaps = true; issues.push('Non-increasing presentation timestamps'); } if (s.deltas.size < 32) s.deltas.add(String(delta)); }
        s.firstPts ??= pts; s.lastPts = pts; s.lastDuration = row.duration ?? row.pkt_duration ?? null;
      }
      frames.write({ ...row, streamIndex: s.streamIndex, frameIndex: s.frames++, timeBase: s.timeBase, pts: pts ?? null,
        ptsSource: row.pts ? 'pts' : 'best_effort_timestamp' });
      if (row.key_frame === '1') s.keyframes++;
    } });
  } finally { frames.close(); }
  assert([...streams.values()].filter(s => s.type === 'video').every(s => s.frames > 0), 'No decoded frames for a video stream');
  const packets = new GzipLines(path.join(c.dir, 'packets.jsonl.gz'));
  try {
    await execute(c.tools.ffprobe.binary, ['-v', 'error', ...input(c), '-show_packets', '-show_entries',
      'packet=stream_index,pts,dts,duration,size,pos,flags:packet_side_data=', '-of', 'compact=p=0:nk=0'], c, { onLine: line => {
      const r = compact(line); if (r.stream_index !== undefined) packets.write({ ...r, timeBase: streams.get(Number(r.stream_index))?.timeBase ?? null });
    } });
  } finally { packets.close(); }
  const summary = { schemaVersion: 1, sourceSha256: c.clip.sha256, streams: [...streams.values()].map(s => ({ ...s, deltas: [...s.deltas],
    variableFrameTiming: s.deltas.size > 1, lastDuration: s.lastDuration })), issues: [...new Set(issues)] };
  json(c, 'timing.json', summary);
  return result({ fullFrameTable: true, fullPacketTable: true, frames: total, packets: packets.count }, issues.length ? { state: 'needs-review', reason: summary.issues.join('; ') } : {});
}
async function metadataFilter(c, args, file, onRow) {
  const rows = new GzipLines(path.join(c.dir, file)); let row;
  const flush = () => { if (row) { rows.write(row); onRow?.(row); } };
  try {
    await execute(c.tools.ffmpeg.binary, args, c, { onLine: line => {
      const match = /^frame:(\d+)\s+pts:(-?\d+)\s+pts_time:(\S+)/.exec(line);
      if (match) { flush(); row = { frameIndex: Number(match[1]), pts: match[2], seconds: Number(match[3]), metrics: {} }; }
      else if (line.startsWith('lavfi.') && row) { const i = line.indexOf('='); assert(i > 0, 'Invalid signal metadata'); row.metrics[line.slice(0, i)] = line.slice(i + 1); }
    } }); flush();
  } finally { rows.close(); }
  return rows.count;
}
export async function signal(c) {
  const p = get(c, 'probe', 'technical.json'), timing = get(c, 'timing', 'timing.json'), settings = c.config.signal, summaries = [];
  for (const s of p.streams.filter(s => s.codec_type === 'video')) {
    const info = timing.streams.find(t => t.streamIndex === s.index), events = [], aggregates = {}, cuts = [];
    const filter = `signalstats=stat=tout+vrep+brng,scdet=threshold=${settings.sceneThreshold},blackdetect=d=${settings.blackDuration}:pix_th=${settings.blackPixelThreshold},freezedetect=n=${settings.freezeNoiseDb}dB:d=${settings.freezeSeconds},blurdetect,metadata=mode=print:file=-`;
    const count = await metadataFilter(c, [...ff(c), '-copyts', '-noautorotate', ...input(c), '-map', `0:${s.index}`, '-an', '-sn', '-dn',
      '-vf', filter, '-fps_mode', 'passthrough', '-f', 'null', '-'], `signal-${s.index}.jsonl.gz`, row => {
      for (const [key, text] of Object.entries(row.metrics)) {
        const value = Number(text); if (!Number.isFinite(value)) continue;
        const a = aggregates[key] ?? { minimum: value, maximum: value, sum: 0, samples: 0 };
        a.minimum = Math.min(a.minimum, value); a.maximum = Math.max(a.maximum, value); a.sum += value; a.samples++; aggregates[key] = a;
        if (/black_(start|end)|freeze_(start|end|duration)/.test(key)) events.push({ metric: key, value, pts: row.pts, frameIndex: row.frameIndex });
      }
      if (row.metrics['lavfi.scd.time'] !== undefined) cuts.push({ pts: row.pts, frameIndex: row.frameIndex, score: Number(row.metrics['lavfi.scd.score']) });
    });
    assert(count === info.frames, 'Signal coverage differs from decoded frame count');
    const hashes = new GzipLines(path.join(c.dir, `frame-hashes-${s.index}.jsonl.gz`)); let previous, duplicates = 0, index = 0;
    try {
      await execute(c.tools.ffmpeg.binary, [...ff(c), '-copyts', '-noautorotate', ...input(c), '-map', `0:${s.index}`, '-an', '-sn', '-dn',
        '-fps_mode', 'passthrough', '-enc_time_base', s.time_base, '-f', 'framehash', '-hash', 'sha256', '-'], c, { onLine: line => {
        if (!line.trim() || line.startsWith('#')) return;
        const fields = line.split(',').map(s => s.trim()); assert(fields.length === 6 && /^[a-f0-9]{64}$/.test(fields[5]), 'Malformed decoded frame hash');
        const duplicateOfPrevious = fields[5] === previous; if (duplicateOfPrevious) duplicates++;
        hashes.write({ streamIndex: s.index, frameIndex: index++, pts: fields[2], duration: fields[3], timeBase: s.time_base, sha256: fields[5], duplicateOfPrevious }); previous = fields[5];
      } });
    } finally { hashes.close(); }
    assert(index === info.frames, 'Decoded fingerprint coverage differs from timing');
    const boundaries = [{ pts: info.firstPts, frameIndex: 0 }, ...cuts.filter(x => x.frameIndex > 0)];
    const spans = boundaries.map((start, i) => ({ startPts: start.pts, endPts: boundaries[i + 1]?.pts ??
      (info.lastDuration && /^\d+$/.test(info.lastDuration) ? String(BigInt(info.lastPts) + BigInt(info.lastDuration)) : null),
      startFrame: start.frameIndex, endFrameExclusive: boundaries[i + 1]?.frameIndex ?? info.frames }));
    summaries.push({ streamIndex: s.index, timeBase: s.time_base, frames: count, cuts, spans, events, consecutiveDuplicateFrames: duplicates,
      aggregates: Object.fromEntries(Object.entries(aggregates).map(([k, a]) => [k, { minimum: a.minimum, maximum: a.maximum, mean: a.sum / a.samples, samples: a.samples }])) });
  }
  json(c, 'scenes.json', { schemaVersion: 1, sourceSha256: c.clip.sha256, settings, streams: summaries,
    interpretation: 'Measured signals and cut candidates. Darkness, stillness, fades, blur and duplication are not artistic defects. No optical-flow or anatomy claim.' });
  return result({ allVideoFrames: true, streams: summaries.map(s => ({ streamIndex: s.streamIndex, frames: s.frames })) });
}
export async function audio(c) {
  const p = get(c, 'probe', 'technical.json'), streams = p.streams.filter(s => s.codec_type === 'audio'), summaries = [];
  if (!streams.length) { json(c, 'audio.json', { schemaVersion: 1, presence: 'absent', streams: [] }); return { state: 'not-applicable', reason: 'No audio stream in the verified container', coverage: { presence: 'absent' } }; }
  for (const s of streams) {
    const settings = c.config.signal, events = [], envelope = []; let lastMetrics;
    const filter = `astats=metadata=1:reset=1,silencedetect=n=${settings.silenceDb}dB:d=${settings.silenceSeconds},ebur128=metadata=1:peak=true,asettb=expr=1/1000000,ametadata=mode=print:file=-`;
    const count = await metadataFilter(c, [...ff(c), '-copyts', ...input(c), '-map', `0:${s.index}`, '-vn', '-sn', '-dn', '-af', filter, '-f', 'null', '-'], `audio-${s.index}.jsonl.gz`, row => {
      lastMetrics = row.metrics;
      envelope.push({ seconds: row.seconds, pts: row.pts, rmsDb: row.metrics['lavfi.astats.Overall.RMS_level'] ?? null, peakDb: row.metrics['lavfi.astats.Overall.Peak_level'] ?? null });
      for (const [key, value] of Object.entries(row.metrics)) if (/silence_(start|end|duration)/.test(key)) events.push({ metric: key, value: Number(value), detectedAtSeconds: row.seconds });
    });
    assert(count > 0, 'Audio analysis produced no measurements');
    // Explicit filter output time base; never infer it from the 100ms reporting cadence.
    summaries.push({ streamIndex: s.index, sourceTimeBase: s.time_base, measurementTimeBase: '1/1000000', frames: count, events,
      integratedLufs: lastMetrics?.['lavfi.r128.I'] ?? null, loudnessRangeLu: lastMetrics?.['lavfi.r128.LRA'] ?? null,
      truePeak: lastMetrics?.['lavfi.r128.true_peak'] ?? null, classification: 'unrun' });
    json(c, `waveform-${s.index}.json`, { streamIndex: s.index, measurementTimeBase: '1/1000000', envelope });
    await execute(c.tools.ffmpeg.binary, [...ff(c), ...input(c), '-filter_complex', `[0:${s.index}]showwavespic=s=1200x240:split_channels=1:colors=0x7bdff2[v]`,
      '-map', '[v]', '-frames:v', '1', path.join(c.dir, `waveform-${s.index}.png`)], c);
  }
  json(c, 'audio.json', { schemaVersion: 1, sourceSha256: c.clip.sha256, presence: 'present', streams: summaries,
    interpretation: 'Quiet/silent signal is distinct from absent audio. Speech, music and event classification require separate adapters.' });
  return result({ allAudioStreams: true, streams: summaries.length });
}
export async function sampledFrames(c) {
  const p = get(c, 'probe', 'technical.json'), video = p.streams.find(s => s.codec_type === 'video'), timing = get(c, 'timing', 'timing.json');
  const info = timing.streams.find(s => s.streamIndex === video.index), scene = get(c, 'signal', 'scenes.json').streams.find(s => s.streamIndex === video.index);
  assert(!info.timestampGaps, 'Preview sampling requires reviewed presentation timestamps');
  const wanted = new Set([0, info.frames - 1]);
  for (const cut of scene.cuts) for (const n of [cut.frameIndex - 1, cut.frameIndex, cut.frameIndex + 1]) if (n >= 0 && n < info.frames) wanted.add(n);
  let grid = -Infinity, candidates = [];
  for await (const f of readLines(path.join(c.runDir, 'steps/timing/frames.jsonl.gz'))) {
    if (f.streamIndex !== video.index) continue;
    const sec = seconds(f.pts, f.timeBase);
    if (sec >= grid) { wanted.add(f.frameIndex); grid = sec + c.config.preview.gridSeconds; }
    if (wanted.has(f.frameIndex)) candidates.push({ frameIndex: f.frameIndex, streamIndex: f.streamIndex, pts: f.pts, timeBase: f.timeBase,
      seconds: sec, durationPts: f.duration ?? f.pkt_duration ?? null });
  }
  const allCount = candidates.length, limit = c.config.preview.maxKeyframes;
  if (candidates.length > limit) candidates = Array.from({ length: limit }, (_, i) => candidates[Math.round(i * (candidates.length - 1) / (limit - 1))]);
  const byIndex = new Map(candidates.map(f => [f.frameIndex, f])), seen = new Map(), selected = [], duplicates = [];
  for await (const h of readLines(path.join(c.runDir, 'steps/signal', `frame-hashes-${video.index}.jsonl.gz`))) {
    const f = byIndex.get(h.frameIndex); if (!f) continue;
    if (seen.has(h.sha256) && f.frameIndex !== 0 && f.frameIndex !== info.frames - 1) duplicates.push({ ...f, representedBy: seen.get(h.sha256) });
    else { selected.push({ ...f, decodedSha256: h.sha256 }); seen.set(h.sha256, f.frameIndex); }
  }
  return { video, info, selected, duplicates, coverage: { method: 'first-last, presentation-time grid and cut neighbors; exact decoded-frame deduplication', gridSeconds: c.config.preview.gridSeconds,
    candidateFrames: allCount, selectedFrames: selected.length, capped: allCount > limit, sourceFrames: info.frames,
    limitation: 'Sampled observations cannot certify unseen frames or brief events.' } };
}
export async function preview(c) {
  const sample = await sampledFrames(c), { video, info, selected } = sample;
  if (['smpte2084', 'arib-std-b67'].includes(video.color_transfer)) {
    json(c, 'preview.json', { schemaVersion: 1, coverage: sample.coverage, samples: [], displayConversion: 'HDR requires a reviewed tone-map profile' });
    return { state: 'needs-review', reason: 'HDR display conversion has not been qualified; no misleading SDR preview was made', coverage: sample.coverage };
  }
  const side = c.config.preview.maxSide, scale = `scale=w='trunc(iw*sar/2)*2':h=ih,scale=${side}:${side}:force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1`;
  const frameDir = path.join(c.dir, 'keyframes'); fs.mkdirSync(frameDir, { mode: 0o700 });
  const selection = frameSelection(selected.map(f => f.frameIndex));
  await execute(c.tools.ffmpeg.binary, [...ff(c), ...input(c), '-map', `0:${video.index}`, '-an', '-sn', '-vf', `select=${selection},${scale}`, '-fps_mode', 'vfr',
    '-q:v', '3', path.join(frameDir, '%06d.jpg')], c);
  const images = fs.readdirSync(frameDir).sort(); assert(images.length === selected.length, 'Keyframe selection coverage mismatch');
  selected.forEach((f, i) => { f.path = `keyframes/${images[i]}`; });
  fs.copyFileSync(path.join(c.dir, selected[0].path), path.join(c.dir, 'poster.jpg'), fs.constants.COPYFILE_EXCL);
  // Time labels are embedded in the HTML contact sheet; image pixels remain unchanged.
  const cards = selected.map(f => `<figure><img src="${f.path}" loading="lazy"><figcaption>${f.seconds.toFixed(3)} s · frame ${f.frameIndex} · PTS ${f.pts}</figcaption></figure>`).join('');
  fs.writeFileSync(path.join(c.dir, 'contact-sheet.html'), `<!doctype html><meta charset="utf-8"><title>Clip contact sheet</title><style>body{background:#15191f;color:#edf2f7;font:14px system-ui;display:flex;flex-wrap:wrap}figure{margin:8px}img{width:240px;height:200px;object-fit:contain}figcaption{padding:8px}</style>${cards}`, { flag: 'wx', mode: 0o600 });
  const start = seconds(info.firstPts, video.time_base), settings = c.config.preview;
  await execute(c.tools.ffmpeg.binary, [...ff(c), '-copyts', ...input(c), '-map', `0:${video.index}`, '-map', '0:a?', '-sn', '-dn',
    '-vf', `${scale},setpts=PTS-${info.firstPts}`, '-af', `asetpts=PTS-(${start})/TB`, '-fps_mode', 'passthrough', '-enc_time_base:v', video.time_base,
    '-c:v', 'libx264', '-threads', String(c.config.threads), '-preset', 'fast', '-crf', String(settings.crf), '-maxrate', `${settings.videoKbps}k`, '-bufsize', `${settings.videoKbps * 2}k`,
    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', `${settings.audioKbps}k`, '-avoid_negative_ts', 'disabled', '-movflags', '+faststart', path.join(c.dir, 'preview.mp4')], c);
  const map = new GzipLines(path.join(c.dir, 'preview-timing.jsonl.gz')); let count = 0;
  try {
    await execute(c.tools.ffprobe.binary, ['-v', 'error', '-protocol_whitelist', 'file,pipe', '-i', path.join(c.dir, 'preview.mp4'), '-select_streams', 'v:0', '-show_frames',
      '-show_entries', 'frame=pts,pts_time:frame_side_data=', '-of', 'compact=p=0:nk=0'], c, { onLine: line => { const r = compact(line); if (r.pts !== undefined) map.write({ sourceFrameIndex: count++, previewPts: r.pts, previewSeconds: Number(r.pts_time) }); } });
  } finally { map.close(); }
  assert(count === info.frames, 'Preview changed the decoded frame count');
  const previewIterator = readLines(path.join(c.dir, 'preview-timing.jsonl.gz'))[Symbol.asyncIterator]();
  for await (const frame of readLines(path.join(c.runDir, 'steps/timing/frames.jsonl.gz'))) {
    if (frame.streamIndex !== video.index) continue;
    const next = await previewIterator.next();
    assert(!next.done && next.value.sourceFrameIndex === frame.frameIndex
      && Math.abs(next.value.previewSeconds - (seconds(frame.pts, frame.timeBase) - start)) < 0.002,
    'Preview presentation timestamps no longer map to original frames');
  }
  assert((await previewIterator.next()).done, 'Unexpected preview timing entries');
  const subtitles = [];
  for (const s of get(c, 'probe', 'technical.json').streams.filter(s => s.codec_type === 'subtitle')) {
    if (!['mov_text', 'subrip', 'ass', 'ssa', 'webvtt', 'text'].includes(s.codec_name)) { subtitles.push({ streamIndex: s.index, state: 'needs-review', reason: 'Image subtitle extraction is not configured' }); continue; }
    const file = `subtitles-${s.index}.vtt`;
    await execute(c.tools.ffmpeg.binary, [...ff(c), ...input(c), '-map', `0:${s.index}`, '-c:s', 'webvtt', path.join(c.dir, file)], c);
    subtitles.push({ streamIndex: s.index, state: 'complete', file, timing: 'Source subtitle timestamps; no frame-rate conversion' });
  }
  json(c, 'preview.json', { schemaVersion: 1, sourceSha256: c.clip.sha256, videoStreamIndex: video.index, coverage: sample.coverage,
    samples: selected, duplicates: sample.duplicates, sourceFirstPts: info.firstPts, sourceTimeBase: video.time_base,
    previewOriginSourceSeconds: start, frameMapping: 'preview-timing.jsonl.gz joins by sourceFrameIndex to the full original timing table',
    displayConversion: { autorotate: true, sourceSampleAspectRatio: video.sample_aspect_ratio, sourceDisplayMatrix: video.side_data_list ?? [], outputSampleAspectRatio: '1:1', maxSide: side, colorTransfer: video.color_transfer ?? 'unspecified' },
    audio: 'All source audio streams retained in AAC; PTS shifted by the same video origin', subtitles });
  return result(sample.coverage, subtitles.some(s => s.state === 'needs-review') ? { state: 'needs-review', reason: 'An embedded image subtitle stream needs a qualified extraction adapter' } : {});
}
export const extractors = { evidence, probe, decode, timing, signal, audio, preview };
