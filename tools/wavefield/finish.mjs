#!/usr/bin/env node
/** Project-scoped finish using the maintained editor after verified analysis.
 * Shared search refresh is separate from this film's delivery checks. */
import fs from 'node:fs';
import path from 'node:path';
import { finish, registerFinishClips } from '../production/edit.mjs';
import { checkProject } from '../production/clip-analysis-workflow.mjs';
import { withLock } from '../production/clip-analysis-store.mjs';

const repo = process.cwd();
const root = path.resolve(process.argv[2] ?? 'data/workspace/wavefield-v1');
const recover = process.argv.slice(3).includes('--recover-project-lock');
if (process.argv.slice(3).some(arg => arg !== '--recover-project-lock')) throw new Error('Unknown option');
const evidence = path.join(root, 'revisions/v4-4k/qa');
const result = await withLock(repo, 'project-wavefield', async () => {
  const registered = registerFinishClips(root, 'v4', 'v4-4k', 'edit/finish-v4-4k.json', { catalogRoot: repo });
  if (registered.projectId !== 'wavefield') throw new Error('Wrong project for this recipe');
  const checked = checkProject('wavefield', repo);
  fs.writeFileSync(path.join(evidence, 'direct-finish-analysis-check.json'), JSON.stringify(checked, null, 2) + '\n', { flag: 'wx' });
  if (checked.status !== 'complete') throw new Error('Required project analysis is incomplete');
  return finish(root, 'v4', 'v4-4k', 'edit/finish-v4-4k.json', { catalogRoot: repo });
}, { recover });
console.log(JSON.stringify({ ...result, projectAnalysis: 'verified-complete',
  sharedSearchIndex: 'refresh-deferred; required clip extraction and verification remain complete' }, null, 2));
