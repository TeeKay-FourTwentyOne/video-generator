#!/usr/bin/env node
/*
 * study-audio.cjs — turn a transcript into a single study-audio MP3 via ElevenLabs.
 *
 * Pipeline: copy transcript into data/study/<slug>/ -> estimate credits/cost ->
 * (gate on real-overage cost cap) -> chunk -> TTS each chunk -> concat -> optional GCS upload.
 *
 * ElevenLabs is a flat monthly subscription billed in CREDITS (= characters of input
 * text). Generation that fits inside the remaining monthly quota is FREE. Only the
 * portion that spills past the quota is a real dollar charge (usage-based billing).
 * The spending cap therefore gates on estimated OVERAGE dollars, not the notional
 * quota-share value of within-plan credits.
 *
 * Usage:
 *   node tools/study-audio.cjs <transcriptPath> [options]
 *   node tools/study-audio.cjs <transcriptPath> --estimate          # dry run, never spends
 *
 * Options:
 *   --estimate            Print the estimate and exit. No generation, no spend.
 *   --slug=NAME           Folder name under data/study (default: derived from filename).
 *   --voice=ID            ElevenLabs voice_id (default: Bella, the "AI Explains" voice).
 *   --model=ID            model_id (default: eleven_turbo_v2_5 = 0.5 credits/char).
 *   --speed=N             Voice speed 0.7-1.2 (default: 1.0; explainers used ~1.1).
 *   --stability=N         Voice stability (default: 0.5).
 *   --similarity=N        similarity_boost (default: 0.75).
 *   --max-cost=N          Real-overage USD cap (default: 10). Within-quota work is free.
 *   --confirm             Authorize generation even if est. overage exceeds the cap.
 *   --upload / --no-upload  Push final MP3 to GCS + print a 7-day signed URL (default: upload).
 *   --raw                 Do NOT strip markdown before narration (default: strip).
 *   --move                Delete the source transcript after copying it in (default: copy only).
 *   --chunk=N             Max characters per TTS request (default: 2500).
 *   --json                Machine-readable output.
 *
 * Exit codes: 0 ok · 1 usage/setup error · 10 blocked by cost cap · 3 runtime error.
 */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const cfg = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'config.json'), 'utf8'));
const KEY = cfg.elevenLabsKey;
if (!KEY) { console.error('elevenLabsKey not set in data/config.json'); process.exit(1); }

// Monthly subscription price ($/month) per tier, for the overage-cost estimate.
// Quota denominator is read live from the subscription (character_limit).
const PRICE = { starter: 5, creator: 22, pro: 99, scale: 330 };
const DEFAULT_VOICE = 'hpp4J3VqNfWAUOO0d1Us'; // Bella - Professional, Bright, Warm ("AI Explains")
const DEFAULT_MODEL = 'eleven_turbo_v2_5';     // 0.5 credits/char

// ---- args ----
const argv = process.argv.slice(2);
const positional = [];
const opt = {};
for (const a of argv) {
  const m = a.match(/^--([^=]+)(?:=(.*))?$/);
  if (m) opt[m[1]] = m[2] === undefined ? true : m[2];
  else positional.push(a);
}
const transcriptPath = positional[0];
if (!transcriptPath) {
  console.error('Usage: study-audio.cjs <transcriptPath> [--estimate] [options]');
  process.exit(1);
}
if (!fs.existsSync(transcriptPath)) {
  console.error(`Transcript not found: ${transcriptPath}`);
  process.exit(1);
}

const ESTIMATE_ONLY = !!opt.estimate;
const VOICE = opt.voice || DEFAULT_VOICE;
const MODEL = opt.model || DEFAULT_MODEL;
const SPEED = opt.speed !== undefined ? parseFloat(opt.speed) : 1.0;
const STABILITY = opt.stability !== undefined ? parseFloat(opt.stability) : 0.5;
const SIMILARITY = opt.similarity !== undefined ? parseFloat(opt.similarity) : 0.75;
const MAX_COST = opt['max-cost'] !== undefined ? parseFloat(opt['max-cost']) : 10;
const CONFIRM = !!opt.confirm;
const UPLOAD = opt['no-upload'] ? false : true; // default upload
const RAW = !!opt.raw;
const MOVE = !!opt.move;
const CHUNK = opt.chunk !== undefined ? parseInt(opt.chunk, 10) : 2500;
const JSON_OUT = !!opt.json;
const WPM = 150; // narration pace baseline for duration estimate

const slug = (opt.slug || path.basename(transcriptPath).replace(/\.[^.]+$/, ''))
  .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'study';

// ---- text prep ----
const rawText = fs.readFileSync(transcriptPath, 'utf8');

