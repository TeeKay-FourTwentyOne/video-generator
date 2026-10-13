/** Read-only discovery of historical evidence; imports independent masters, never moves originals. */
import fs from 'node:fs';
import path from 'node:path';
import { REPO, VIDEO_EXTENSIONS, readJson, hashFile, digest, importClip, updateClip, readClip, recordUse,
  atomicJson, publicText, publicStrings, generationMetadata, listClips, canonical } from './clip-library.mjs';
import { readProjectIdentity, validateProjectId } from './project-identity.mjs';

export function walk(root) {
  if (!fs.existsSync(root)) return [];
  const files = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    if (entry.isSymbolicLink()) continue;
    const file = path.join(root, entry.name);
    if (entry.isDirectory()) files.push(...walk(file)); else if (entry.isFile()) files.push(file);
  }
  return files;
}
const read = file => { try { return readJson(file); } catch { return null; } };
const values = value => Array.isArray(value) ? value : Object.values(value ?? {});
const forward = p => p.replaceAll('\\', '/');
function workspaceFor(file, repo) {
  const relative = forward(path.relative(repo, file));
  const m = /^(data\/(?:workspace|workspace-archive|projects)\/[^/]+)(?:\/|$)/.exec(relative);
  return m ? path.join(repo, m[1]) : null;
}
export function projectIdFor(root, repo = REPO, { projectId } = {}) {
  const explicit = readProjectIdentity(root);
  const identities = new Set();
  if (explicit !== undefined) identities.add(explicit);
  if (projectId !== undefined) identities.add(validateProjectId(projectId));
  const relative = forward(path.relative(repo, root));
  for (const file of walk(path.join(repo, 'briefs')).filter(f => path.basename(f) === 'production.json')) {
    const record = read(file);
    if (record?.workspace?.path === relative) identities.add(validateProjectId(record.projectId));
  }
  if (identities.size > 1) throw new Error('Project identity conflict between initialization, workspace.json or public production records');
  return identities.values().next().value ?? publicText(path.basename(root)) ?? `collection-${digest(relative).slice(0, 12)}`;
}

