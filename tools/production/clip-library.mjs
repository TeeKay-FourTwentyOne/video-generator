/** Shared, local-only clip catalog. Media identity is the SHA-256 of the original bytes. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash, randomUUID } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { scanText } from '../privacy-check.mjs';
import { readSnapshot, snapshotHash, validateSnapshot, writeSnapshot } from './generation-snapshot.mjs';

export const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const VIDEO_EXTENSIONS = new Set(['.mp4', '.mov', '.webm', '.mkv', '.m4v', '.avi']);
export const digest = value => createHash('sha256').update(value).digest('hex');
export const canonical = value => Array.isArray(value) ? value.map(canonical) : value && typeof value === 'object'
  ? Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])])) : value;
const equal = (a, b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
export const readJson = file => JSON.parse(fs.readFileSync(file, 'utf8'));
export function hashFile(file) {
  const hash = createHash('sha256'), buffer = Buffer.alloc(1024 * 1024), fd = fs.openSync(file, 'r');
  try { for (let n; (n = fs.readSync(fd, buffer, 0, buffer.length, null));) hash.update(buffer.subarray(0, n)); }
  finally { fs.closeSync(fd); }
  return hash.digest('hex');
}
export function safePath(root, relative) {
  if (typeof relative !== 'string' || !relative || path.isAbsolute(relative) || relative.includes('\\')) throw new Error('Expected relative catalog path');
  const base = path.resolve(root), file = path.resolve(base, relative);
  if (!file.startsWith(base + path.sep)) throw new Error('Catalog path escapes root');
  for (let p = file; p !== base; p = path.dirname(p)) {
    try { if (fs.lstatSync(p).isSymbolicLink()) throw new Error('Symlink catalog paths are not supported'); }
    catch (e) { if (e.code !== 'ENOENT') throw e; }
  }
  return file;
}
export function atomicJson(file, value) {
  const text = JSON.stringify(value, null, 2) + '\n';
  if (fs.existsSync(file) && fs.readFileSync(file, 'utf8') === text) return;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.${randomUUID()}.tmp`;
  try { fs.writeFileSync(tmp, text, { flag: 'wx' }); fs.renameSync(tmp, file); }
  finally { fs.rmSync(tmp, { force: true }); }
}
export function run(binary, args) {
  const result = spawnSync(binary, args, { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
  if (result.error || result.status !== 0) throw new Error(`${binary} failed; inspect the local media (details withheld)`);
  return result.stdout;
}
export function technical(file) {
  const probe = JSON.parse(run('ffprobe', ['-v', 'error', '-show_streams', '-show_format', '-of', 'json', file]));
  const video = probe.streams?.find(s => s.codec_type === 'video');
  if (!video || !(video.width > 0) || !(video.height > 0)) throw new Error('Media has no video stream');
  const duration = Number(video.duration ?? probe.format.duration);
  if (!Number.isFinite(duration) || duration <= 0) throw new Error('Media has no finite duration');
  const frames = Number(video.nb_frames);
  return { durationSeconds: duration, width: video.width, height: video.height,
    frameRate: video.avg_frame_rate, frameCount: Number.isSafeInteger(frames) && frames > 0 ? frames : null,
    videoCodec: video.codec_name, audioCodec: probe.streams.find(s => s.codec_type === 'audio')?.codec_name ?? null };
}
export function publicText(value) {
  if (typeof value !== 'string' || !value.trim()) return null;
  // Withhold the entire field, never publish a partially redacted prompt as the original.
  if (scanText(value).length || /(?:https?:\/\/|gs:\/\/|(?:^|\s)\/(?:tmp|private|Volumes|Users|home)\/|\b[A-Z]:[\\/])/i.test(value)
      || /(?:[$€£]\s*\d|\b(?:USD|EUR|GBP)\s*\d|\d(?:[\d,.]*\d)?\s*(?:USD|EUR|GBP|dollars?|cents?)\b)/i.test(value)) return null;
  return value.trim();
}
export const safeLabel = value => publicText(value) ?? 'Unlabeled clip';
export const publicStrings = values => [...new Set((Array.isArray(values) ? values : []).map(publicText).filter(Boolean))].sort();
export function generationMetadata(input = {}, source = 'generation-request') {
  const raw = input.prompt ?? input.veo_prompt ?? input.veoPrompt, prompt = publicText(raw);
  const parameters = {};
  for (const key of ['durationSeconds', 'aspectRatio', 'resolution', 'generateAudio', 'mode', 'ratio',
    'outputFormat', 'promptExpansionMode', 'sampleCount']) {
    const value = (input.parameters ?? input)[key];
    if (typeof value === 'string' && publicText(value)) parameters[key] = value;
    else if (typeof value === 'boolean' || typeof value === 'number' && Number.isFinite(value)) parameters[key] = value;
  }
  return { source, prompt, promptStatus: prompt ? 'recorded' : raw ? 'withheld' : 'unknown',
    promptId: prompt ? `prompt_${digest(prompt)}` : null, provider: publicText(input.provider), model: publicText(input.model),
    seed: Number.isSafeInteger(input.seed) ? input.seed : null,
    createdAt: typeof input.createdAt === 'string' && /^\d{4}-\d{2}-\d{2}T[\d:.]+Z$/.test(input.createdAt) ? input.createdAt : null,
    parameters,
    ...(Object.hasOwn(input, 'requestedModel') ? { requestedModel: publicText(input.requestedModel) } : {}),
    ...(Array.isArray(input.sources) ? { sources: input.sources.map(s => {
      const ref = { role: publicText(s.role), sha256: s.sha256, bytes: s.bytes };
      for (const k of ['width', 'height', 'durationSeconds']) if (Number.isFinite(s[k])) ref[k] = s[k];
      if (publicText(s.mimeType)) ref.mimeType = s.mimeType;
      return ref;
    }) } : {}) };
}
export function assertId(id) {
  if (!/^clip_[a-f0-9]{64}$/.test(id ?? '')) throw new Error('Invalid clip ID; use clip_<SHA-256>');
}
export function metadataPath(id, repo = REPO) { assertId(id); return safePath(repo, `catalog/clips/${id}.json`); }
export function mediaPath(record, repo = REPO) {
  assertId(record.id);
  if (!VIDEO_EXTENSIONS.has(record.extension)) throw new Error('Invalid clip extension');
  return safePath(repo, `data/clips/${record.id}/source${record.extension}`);
}
export function readClip(id, repo = REPO) {
  const record = readJson(metadataPath(id, repo)); validateClip(record);
  if (record.id !== id) throw new Error('Clip record identity mismatch');
  return record;
}
export function resolveClip(id, repo = REPO, verify = true) {
  const record = readClip(id, repo), file = mediaPath(record, repo);
  if (!fs.existsSync(file)) {
    // Explicitly mapped historical copies remain local sources after duplicate
    // reclamation. Always hash a fallback; never mask a corrupt canonical master.
    const locationsFile = safePath(repo, 'data/clips/locations.json');
    const locations = fs.existsSync(locationsFile) ? readJson(locationsFile) : null;
    for (const [relative, mapping] of Object.entries(locations?.locations ?? {}).sort(([a], [b]) => a.localeCompare(b))) {
      if (mapping.id !== id || mapping.bytes !== record.bytes) continue;
      try {
        const candidate = safePath(repo, relative), st = fs.lstatSync(candidate);
        if (st.isFile() && st.size === record.bytes && hashFile(candidate) === record.sha256) return candidate;
      } catch { /* An unavailable historical mapping is not verified media. */ }
    }
    throw new Error(`Clip bytes unavailable locally: ${id}; restore with clips cloud fetch`);
  }
  if (verify && (fs.statSync(file).size !== record.bytes || hashFile(file) !== record.sha256)) throw new Error(`Clip source hash changed: ${id}`);
  return file;
}
function lock(id, repo, action) {
  const dir = safePath(repo, `data/clips/.locks/${id}`); fs.mkdirSync(path.dirname(dir), { recursive: true });
  try { fs.mkdirSync(dir); } catch (e) { if (e.code === 'EEXIST') throw new Error('Clip catalog writer lock exists; recover the prior writer first'); throw e; }
  try { return action(); } finally { fs.rmdirSync(dir); }
}
const unique = rows => [...new Map(rows.map(x => [JSON.stringify(x), x])).values()].sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)));
export function mergeClip(record, metadata = {}) {
  for (const field of ['labels', 'collections', 'legacyIds', 'tags']) record[field] = publicStrings([...record[field], ...(metadata[field] ?? [])]);
  for (const field of ['generations', 'analysis', 'characters']) record[field] = unique([...record[field], ...(metadata[field] ?? [])]);
  if (metadata.analysisRefs) record.analysisRefs = unique([...(record.analysisRefs ?? []), ...metadata.analysisRefs]);
  if (metadata.kind && (record.kind === 'unknown' || metadata.kind === 'source')) record.kind = metadata.kind;
  validateClip(record); return record;
}
/** Independent copy (APFS reflink when available), verified before atomic no-clobber install. */
export function importClip(file, metadata = {}, repo = REPO) {
  const sha256 = hashFile(file), id = `clip_${sha256}`;
  const snapshot = metadata.generationSnapshot ? validateSnapshot(metadata.generationSnapshot) : null;
  if (snapshot) metadata = { ...metadata, generations: [...(metadata.generations ?? []),
    { ...generationMetadata(snapshot, 'creation-snapshot'), snapshotSha256: snapshotHash(snapshot) }] };
  return lock(id, repo, () => {
    const recordPath = metadataPath(id, repo);
    const existing = fs.existsSync(recordPath) ? readClip(id, repo) : null;
    const extension = path.extname(file).toLowerCase();
    if (!VIDEO_EXTENSIONS.has(extension)) throw new Error('Unsupported video extension');
    const record = mergeClip(existing ?? { schemaVersion: 1, id, sha256, bytes: fs.statSync(file).size, extension,
      kind: 'unknown', technical: technical(file), labels: [], collections: [], legacyIds: [], generations: [],
      analysis: [], characters: [], tags: [], availability: { status: 'local-only', urls: [], license: null } }, metadata);
    const target = mediaPath(record, repo); fs.mkdirSync(path.dirname(target), { recursive: true });
    if (!fs.existsSync(target)) {
      const tmp = `${target}.${randomUUID()}.part`;
      try {
        fs.copyFileSync(file, tmp, fs.constants.COPYFILE_EXCL | fs.constants.COPYFILE_FICLONE);
        if (hashFile(tmp) !== sha256 || hashFile(file) !== sha256) throw new Error('Source changed during clip import');
        fs.chmodSync(tmp, 0o444); fs.linkSync(tmp, target);
      } finally { fs.rmSync(tmp, { force: true }); }
    } else if (hashFile(target) !== sha256) throw new Error('Existing clip master hash mismatch; never overwrite it');
    // Retain exact private evidence with the content-addressed master, independently of the workspace.
    if (snapshot) writeSnapshot(safePath(repo, `data/clips/${id}/generations/${snapshotHash(snapshot)}.json`), snapshot);
    atomicJson(recordPath, record);
    return { id, sha256, path: path.relative(repo, target).split(path.sep).join('/'), record };
  });
}
export function verifyClipSnapshots(record, repo = REPO) {
  for (const generation of record.generations) {
    if (!generation.snapshotSha256) continue;
    const file = safePath(repo, `data/clips/${record.id}/generations/${generation.snapshotSha256}.json`);
    const snapshot = readSnapshot(file);
    if (snapshotHash(snapshot) !== generation.snapshotSha256
        || !equal(generation, { ...generationMetadata(snapshot, 'creation-snapshot'), snapshotSha256: snapshotHash(snapshot) }))
      throw new Error('Clip generation snapshot differs from its catalog evidence');
  }
}
export function updateClip(id, metadata, repo = REPO) {
  return lock(id, repo, () => { const record = mergeClip(readClip(id, repo), metadata); atomicJson(metadataPath(id, repo), record); return record; });
}
export function listClips(repo = REPO) {
  const dir = safePath(repo, 'catalog/clips');
  return fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort().map(f => readClip(f.slice(0, -5), repo)) : [];
}

