/** Original presentation time mapping, independent of a VAD-shortened timeline. */
import fs from 'node:fs';
import path from 'node:path';
import { readJson } from './clip-library.mjs';
import { assert, privateJson, fileIdentity } from './clip-analysis-store.mjs';
import { execute, readLines, seconds } from './clip-analysis-process.mjs';

export function audioMapping(frames, stream, sampleCount) {
  assert(frames.length && frames.every(f => /^-?\d+$/.test(f.pts) && Number(f.nb_samples) > 0), 'Missing decoded audio timing');
  const rate = Number(stream.sample_rate), origin = seconds(frames[0].pts, stream.time_base), gaps = [];
  const [timeNum, timeDen] = stream.time_base.split('/').map(Number), tolerance = Math.max(1 / rate, timeNum / timeDen) + 0.00001;
  assert(Number.isSafeInteger(rate) && rate > 0 && Number.isSafeInteger(sampleCount) && sampleCount > 0, 'Invalid resampled audio measurements');
  let end = origin;
  for (const frame of frames) {
    const start = seconds(frame.pts, stream.time_base), delta = start - end;
    assert(delta >= -tolerance, 'Overlapping audio timestamps require a qualified mapping');
    if (delta > tolerance) gaps.push({ startSeconds: end, endSeconds: start, treatment: 'silence inserted by timestamp-aware resampling' });
    end = start + Number(frame.nb_samples) / rate;
  }
  assert(Math.abs(sampleCount / 16000 - (end - origin)) <= 0.002, 'Resampled audio duration does not match source presentation timing');
  return { schemaVersion: 1, streamIndex: stream.index, originPts: frames[0].pts, sourceTimeBase: stream.time_base,
    sourceOriginSeconds: origin, sourceEndSeconds: end, sourceSampleRate: rate, sampleRate: 16000, sampleCount, gaps, timestampToleranceSeconds: tolerance,
    offsetTimeline: 'original-resampled-audio', silenceRemoved: false,
    filter: 'asetpts=PTS-STARTPTS,aresample=16000:async=1:min_hard_comp=0.000001:first_pts=0',
    sourceTimingEvidence: '../timing/frames.jsonl.gz',
    mapping: 'source time = exact first decoded source PTS + resampled sample offset / 16000; VAD original offsets use this unshortened audio' };
}

