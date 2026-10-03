/** Qualified Vertex variants. Pricing checked 2026-10-03; reverify before new productions.
 * https://cloud.google.com/vertex-ai/generative-ai/pricing#veo
 * GA 3.1 model card currently documents 720p/1080p, 24 fps, 4/6/8s.
 */
export const VEO_MODELS = {
  "veo-3.1": "veo-3.1-generate-001",
  "veo-3.1-prod": "veo-3.1-generate-001",
  "veo-3.1-fast": "veo-3.1-fast-generate-001",
  "veo-3.1-fast-prod": "veo-3.1-fast-generate-001",
  "veo-2.0": "veo-2.0-generate-001",
} as const;
export type VeoModelAlias = keyof typeof VEO_MODELS;
export interface VeoSpec {
  prompt: string; model?: VeoModelAlias; durationSeconds?: number;
  aspectRatio?: string; generateAudio?: boolean; resolution?: "720p" | "1080p" | "4k";
  seed?: number; firstFramePath?: string; lastFramePath?: string;
}
export function qualifyVeo(options: VeoSpec) {
  const model = options.model ?? "veo-3.1-prod";
  const modelId = VEO_MODELS[model];
  if (!modelId || model === "veo-2.0") throw new Error("Use a qualified Veo 3.1 GA model; legacy Veo 2 requires separate qualification");
  const durationSeconds = options.durationSeconds ?? 8;
  const resolution = options.resolution ?? "1080p";
  const aspectRatio = options.aspectRatio ?? "9:16";
  const generateAudio = options.generateAudio ?? true;
  if (!options.prompt?.trim()) throw new Error("Prompt cannot be empty");
  if (![4, 6, 8].includes(durationSeconds)) throw new Error("Duration must be exactly 4, 6 or 8 seconds; no silent snapping");
  if (!["720p", "1080p"].includes(resolution)) throw new Error("This GA adapter is qualified for 720p/1080p only");
  if (!["9:16", "16:9"].includes(aspectRatio)) throw new Error("Veo supports 9:16 and 16:9, not square");
  if (options.lastFramePath && !options.firstFramePath) throw new Error("Last frame requires a first frame");
  if (options.seed !== undefined && (!Number.isInteger(options.seed) || options.seed < 0 || options.seed > 4294967295))
    throw new Error("Seed must be a uint32; seeds aid provenance, not guaranteed deterministic replay");
  const fast = modelId.includes("fast");
  const rate = fast ? (generateAudio ? (resolution === "1080p" ? .12 : .10) : (resolution === "1080p" ? .10 : .08)) : (generateAudio ? .40 : .20);
  return { modelId, durationSeconds, resolution, aspectRatio, generateAudio,
    estimatedUsd: Math.round(rate * durationSeconds * 1e6) / 1e6, rateUsdPerSecond: rate };
}