function stripMarkdown(s) {
  return s
    .replace(/```[\s\S]*?```/g, ' ')          // fenced code blocks
    .replace(/`([^`]+)`/g, '$1')              // inline code
    .replace(/^\s{0,3}#{1,6}\s+/gm, '')       // heading markers
    .replace(/^\s{0,3}>\s?/gm, '')            // blockquote markers
    .replace(/^\s*[-*+]\s+/gm, '')            // bullet markers
    .replace(/^\s*\d+\.\s+/gm, '')            // numbered list markers
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')     // images
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')  // links -> text
    .replace(/(\*\*|__)(.*?)\1/g, '$2')       // bold
    .replace(/(\*|_)(.*?)\1/g, '$2')          // italic
    .replace(/^\s*([-*_]\s*){3,}$/gm, '')     // horizontal rules
    .replace(/\n{3,}/g, '\n\n')               // collapse blank runs
    .trim();
}

const text = RAW ? rawText.trim() : stripMarkdown(rawText);
const charCount = text.length;
const wordCount = text.split(/\s+/).filter(Boolean).length;

// ---- estimate ----
const creditsPerChar = /flash|turbo/i.test(MODEL) ? 0.5 : 1.0;
const credits = Math.round(charCount * creditsPerChar);
const durationMin = wordCount / (WPM * SPEED);

async function getSubscription() {
  const r = await fetch('https://api.elevenlabs.io/v1/user/subscription', { headers: { 'xi-api-key': KEY } });
  if (!r.ok) throw new Error(`subscription HTTP ${r.status}: ${await r.text()}`);
  return r.json();
}

function fmtDuration(min) {
  const s = Math.round(min * 60);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

// ---- chunking ----
function chunkText(s, max) {
  const paras = s.split(/\n{2,}/);
  const out = [];
  let buf = '';
  const push = () => { if (buf.trim()) out.push(buf.trim()); buf = ''; };
  for (const para of paras) {
    if ((buf + '\n\n' + para).length <= max) { buf = buf ? buf + '\n\n' + para : para; continue; }
    push();
    if (para.length <= max) { buf = para; continue; }
    // paragraph too long: split on sentence boundaries
    const sentences = para.match(/[^.!?]+[.!?]+(\s|$)|[^.!?]+$/g) || [para];
    for (const sent of sentences) {
      if ((buf + ' ' + sent).length <= max) { buf = buf ? buf + ' ' + sent : sent; continue; }
      push();
      if (sent.length <= max) { buf = sent; continue; }
      // single sentence too long: hard split
      for (let i = 0; i < sent.length; i += max) out.push(sent.slice(i, i + max).trim());
    }
  }
  push();
  return out;
}

async function ttsChunk(chunk, prev, next, outPath) {
  const body = {
    text: chunk,
    model_id: MODEL,
    voice_settings: { stability: STABILITY, similarity_boost: SIMILARITY, speed: SPEED },
  };
  if (prev) body.previous_text = prev;
  if (next) body.next_text = next;
  const url = `https://api.elevenlabs.io/v1/text-to-speech/${VOICE}?output_format=mp3_44100_128`;
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'xi-api-key': KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`TTS HTTP ${r.status}: ${await r.text()}`);
  fs.writeFileSync(outPath, Buffer.from(await r.arrayBuffer()));
}

