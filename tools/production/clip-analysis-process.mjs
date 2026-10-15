import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { gzipSync, createGunzip } from 'node:zlib';
import { createInterface } from 'node:readline';
import { once } from 'node:events';
import { assert, filesUnder, checkSpace } from './clip-analysis-store.mjs';

export function offlineEnv(threads = 2) {
  return { PATH: process.env.PATH, HOME: process.env.HOME, TMPDIR: process.env.TMPDIR ?? '/tmp',
    LANG: 'C.UTF-8', LC_ALL: 'C', HF_HUB_OFFLINE: '1', TRANSFORMERS_OFFLINE: '1', HF_DATASETS_OFFLINE: '1',
    HF_HUB_DISABLE_TELEMETRY: '1', DO_NOT_TRACK: '1', TOKENIZERS_PARALLELISM: 'false', PYTHONDONTWRITEBYTECODE: '1', PYTHONNOUSERSITE: '1',
    OMP_NUM_THREADS: String(threads), OPENBLAS_NUM_THREADS: String(threads), MKL_NUM_THREADS: String(threads) };
}
export function toolVersion(binary) {
  const p = spawnSync(binary, ['-version'], { encoding: 'utf8', timeout: 10000, maxBuffer: 1024 * 1024, env: offlineEnv() });
  assert(p.status === 0, 'Required local analysis tool is unavailable');
  return p.stdout.trim();
}
export function resolveBinary(binary) {
  const candidates = binary.includes('/') ? [path.resolve(binary)] : (process.env.PATH ?? '').split(path.delimiter).map(p => path.join(p, binary));
  for (const c of candidates) { try { fs.accessSync(c, fs.constants.X_OK); return fs.realpathSync(c); } catch {} }
  throw new Error('Required local analysis executable is unavailable');
}
/** No shell, no inherited provider credentials, bounded output, wall time and free space. */
export async function execute(binary, args, context, { onLine, stdoutFile, networkDenied = false } = {}) {
  const { dir, config } = context, started = Date.now(), seq = context.commands.length;
  checkSpace(dir, config.limits);
  const stderrFile = path.join(dir, `command-${seq}.stderr.log`), stderr = fs.openSync(stderrFile, 'wx', 0o600);
  let program = binary, argv = args;
  if (networkDenied) {
    assert(process.platform === 'darwin' && fs.existsSync('/usr/bin/sandbox-exec'), 'Offline model execution needs an OS network-denial sandbox');
    program = '/usr/bin/sandbox-exec'; argv = ['-p', '(version 1)(allow default)(deny network*)', binary, ...args];
  }
  const child = spawn(program, argv, { cwd: dir, env: offlineEnv(config.threads), stdio: ['ignore', 'pipe', stderr] });
  const command = { binary, args, startedAt: new Date(started).toISOString(), networkDenied, peakRssBytes: null, rssMethod: 'sampled child RSS; excludes GPU allocations' };
  context.commands.push(command);
  let failure, bytes = 0, pending = '', stopTimer;
  const stop = error => { failure ??= error; child.kill('SIGTERM'); stopTimer ??= setTimeout(() => child.kill('SIGKILL'), 2000); };
  const finished = new Promise(resolve => { child.on('error', e => { failure = new Error(`Analysis executable could not start (${e.code ?? 'unknown'})`); }); child.on('close', (code, signal) => resolve({ code, signal })); });
  const timer = setInterval(() => {
    try {
      if (Date.now() - started > config.limits.timeoutSeconds * 1000) throw new Error('Analysis execution time limit exceeded');
      checkSpace(dir, config.limits);
      const size = filesUnder(dir).reduce((s, p) => s + fs.statSync(path.join(dir, p)).size, 0);
      if (size > config.limits.maxOutputBytes) throw new Error('Analysis output limit exceeded');
      const p = spawnSync('/bin/ps', ['-o', 'rss=', '-p', String(child.pid)], { encoding: 'utf8', timeout: 1000 });
      const rss = Number(p.stdout?.trim()) * 1024;
      if (Number.isFinite(rss)) command.peakRssBytes = Math.max(command.peakRssBytes ?? 0, rss);
    } catch (e) { stop(e); }
  }, 1000);
  let out;
  try {
    if (stdoutFile) out = fs.openSync(stdoutFile, 'wx', 0o600);
    for await (const chunk of child.stdout) {
      bytes += chunk.length;
      if (bytes > config.limits.maxOutputBytes) { stop(new Error('Analysis stdout limit exceeded')); break; }
      if (out !== undefined) fs.writeSync(out, chunk);
      if (onLine) {
        pending += chunk.toString('utf8'); let i;
        while ((i = pending.indexOf('\n')) >= 0) { await onLine(pending.slice(0, i)); pending = pending.slice(i + 1); }
        assert(pending.length < 2 * 1024 * 1024, 'Analysis parser line limit exceeded');
      }
    }
    if (onLine && pending.trim()) await onLine(pending);
  } catch (e) { stop(e); }
  const result = await finished;
  clearInterval(timer); clearTimeout(stopTimer); fs.closeSync(stderr); if (out !== undefined) fs.closeSync(out);
  command.elapsedMs = Date.now() - started; command.exitCode = result.code; command.signal = result.signal;
  if (failure) throw failure;
  assert(result.code === 0, 'Local analysis command failed; retained private diagnostics');
  const size = filesUnder(dir).reduce((s, p) => s + fs.statSync(path.join(dir, p)).size, 0);
  assert(size <= config.limits.maxOutputBytes, 'Analysis output limit exceeded');
  return command;
}
export class GzipLines {
  constructor(file) { this.fd = fs.openSync(file, 'wx', 0o600); this.pending = ''; this.count = 0; }
  write(row) { this.pending += JSON.stringify(row) + '\n'; this.count++; if (this.pending.length >= 512 * 1024) this.flush(); }
  flush() { if (this.pending) { fs.writeSync(this.fd, gzipSync(this.pending)); this.pending = ''; } }
  close() { if (!this.count) fs.writeSync(this.fd, gzipSync('')); this.flush(); fs.closeSync(this.fd); }
}
export async function* readLines(file) {
  const source = fs.createReadStream(file), unzip = createGunzip();
  source.on('error', e => unzip.destroy(e)); source.pipe(unzip);
  const lines = createInterface({ input: unzip, crlfDelay: Infinity });
  // readline does not forward input errors through its iterator on all supported Node versions.
  let failure; unzip.on('error', e => { failure = e; lines.close(); });
  try { for await (const line of lines) if (line.trim()) yield JSON.parse(line); if (failure) throw failure; }
  finally { lines.close(); source.destroy(); unzip.destroy(); }
}
export function compact(line) {
  // Only numeric/timing/codec-enum fields are requested. Reject unexpected escaped delimiters.
  assert(!line.includes('\\|'), 'Unexpected escaped field in timing output');
  const values = {};
  for (const field of line.split('|')) { const i = field.indexOf('='); if (i > 0) values[field.slice(0, i)] = field.slice(i + 1); }
  return values;
}
export function seconds(pts, timeBase) {
  assert(/^-?\d+$/.test(String(pts)) && /^\d+\/[1-9]\d*$/.test(timeBase), 'Missing exact presentation timestamp');
  const [n, d] = timeBase.split('/').map(BigInt);
  // Float seconds are convenience values only; exact PTS and rational time base remain authoritative.
  return Number(BigInt(pts) * n) / Number(d);
}