function sourceTime(samples, mapping) {
  const [n, d] = mapping.sourceTimeBase.split('/').map(BigInt);
  return { numerator: String(BigInt(mapping.originPts) * n * 16000n + BigInt(samples) * d), denominator: String(d * 16000n) };
}
function span(offsets, mapping) {
  assert(Number.isSafeInteger(offsets?.from) && Number.isSafeInteger(offsets?.to) && offsets.from >= 0 && offsets.to >= offsets.from,
    'Missing or invalid original-audio speech offsets');
  // The pinned Silero implementation rounds its final probability window up to
  // 512 samples. Original-time token getters may add one 10 ms timestamp tick.
  // Retain that estimate, but expose only its intersection with decoded audio.
  assert(offsets.to <= mapping.sampleCount / 16 + 512 / 16 + 10, 'Speech offset exceeds resampled audio');
  const from = Math.min(offsets.from * 16, mapping.sampleCount), to = Math.min(offsets.to * 16, mapping.sampleCount);
  return { rawOffsets: { ...offsets, unit: 'milliseconds', timeline: 'original-resampled-audio' },
    startSeconds: mapping.sourceOriginSeconds + from / 16000, endSeconds: mapping.sourceOriginSeconds + to / 16000,
    sourceStart: sourceTime(from, mapping), sourceEnd: sourceTime(to, mapping),
    ...(offsets.to * 16 > mapping.sampleCount ? { boundaryAdjustment: {
      treatment: 'Intersection with decoded audio; original model offsets retained',
      startTrimmedMilliseconds: offsets.from - from / 16, endTrimmedMilliseconds: offsets.to - to / 16,
      reason: 'Pinned VAD final-window padding and centisecond token resolution can extend beyond available audio',
    } } : {}) };
}
export function normalizeSpeech(raw, mapping, { sourceSha256, model }) {
  assert(raw?.schemaVersion === 2 && raw.contract === 'whisper.cpp-original-time-v1' && raw.sampleRate === mapping.sampleRate
    && raw.sampleCount === mapping.sampleCount && raw.timing?.unit === 'milliseconds'
    && raw.timing.segments === 'original-resampled-audio' && raw.timing.tokens === 'original-resampled-audio'
    && raw.timing.rawTokens === 'vad-processed-audio' && Array.isArray(raw.vad) && Array.isArray(raw.transcription),
  'Unqualified Whisper/VAD timestamp contract');
  const base = { sourceSha256, evidenceType: 'model-observation', streamIndex: mapping.streamIndex,
    confidence: { source: model, value: null, interpretation: 'uncalibrated model score' } };
  const vadSpans = raw.vad.map((v, i) => ({ ...base, index: i, ...span(v, mapping), classification: 'speech-candidate' }));
  for (let i = 1; i < vadSpans.length; i++) assert(vadSpans[i].startSeconds >= vadSpans[i - 1].endSeconds, 'VAD spans overlap or are unordered');
  const evidenceIntervals = timing => {
    const intervals = vadSpans.filter(v => v.endSeconds > timing.startSeconds && v.startSeconds < timing.endSeconds)
      .map(v => ({ startSeconds: Math.max(v.startSeconds, timing.startSeconds), endSeconds: Math.min(v.endSeconds, timing.endSeconds), vadIndex: v.index }));
    const duration = timing.endSeconds - timing.startSeconds, supported = intervals.reduce((n, v) => n + v.endSeconds - v.startSeconds, 0);
    const warnings = [];
    if (timing.boundaryAdjustment) warnings.push('Model endpoint exceeds decoded audio; the displayed range is its intersection with available samples, not a verified boundary');
    if (duration - supported > .03) warnings.push('Estimated boundary crosses audio outside VAD speech spans; do not treat this as a continuous word or speech interval');
    return { vadIntersections: intervals, crossesVadGap: duration - supported > .03,
      timingWarning: warnings.join('; ') || null };
  };
  const observations = raw.transcription.flatMap((s, segmentIndex) => {
    assert(typeof s.text === 'string' && Array.isArray(s.tokens), 'Malformed speech segment');
    const timing = span(s.offsets, mapping);
    if (!s.text.trim()) return [];
    const tokens = s.tokens.map((t, tokenIndex) => {
      assert(typeof t.bytesHex === 'string' && /^(?:[a-f0-9]{2})*$/.test(t.bytesHex) && typeof t.special === 'boolean'
        && Number.isInteger(t.id) && Number.isFinite(t.p) && t.p >= 0 && t.p <= 1, 'Malformed speech token');
      return { ...t, tokenIndex, ...(t.offsets === null ? { timingState: 'unavailable' } : { ...span(t.offsets, mapping),
        rawOffsets: { ...t.rawOffsets, unit: 'milliseconds', timeline: 'vad-processed-audio' },
        originalAudioOffsets: t.offsets, timingState: 'estimated' }) };
    });
    const words = []; let group = [];
    const flush = () => {
      if (!group.length) return;
      const text = Buffer.concat(group.map(t => Buffer.from(t.bytesHex, 'hex'))).toString('utf8');
      if (text.trim()) {
        const timed = group.every(t => t.timingState === 'estimated');
        const timing = timed ? span({ from: group[0].offsets.from, to: Math.max(...group.map(t => t.offsets.to)) }, mapping) : {};
        const evidence = timed ? evidenceIntervals(timing) : {};
        words.push({ text, tokenIndices: group.map(t => t.tokenIndex), timingState: timed ? timing.boundaryAdjustment ? 'ambiguous-source-boundary' : evidence.crossesVadGap ? 'ambiguous-vad-gap' : 'estimated' : 'unavailable',
          ...timing, ...evidence,
          grouping: 'whitespace-delimited token group; not a forced alignment or universal word tokenizer' });
      }
      group = [];
    };
    for (const t of tokens.filter(t => !t.special)) {
      if (/^\s/u.test(Buffer.from(t.bytesHex, 'hex').toString('utf8'))) flush();
      group.push(t);
    }
    flush();
    return [{ ...base, ...timing, ...evidenceIntervals(timing), segmentIndex, text: s.text, tokens, words,
      languageHypothesis: raw.language?.hypothesis ?? null, languageConfidence: null,
      timingInterpretation: 'Model-estimated boundaries; original-audio API mapping, not a verified alignment' }];
  });
  assert(vadSpans.length || !observations.length, 'ASR returned text without any VAD speech evidence');
  return { observations, report: { streamIndex: mapping.streamIndex, mapping, vadSpans, language: raw.language,
    asrState: observations.length ? 'transcript-candidate' : 'empty-transcript', vadState: vadSpans.length ? 'speech-candidates' : 'no-speech-detected',
    timingWarnings: observations.flatMap(o => o.words.filter(w => w.timingState !== 'estimated').map(w => ({ segmentIndex: o.segmentIndex, word: w.text, timingState: w.timingState }))),
    contentClassification: { speech: 'unreviewed', music: 'unrun', sungVocals: 'unrun', silence: 'see separate signal measurements' },
    limitations: 'VAD and ASR do not establish silence, absence of vocals, or an audio content classification' } };
}

export async function transcribe(c, adapter, streams) {
  const observations = [], reports = [];
  for (const stream of streams.filter(s => s.codec_type === 'audio')) {
    const frames = [];
    for await (const f of readLines(path.join(c.runDir, 'steps/timing/frames.jsonl.gz'))) if (f.streamIndex === stream.index) frames.push(f);
    const pcm = path.join(c.dir, `audio-${stream.index}.f32le`), request = path.join(c.dir, `speech-${stream.index}.request.json`), output = path.join(c.dir, `speech-${stream.index}.raw.json`);
    await execute(c.tools.ffmpeg.binary, ['-nostdin', '-v', 'error', '-xerror', '-threads', String(c.config.threads), '-filter_threads', '1',
      '-protocol_whitelist', 'file,pipe', '-copyts', '-i', c.source, '-map', `0:${stream.index}`, '-vn', '-sn', '-dn',
      '-af', 'asetpts=PTS-STARTPTS,aresample=16000:async=1:min_hard_comp=0.000001:first_pts=0', '-ac', '1', '-c:a', 'pcm_f32le', '-f', 'f32le', pcm], c);
    const identity = fileIdentity(pcm), mapping = audioMapping(frames, stream, identity.bytes / 4);
    mapping.resampledAudio = { ...identity, format: 'mono little-endian float32', retained: false };
    privateJson(path.join(c.dir, `audio-${stream.index}.mapping.json`), mapping);
    privateJson(request, { schemaVersion: 1, audioFile: pcm, settings: adapter.settings, threads: c.config.threads });
    await execute(adapter.executable, [request, output], c, { networkDenied: true });
    const result = normalizeSpeech(readJson(output), mapping, { sourceSha256: c.clip.sha256, model: adapter.identity.model });
    observations.push(...result.observations); reports.push({ ...result.report, rawOutput: path.basename(output) });
    fs.rmSync(pcm); // Only this attempt's disposable resampling; preserve failed attempts.
  }
  return { schemaVersion: 1, speechEvidenceVersion: 2, observations, reports };
}