(async () => {
  const sub = await getSubscription();
  const used = sub.character_count || 0;
  const limit = sub.character_limit || 0;
  const remaining = Math.max(0, limit - used);
  const overageCredits = Math.max(0, credits - remaining);
  const pricePerChar = (PRICE[sub.tier] || 0) / (limit || 1);
  const overageUsd = overageCredits * pricePerChar;
  const withinQuota = overageCredits === 0;

  const est = {
    slug, transcript: transcriptPath, model: MODEL, voice: VOICE, speed: SPEED,
    chars: charCount, words: wordCount, credits_per_char: creditsPerChar, credits,
    est_duration: fmtDuration(durationMin), est_duration_min: +durationMin.toFixed(2),
    subscription: { tier: sub.tier, used, limit, remaining },
    within_quota: withinQuota, overage_credits: overageCredits,
    est_overage_usd: +overageUsd.toFixed(2), cost_cap_usd: MAX_COST,
  };

  if (JSON_OUT && ESTIMATE_ONLY) { console.log(JSON.stringify(est, null, 2)); return; }

  // ---- report ----
  console.log(`study-audio  "${slug}"`);
  console.log(`  source     ${transcriptPath}`);
  console.log(`  text       ${charCount.toLocaleString()} chars · ${wordCount.toLocaleString()} words${RAW ? ' (raw)' : ' (markdown stripped)'}`);
  console.log(`  model      ${MODEL}  (${creditsPerChar} credit/char)  · voice ${VOICE} · speed ${SPEED}`);
  console.log(`  credits    ${credits.toLocaleString()}   → est. audio ~${fmtDuration(durationMin)}`);
  console.log(`  plan       ${sub.tier}: ${used.toLocaleString()}/${limit.toLocaleString()} used · ${remaining.toLocaleString()} remaining this cycle`);
  if (withinQuota) {
    console.log(`  cost       FREE — fits within subscription quota (no overage)`);
  } else {
    console.log(`  cost       ${overageCredits.toLocaleString()} credits past quota → est. ~$${overageUsd.toFixed(2)} real overage (cap $${MAX_COST.toFixed(2)})`);
  }

  if (ESTIMATE_ONLY) { console.log(`  (estimate only — nothing generated)`); return; }

  // ---- cost gate ----
  if (!withinQuota && overageUsd > MAX_COST && !CONFIRM) {
    console.error(`\nBLOCKED: est. overage $${overageUsd.toFixed(2)} exceeds cap $${MAX_COST.toFixed(2)}.`);
    console.error(`Re-run with --confirm to authorize, or raise --max-cost.`);
    process.exit(10);
  }

  // ---- stage transcript into data/study/<slug>/ ----
  const studyDir = path.join(ROOT, 'data', 'study', slug);
  fs.mkdirSync(studyDir, { recursive: true });
  const ext = path.extname(transcriptPath) || '.txt';
  const stagedTranscript = path.join(studyDir, `transcript${ext}`);
  fs.copyFileSync(transcriptPath, stagedTranscript);
  if (MOVE && path.resolve(transcriptPath) !== path.resolve(stagedTranscript)) fs.unlinkSync(transcriptPath);
  console.log(`\n  staged     ${path.relative(ROOT, stagedTranscript)}${MOVE ? ' (source moved)' : ''}`);

  // ---- generate chunks ----
  const chunks = chunkText(text, CHUNK);
  const chunkDir = path.join(studyDir, 'chunks');
  fs.mkdirSync(chunkDir, { recursive: true });
  console.log(`  chunks     ${chunks.length} (≤${CHUNK} chars each)`);
  const chunkPaths = [];
  for (let i = 0; i < chunks.length; i++) {
    const outPath = path.join(chunkDir, `chunk_${String(i).padStart(3, '0')}.mp3`);
    process.stdout.write(`  tts        ${i + 1}/${chunks.length}\r`);
    await ttsChunk(chunks[i], chunks[i - 1], chunks[i + 1], outPath);
    chunkPaths.push(outPath);
  }
  console.log(`\n  tts        done (${chunks.length} chunks)`);

  // ---- concat ----
  const finalPath = path.join(studyDir, `${slug}.mp3`);
  if (chunkPaths.length === 1) {
    fs.copyFileSync(chunkPaths[0], finalPath);
  } else {
    const listPath = path.join(chunkDir, 'concat.txt');
    fs.writeFileSync(listPath, chunkPaths.map((p) => `file '${p.replace(/'/g, "'\\''")}'`).join('\n'));
    execFileSync('ffmpeg', ['-y', '-f', 'concat', '-safe', '0', '-i', listPath, '-c', 'copy', finalPath], { stdio: 'ignore' });
  }
  let finalDur = '';
  try {
    finalDur = execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', finalPath]).toString().trim();
  } catch { /* ignore */ }
  const mb = (fs.statSync(finalPath).size / 1048576).toFixed(1);
  console.log(`  audio      ${path.relative(ROOT, finalPath)}  (${mb} MB${finalDur ? `, ${fmtDuration(parseFloat(finalDur) / 60)}` : ''})`);

  // ---- upload ----
  let signedUrl = null;
  if (UPLOAD) {
    try {
      const out = execFileSync('node', [path.join(__dirname, 'gcp', 'share.cjs'), finalPath, `study/${slug}/${slug}.mp3`, 'audio/mpeg', '7']).toString();
      const m = out.match(/SIGNED_URL (\S+)/);
      signedUrl = m ? m[1] : null;
      console.log(`  uploaded   gs://.../study/${slug}/${slug}.mp3  (7-day signed URL)`);
      if (signedUrl) console.log(`\n  ${signedUrl}`);
    } catch (e) {
      console.error(`  upload failed: ${e.message}`);
    }
  }

  if (JSON_OUT) console.log('\n' + JSON.stringify({ ...est, final: path.relative(ROOT, finalPath), duration: finalDur, signed_url: signedUrl }, null, 2));
})().catch((e) => { console.error(e.message || e); process.exit(3); });
