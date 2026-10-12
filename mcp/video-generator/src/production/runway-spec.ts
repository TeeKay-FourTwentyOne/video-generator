/** Qualified Runway Gen-4.5 / Gen-4 Turbo MP4 generation, checked 2026-10-11.
 * Contract: github.com/runwayml/openapi; rates: docs.dev.runwayml.com/guides/pricing/
 * This deliberately excludes model routers, third-party models and paid output formats.
 */
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { resolvePath } from "../utils/paths.js";

export const RUNWAY_MODELS = ["gen4.5", "gen4_turbo"] as const;
export type RunwayModel = typeof RUNWAY_MODELS[number];
export interface RunwaySpec {
  provider?: "runway";
  model?: string;
  prompt: string;
  durationSeconds?: number;
  aspectRatio?: string;
  resolution?: string;
  firstFramePath?: string;
  seed?: number;
  generateAudio?: boolean;
}
const ratios: Record<string, string> = { "16:9": "1280:720", "9:16": "720:1280", "1:1": "960:960" };
const fields = new Set(["provider", "model", "prompt", "durationSeconds", "aspectRatio", "resolution",
  "firstFramePath", "seed", "generateAudio", "budgetFile", "requestId"]);

export function qualifyRunway(options: RunwaySpec) {
  if (!options || typeof options !== "object") throw new Error("Runway request must be an object");
  for (const key of Object.keys(options)) if (!fields.has(key)) throw new Error(`Unsupported Runway option: ${key}`);
  if (options.provider !== undefined && options.provider !== "runway") throw new Error("Runway requires provider: runway");
  const modelId = options.model ?? "gen4.5";
  if (!RUNWAY_MODELS.includes(modelId as RunwayModel)) throw new Error("Qualified Runway models are gen4.5 and gen4_turbo");
  if (typeof options.prompt !== "string" || !options.prompt.trim() || options.prompt.length > 1000)
    throw new Error("Runway prompt must contain 1–1000 UTF-16 code units");
  const durationSeconds = options.durationSeconds ?? 8;
  if (!Number.isInteger(durationSeconds) || durationSeconds < 2 || durationSeconds > 10)
    throw new Error("Runway duration must be an integer from 2 to 10 seconds");
  if (options.firstFramePath !== undefined && (typeof options.firstFramePath !== "string" || !options.firstFramePath.trim()))
    throw new Error("Runway first frame must be a nonempty local path");
  if (modelId === "gen4_turbo" && !options.firstFramePath) throw new Error("Gen-4 Turbo requires a starting image");
  const aspectRatio = options.aspectRatio ?? "16:9";
  if (!Object.hasOwn(ratios, aspectRatio) || (aspectRatio === "1:1" && !options.firstFramePath))
    throw new Error("Qualified Runway ratios are 16:9 or 9:16, plus 1:1 for image-to-video");
  if (options.resolution !== undefined && options.resolution !== "720p")
    throw new Error("Runway supports only the native 720p tier in this adapter (960x960 for square)");
  if (options.generateAudio !== undefined && options.generateAudio !== false)
    throw new Error("These Runway models have no native audio; omit generateAudio or set false");
  if (options.seed !== undefined && (!Number.isInteger(options.seed) || options.seed < 0 || options.seed > 4294967295))
    throw new Error("Runway seed must be an unsigned 32-bit integer");
  const creditsPerSecond = modelId === "gen4.5" ? 12 : 5;
  const estimatedCredits = durationSeconds * creditsPerSecond;
  return { modelId: modelId as RunwayModel, durationSeconds, aspectRatio, resolution: "720p", ratio: ratios[aspectRatio],
    mode: options.firstFramePath ? "image-to-video" : "text-to-video", seed: options.seed, generateAudio: false,
    outputFormat: "mp4", creditsPerSecond, estimatedCredits, estimatedUsd: estimatedCredits / 100, pricingChecked: "2026-10-11" };
}

/** Local-only preparation. Inline image limit includes base64 expansion; no public upload. */
export function prepareRunwayRequest(options: RunwaySpec) {
  const quote = qualifyRunway(options);
  const sources: Array<{ role: string; sha256: string; bytes: number; width: number; height: number }> = [];
  let promptImage: string | undefined;
  if (options.firstFramePath) {
    const filename = resolvePath(options.firstFramePath);
    const formats: Record<string, [string, string]> = {
      ".png": ["image/png", "png"], ".jpg": ["image/jpeg", "mjpeg"],
      ".jpeg": ["image/jpeg", "mjpeg"], ".webp": ["image/webp", "webp"],
    };
    const format = formats[path.extname(filename).toLowerCase()];
    if (!format) throw new Error("Runway local frames must be PNG, JPEG or WebP");
    const stat = fs.statSync(filename);
    if (!stat.isFile() || !stat.size || Math.ceil(stat.size / 3) * 4 + 64 > 5_000_000)
      throw new Error("Runway frame exceeds the 5 MB encoded data URI limit or is empty");
    const probe = spawnSync("ffprobe", ["-v", "error", "-show_streams", "-of", "json", filename],
      { encoding: "utf8", timeout: 30_000, maxBuffer: 1024 * 1024 });
    if (probe.error || probe.status !== 0) throw new Error("ffprobe could not inspect the Runway starting image");
    const streams = JSON.parse(probe.stdout).streams;
    const stream = streams?.find((s: { codec_type: string }) => s.codec_type === "video");
    if (!stream || stream.codec_name !== format[1] || ![stream.width, stream.height].every(n => Number.isInteger(n) && n >= 256 && n <= 4096))
      throw new Error("Runway adapter requires correctly encoded still images with dimensions 256–4096");
    const [w, h] = quote.ratio.split(":").map(Number);
    if (stream.width * h !== stream.height * w)
      throw new Error("Runway starting image aspect ratio must match the output; crop explicitly before submitting");
    const bytes = fs.readFileSync(filename), after = fs.statSync(filename);
    if (bytes.length !== stat.size || after.mtimeMs !== stat.mtimeMs || after.ino !== stat.ino)
      throw new Error("Runway starting image changed during preparation");
    promptImage = `data:${format[0]};base64,${bytes.toString("base64")}`;
    sources.push({ role: "first_frame", sha256: createHash("sha256").update(bytes).digest("hex"),
      bytes: bytes.length, width: stream.width, height: stream.height });
  }
  const endpoint = promptImage ? "/v1/image_to_video" : "/v1/text_to_video";
  const body = { model: quote.modelId, promptText: options.prompt, duration: quote.durationSeconds,
    ratio: quote.ratio, ...(quote.seed === undefined ? {} : { seed: quote.seed }), ...(promptImage ? { promptImage } : {}) };
  const serializedBody = JSON.stringify(body);
  const fingerprint = createHash("sha256").update(JSON.stringify({ provider: "runway", endpoint, body })).digest("hex");
  return { quote, sources, endpoint, serializedBody, fingerprint };
}
