import fs from "fs";
import path from "path";
import { createHash } from "node:crypto";
import { atomicJson, readLedger, reserveSpend, updateSpend } from "../production/ledger.js";
import { qualifyVeo, type VeoModelAlias } from "../production/veo-spec.js";
export { VEO_MODELS, type VeoModelAlias } from "../production/veo-spec.js";
import { getGoogleAccessToken, buildVertexUrl } from "./google-auth.js";
import {
  uploadBytesToGcs,
  buildObjectName,
  inferImageMimeType,
} from "./gcs.js";
import { resolvePath } from "../utils/paths.js";
import { importClip, generationMetadata, REPO } from "../../../../tools/production/clip-library.mjs";
import { loadConfig } from "../utils/config.js";
import { readGenerationSnapshot, saveGenerationSnapshot, snapshotHash } from "../../../../tools/production/generation-snapshot.mjs";

const VEO_MODEL_DEFAULT = "veo-3.1-generate-001";

export interface VeoSubmitOptions {
  prompt: string;
  budgetFile?: string;
  requestId?: string;
  aspectRatio?: string;
  durationSeconds?: number;
  firstFramePath?: string;
  lastFramePath?: string;
  model?: VeoModelAlias;
  seed?: number;
  generateAudio?: boolean;
  resolution?: "720p" | "1080p" | "4k";
}

export interface VeoSubmitResult {
  operationName: string;
  model: string;
  seed?: number;
}

export interface VeoPollResult {
  done: boolean;
  operationName: string;
  video?: {
    bytesBase64Encoded?: string;
    uri?: string;
    gcsUri?: string;
  };
  error?: string;
}

export interface VeoDownloadResult {
  filename: string;
  path: string;
  duration: number | null;
  clipId: string;
  sha256: string;
}

async function buildImageField(
  imagePath: string,
  bytes: Buffer,
  bucket: string | undefined,
  gcsPrefix: string
): Promise<Record<string, string>> {
  const mimeType = inferImageMimeType(imagePath);
  if (bucket) {
    const objectName = buildObjectName(gcsPrefix, imagePath);
    const gcsUri = await uploadBytesToGcs(bytes, bucket, objectName, mimeType);
    return { gcsUri, mimeType };
  }
  return {
    bytesBase64Encoded: bytes.toString("base64"),
    mimeType,
  };
}

/**
 * Submit a video generation request to Veo
 * Returns operation name for polling
 */
