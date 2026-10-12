#!/usr/bin/env node
/** Offline discovery, ingestion, validation and analytics. Never calls a provider. */
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { REPO, readJson, importClip, resolveClip, readClip, listClips, listUses, analytics, search, run,
  hashFile, recordUse, safePath, atomicJson, validateUse, canonical } from './clip-library.mjs';
import { migrate } from './clip-import.mjs';

export function extract(id, inFrame, frames, output, repo = REPO) {
  if (!Number.isSafeInteger(inFrame) || inFrame < 0 || !Number.isSafeInteger(frames) || frames < 1) throw new Error('Specify integer frame range');
  const source = resolveClip(id, repo), clip = readClip(id, repo);
  let available = clip.technical.frameCount;
  if (available === null) available = Number(run('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', source]).trim());
  if (!Number.isSafeInteger(available) || inFrame + frames > available) throw new Error('Requested range exceeds source frames');
  const target = safePath(repo, output);
  if (!target.startsWith(path.join(repo, 'data/workspace') + path.sep) || path.extname(target) !== '.mp4') throw new Error('Extract into a new MP4 under data/workspace');
  if (fs.existsSync(target) || fs.existsSync(`${target}.clip.json`)) throw new Error('Extraction already exists');
  fs.mkdirSync(path.dirname(target), { recursive: true });
  run('ffmpeg', ['-v', 'error', '-n', '-i', source, '-an', '-vf', `trim=start_frame=${inFrame}:end_frame=${inFrame + frames},setpts=PTS-STARTPTS`,
    '-frames:v', String(frames), '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', target]);
  run('ffmpeg', ['-v', 'error', '-i', target, '-f', 'null', '-']);
  const actual = Number(run('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-count_frames', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', target]).trim());
  if (actual !== frames || hashFile(source) !== clip.sha256) throw new Error('Extract verification failed');
  const result = { schemaVersion: 1, clipId: id, sourceSha256: clip.sha256, inFrame, frames, frameRate: clip.technical.frameRate,
    output, sha256: hashFile(target), audio: 'omitted' };
  atomicJson(`${target}.clip.json`, result); return result;
}
export async function main(args, repo = REPO) {
  const [verb, ...rest] = args;
  if (!verb || verb === 'help') return { commands: ['migrate', 'import FILE [PUBLIC_METADATA.json]', 'search QUERY', 'show CLIP_ID',
    'resolve CLIP_ID', 'extract CLIP_ID IN_FRAME FRAMES data/workspace/PROJECT/edit/portion.mp4', 'record-use PUBLIC_USE.json',
    'analytics', 'index [--check]', 'validate [--media]'], storage: 'data/clips/<clip_id>/source.<ext>', metadata: 'catalog/clips and catalog/uses' };
  if (verb === 'migrate') {
    const report = migrate(repo, event => process.stderr.write(JSON.stringify(event) + '\n'));
    return { ...report, failedFiles: report.failedFiles.length, unresolvedMetadata: report.unresolvedMetadata.length,
      unsupportedEdits: report.unsupportedEdits.length, missingReferences: report.missingReferences.length, report: 'data/clips/migration-report.json' };
  }
  if (verb === 'import') return importClip(path.resolve(rest[0]), rest[1] ? readJson(rest[1]) : {}, repo);
  if (verb === 'search') return search(rest.join(' '), repo);
  if (verb === 'show') return { ...readClip(rest[0], repo), uses: listUses(repo).filter(u => u.clipId === rest[0]) };
  if (verb === 'resolve') return { path: path.relative(repo, resolveClip(rest[0], repo)) };
  if (verb === 'extract') return extract(rest[0], Number(rest[1]), Number(rest[2]), rest[3], repo);
  if (verb === 'record-use') return recordUse(readJson(rest[0]), repo);
  if (verb === 'analytics') return analytics(repo);
  if (verb === 'index') {
    if (rest.some(a => a !== '--check')) throw new Error('Unknown index option');
    const uses = listUses(repo), counts = new Map();
    for (const use of uses) { const c = counts.get(use.clipId) ?? { planned: 0, rendered: 0 }; c[use.status]++; counts.set(use.clipId, c); }
    const clips = listClips(repo).map(c => ({ id: c.id, metadata: `clips/${c.id}.json`, labels: c.labels, kind: c.kind,
      collections: c.collections, durationSeconds: c.technical.durationSeconds, width: c.technical.width, height: c.technical.height,
      hasPrompt: c.generations.some(g => !!g.prompt), uses: counts.get(c.id) ?? { planned: 0, rendered: 0 } }));
    const index = { schemaVersion: 1, clips }, file = safePath(repo, 'catalog/index.json');
    if (rest.includes('--check')) {
      if (!fs.existsSync(file) || JSON.stringify(canonical(readJson(file))) !== JSON.stringify(canonical(index))) throw new Error('Catalog index is stale; run npm run clips -- index');
    } else atomicJson(file, index);
    return { clips: clips.length, index: 'catalog/index.json', checked: rest.includes('--check') };
  }
  if (verb === 'validate') {
    if (rest.some(a => a !== '--media')) throw new Error('Unknown validate option');
    const clips = listClips(repo), uses = listUses(repo), ids = new Map(clips.map(c => [c.id, c]));
    for (const use of uses) {
      if (!ids.has(use.clipId)) throw new Error('Usage references missing clip metadata');
      validateUse(use, ids.get(use.clipId));
    }
    if (rest.includes('--media')) for (const clip of clips) resolveClip(clip.id, repo);
    return { clips: clips.length, uses: uses.length, mediaVerified: rest.includes('--media'), valid: true };
  }
  throw new Error('Unknown clips command; run npm run clips -- help');
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main(process.argv.slice(2)).then(value => console.log(JSON.stringify(value, null, 2)))
    .catch(error => { console.error(error.message); process.exitCode = 1; });
}
