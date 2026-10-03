import fs from "fs";
import path from "path";
import { createHash } from "node:crypto";
import { readLedger, reserveSpend, updateSpend } from "../production/ledger.js";
import { qualifyVeo, type VeoModelAlias } from "../production/veo-spec.js";
export { VEO_MODELS, type VeoModelAlias } from "../production/veo-spec.js";
import { getGoogleAccessToken, buildVertexUrl } from "./google-auth.js";
import {
  uploadFileToGcs,
  buildObjectName,
  inferImageMimeType,
} from "./gcs.js";
import { VIDEO_DIR, resolvePath } from "../utils/paths.js";
import { loadConfig } from "../utils/config.js";

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
}

/**
 * Load image as base64 (fallback path when GCS bucket is not configured)
 */
function loadImageBase64(imagePath: string): string {
  const resolved = resolvePath(imagePath);
  if (!fs.existsSync(resolved)) {
    throw new Error(`Image not found: ${resolved}`);
  }
  return fs.readFileSync(resolved).toString("base64");
}

async function buildImageField(
  imagePath: string,
  bucket: string | undefined,
  gcsPrefix: string
): Promise<Record<string, string>> {
  const mimeType = inferImageMimeType(imagePath);
  if (bucket) {
    const objectName = buildObjectName(gcsPrefix, imagePath);
    const gcsUri = await uploadFileToGcs(imagePath, bucket, objectName, mimeType);
    return { gcsUri, mimeType };
  }
  return {
    bytesBase64Encoded: loadImageBase64(imagePath),
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
  if (!options.budgetFile || !options.requestId)
    throw new Error("Veo requires budgetFile and a stable requestId. Use the production CLI to initialize an authorized all-in budget.");
  const budgetFile = resolvePath(options.budgetFile);
  const requestId = options.requestId;
  const anchorHash = (p: string | undefined) => p ? createHash("sha256").update(fs.readFileSync(resolvePath(p))).digest("hex") : null;
  const fingerprint = createHash("sha256").update(JSON.stringify({ ...spec, prompt,
    first: anchorHash(firstFramePath), last: anchorHash(lastFramePath), seed: options.seed ?? null })).digest("hex");
  const existing = readLedger(budgetFile).entries.find(e => e.id === requestId);
  if (existing) {
    if (existing.fingerprint !== fingerprint) throw new Error("Request ID reused with changed content; preserve the original and use a new attempt ID");
    if (existing.operationName) return { operationName: existing.operationName, model: existing.model!, seed: existing.seed };
    throw new Error("Request already reserved without a known operation; reconcile it before any new paid attempt");
  }
  // Deterministic seed selection makes crash recovery inspectable; provider output is not guaranteed deterministic.
  const effectiveSeed = options.seed ?? parseInt(createHash("sha256").update(requestId).digest("hex").slice(0, 8), 16);
  // Reserve before auth, uploads or POST. Failure never releases money automatically.
  reserveSpend(budgetFile, { id: requestId, category: "veo", fingerprint, usd: spec.estimatedUsd, note: "Veo generation attempt" });
  try {
    const { accessToken, projectId } = await getGoogleAccessToken();
    const bucket = loadConfig().veoGcsBucket;
    // Build instance with optional reference frames
    const instance: Record<string, unknown> = { prompt };

    if (firstFramePath) {
      instance.image = await buildImageField(
        firstFramePath,
        bucket,
        "veo-inputs/image"
      );
    }

    if (lastFramePath) {
      instance.lastFrame = await buildImageField(
        lastFramePath,
        bucket,
        "veo-inputs/last-frame"
      );
    }

    const parameters: Record<string, unknown> = {
      aspectRatio,
      durationSeconds: validDuration,
      seed: effectiveSeed,
      sampleCount: 1,
    };

    // generateAudio is supported on Veo 3+ models
    if (generateAudio !== undefined) {
      parameters.generateAudio = generateAudio;
    }

    // Only the qualified GA resolutions reach this point.
    if (resolution) {
      parameters.resolution = resolution;
    }

    // storageUri tells Veo to write the output MP4 to GCS and return a URI,
    // instead of returning a multi-MB base64-encoded video inline.
    if (bucket) {
      const stamp = Date.now().toString(36);
      const rand = Math.random().toString(36).slice(2, 8);
      parameters.storageUri = `gs://${bucket}/veo-outputs/${stamp}-${rand}/`;
    }

    const requestBody = {
      instances: [instance],
      parameters,
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
    updateSpend(budgetFile, requestId, { status: "submitted", operationName: data.name, model: modelId, seed: effectiveSeed });
    return { operationName: data.name, model: modelId, seed: effectiveSeed };
  } catch (error) {
    updateSpend(budgetFile, requestId, { status: "uncertain", evidence: "Submission did not complete locally; reservation retained. Inspect private provider logs before another attempt." });
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
  result: VeoPollResult
): Promise<VeoDownloadResult> {
  if (!result.video) {
    throw new Error("No video in result");
  }

  const timestamp = Date.now();
  const randomId = Math.random().toString(36).substring(2, 8);
  const filename = `veo_${timestamp}_${randomId}.mp4`;
  const outputPath = path.join(VIDEO_DIR, filename);

  // Ensure video directory exists
  if (!fs.existsSync(VIDEO_DIR)) {
    fs.mkdirSync(VIDEO_DIR, { recursive: true });
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

  // Get video duration via ffprobe
  const duration = await getVideoDuration(outputPath);

  return {
    filename,
    path: `/video/${filename}`,
    duration,
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

/**
 * Get video duration using ffprobe
 */
async function getVideoDuration(filepath: string): Promise<number | null> {
  const { execFile } = await import("child_process");
  const { promisify } = await import("util");
  const execAsync = promisify(execFile);

  try {
    const { stdout } = await execAsync(
      "ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filepath]
    );
    return parseFloat(stdout.trim());
  } catch {
    return null;
  }
}