export function migrate(repo = REPO, progress = () => {}) {
  const data = path.join(repo, 'data');
  const files = fs.readdirSync(data, { withFileTypes: true }).filter(e => e.isDirectory() && e.name !== 'clips')
    .flatMap(e => walk(path.join(data, e.name))).filter(f => VIDEO_EXTENSIONS.has(path.extname(f).toLowerCase()));
  const locations = {}, byName = new Map(), records = new Map(), additions = new Map(), projectIds = new Map();
  const report = { schemaVersion: 1, scannedFiles: files.length, importedFiles: 0, uniqueClips: 0, duplicateFiles: 0,
    failedFiles: [], unresolvedMetadata: [], unsupportedEdits: [], missingReferences: [], uses: 0, sourceHashesVerified: 0 };
  const collection = file => {
    const ws = workspaceFor(file, repo);
    if (!ws) return null;
    if (!projectIds.has(ws)) projectIds.set(ws, projectIdFor(ws, repo));
    return projectIds.get(ws);
  };
  const jsonFiles = ['workspace', 'workspace-archive', 'projects'].flatMap(base => walk(path.join(data, base)))
    .filter(f => f.endsWith('.json') && fs.statSync(f).size <= 8 * 1024 * 1024);
  // Resolve all workspace identities before importing any master or updating the catalog.
  for (const file of [...files, ...jsonFiles]) collection(file);
  for (const [index, file] of files.entries()) {
    const relative = forward(path.relative(repo, file));
    try {
      const sha256 = hashFile(file), id = `clip_${sha256}`;
      let record = records.get(id);
      if (!record) {
        const kind = /\/(?:final|exports|review)\//.test(relative) ? 'delivery'
          : /\/(?:edit|scratch|temp)\//.test(relative) ? 'derived' : 'unknown';
        record = importClip(file, { labels: [path.basename(file)], kind }, repo).record;
        if (record.id !== id) throw new Error('Source changed during inventory');
        records.set(id, record);
      }
      locations[relative] = { id, bytes: fs.statSync(file).size };
      const ids = byName.get(path.basename(file)) ?? new Set(); ids.add(id); byName.set(path.basename(file), ids);
      const a = additions.get(id) ?? { labels: [], collections: [], legacyIds: [], generations: [], analysis: [], characters: [], tags: [] };
      a.labels.push(path.basename(file)); const project = collection(file); if (project) a.collections.push(project); additions.set(id, a);
      report.importedFiles++; report.sourceHashesVerified++;
    } catch (e) { report.failedFiles.push({ path: relative, reason: e.message }); }
    if (index % 100 === 0) progress({ scanned: index + 1, total: files.length, unique: records.size });
  }
  const uniqueImported = records.size;
  // Sources acquired directly into the library have no historical path to inventory.
  for (const record of listClips(repo)) if (!records.has(record.id)) {
    records.set(record.id, record);
    additions.set(record.id, { labels: [], collections: [], legacyIds: [], generations: [], analysis: [], characters: [], tags: [] });
  }
  function match(value, context, sha256) {
    if (typeof sha256 === 'string') return records.has(`clip_${sha256}`) ? `clip_${sha256}` : null;
    if (typeof value !== 'string') return null;
    if (/^clip_[a-f0-9]{64}$/.test(value)) return records.has(value) ? value : null;
    const text = forward(value), marker = text.indexOf('data/');
    const relative = marker >= 0 ? text.slice(marker) : text.startsWith('/video/') ? `data${text}` : text;
    const candidates = [relative];
    if (context) {
      candidates.push(forward(path.relative(repo, path.resolve(path.dirname(context), text))));
      const ws = workspaceFor(context, repo);
      if (ws) candidates.push(forward(path.relative(repo, path.resolve(ws, text))));
    }
    for (const candidate of [...candidates]) {
      candidates.push(candidate.replace('data/workspace/', 'data/workspace-archive/'));
      candidates.push(candidate.replace('data/workspace-archive/', 'data/workspace/'));
    }
    for (const candidate of candidates) if (locations[candidate]) return locations[candidate].id;
    // Basenames are acceptable only when every matching file has identical bytes.
    const ids = byName.get(path.posix.basename(text));
    return ids?.size === 1 ? [...ids][0] : null;
  }
  const add = (id, field, item) => { if (id && item) additions.get(id)[field].push(item); };
  const generation = (id, input, source) => { if (!id) return; add(id, 'generations', generationMetadata(input, source)); additions.get(id).kind = 'source'; };
  const legacy = read(path.join(repo, 'docs/clip-metadata/clips.json'));
  const legacyIds = new Map();
  for (const c of values(legacy?.clips)) {
    const id = match(c.path ?? c.filename);
    if (!id) { report.unresolvedMetadata.push({ source: 'clip-metadata', legacyId: c.clip_id }); continue; }
    legacyIds.set(c.clip_id, id); add(id, 'legacyIds', `clip-metadata:${c.clip_id}`);
    if (c.provenance?.veo_prompt) generation(id, { prompt: c.provenance.veo_prompt, provider: 'veo' }, 'legacy-clip-metadata');
    if (c.provenance?.project_id) add(id, 'collections', c.provenance.project_id);
    add(id, 'analysis', { source: 'legacy-clip-metadata', model: null, summary: publicText(c.frames?.overall_summary),
      transcript: publicText(c.audio?.transcription?.full_text), tags: publicStrings(c.tags),
      frames: (c.frames?.descriptions ?? []).filter(f => Number.isFinite(f.timestamp) && f.timestamp >= 0 && publicText(f.description))
        .map(f => ({ seconds: f.timestamp, text: publicText(f.description) })) });
    additions.get(id).tags.push(...publicStrings(c.tags));
  }
  const manifest = read(path.join(repo, 'mcp/veo-clips-mcp/manifest.json'));
  for (const c of values(manifest?.clips)) {
    const id = match(c.filePath ?? c.filename);
    if (!id) { report.unresolvedMetadata.push({ source: 'legacy-search-manifest', legacyId: c.filename }); continue; }
    add(id, 'legacyIds', `legacy-search:${c.filename}`);
    if (c.originalPrompt) generation(id, { prompt: c.originalPrompt }, 'legacy-search-manifest');
    if (c.analysis) add(id, 'analysis', { source: 'legacy-search-manifest', model: publicText(manifest.model),
      summary: publicText(c.analysis.description), transcript: publicText(c.analysis.audio?.speechTranscript),
      tags: publicStrings(c.analysis.suggestedTags), frames: [] });
    additions.get(id).tags.push(...publicStrings(c.analysis?.suggestedTags));
  }
  for (const c of values(read(path.join(repo, 'docs/clip-metadata/characters.json'))?.characters)) {
    for (const legacyId of c.clip_ids ?? []) add(legacyIds.get(legacyId), 'characters', { id: c.character_id,
      name: publicText(c.name), description: publicText(c.description), source: 'legacy-character-cluster' });
  }
  const jobs = new Map();
  for (const j of values(read(path.join(repo, 'jobs.json')))) {
    const id = match(j.result?.path ?? j.result?.filename);
    if (!id || j.type !== 'veo-generate') continue;
    jobs.set(j.id, id);
    generation(id, { ...j.input, model: j.result?.model ?? j.input?.model, seed: j.result?.seed ?? j.input?.seed, provider: 'veo', createdAt: j.createdAt }, 'legacy-job');
  }
  const documents = new Map(jsonFiles.map(f => [f, read(f)]).filter(([, x]) => x));
  // Earlier shell generators saved a job receipt beside its exact prompt text.
  for (const [file, doc] of documents) {
    if (!file.endsWith('.job.json') || typeof doc.output !== 'string') continue;
    const id = match(doc.output, file, doc.sha256), promptFile = file.replace(/\.job\.json$/, '.prompt.txt');
    if (!id || !fs.existsSync(promptFile) || fs.lstatSync(promptFile).isSymbolicLink()) continue;
    generation(id, { prompt: fs.readFileSync(promptFile, 'utf8'), model: doc.model, seed: doc.seed, createdAt: doc.submittedAt }, 'paired-job-prompt-file');
  }
  // Exact film request -> asset joins; a plan is explicitly labeled as plan evidence.
  for (const [file, doc] of documents) {
    if (path.basename(file) !== 'film.json' || !Array.isArray(doc.shots)) continue;
    const root = path.dirname(file);
    for (const shot of doc.shots) {
      const requestId = shot.requestId ?? `${shot.id}-v1`, asset = read(path.join(root, `operations/${requestId}.asset.json`));
    const id = asset ? match(asset.clipId ?? asset.path, file, asset.sha256) : match(`clips/${requestId}.mp4`, file);
      if (!id || !shot.request) continue;
      const request = { ...shot.request };
      if (request.promptFile) {
        const promptFile = path.resolve(root, request.promptFile);
        if (promptFile.startsWith(root + path.sep) && fs.existsSync(promptFile) && !fs.lstatSync(promptFile).isSymbolicLink()) request.prompt = fs.readFileSync(promptFile, 'utf8');
      }
      const operation = read(path.join(root, `operations/${requestId}.json`));
      const original = operation?.prompt ? operation : request;
      generation(id, { ...original, provider: original.provider ?? 'veo', model: operation?.model ?? request.model,
        seed: operation?.seed ?? request.seed }, operation?.prompt ? 'saved-operation-request' : 'film-plan');
    }
  }
  // Import explicitly paired prompt/media records and project associations, never guess from shot order.
  for (const [file, doc] of documents) {
    function visit(obj) {
      if (Array.isArray(obj)) { obj.forEach(visit); return; }
      if (!obj || typeof obj !== 'object') return;
      const refs = ['clip', 'file', 'filename', 'path', 'output', 'video', 'videoPath', 'video_path', 'source_file']
        .map(k => obj[k]).filter(v => typeof v === 'string' && VIDEO_EXTENSIONS.has(path.extname(v).toLowerCase()));
      const id = jobs.get(obj.job_id) ?? (refs.length === 1 ? match(refs[0], file, obj.sha256) : null);
      if (id) {
        add(id, 'collections', publicText(doc.project_id ?? collection(file)));
        if (obj.prompt || obj.veo_prompt || obj.veoPrompt) generation(id, obj, 'paired-media-record');
      }
      Object.values(obj).forEach(visit);
    }
    visit(doc);
  }
  for (const [id, metadata] of additions) updateClip(id, metadata, repo);
  // Frame edits are usable only when the source hash or an unambiguous media reference resolves.
  const edits = new Map();
  for (const [file, doc] of documents) {
    if (!Array.isArray(doc.segments) || !doc.segments.some(s => s.inFrame !== undefined && s.frames !== undefined)) continue;
    const root = workspaceFor(file, repo); if (!root) continue;
    const version = forward(path.relative(root, file)).replace(/\.json$/, '');
    edits.set(`${root}:${version}`, { file, root, version, edit: doc, delivery: null });
  }
  for (const [file, doc] of documents) {
    if (path.basename(file) !== 'delivery.json' || !Array.isArray(doc.edit?.segments)) continue;
    const root = workspaceFor(file, repo); if (!root) continue;
    const version = `edit/${doc.version ?? path.basename(path.dirname(file))}`, key = `${root}:${version}`;
    const output = match(doc.output, file, doc.sha256);
    const previous = edits.get(key);
    // Saved delivery proves only its own exact edit; changed plans remain planned.
    const comparable = (segments, context) => segments.map(s => {
      const id = match(s.clipId ?? s.source, context, s.sha256);
      return { ...s, source: undefined, clipId: id, sha256: s.sha256 ?? id?.slice(5) };
    });
    if (previous && JSON.stringify(canonical(comparable(previous.edit.segments, previous.file))) !== JSON.stringify(canonical(comparable(doc.edit.segments, file)))) {
      edits.set(`${key}:rendered`, { file, root, version: `${version}-rendered`, edit: doc.edit, delivery: output ? doc : null });
    } else edits.set(key, { file, root, version, edit: doc.edit, delivery: output ? doc : null });
  }
  for (const { file, root, version, edit, delivery } of edits.values()) {
    let at = 0;
    const plan = read(path.join(root, 'film.json'));
    for (const [index, segment] of edit.segments.entries()) {
      const timelineStartFrame = at;
      at = at !== null && Number.isInteger(segment.frames) && segment.frames > 0 ? at + segment.frames : null;
      const id = match(segment.clipId ?? segment.source, file, segment.sha256), clip = id ? readClip(id, repo) : null;
      const fps = plan?.fps ?? (clip ? (() => { const [n, d] = clip.technical.frameRate.split('/').map(Number); return n / d; })() : null);
      if (!id || !Number.isInteger(segment.inFrame) || !Number.isInteger(segment.frames) || segment.inFrame < 0 || segment.frames <= 0 || !(fps > 0)) {
        report.missingReferences.push({ path: forward(path.relative(repo, file)), segment: index }); continue;
      }
      try {
        recordUse({ clipId: id, projectId: collection(file), editVersion: version, segmentIndex: index,
          shotId: publicText(segment.shotId ?? segment.id), status: delivery ? 'rendered' : 'planned', evidence: 'saved-frame-edit',
          range: { unit: 'frames', start: segment.inFrame, length: segment.frames, fps }, timelineStartFrame,
          outputSha256: delivery?.sha256 ?? null }, repo);
        report.uses++;
      } catch (e) { report.unsupportedEdits.push({ path: forward(path.relative(repo, file)), segment: index, reason: e.message }); }
    }
  }
  // Legacy episode manifests specify their own source in/out times. Treat them as
  // plans unless a delivery explicitly captures this exact timeline.
  for (const [file, doc] of documents) {
    if (!Array.isArray(doc.timeline) || !Array.isArray(doc.shots)) continue;
    const root = workspaceFor(file, repo); if (!root) continue;
    const shots = new Map(doc.shots.map(s => [s.id, s]));
    for (const [index, entry] of doc.timeline.entries()) {
      if (typeof entry.clip !== 'string' || !Number.isFinite(entry.in) || !Number.isFinite(entry.out) || entry.in < 0 || entry.out <= entry.in) continue;
      const shot = shots.get(entry.clip), id = match(shot?.clip, file, shot?.sha256);
      if (!id) { report.missingReferences.push({ path: forward(path.relative(repo, file)), segment: index }); continue; }
      try {
        recordUse({ clipId: id, projectId: collection(file), editVersion: forward(path.relative(root, file)).replace(/\.json$/, ''),
          segmentIndex: index, shotId: publicText(entry.clip), status: 'planned', evidence: 'saved-episode-timeline',
          range: { unit: 'seconds', start: entry.in, length: entry.out - entry.in, fps: null }, timelineStartFrame: null, outputSha256: null }, repo);
        report.uses++;
      } catch (e) { report.unsupportedEdits.push({ path: forward(path.relative(repo, file)), segment: index, reason: e.message }); }
    }
  }
  report.uniqueClips = records.size; report.duplicateFiles = report.importedFiles - uniqueImported;
  atomicJson(path.join(data, 'clips/locations.json'), { schemaVersion: 1, locations });
  atomicJson(path.join(data, 'clips/migration-report.json'), report);
  return report;
}
