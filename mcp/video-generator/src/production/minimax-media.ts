/** Local, immutable source preparation. No uploads or provider requests. */
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { resolvePath } from "../utils/paths.js";
import { qualifyMiniMax, validateMiniMax, type MiniMaxSpec } from "./minimax-spec.js";

const mimeTypes: Record<string, string> = {
  ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp",
  ".mp4": "video/mp4", ".wav": "audio/wav", ".mp3": "audio/mp3",
};
export const MINIMAX_MAX_BODY_BYTES = 64_000_000;
interface MediaInput { path: string; role: string; kind: "image" | "video" | "audio" }

export function prepareMiniMaxRequest(options: MiniMaxSpec) {
  const validated = validateMiniMax(options);
  const inputs: MediaInput[] = [];
  if (options.firstFramePath) inputs.push({ path: options.firstFramePath, role: "first_frame", kind: "image" });
  if (options.lastFramePath) inputs.push({ path: options.lastFramePath, role: "last_frame", kind: "image" });
  for (const p of options.referenceImagePaths ?? []) inputs.push({ path: p, role: "reference_image", kind: "image" });
  for (const p of options.referenceVideoPaths ?? []) inputs.push({ path: p, role: "reference_video", kind: "video" });
  for (const p of options.referenceAudioPaths ?? []) inputs.push({ path: p, role: "reference_audio", kind: "audio" });
  const content: Array<Record<string, unknown>> = [{ type: "text", text: options.prompt }];
  const sources: Array<{ role: string; sha256: string; bytes: number; durationSeconds?: number; width?: number; height?: number }> = [];
  const durations = { video: [] as number[], audio: [] as number[] };
  let bodyBytes = Buffer.byteLength(options.prompt) + 4096;
  for (const input of inputs) {
    const filename = resolvePath(input.path);
    const mime = mimeTypes[path.extname(filename).toLowerCase()];
    if (!mime?.startsWith(input.kind + "/")) throw new Error("Unsupported local MiniMax media format; use PNG/JPEG/WebP, MP4, WAV/MP3");
    const stat = fs.statSync(filename);
    const limit = input.kind === "image" ? 30_000_000 : input.kind === "video" ? 50_000_000 : 15_000_000;
    if (!stat.isFile() || stat.size === 0 || stat.size > limit) throw new Error("MiniMax input exceeds its per-file size limit or is empty");
    bodyBytes += Math.ceil(stat.size / 3) * 4;
    if (bodyBytes > MINIMAX_MAX_BODY_BYTES) throw new Error("MiniMax inline request exceeds 64 MB; reduce reference sizes");
    const probe = spawnSync("ffprobe", ["-v", "error", "-show_streams", "-show_format", "-of", "json", filename],
      { encoding: "utf8", maxBuffer: 1024 * 1024, timeout: 30_000 });
    if (probe.error || probe.status !== 0) throw new Error("ffprobe could not inspect a MiniMax input");
    const info = JSON.parse(probe.stdout);
    const stream = info.streams?.find((s: { codec_type: string }) => s.codec_type === (input.kind === "audio" ? "audio" : "video"));
    if (!stream) throw new Error("MiniMax input is missing its required media stream");
    if (input.kind === "image") {
      const expectedCodec: Record<string, string> = { "image/png": "png", "image/jpeg": "mjpeg", "image/webp": "webp" };
      if (stream.codec_name !== expectedCodec[mime]) throw new Error("MiniMax image encoding does not match its file extension");
    }
    if (input.kind !== "audio") {
      const { width, height } = stream;
      if (![width, height].every(n => Number.isInteger(n) && n >= 256 && n <= 5760) || width / height < .4 || width / height > 2.5)
        throw new Error("MiniMax images/videos need dimensions 256–5760 and a ratio between 2:5 and 5:2");
      // MiniMax ignores ratio for I2V. Refuse an anchor that would silently change the planned canvas.
      const [w, h] = validated.aspectRatio.split(":").map(Number);
      if ((input.role === "first_frame" || input.role === "last_frame") && width * h !== height * w)
        throw new Error("MiniMax first/last frame aspect ratio must match the planned aspect ratio; crop explicitly first");
    }
    if (input.kind === "video") {
      const [n, d] = String(stream.avg_frame_rate).split("/").map(Number);
      if (!["h264", "hevc"].includes(stream.codec_name) || !Number.isFinite(n / d) || n / d < 23.976 || n / d > 60
          || info.streams.some((s: { codec_type: string; codec_name: string }) => s.codec_type === "audio" && !["aac", "mp3"].includes(s.codec_name)))
        throw new Error("MiniMax reference video needs H.264/H.265 at 23.976–60 fps and AAC/MP3 audio");
    }
    const durationSeconds = input.kind === "image" ? undefined : Number(info.format?.duration ?? stream.duration);
    if (input.kind !== "image") durations[input.kind].push(durationSeconds!);
    const bytes = fs.readFileSync(filename);
    const after = fs.statSync(filename);
    if (bytes.length !== stat.size || after.mtimeMs !== stat.mtimeMs || after.ino !== stat.ino)
      throw new Error("MiniMax source changed during preparation");
    sources.push({ role: input.role, sha256: createHash("sha256").update(bytes).digest("hex"), bytes: bytes.length,
      durationSeconds, width: stream.width, height: stream.height });
    content.push({ type: `${input.kind}_url`, role: input.role,
      [`${input.kind}_url`]: { url: `data:${mime};base64,${bytes.toString("base64")}` } });
  }
  const quote = qualifyMiniMax(options, durations);
  const body = { model: quote.modelId, content, resolution: quote.resolution, duration: quote.durationSeconds,
    ratio: quote.mode === "image-to-video" ? "adaptive" : quote.aspectRatio,
    ...(quote.promptExpansionMode ? { extra: { prompt_expansion_mode: quote.promptExpansionMode } } : {}) };
  const serializedBody = JSON.stringify(body);
  if (Buffer.byteLength(serializedBody) > MINIMAX_MAX_BODY_BYTES) throw new Error("MiniMax inline request exceeds 64 MB");
  const fingerprint = createHash("sha256").update(JSON.stringify({ provider: "minimax", body: { ...body, content: undefined },
    prompt: options.prompt, aspectRatio: quote.aspectRatio, sources })).digest("hex");
  return { quote, sources, fingerprint, serializedBody };
}
