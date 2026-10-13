/** Metered qualification of the repository's existing Google image path.
 * Uses the same Vertex provider/auth as nano-banana.cjs, no SDK or new service.
 */
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { getGoogleAccessToken, buildVertexUrl } from '../../mcp/video-generator/dist/clients/google-auth.js';
import { reserveSpend, updateSpend, reconcileSpend, atomicJson } from '../../mcp/video-generator/dist/production/ledger.js';
import { localPath, hashFile } from './film.mjs';
import { saveGenerationSnapshot, snapshotHash } from './generation-snapshot.mjs';

export async function generateAnchor(root, request) {
  if (typeof request.id !== 'string' || !/^[A-Za-z0-9_-]+$/.test(request.id)) throw new Error('Image request needs a stable id');
  if (!['9:16', '16:9', '1:1'].includes(request.aspectRatio)) throw new Error('Unsupported image aspect ratio');
  const model = 'gemini-3-pro-image';
  const output = localPath(root, request.output);
  if (fs.existsSync(output)) throw new Error('Refusing to replace an existing image');
  const prompt = fs.readFileSync(localPath(root, request.promptFile), 'utf8');
  if (prompt.length > 12000) throw new Error('Prompt exceeds qualified image request size');
  if ((request.refs ?? []).length > 3) throw new Error('At most three reference images in the bounded image route');
  const sources = [];
  const parts = (request.refs ?? []).map(ref => {
    const p = localPath(root, ref);
    if (fs.statSync(p).size > 8 * 1024 * 1024) throw new Error('Reference exceeds 8 MiB limit');
    const bytes = fs.readFileSync(p), mimeType = /\.jpe?g$/i.test(p) ? 'image/jpeg' : 'image/png';
    sources.push({ role: 'reference_image', sha256: createHash('sha256').update(bytes).digest('hex'), bytes: bytes.length, mimeType });
    return { inlineData: { mimeType, data: bytes.toString('base64') } };
  });
  parts.push({ text: prompt });
  const body = { contents: [{ role: 'user', parts }], generationConfig: {
    responseModalities: ['IMAGE', 'TEXT'], maxOutputTokens: 6144,
    imageConfig: { aspectRatio: request.aspectRatio, imageSize: '2K' } } };
  const budget = localPath(root, 'budget.json');
  const usageFile = localPath(root, `operations/${request.id}.usage.json`);
  localPath(root, `operations/${request.id}.request.json`);
  const fingerprint = createHash('sha256').update(JSON.stringify(body)).digest('hex');
  // Worst-case output at $120/M plus bounded inputs; retain reserve until usage is reconciled.
  reserveSpend(budget, { id: request.id, category: 'image', usd: .80,
    fingerprint, note: 'Bounded 2K Google image generation' });
  try {
    const snapshot = saveGenerationSnapshot(budget, { provider: 'google-image', requestId: request.id, fingerprint, prompt,
      model, parameters: body.generationConfig, sources, api: { endpoint: 'generateContent', version: 'v1', location: 'global' } });
    const { accessToken, projectId } = await getGoogleAccessToken();
    const response = await fetch(buildVertexUrl(projectId, model, 'generateContent', 'global'), {
      method: 'POST', headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body), signal: AbortSignal.timeout(240000) });
    if (response.status === 429) {
      // Rate limited: the provider rejected the request before any generation, so the reservation is
      // reconciled to zero on that evidence. There is still no automatic retry; re-request under a new ID.
      updateSpend(budget, request.id, { status: 'failed', evidence: 'HTTP 429 rate limit; request rejected before generation' });
      reconcileSpend(budget, request.id, 0, 'HTTP 429 rate limit response: request rejected before generation, no usage record');
      throw Object.assign(new Error('Google image request was rate limited (HTTP 429); wait about ten seconds and re-request under a new ID'), { rateLimited: true });
    }
    if (!response.ok) throw new Error(`Google image request failed with HTTP ${response.status}`);
    const data = await response.json();
    const image = data.candidates?.[0]?.content?.parts?.find(p => p.inlineData?.mimeType?.startsWith('image/'));
    atomicJson(usageFile, { model, modelVersion: data.modelVersion ?? null, snapshotSha256: snapshotHash(snapshot), usage: data.usageMetadata ?? null,
      finishReason: data.candidates?.[0]?.finishReason, output: request.output });
    if (!image) throw new Error('Image request completed without image; inspect usage record before any new attempt');
    fs.writeFileSync(output, Buffer.from(image.inlineData.data, 'base64'), { flag: 'wx' });
    atomicJson(localPath(root, `operations/${request.id}.asset.json`), { output: request.output, sha256: hashFile(output),
      snapshotSha256: snapshotHash(snapshot), createdAt: new Date().toISOString() });
    updateSpend(budget, request.id, { status: 'complete', model, evidence: `SHA256 ${hashFile(output)}; usage record saved` });
    return { output: request.output, sha256: hashFile(output), model, usage: data.usageMetadata ?? null };
  } catch (error) {
    if (!error.rateLimited)
      updateSpend(budget, request.id, { status: 'uncertain', evidence: 'Image request did not complete locally; retained full reserve, no automatic retry' });
    throw error;
  }
}