export async function submitVeoGeneration(
  options: VeoSubmitOptions
): Promise<VeoSubmitResult> {
  const spec = qualifyVeo(options);
  const { prompt, firstFramePath, lastFramePath } = options;
  const { modelId, durationSeconds: validDuration, aspectRatio, generateAudio, resolution } = spec;
  if (!options.budgetFile || typeof options.requestId !== "string" || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$/.test(options.requestId))
    throw new Error("Veo requires budgetFile and a stable requestId. Use the production CLI to initialize an authorized all-in budget.");
  const budgetFile = resolvePath(options.budgetFile);
  const requestId = options.requestId;
  // Hash and send the same in-memory bytes, even if the original is edited during auth/upload.
  const firstBytes = firstFramePath ? fs.readFileSync(resolvePath(firstFramePath)) : undefined;
  const lastBytes = lastFramePath ? fs.readFileSync(resolvePath(lastFramePath)) : undefined;
  const anchorHash = (bytes: Buffer | undefined) => bytes ? createHash("sha256").update(bytes).digest("hex") : null;
  const fingerprint = createHash("sha256").update(JSON.stringify({ ...spec, prompt,
    first: anchorHash(firstBytes), last: anchorHash(lastBytes), seed: options.seed ?? null })).digest("hex");
  const journalFile = path.join(path.dirname(budgetFile), "operations", `${requestId}.json`);
  const existing = readLedger(budgetFile).entries.find(e => e.id === requestId);
  if (existing) {
    if (existing.category !== "veo" || existing.fingerprint !== fingerprint) throw new Error("Request ID reused with changed content; preserve the original and use a new attempt ID");
    if (existing.operationName) return { operationName: existing.operationName, model: existing.model!, seed: existing.seed };
    if (fs.existsSync(journalFile)) {
      const saved = JSON.parse(fs.readFileSync(journalFile, "utf8"));
      if (saved.provider === "veo" && saved.fingerprint === fingerprint && saved.operationName) {
        updateSpend(budgetFile, requestId, { status: "submitted", operationName: saved.operationName, model: modelId, seed: saved.seed });
        return { operationName: saved.operationName, model: modelId, seed: saved.seed };
      }
    }
    throw new Error("Request already reserved without a known operation; reconcile it before any new paid attempt");
  }
  if (fs.existsSync(journalFile)) throw new Error("Existing Veo operation record has no matching reservation; inspect before proceeding");
  // Deterministic seed selection makes crash recovery inspectable; provider output is not guaranteed deterministic.
  const effectiveSeed = options.seed ?? parseInt(createHash("sha256").update(requestId).digest("hex").slice(0, 8), 16);
  // Reserve before auth, uploads or POST. Failure never releases money automatically.
  reserveSpend(budgetFile, { id: requestId, category: "veo", fingerprint, usd: spec.estimatedUsd, note: "Veo generation attempt" });
  const parameters = { aspectRatio, durationSeconds: validDuration, seed: effectiveSeed, sampleCount: 1, generateAudio, resolution };
  const sources = [firstBytes && { role: "first_frame", sha256: anchorHash(firstBytes), bytes: firstBytes.length,
    mimeType: inferImageMimeType(firstFramePath!) }, lastBytes && { role: "last_frame", sha256: anchorHash(lastBytes),
    bytes: lastBytes.length, mimeType: inferImageMimeType(lastFramePath!) }].filter(Boolean);
  const record = { schemaVersion: 1, provider: "veo", requestId, fingerprint, prompt, model: modelId,
    seed: effectiveSeed, parameters, sources, createdAt: new Date().toISOString() };
  let operationName: string | undefined;
  try {
    const snapshot = saveGenerationSnapshot(budgetFile, { provider: "veo", requestId, fingerprint, prompt,
      requestedModel: options.model, model: modelId, seed: effectiveSeed,
      parameters: { ...parameters, mode: firstFramePath ? "image-to-video" : "text-to-video" }, sources,
      api: { endpoint: "predictLongRunning", version: "v1", location: "us-central1" } });
    Object.assign(record, { snapshotSha256: snapshotHash(snapshot) });
    atomicJson(journalFile, { ...record, status: "reserved" });
    const { accessToken, projectId } = await getGoogleAccessToken();
    const bucket = loadConfig().veoGcsBucket;
    // Build instance with optional reference frames
    const instance: Record<string, unknown> = { prompt };

    if (firstFramePath) {
      instance.image = await buildImageField(
        firstFramePath,
        firstBytes!,
        bucket,
        "veo-inputs/image"
      );
    }

    if (lastFramePath) {
      instance.lastFrame = await buildImageField(
        lastFramePath,
        lastBytes!,
        bucket,
        "veo-inputs/last-frame"
      );
    }

    const transportParameters: Record<string, unknown> = { ...parameters };

    // storageUri tells Veo to write the output MP4 to GCS and return a URI,
    // instead of returning a multi-MB base64-encoded video inline.
    if (bucket) {
      const stamp = Date.now().toString(36);
      const rand = Math.random().toString(36).slice(2, 8);
      transportParameters.storageUri = `gs://${bucket}/veo-outputs/${stamp}-${rand}/`;
    }

    const requestBody = {
      instances: [instance],
      parameters: transportParameters,
    };

    const url = buildVertexUrl(projectId, modelId, "predictLongRunning");

    const response = await fetch(url, {
      method: "POST",
      signal: AbortSignal.timeout(120_000),
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Veo submission failed: ${response.status} ${errorText}`);
    }

    const data = (await response.json()) as { name: string };
    if (!data.name) throw new Error("Veo response omitted operation name; submission outcome is uncertain");
    operationName = data.name;
    atomicJson(journalFile, { ...record, operationName, status: "submitted" });
    updateSpend(budgetFile, requestId, { status: "submitted", operationName, model: modelId, seed: effectiveSeed });
    return { operationName, model: modelId, seed: effectiveSeed };
  } catch (error) {
    const status = operationName ? "submitted" : "uncertain";
    const evidence = "Submission did not complete locally; reservation retained. Inspect private provider logs before another attempt.";
    try { atomicJson(journalFile, { ...record, operationName, status, evidence }); } catch { /* Preserve ledger recovery below. */ }
    try { updateSpend(budgetFile, requestId, { status, operationName, model: modelId, seed: effectiveSeed, evidence }); } catch { /* Journal retains evidence. */ }
    throw error;
  }
}

/**
 * Poll Veo operation status
 */
export async function pollVeoOperation(
  operationName: string,
  modelId?: string
): Promise<VeoPollResult> {
  const { accessToken, projectId } = await getGoogleAccessToken();

  // Extract model from operation name if not provided (e.g. .../models/veo-3.1-generate-001/operations/...)
  if (!modelId) {
    const match = operationName.match(/models\/([^/]+)\/operations/);
    if (match) modelId = match[1];
  }

  const url = buildVertexUrl(projectId, modelId || VEO_MODEL_DEFAULT, "fetchPredictOperation");

  const response = await fetch(url, {
    method: "POST",
    signal: AbortSignal.timeout(120_000),
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ operationName }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Veo poll failed: ${response.status} ${errorText}`);
  }

  return interpretVeoOperation(await response.json(), operationName);
}

/** Pure operation decoder, tested without credentials. A terminal empty response is never pending. */
export function interpretVeoOperation(raw: unknown, operationName: string): VeoPollResult {
  const data = raw as { done?: boolean; error?: { message?: string }; response?: {
    videos?: VeoPollResult["video"][]; raiMediaFilteredCount?: number; raiMediaFilteredReasons?: string[];
  } };
  if (!data || typeof data !== "object") throw new Error("Malformed Veo operation response");
  if (data.error) return { done: true, operationName, error: data.error.message || "Veo operation failed" };
  if (!data.done) return { done: false, operationName };
  const video = data.response?.videos?.[0];
  if (video && (video.bytesBase64Encoded || video.gcsUri || video.uri)) return { done: true, operationName, video };
  return { done: true, operationName, error: data.response?.raiMediaFilteredCount
    ? "Veo completed with filtered output; no automatic retry" : "Veo completed without usable video" };
}

/**
 * Download video from Veo result and save to disk
 */
export async function downloadVeoVideo(
  result: VeoPollResult,
  options: { request?: Record<string, unknown>; generationSource?: string; generationSnapshot?: Record<string, any>;
    collections?: string[]; catalogRoot?: string } = {}
): Promise<VeoDownloadResult> {
  if (!result.video) {
    throw new Error("No video in result");
  }

  const timestamp = Date.now();
  const randomId = Math.random().toString(36).substring(2, 8);
  const filename = `veo_${timestamp}_${randomId}.mp4`;
  const incoming = path.join(options.catalogRoot ?? REPO, 'data/clips/.incoming');
  const outputPath = path.join(incoming, filename);

  // Ensure video directory exists
  if (!fs.existsSync(incoming)) {
    fs.mkdirSync(incoming, { recursive: true });
  }

  const gcsUri = result.video.gcsUri || result.video.uri;
  if (result.video.bytesBase64Encoded) {
    const buffer = Buffer.from(result.video.bytesBase64Encoded, "base64");
    fs.writeFileSync(outputPath, buffer);
  } else if (gcsUri) {
    const { accessToken } = await getGoogleAccessToken();
    const videoData = await downloadFromGcs(gcsUri, accessToken);
    fs.writeFileSync(outputPath, videoData);
  } else {
    throw new Error("No video data or URI in result");
  }

  let snapshot = options.generationSnapshot;
  // Legacy jobs also submit through this client and retain their budget/request identity.
  if (!snapshot && typeof options.request?.budgetFile === 'string' && typeof options.request?.requestId === 'string') {
    const budgetFile = resolvePath(options.request.budgetFile);
    const entry = readLedger(budgetFile).entries.find(e => e.id === options.request!.requestId);
    if (!entry || entry.operationName !== result.operationName) throw new Error('Veo download does not match the reserved operation');
    const journalFile = path.join(path.dirname(budgetFile), 'operations', `${entry.id}.json`);
    const journal = fs.existsSync(journalFile) ? JSON.parse(fs.readFileSync(journalFile, 'utf8')) : {};
    snapshot = readGenerationSnapshot(budgetFile, entry.id, { provider: 'veo', fingerprint: entry.fingerprint, model: entry.model,
      snapshotSha256: journal.snapshotSha256 });
  }
  const clip = importClip(outputPath, { kind: 'source', generationSnapshot: snapshot, collections: options.collections,
    generations: snapshot ? [] : [generationMetadata({ ...options.request, provider: 'veo' }, options.generationSource)] }, options.catalogRoot);
  fs.unlinkSync(outputPath);

  return {
    filename: `${clip.id}.mp4`,
    path: clip.path,
    duration: clip.record.technical.durationSeconds,
    clipId: clip.id,
    sha256: clip.sha256,
  };
}

/**
 * Download file from GCS URI
 */
async function downloadFromGcs(
  gcsUri: string,
  accessToken: string
): Promise<Buffer> {
  // Convert the provider's GCS object URI to its authenticated HTTPS endpoint.
  const httpsUrl = gcsUri.replace(
    /^gs:\/\/([^/]+)\/(.+)$/,
    "https://storage.googleapis.com/$1/$2"
  );

  const parsed = new URL(httpsUrl);
  if (parsed.protocol !== "https:" || parsed.hostname !== "storage.googleapis.com" || parsed.username || parsed.password)
    throw new Error("Refusing to send Google credentials to a non-GCS download URL");
  const response = await fetch(httpsUrl, {
    redirect: "error",
    signal: AbortSignal.timeout(120_000),
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!response.ok) {
    throw new Error(`Failed to download from GCS: ${response.status}`);
  }

  const arrayBuffer = await response.arrayBuffer();
  return Buffer.from(arrayBuffer);
}
