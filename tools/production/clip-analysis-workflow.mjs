/** Project-scoped analysis handoff. Imports stay fast; delivery drains and verifies the work. */
import fs from 'node:fs';
import path from 'node:path';
import { REPO, safePath, readJson, readClip, listClips, listUses, resolveClip, hashFile, requestClipAnalysis } from './clip-library.mjs';
import { validateProjectId } from './project-identity.mjs';
import { analyzeClip, toolIdentity, adoptRun } from './clip-analysis.mjs';
import { configFor, sha, runIdentity, runPath, verifyRun, privateJson, retainConfig, externalizeConfig,
  readAnalysisDocument, withLock, now, assert } from './clip-analysis-store.mjs';
import { buildSearch } from './clip-analysis-views.mjs';

const policyPath = repo => safePath(repo, 'data/clips/analysis/workflow.json');
const reportPath = (projectId, repo) => safePath(repo, `data/clips/analysis/projects/${projectId}.json`);

export function configureDefault(file, repo = REPO) {
  assert(typeof file === 'string' && file.startsWith('data/'), 'Analysis profile must be an explicitly provisioned private file under data/');
  const config = configFor(readJson(safePath(repo, file)));
  toolIdentity(config); // Check local tools, runtimes and model pins before changing the default.
  const ref = retainConfig(config, repo);
  privateJson(policyPath(repo), externalizeConfig({ schemaVersion: 1, configuredAt: now(), config }, ref));
  return { profile: config.profile, configSha256: sha(config), required: config.required,
    policy: 'data/clips/analysis/workflow.json', humanQualification: 'not-implied' };
}

function context(repo, supplied) {
  let config;
  if (supplied) config = configFor(supplied);
  else {
    assert(fs.existsSync(policyPath(repo)), 'No default analysis profile. Run clips analysis configure-default data/clips/analysis/profiles/PROFILE.json after explicit local provisioning.');
    const policy = readAnalysisDocument(policyPath(repo), repo);
    assert(policy.schemaVersion === 1, 'Unsupported analysis workflow policy');
    config = configFor(policy.config);
  }
  return { config, tools: toolIdentity(config) };
}

function projectClips(projectId, repo) {
  validateProjectId(projectId);
  const ids = new Set(listClips(repo).filter(c => c.collections.includes(projectId)).map(c => c.id));
  for (const use of listUses(repo)) if (use.projectId === projectId) ids.add(use.clipId);
  assert(ids.size > 0, 'No catalog clips associated with this project; import sources with the project collection first');
  return [...ids].sort().map(id => readClip(id, repo));
}

function inspect(clip, ctx, repo) {
  const identity = runIdentity(clip, ctx.config, { ...ctx.tools, catalogEvidenceSha256: sha(clip) });
  const row = { clipId: clip.id, runId: identity.runId, catalogSha256: sha(clip), status: 'pending', steps: {} };
  try {
    resolveClip(clip.id, repo); // Verify actual source bytes, not just catalog membership.
    const dir = runPath(clip.id, identity.runId, repo), manifest = path.join(dir, 'manifest.json');
    if (!fs.existsSync(manifest)) {
      const state = path.join(dir, 'state.json');
      if (fs.existsSync(state)) {
        row.steps = Object.fromEntries(Object.entries(readAnalysisDocument(state, repo).steps).map(([k, v]) => [k, v.state]));
        row.status = Object.values(row.steps).includes('failed') ? 'failed' : 'pending';
      }
      return row;
    }
    const m = verifyRun(clip.id, identity.runId, repo);
    row.status = 'complete'; row.manifestSha256 = hashFile(manifest);
    row.steps = Object.fromEntries(Object.entries(m.steps).map(([k, v]) => [k, v.state]));
  } catch (error) { row.status = 'invalid'; row.error = error.message; }
  return row;
}

function report(projectId, clips, ctx, repo) {
  const rows = clips.map(c => inspect(c, ctx, repo));
  return { schemaVersion: 1, projectId, checkedAt: now(), profile: ctx.config.profile,
    configSha256: sha(ctx.config), required: ctx.config.required, clips: rows.length,
    status: rows.every(r => r.status === 'complete') ? 'complete' : 'incomplete',
    counts: Object.fromEntries(['complete', 'pending', 'failed', 'invalid'].map(s => [s, rows.filter(r => r.status === s).length])),
    humanReview: 'not-asserted', needsReview: rows.filter(r => Object.values(r.steps).includes('needs-review')).map(r => r.clipId), rows };
}

