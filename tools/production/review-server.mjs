#!/usr/bin/env node
/** Loopback-only native review server. Byte ranges let video shot buttons seek. */
import { createServer } from 'node:http';
import { createReadStream } from 'node:fs';
import { realpath, lstat } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const allowed = /^(review\.html|delivery\.json|film(?:_debug)?\.mp4|shot-\d+\.jpg)$/;
const mime = { '.html': 'text/html; charset=utf-8', '.json': 'application/json', '.mp4': 'video/mp4', '.jpg': 'image/jpeg' };

export function byteRange(header, size) {
  const m = /^bytes=(\d*)-(\d*)$/.exec(header);
  if (!m || (!m[1] && !m[2]) || size < 1) return null;
  let start, end;
  if (!m[1]) {
    const length = Number(m[2]);
    if (!Number.isSafeInteger(length) || length < 1) return null;
    start = Math.max(0, size - length); end = size - 1;
  } else {
    start = Number(m[1]); end = m[2] ? Number(m[2]) : size - 1;
    if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start >= size || end < start) return null;
    end = Math.min(end, size - 1);
  }
  return { start, end };
}

export async function startReviewServer(directory, port = 0) {
  if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('Port must be 0 through 65535');
  const root = await realpath(directory);
  if (!(await lstat(root)).isDirectory()) throw new Error('Review root must be a directory');
  const server = createServer(async (req, res) => {
    const finish = (status, headers = {}) => { res.writeHead(status, headers); res.end(); };
    if (!['GET', 'HEAD'].includes(req.method)) return finish(405, { Allow: 'GET, HEAD' });
    try {
      const name = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname).slice(1) || 'review.html';
      if (!allowed.test(name)) return finish(404);
      const file = path.join(root, name), stat = await lstat(file);
      if (!stat.isFile() || stat.isSymbolicLink()) return finish(404);
      const headers = { 'Content-Type': mime[path.extname(name)], 'Accept-Ranges': 'bytes',
        'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' };
      let range;
      if (req.headers.range && req.method === 'GET') {
        range = byteRange(req.headers.range, stat.size);
        if (!range) return finish(416, { ...headers, 'Content-Range': `bytes */${stat.size}` });
        headers['Content-Range'] = `bytes ${range.start}-${range.end}/${stat.size}`;
      }
      headers['Content-Length'] = range ? range.end - range.start + 1 : stat.size;
      res.writeHead(range ? 206 : 200, headers);
      if (req.method === 'HEAD') return res.end();
      const stream = createReadStream(file, range || undefined);
      stream.on('error', () => res.destroy());
      res.on('close', () => stream.destroy());
      stream.pipe(res);
    } catch { if (!res.headersSent) finish(404); else res.destroy(); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', resolve); });
  return { server, url: `http://127.0.0.1:${server.address().port}/review.html` };
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  const [directory, port, ...extra] = process.argv.slice(2);
  if (!directory || extra.length) throw new Error('Usage: review-server.mjs FINAL_DIRECTORY [PORT]');
  const { url } = await startReviewServer(directory, port === undefined ? 0 : Number(port));
  console.log(url);
}