// The checked-in JSON schemas are also the runtime allowlists. Unknown fields fail closed.
const schemas = {};
function validate(value, schema, at = 'record') {
  if (schema.const !== undefined && value !== schema.const) throw new Error(`${at}: invalid constant`);
  if (schema.enum && !schema.enum.includes(value)) throw new Error(`${at}: invalid value`);
  const types = Array.isArray(schema.type) ? schema.type : [schema.type];
  const matches = type => type === 'null' ? value === null : type === 'array' ? Array.isArray(value)
    : type === 'object' ? value !== null && typeof value === 'object' && !Array.isArray(value)
    : type === 'integer' ? Number.isSafeInteger(value) : type === 'number' ? typeof value === 'number' && Number.isFinite(value) : typeof value === type;
  if (schema.type && !types.some(matches)) throw new Error(`${at}: invalid type`);
  if (value === null) return;
  if (typeof value === 'object' && !Array.isArray(value)) {
    for (const key of schema.required ?? []) if (!Object.hasOwn(value, key)) throw new Error(`${at}: missing ${key}`);
    for (const key of Object.keys(value)) {
      if (!schema.properties?.[key]) throw new Error(`${at}: unknown field (value withheld)`);
      validate(value[key], schema.properties[key], `${at}.${key}`);
    }
  }
  if (Array.isArray(value)) value.forEach((v, i) => validate(v, schema.items, `${at}[${i}]`));
  if (typeof value === 'string' && schema.pattern && !new RegExp(schema.pattern).test(value)) throw new Error(`${at}: invalid format`);
  if (typeof value === 'number' && schema.minimum !== undefined && value < schema.minimum) throw new Error(`${at}: below minimum`);
}
export function validateRecord(record, name) {
  schemas[name] ??= readJson(path.join(REPO, `docs/schemas/${name}.schema.json`));
  validate(record, schemas[name]);
  const json = JSON.stringify(record);
  if (scanText(json).length) throw new Error(`${name}: private text (value withheld)`);
  // URLs have their own constrained field; all other strings use the publication filter.
  function check(v, key) {
    if (typeof v === 'string' && v && key !== 'urls' && publicText(v) === null) throw new Error(`${name}: non-public text (value withheld)`);
    if (Array.isArray(v)) v.forEach(x => check(x, key));
    else if (v && typeof v === 'object') Object.entries(v).forEach(([k, x]) => check(x, k));
  }
  check(record);
  for (const url of record.availability?.urls ?? []) {
    const u = new URL(url);
    if (u.protocol !== 'https:' || u.username || u.password || u.search || u.hash || !u.hostname.includes('.') || /^(localhost|127\.|0\.|\[)/.test(u.hostname)) throw new Error('Expected an unsigned public HTTPS media URL');
  }
  if (record.availability && ((record.availability.status === 'public') !== (record.availability.urls.length > 0)))
    throw new Error('Public availability requires at least one public URL');
}
export function validateClip(record) {
  validateRecord(record, 'clip');
  if (record.id !== `clip_${record.sha256}`) throw new Error('Clip hash and ID disagree');
  for (const ref of record.analysisRefs ?? []) if (ref.inputSha256 !== record.sha256) throw new Error('Analysis reference has a different input identity');
  for (const g of record.generations) {
    if ((g.promptStatus === 'recorded') !== (typeof g.prompt === 'string' && !!g.prompt)) throw new Error('Prompt status disagrees with text');
    if (g.promptId !== (g.prompt ? `prompt_${digest(g.prompt)}` : null)) throw new Error('Prompt ID mismatch');
  }
}
const useId = use => `use_${digest(JSON.stringify([use.projectId, use.editVersion, use.segmentIndex, use.evidence]))}`;
export function validateUse(record, clip) {
  validateRecord(record, 'clip-use');
  if (record.id !== useId(record)) throw new Error('Usage identity mismatch');
  if ((record.status === 'rendered') !== (record.outputSha256 !== null)) throw new Error('Rendered usage requires an output hash');
  if (record.range?.unit === 'frames' && (![record.range.start, record.range.length].every(Number.isSafeInteger) || !(record.range.fps > 0)))
    throw new Error('Frame usage requires integer ranges and a positive fps');
  if (record.range?.unit === 'seconds' && record.range.fps !== null) throw new Error('Second ranges do not have a frame rate');
  if (!clip) return;
  if (record.range?.unit === 'frames' && clip.technical.frameCount !== null && record.range.start + record.range.length > clip.technical.frameCount)
    throw new Error('Usage exceeds source frames');
  if (record.range?.unit === 'seconds' && record.range.start + record.range.length > clip.technical.durationSeconds + .001)
    throw new Error('Usage exceeds source duration');
}
export function recordUse(use, repo = REPO) {
  const record = { ...use, schemaVersion: 1, id: useId(use) };
  validateUse(record, readClip(record.clipId, repo));
  return lock(record.id, repo, () => {
    const file = safePath(repo, `catalog/uses/${record.id}.json`);
    if (fs.existsSync(file)) {
      const old = readJson(file);
      // A saved delivery can confirm the same planned occurrence, but cannot replace its range or clip.
      const upgraded = { ...old, status: record.status, outputSha256: record.outputSha256 };
      if (!equal(old, record) && !(old.status === 'planned' && record.status === 'rendered' && equal(upgraded, record)))
        throw new Error('Usage identity already exists with different content');
    }
    atomicJson(file, record); return record;
  });
}
export function listUses(repo = REPO) {
  const folder = safePath(repo, 'catalog/uses');
  return fs.existsSync(folder) ? fs.readdirSync(folder).filter(f => f.endsWith('.json')).sort().map(f => {
    const record = readJson(safePath(repo, `catalog/uses/${f}`)); validateUse(record);
    if (`${record.id}.json` !== f) throw new Error('Usage record identity mismatch'); return record;
  }) : [];
}
export function analytics(repo = REPO) {
  const clips = listClips(repo), uses = listUses(repo), counts = new Map();
  for (const u of uses) { const rows = counts.get(u.clipId) ?? []; rows.push(u); counts.set(u.clipId, rows); }
  const rows = clips.map(c => {
    const events = counts.get(c.id) ?? [], rendered = events.filter(u => u.status === 'rendered');
    return { clipId: c.id, kind: c.kind, labels: c.labels, prompts: c.generations.filter(g => g.prompt).map(g => ({ promptId: g.promptId, prompt: g.prompt, model: g.model, evidence: g.source })),
      recordedUses: events.length, renderedUses: rendered.length, plannedUses: events.filter(u => u.status === 'planned').length,
      projects: [...new Set(rendered.map(u => u.projectId))].sort(),
      sourceSecondsUsed: rendered.reduce((n, u) => n + (u.range ? u.range.length / (u.range.unit === 'frames' ? u.range.fps : 1) : 0), 0) };
  });
  const prompts = new Map();
  for (const row of rows) for (const p of new Map(row.prompts.map(p => [p.promptId, p])).values()) {
    const group = prompts.get(p.promptId) ?? { promptId: p.promptId, prompt: p.prompt, clips: [], renderedUses: 0, plannedUses: 0, projects: [], models: [] };
    group.clips.push(row.clipId); group.renderedUses += row.renderedUses; group.plannedUses += row.plannedUses;
    group.projects = publicStrings([...group.projects, ...row.projects]);
    group.models = publicStrings([...group.models, ...row.prompts.filter(q => q.promptId === p.promptId).map(q => q.model)]);
    prompts.set(p.promptId, group);
  }
  return { schemaVersion: 1, clips: clips.length, recordedUses: uses.length, clipsWithPrompts: rows.filter(r => r.prompts.length).length,
    clipsWithRecordedUses: counts.size, caveat: 'Historical usage is incomplete. Rendered means a matching saved delivery record, not publication or audience views. Copies and project membership are not uses. Reused seconds count occurrences, not unique source coverage. Prompt groups may overlap when a clip has multiple recorded prompts.',
    byPrompt: [...prompts.values()].sort((a, b) => a.promptId.localeCompare(b.promptId)), rows };
}
export function search(query, repo = REPO) {
  const q = String(query ?? '').toLowerCase();
  return listClips(repo).filter(c => JSON.stringify(c).toLowerCase().includes(q)).map(c => ({ id: c.id, kind: c.kind, labels: c.labels, collections: c.collections,
    durationSeconds: c.technical.durationSeconds, summary: c.analysis[0]?.summary ?? null }));
}
