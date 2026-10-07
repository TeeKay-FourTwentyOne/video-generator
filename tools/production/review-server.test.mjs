import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { startReviewServer } from './review-server.mjs';

test('review server supports native video ranges without exposing the workspace', async t => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'review-server-'));
  await fs.writeFile(path.join(root, 'film.mp4'), '01234567');
  await fs.writeFile(path.join(root, 'review.html'), '<video src="film.mp4"></video>');
  await fs.writeFile(path.join(root, 'private.txt'), 'must not serve');
  await fs.symlink(path.join(root, 'private.txt'), path.join(root, 'delivery.json'));
  const { server, url } = await startReviewServer(root);
  t.after(async () => { server.closeAllConnections(); await new Promise(r => server.close(r)); await fs.rm(root, { recursive: true, force: true }); });
  const movie = new URL('film.mp4', url);
  assert.equal(server.address().address, '127.0.0.1');
  for (const [range, body, contentRange] of [['bytes=2-4', '234', 'bytes 2-4/8'], ['bytes=-2', '67', 'bytes 6-7/8'], ['bytes=5-', '567', 'bytes 5-7/8']]) {
    const res = await fetch(movie, { headers: { Range: range } });
    assert.equal(res.status, 206); assert.equal(res.headers.get('content-range'), contentRange);
    assert.equal(res.headers.get('content-length'), String(body.length)); assert.equal(await res.text(), body);
  }
  for (const range of ['bytes=8-', 'bytes=5-2', 'bytes=-0', 'bytes=0-1,4-5']) {
    const res = await fetch(movie, { headers: { Range: range } });
    assert.equal(res.status, 416); assert.equal(res.headers.get('content-range'), 'bytes */8');
  }
  const head = await fetch(movie, { method: 'HEAD' });
  assert.equal(head.status, 200); assert.equal(head.headers.get('content-length'), '8'); assert.equal(await head.text(), '');
  assert.equal(await (await fetch(movie)).text(), '01234567');
  assert.equal((await fetch(url)).status, 200);
  assert.equal((await fetch(movie, { method: 'POST' })).status, 405);
  for (const name of ['private.txt', 'delivery.json', '%2e%2e%2fprivate.txt', '']) {
    const target = name ? new URL(name, url) : new URL('nested/', url);
    assert.equal((await fetch(target)).status, 404);
  }
});