export function checkProject(projectId, repo = REPO, { config } = {}) {
  validateProjectId(projectId);
  const ctx = context(repo, config), clips = projectClips(projectId, repo);
  const result = report(projectId, clips, ctx, repo);
  assert(sha(clips) === sha(projectClips(projectId, repo)), 'Project evidence changed during verification; check again');
  return result;
}

export async function processProject(projectId, repo = REPO, { config, retry = false, recover = false, progress = () => {} } = {}) {
  validateProjectId(projectId);
  return withLock(repo, `project-${projectId}`, async () => {
    const clips = projectClips(projectId, repo), ctx = context(repo, config), attempts = [];
    const before = clips.map(c => ({ id: c.id, sha256: sha(c) }));
    for (const clip of clips) {
      const request = requestClipAnalysis(clip, repo);
      const prior = inspect(clip, ctx, repo);
      if (prior.status === 'complete') { attempts.push({ clipId: clip.id, runId: prior.runId, reused: true, request }); continue; }
      try {
        const result = await analyzeClip(clip.id, repo, { config: ctx.config, tools: ctx.tools, retry, recover, progress });
        attempts.push({ ...result, request });
        if (result.status === 'complete') await adoptRun(clip.id, result.runId, repo);
      } catch (error) { attempts.push({ clipId: clip.id, status: 'failed', error: error.message, request }); }
      privateJson(reportPath(projectId, repo), { ...report(projectId, clips, ctx, repo), attempts });
    }
    const current = projectClips(projectId, repo);
    assert(sha(before) === sha(current.map(c => ({ id: c.id, sha256: sha(c) }))), 'Project clip membership or evidence changed during analysis; rerun for the current project');
    // Do not accept a batch if code, executables or model pins changed during execution.
    assert(sha(ctx.tools) === sha(toolIdentity(ctx.config)), 'Analysis tools changed during project processing');
    const result = { ...report(projectId, current, ctx, repo), attempts };
    if (attempts.some(a => a.status === 'failed' || a.status === 'incomplete')) result.status = 'incomplete';
    if (result.status === 'complete') {
      const coveragePath = safePath(repo, 'data/clips/analysis/coverage.json');
      const indexed = new Set(fs.existsSync(coveragePath) ? readJson(coveragePath).runs.map(r => r.runId) : []);
      if (result.rows.some(r => !indexed.has(r.runId))) result.index = await buildSearch(repo);
      for (const row of result.rows) {
        const receipt = safePath(repo, `data/clips/analysis/intake/${row.clipId}/${row.catalogSha256}.${row.runId}.complete.json`);
        privateJson(receipt, { schemaVersion: 1, clipId: row.clipId, catalogSha256: row.catalogSha256,
          runId: row.runId, manifestSha256: row.manifestSha256, configSha256: result.configSha256 }, true);
      }
    }
    privateJson(reportPath(projectId, repo), result);
    return { ...result, report: path.relative(repo, reportPath(projectId, repo)) };
  }, { recover });
}

export async function workflowMain(args, repo = REPO) {
  const [verb, ...rest] = args;
  if (verb === 'configure-default') {
    assert(rest.length === 1, 'Use analysis configure-default PRIVATE_PROFILE.json');
    return configureDefault(rest[0], repo);
  }
  const positional = rest.filter(a => !a.startsWith('--')), flags = rest.filter(a => a.startsWith('--'));
  assert(verb === 'process-project' && positional.length === 1
    && flags.every(f => ['--check', '--retry', '--recover'].includes(f) || f.startsWith('--config=') && f.length > 9)
    && new Set(flags.map(f => f.split('=')[0])).size === flags.length, 'Use analysis process-project PROJECT_ID [--config=PRIVATE.json] [--check] [--retry] [--recover]');
  assert(!flags.includes('--check') || !flags.some(f => ['--retry', '--recover'].includes(f)), 'Check mode cannot retry or recover work');
  const configFile = flags.find(f => f.startsWith('--config='))?.slice(9);
  assert(!configFile || configFile.startsWith('data/'), 'Analysis configuration must remain under data/');
  const options = { config: configFile ? readJson(safePath(repo, configFile)) : undefined,
    retry: flags.includes('--retry'), recover: flags.includes('--recover'), progress: e => process.stderr.write(JSON.stringify(e) + '\n') };
  return flags.includes('--check') ? checkProject(positional[0], repo, options) : processProject(positional[0], repo, options);
}
