#!/usr/bin/env node
/** Public, source-only production summaries. No provider, Git or archive writes. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { MANIFEST, verifyArchive } from './archive.mjs';
import { validateShape, publicProjection, safePath, sha256, checkPublicText } from './record-schema.mjs';

export const REPOSITORY_URL = 'https://github.com/TeeKay-FourTwentyOne/video-generator';
const recordPath = id => `briefs/${id}/production.json`;
const json = value => JSON.stringify(value, null, 2) + '\n';
const exists = file => fs.lstat(file).then(() => true, e => { if (e.code === 'ENOENT') return false; throw e; });
const readJson = async (repo, relative) => JSON.parse(await fs.readFile(await safePath(repo, relative), 'utf8'));
const requireValue = (condition, message) => { if (!condition) throw new Error(message); };

export async function atomicWrite(repo, relative, bytes) {
  const target = await safePath(repo, relative);
  await fs.mkdir(path.dirname(target), { recursive: true });
  const temporary = `${target}.${randomUUID()}.tmp`;
  try {
    await fs.writeFile(temporary, bytes, { flag: 'wx' });
    await fs.rename(temporary, target);
  } finally { await fs.unlink(temporary).catch(e => { if (e.code !== 'ENOENT') throw e; }); }
}

export async function hashFile(file) {
  const handle = await fs.open(file, 'r');
  try {
    const before = await handle.stat(), hash = createHash('sha256');
    for await (const chunk of handle.createReadStream({ autoClose: false })) hash.update(chunk);
    const after = await handle.stat();
    requireValue(before.size === after.size && before.mtimeMs === after.mtimeMs && before.ctimeMs === after.ctimeMs,
      'File changed while hashing');
    return hash.digest('hex');
  } finally { await handle.close(); }
}

function markdownLinks(text) {
  const prose = text.replace(/^\s*(`{3,}|~{3,})[^\n]*\n[\s\S]*?^\s*\1\s*$/gm, '');
  return [...prose.matchAll(/\[[^\]\n]*\]\(<?([^\s)>]+)>?(?:\s+"[^"]*")?\)|^\s*\[[^\]]+\]:\s*<?([^\s>]+)>?/gm)]
    .map(m => m[1] ?? m[2]);
}

export async function checkLinks(repo, relative, text, { allowMissingViews = false, projectId } = {}) {
  for (const link of markdownLinks(text)) {
    if (/^(?:https?:|mailto:|#)/i.test(link)) continue;
    const target = decodeURIComponent(link.split('#')[0]);
    requireValue(!path.isAbsolute(target) && !target.includes('\\') && !target.includes(':'), `${relative}: invalid document link`);
    const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(relative), target));
    // Historical media links are local evidence, not requirements on a fresh clone.
    if (resolved.startsWith('data/')) continue;
    if (allowMissingViews && (resolved === `briefs/${projectId}/README.md` ||
        /^briefs\/[a-z0-9-]+\/README\.md$/.test(resolved) &&
        await exists(await safePath(repo, resolved.replace(/README\.md$/, 'production.json'))))) continue;
    requireValue(await exists(await safePath(repo, resolved)), `${relative}: broken link to ${resolved}`);
  }
}

const outcomes = {
  'technical-check': ['passed', 'failed', 'pending'],
  'visual-review': ['inspected', 'pending', 'not-claimed'],
  'audio-listening': ['passed', 'failed', 'pending', 'not-claimed'],
  'artistic-approval': ['approved', 'pending', 'not-claimed'],
  'finishing-authorization': ['authorized', 'pending', 'not-claimed'],
  publication: ['user-confirmed', 'public-page-verified', 'supplied-processing'],
};

export async function validateRecord(repo, record, { allowStaleDescription = false, allowMissingViews = false } = {}) {
  validateShape(record);
  checkPublicText(json(record), recordPath(record.projectId), repo);
  const prefix = `briefs/${record.projectId}/`;
  for (const [field, filename] of [['briefPath', 'brief.md'], ['descriptionPath', 'description.md'],
    ['decisionsPath', 'decisions.md'], ['handoffPath', 'handoff.md']]) {
    if (record[field]) requireValue(record[field] === `${prefix}${filename}`, `${field} must identify the project canonical document`);
  }
  const documents = ['briefPath', 'descriptionPath', 'decisionsPath', 'handoffPath'].flatMap(k => record[k] ? [record[k]] : []);
  for (const file of documents) requireValue(file.startsWith(prefix) && file.endsWith('.md'), 'Project documents must be local Markdown');
  for (const document of record.supportingDocuments ?? []) {
    requireValue(document.path.startsWith(prefix) && /\.(md|json)$/.test(document.path) &&
      !documents.includes(document.path) && !['README.md', 'production.json'].includes(path.posix.basename(document.path)),
    'Supporting documents must be unique project Markdown or JSON sources');
    documents.push(document.path);
  }
  requireValue(Boolean(record.descriptionPath) === Boolean(record.descriptionSha256), 'Description path and hash are a pair');
  if (record.seriesPath) requireValue(Boolean(record.seriesId) && /^(briefs|series)\/.+\.md$/.test(record.seriesPath), 'Invalid series document');
  if (record.workspace) {
    const archived = ['archived', 'archived-verified'].includes(record.workspace.state);
    requireValue(record.workspace.path.startsWith(archived ? 'data/workspace-archive/' : 'data/workspace/'), 'Workspace state and locator disagree');
    requireValue(Boolean(record.archive) === (record.workspace.state === 'archived-verified'), 'Verified archive state requires its verification record');
  } else requireValue(!record.archive && !record.artifacts.length, 'Artifacts and archive require a workspace');
  if (record.archive) requireValue(record.archive.manifestPath === `${record.workspace.path}/${MANIFEST}`, 'Archive manifest locator disagrees');
  const versions = new Map();
  const paths = new Set();
  for (const artifact of record.artifacts) {
    requireValue(!versions.has(artifact.version), 'Duplicate artifact version');
    versions.set(artifact.version, artifact);
    requireValue(/\.(mp4|mov|mkv|webm)$/.test(artifact.path), 'Artifact must identify a video file');
    const folder = path.posix.dirname(artifact.path);
    requireValue(!artifact.descriptionCopyPath || artifact.descriptionCopyPath === path.posix.join(folder, 'description.txt'), 'Description copy must be beside its video');
    requireValue(!artifact.deliveryRecordPath || artifact.deliveryRecordPath === path.posix.join(folder, 'delivery.json'), 'Delivery record must be beside its video');
    for (const file of [artifact.path, artifact.descriptionCopyPath, artifact.deliveryRecordPath].filter(Boolean)) {
      requireValue(!paths.has(file), 'Duplicate artifact or delivery path'); paths.add(file);
    }
    const duration = artifact.frames * artifact.fps.denominator / artifact.fps.numerator;
    requireValue(Math.abs(duration - artifact.durationSeconds) <= 1e-9, 'Duration must be derived from frames and rational fps');
    requireValue(!artifact.descriptionCopyPath || Boolean(record.descriptionPath), 'Description copy requires a canonical description');
  }
  const selected = record.artifacts.filter(a => a.publishedMaster);
  requireValue(selected.length === (record.status === 'published' && record.publication?.artifactVersion ? 1 : 0),
    'Published master selection must agree with status and explicit publication artifact');
  if (record.publication) {
    const p = record.publication;
    requireValue(!p.artifactVersion || versions.has(p.artifactVersion), 'Publication must identify a recorded artifact when supplied');
    requireValue(Boolean(p.verifiedDate) === (p.evidence === 'public-page-verified'), 'Independent verification needs its own date and evidence');
    requireValue(p.evidence === 'supplied-processing' ? record.status !== 'published' : record.status === 'published',
      'Publication evidence and status disagree; processing is not publication');
    if (selected.length) requireValue(selected[0].version === p.artifactVersion, 'Publication master version disagrees');
  } else requireValue(record.status !== 'published', 'Published status requires publication evidence');
  for (const event of record.reviewEvents) {
    const hasArtifact = Boolean(event.artifactVersion) || Boolean(event.artifactSha256);
    requireValue(event.type === 'publication' || hasArtifact, 'Review event requires an artifact hash and version');
    if (hasArtifact) requireValue(Boolean(event.artifactVersion) && Boolean(event.artifactSha256) &&
      versions.get(event.artifactVersion)?.sha256 === event.artifactSha256, 'Review event must match an artifact hash and version');
    requireValue(outcomes[event.type].includes(event.outcome), 'Review event type and outcome disagree');
    if (event.type === 'publication') requireValue(record.publication?.artifactVersion === event.artifactVersion &&
      record.publication?.evidence === event.outcome, 'Publication event lacks matching evidence');
  }
  if (record.publication) requireValue(record.reviewEvents.some(e => e.type === 'publication' &&
    e.artifactVersion === record.publication.artifactVersion && e.recordedDate === record.publication.recordedDate),
  'Publication needs a dated event separate from technical QA');
  const aliases = new Set();
  for (const alias of record.legacyPaths) {
    requireValue(alias.path.startsWith('briefs/') && alias.path.endsWith('.md') && !alias.path.startsWith(prefix) &&
      !aliases.has(alias.path) && documents.includes(alias.target), 'Invalid or duplicate legacy alias');
    aliases.add(alias.path);
    const text = await fs.readFile(await safePath(repo, alias.path), 'utf8');
    requireValue(markdownLinks(text).some(link => path.posix.normalize(path.posix.join(path.posix.dirname(alias.path), link)) === alias.target),
      'Legacy page must forward to its canonical document');
    await checkLinks(repo, alias.path, text, { allowMissingViews, projectId: record.projectId });
  }
  for (const file of documents) {
    const bytes = await fs.readFile(await safePath(repo, file));
    checkPublicText(bytes.toString('utf8'), file, repo);
    if (file.endsWith('.md')) await checkLinks(repo, file, bytes.toString('utf8'), { allowMissingViews, projectId: record.projectId });
    else JSON.parse(bytes.toString('utf8'));
    if (file === record.descriptionPath) {
      requireValue(allowStaleDescription || sha256(bytes) === record.descriptionSha256, 'Canonical description hash mismatch; run sync-description');
      requireValue(bytes.toString('utf8').trimEnd().endsWith(`\n${REPOSITORY_URL}`), 'Publication text must end with the repository URL');
    }
  }
  if (record.seriesPath) requireValue(await exists(await safePath(repo, record.seriesPath)), 'Series document is missing');
  return publicProjection(record);
}

export async function loadRecords(repo, options = {}) {
  const directory = await safePath(repo, 'briefs');
  const records = [];
  for (const entry of (await fs.readdir(directory, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name, 'en'))) {
    if (!entry.isDirectory()) continue;
    const file = `briefs/${entry.name}/production.json`;
    if (!(await exists(await safePath(repo, file)))) continue;
    const record = await readJson(repo, file);
    requireValue(record.projectId === entry.name, 'Project ID must match directory');
    records.push(await validateRecord(repo, record, options));
  }
  const ids = new Set(records.map(r => r.projectId));
  const aliases = new Set();
  for (const r of records) {
    for (const id of r.relatedProjectIds ?? []) requireValue(ids.has(id) && id !== r.projectId, 'Unresolved related project ID');
    for (const { path: alias } of r.legacyPaths) {
      requireValue(!aliases.has(alias), 'Legacy alias belongs to multiple records'); aliases.add(alias);
    }
  }
  return records;
}

const escape = value => value.replace(/[\\`*_[\]<>|]/g, '\\$&').replace(/[\r\n]/g, ' ');
const note = '<!-- Generated by npm run records -- build. Edit production.json and canonical documents. -->';
export function projectSummary(r) {
  const lines = [`# ${escape(r.title)}`, '', note, '', `Status: **${r.status}**.`, ''];
  if (r.statusNote) lines.push(escape(r.statusNote), '');
  const links = ['[Creative brief](brief.md)', '[Production record](production.json)'];
  for (const [field, label] of [['descriptionPath', 'Publication text'], ['decisionsPath', 'Decisions'], ['handoffPath', 'Handoff'], ['seriesPath', 'Series canon']]) {
    if (r[field]) links.push(`[${label}](${path.posix.relative(`briefs/${r.projectId}`, r[field])})`);
  }
  lines.push(links.join(' · '));
  if (r.supportingDocuments?.length) lines.push('', ...r.supportingDocuments.map(d =>
    `- [${escape(d.label)}](${path.posix.relative(`briefs/${r.projectId}`, d.path)})`));
  if (r.publication) lines.push('', `[${escape(r.publication.platform)} publication](${r.publication.url}) — ${r.publication.evidence}; recorded ${r.publication.recordedDate}.`,
    ...(r.publication.platformPublicationDate ? [`Platform publication date: ${r.publication.platformPublicationDate}.`] : ['Platform publication date is not recorded.']));
  if (r.publication && !r.publication.artifactVersion) lines.push('The publication URL is not linked to a specific local master in this record.');
  if (r.artifacts.length) {
    lines.push('', '| Version | Role | Format | Frames | fps | Duration | Published master |', '| --- | --- | --- | --- | --- | --- | --- |');
    for (const a of r.artifacts) lines.push(`| ${a.version} | ${a.role} | ${a.width} × ${a.height} | ${a.frames} | ${a.fps.numerator}${a.fps.denominator === 1 ? '' : `/${a.fps.denominator}`} | ${Number(a.durationSeconds.toFixed(6))} s | ${a.publishedMaster ? 'Yes' : 'No'} |`);
  }
  if (r.workspace) lines.push('', `Local media: ${r.workspace.state}. Artifacts remain in ignored storage; see the record for their relative locator.`);
  lines.push('', 'Technical checks, listening, artistic approval and publication are separate events in the record.', '');
  return lines.join('\n');
}

export function projectIndex(records) {
  const series = new Map(records.filter(r => r.seriesPath).map(r => [r.seriesId, r.seriesPath]));
  return ['# Production records', '', note, '',
    'Each project has a canonical folder. Older Markdown paths forward to the current documents; shared series canon keeps its existing location. Records include only supported facts, and unknown status does not imply approval or publication.', '',
    'Filter locally with `npm run records -- list --status=review`, `--title=words`, or `--series=series-id`.', '',
    ...(series.size ? [`Shared canon: ${[...series].sort(([a], [b]) => a.localeCompare(b, 'en')).map(([id, file]) => `[${escape(id)}](${path.posix.relative('briefs', file)})`).join(' · ')}.`, ''] : []),
    '| Project | Status | Series | Documents |', '| --- | --- | --- | --- |',
    ...records.map(r => `| [${escape(r.title)}](${r.projectId}/README.md) | ${r.status} | ${r.seriesId ?? '—'} | [Brief](${r.projectId}/brief.md)${r.descriptionPath ? ` · [Description](${r.projectId}/description.md)` : ''}${r.decisionsPath ? ` · [Decisions](${r.projectId}/decisions.md)` : ''} · [Record](${r.projectId}/production.json) |`), ''].join('\n');
}

export async function buildViews(repo, { check = false, dryRun = false } = {}) {
  const records = await loadRecords(repo, { allowMissingViews: true });
  const views = new Map([['briefs/README.md', projectIndex(records)], ...records.map(r => [`briefs/${r.projectId}/README.md`, projectSummary(r)])]);
  const changed = [];
  for (const [file, bytes] of views) {
    const target = await safePath(repo, file);
    const previous = await fs.readFile(target, 'utf8').catch(e => { if (e.code !== 'ENOENT') throw e; });
    if (previous !== bytes) changed.push(file);
  }
  if (check && changed.length) throw new Error(`Generated view drift: ${changed.join(', ')}`);
  if (!check && !dryRun) for (const file of changed) await atomicWrite(repo, file, views.get(file));
  return { records: records.length, changed, written: !check && !dryRun };
}

export async function exportRecord(repo, input, { check = false, dryRun = false } = {}) {
  const record = await validateRecord(repo, input, { allowMissingViews: true });
  const file = recordPath(record.projectId), bytes = json(record);
  const before = await fs.readFile(await safePath(repo, file), 'utf8').catch(e => { if (e.code !== 'ENOENT') throw e; });
  if (check && before !== bytes) throw new Error(`Record drift: ${file}`);
  if (!check && !dryRun && before !== bytes) await atomicWrite(repo, file, bytes);
  return { path: file, changed: before !== bytes, written: !check && !dryRun };
}

async function descriptionChanges(repo, record) {
  const bytes = await fs.readFile(await safePath(repo, record.descriptionPath));
  const hash = sha256(bytes), changes = new Map();
  const canonicalSources = [record.descriptionPath, ...record.legacyPaths.filter(a => a.target === record.descriptionPath).map(a => a.path)];
  for (const artifact of record.artifacts) {
    const copy = artifact.descriptionCopyPath;
    if (copy) {
      const file = `${record.workspace.path}/${copy}`;
      const old = await fs.readFile(await safePath(repo, file)).catch(e => { if (e.code !== 'ENOENT') throw e; });
      if (!old?.equals(bytes)) changes.set(file, bytes);
    }
    if (artifact.deliveryRecordPath && copy) {
      const file = `${record.workspace.path}/${artifact.deliveryRecordPath}`, delivery = await readJson(repo, file);
      if (delivery.description?.sha256 !== hash || delivery.description?.path !== copy ||
          !canonicalSources.includes(delivery.description?.repositorySource)) {
        delivery.description = { ...delivery.description, path: copy, repositorySource: record.descriptionPath, sha256: hash };
        changes.set(file, Buffer.from(json(delivery)));
      }
    }
  }
  if (record.descriptionSha256 !== hash) changes.set(recordPath(record.projectId), Buffer.from(json(publicProjection({ ...record, descriptionSha256: hash }))));
  return changes;
}

export async function syncDescription(repo, record, { check = false, dryRun = false } = {}) {
  await validateRecord(repo, record, { allowStaleDescription: true });
  requireValue(record.descriptionPath, 'No canonical publication text is recorded');
  const changes = await descriptionChanges(repo, record);
  if (check && changes.size) throw new Error(`Description drift: ${[...changes.keys()].join(', ')}`);
  if (check || dryRun || !changes.size) return { changed: [...changes.keys()], written: false };
  requireValue(record.workspace?.state === 'active', 'Description writes require an active workspace; archives stay sealed');
  // Refuse a sealed source as well as an archive, including a nested workspace.
  for (let dir = record.workspace.path; dir.startsWith('data/workspace/'); dir = path.posix.dirname(dir)) {
    requireValue(!(await exists(await safePath(repo, `${dir}/${MANIFEST}`))), 'Sealed workspace cannot be changed');
  }
  const snapshot = `${record.workspace.path}/notes/description-sync/${new Date().toISOString().replace(/[:.]/g, '-')}-${randomUUID()}`;
  const previous = [];
  for (const [file] of changes) {
    const bytes = await fs.readFile(await safePath(repo, file)).catch(e => { if (e.code !== 'ENOENT') throw e; });
    previous.push({ file, existed: Boolean(bytes), sha256: bytes ? sha256(bytes) : null });
    if (bytes) await atomicWrite(repo, `${snapshot}/before/${file}`, bytes);
  }
  await atomicWrite(repo, `${snapshot}/changes.json`, json(previous));
  for (const [file, bytes] of changes) await atomicWrite(repo, file, bytes);
  return { changed: [...changes.keys()], written: true, snapshot };
}

export async function validateLocalEvidence(repo, record) {
  await validateRecord(repo, record);
  for (const a of record.artifacts) {
    const file = await safePath(repo, `${record.workspace.path}/${a.path}`);
    requireValue(await hashFile(file) === a.sha256, `Artifact hash mismatch: ${a.version}`);
    const probe = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries',
      'stream=width,height,avg_frame_rate,nb_read_frames', '-of', 'json', file], { encoding: 'utf8', maxBuffer: 1024 * 1024 });
    requireValue(!probe.error && probe.status === 0, `ffprobe failed: ${a.version}`);
    const s = JSON.parse(probe.stdout).streams?.[0];
    const [n, d] = (s?.avg_frame_rate ?? '').split('/').map(Number);
    requireValue(s?.width === a.width && s?.height === a.height && Number(s?.nb_read_frames) === a.frames &&
      n * a.fps.denominator === d * a.fps.numerator, `Artifact dimensions, fps or frame count mismatch: ${a.version}`);
  }
  if (record.descriptionPath) await syncDescription(repo, record, { check: true });
  if (record.archive) {
    const result = await verifyArchive(repo, path.posix.basename(record.workspace.path));
    requireValue(result.destination === record.workspace.path && result.inventorySha256 === record.archive.inventorySha256, 'Archive inventory identity mismatch');
  }
  return { projectId: record.projectId, artifacts: record.artifacts.length, archiveVerified: Boolean(record.archive),
    artisticApprovalInferred: false, listeningPerformed: false };
}

export async function main(argv, repo = process.cwd()) {
  const [command, ...args] = argv;
  const flags = args.filter(a => a.startsWith('--'));
  const positional = args.filter(a => !a.startsWith('--'));
  const allowed = command === 'list' ? ['status', 'title', 'series'] : command === 'validate' ? ['local-evidence'] : ['check', 'dry-run'];
  for (const flag of flags) {
    const key = flag.slice(2).split('=')[0];
    requireValue(allowed.includes(key) && (command === 'list' ? /^--\w+=.+$/.test(flag) : flag === `--${key}`), 'Unknown or malformed option');
  }
  const options = { check: flags.includes('--check'), dryRun: flags.includes('--dry-run') };
  requireValue(!(options.check && options.dryRun), 'Choose check or dry-run');
  if (command === 'build') { requireValue(!positional.length, 'build takes no project arguments'); return buildViews(repo, options); }
  if (command === 'export') { requireValue(positional.length === 1, 'export requires a reviewed JSON input'); return exportRecord(repo, await readJson(repo, positional[0]), options); }
  if (command === 'sync-description') {
    requireValue(positional.length === 1 && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(positional[0]), 'sync-description requires one project ID');
    return syncDescription(repo, await readJson(repo, recordPath(positional[0])), options);
  }
  if (command === 'list' || command === 'validate') {
    let records = await loadRecords(repo);
    if (command === 'list') {
      requireValue(!positional.length, 'list takes filters, not project arguments');
      for (const f of flags) {
        const at = f.indexOf('='), key = f.slice(2, at), value = f.slice(at + 1);
        records = records.filter(r => key === 'status' ? r.status === value : key === 'series' ? r.seriesId === value : r.title.toLowerCase().includes(value.toLowerCase()));
      }
      return records.map(({ projectId, title, status, seriesId }) => ({ projectId, title, status, ...(seriesId ? { seriesId } : {}) }));
    }
    if (positional.length) {
      requireValue(positional.every(id => records.some(r => r.projectId === id)), 'Unknown project ID');
      records = records.filter(r => positional.includes(r.projectId));
    }
    if (flags.includes('--local-evidence')) {
      const results = [];
      for (const r of records) results.push(await validateLocalEvidence(repo, r));
      return results;
    }
    return { valid: true, records: records.map(r => r.projectId), mode: 'source-only' };
  }
  if (command === 'help' && !args.length) return { usage: 'npm run records -- validate [ID...] [--local-evidence] | build [--check|--dry-run] | list [--status=STATE] [--title=TEXT] [--series=ID] | export INPUT [--check|--dry-run] | sync-description ID [--check|--dry-run]' };
  throw new Error('Unknown command; use npm run records -- help');
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  try { console.log(json(await main(process.argv.slice(2)))); }
  catch (error) { console.error(error.message.replaceAll(process.cwd(), '.')); process.exitCode = 1; }
}
