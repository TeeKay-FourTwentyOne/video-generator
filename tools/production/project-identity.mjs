/** Explicit workspace identity, kept separate from spending and generation evidence. */
import fs from 'node:fs';
import { randomUUID } from 'node:crypto';
import { safePath, publicText } from './clip-library.mjs';

export function validateProjectId(id) {
  if (typeof id !== 'string' || id.length > 100 || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id)
      || publicText(id) !== id)
    throw new Error('Invalid project ID; use at most 100 lowercase letters, digits and single separating hyphens');
  return id;
}

export function readProjectIdentity(root) {
  const file = safePath(root, 'workspace.json');
  let text;
  try { text = fs.readFileSync(file, 'utf8'); }
  catch (e) { if (e.code === 'ENOENT') return undefined; throw e; }
  let metadata;
  try { metadata = JSON.parse(text); }
  catch { throw new Error('Unreadable workspace.json; restore the workspace identity'); }
  if (metadata?.schemaVersion !== 1 || Object.keys(metadata).some(k => !['schemaVersion', 'projectId'].includes(k)))
    throw new Error('Invalid workspace.json; expected schemaVersion 1 and projectId');
  return validateProjectId(metadata.projectId);
}

/** Atomic no-clobber install; retries verify the identity and never replace it. */
export function writeProjectIdentity(root, projectId) {
  validateProjectId(projectId);
  const file = safePath(root, 'workspace.json');
  const verify = () => {
    if (readProjectIdentity(root) !== projectId) throw new Error('Project identity conflict with workspace.json');
  };
  if (fs.existsSync(file)) { verify(); return; }
  fs.mkdirSync(root, { recursive: true });
  const tmp = `${file}.${randomUUID()}.tmp`;
  try {
    const fd = fs.openSync(tmp, 'wx', 0o600);
    try { fs.writeFileSync(fd, JSON.stringify({ schemaVersion: 1, projectId }, null, 2) + '\n'); fs.fsyncSync(fd); }
    finally { fs.closeSync(fd); }
    try { fs.linkSync(tmp, file); }
    catch (e) { if (e.code !== 'EEXIST') throw e; verify(); }
  } finally { fs.rmSync(tmp, { force: true }); }
}
