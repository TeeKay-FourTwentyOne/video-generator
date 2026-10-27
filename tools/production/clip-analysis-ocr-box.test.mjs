import test from 'node:test';
import assert from 'node:assert/strict';
import { validateObservations } from './clip-analysis-adapters.mjs';

const sourceSha256 = 'a'.repeat(64);
const ctx = { sourceSha256, step: 'ocr', streams: [{ index: 0, codec_type: 'video', start_time: 0, duration: 8 }], samples: [{ streamIndex: 0, frameIndex: 48, seconds: 2 }] };
const payload = boxNormalized => ({ schemaVersion: 1, observations: [{ sourceSha256, evidenceType: 'model-observation', streamIndex: 0, startSeconds: 2, endSeconds: 2,
  frameIndices: [48], text: 'x', originalText: 'x', boxNormalized, confidence: { source: 'fixture', value: 0.3, interpretation: 'uncalibrated model score' } }] });

test('OCR boxes tolerate float noise at the frame edge but not an out-of-frame box', () => {
  // Apple Vision reported this box on a real take: the left edge sits a few 1e-9 below zero.
  assert.ok(validateObservations(payload([-5.575968417856656e-09, 0.36562500029296874, 0.044444455040825739, 0.046875]), ctx));
  assert.ok(validateObservations(payload([0, 0, 1, 1.0000000001]), ctx));
  assert.throws(() => validateObservations(payload([-0.01, 0, 1, 1]), ctx), /Invalid OCR text or bounding box/);
  assert.throws(() => validateObservations(payload([0, 0, 1, 1.001]), ctx), /Invalid OCR text or bounding box/);
});
