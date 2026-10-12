/** Direct MiniMax V2 video contract and USD list prices, checked 2026-10-11.
 * https://platform.minimax.io/docs/api-reference/video-generation-v2-create
 * https://platform.minimax.io/docs/guides/pricing-paygo
 * Reservations include input charges; they are not invoice-confirmed spend.
 */
export const MINIMAX_MODELS = ["MiniMax-H3", "MiniMax-H3-Max"] as const;
export type MiniMaxModel = typeof MINIMAX_MODELS[number];
export interface MiniMaxSpec {
  provider?: "minimax";
  prompt: string;
  model?: MiniMaxModel;
  durationSeconds?: number;
  resolution?: "480P" | "768P" | "2K";
  aspectRatio?: string;
  firstFramePath?: string;
  lastFramePath?: string;
  referenceImagePaths?: string[];
  referenceVideoPaths?: string[];
  referenceAudioPaths?: string[];
  promptExpansionMode?: "disabled" | "balanced" | "quality";
}
export interface MiniMaxInputDurations {
  video: number[];
  audio: number[];
}
const ratios = ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"];
const allowedFields = new Set(["provider", "prompt", "model", "durationSeconds", "resolution", "aspectRatio",
  "firstFramePath", "lastFramePath", "referenceImagePaths", "referenceVideoPaths", "referenceAudioPaths",
  "promptExpansionMode", "budgetFile", "requestId"]);

export function validateMiniMax(options: MiniMaxSpec) {
  if (!options || Object.keys(options).some(k => !allowedFields.has(k)))
    throw new Error("Unsupported MiniMax request field; seed and generateAudio are not V2 parameters");
  if (options.provider !== undefined && options.provider !== "minimax") throw new Error("Incorrect MiniMax provider");
  if (typeof options.prompt !== "string" || !options.prompt.trim() || [...options.prompt].length > 7000)
    throw new Error("MiniMax requires a nonempty prompt of at most 7000 characters");
  const modelId = options.model ?? "MiniMax-H3-Max";
  if (!MINIMAX_MODELS.includes(modelId)) throw new Error("Use MiniMax-H3 or MiniMax-H3-Max");
  const max = modelId === "MiniMax-H3-Max";
  const durationSeconds = options.durationSeconds ?? 6;
  const resolution = options.resolution ?? "768P";
  const aspectRatio = options.aspectRatio ?? "16:9";
  if (!Number.isInteger(durationSeconds) || durationSeconds < (max ? 5 : 4) || durationSeconds > 15)
    throw new Error(max ? "H3 Max duration must be an integer from 5 to 15 seconds" : "H3 duration must be an integer from 4 to 15 seconds");
  if (!(max ? ["480P", "768P"] : ["768P", "2K"]).includes(resolution))
    throw new Error("Unsupported MiniMax model/resolution combination (use exact 480P, 768P or 2K spelling)");
  if (!ratios.includes(aspectRatio)) throw new Error("MiniMax requires an explicit supported aspect ratio");
  for (const k of ["firstFramePath", "lastFramePath"] as const)
    if (options[k] !== undefined && (typeof options[k] !== "string" || !options[k]!.trim())) throw new Error("Invalid frame path");
  for (const k of ["referenceImagePaths", "referenceVideoPaths", "referenceAudioPaths"] as const)
    if (options[k] !== undefined && (!Array.isArray(options[k]) || options[k]!.some(p => typeof p !== "string" || !p.trim())))
      throw new Error("MiniMax reference paths must be arrays of local file paths");
  const images = options.referenceImagePaths?.length ?? 0;
  const videos = options.referenceVideoPaths?.length ?? 0;
  const audio = options.referenceAudioPaths?.length ?? 0;
  const frames = Number(!!options.firstFramePath) + Number(!!options.lastFramePath);
  if (frames && images + videos + audio) throw new Error("First/last frames cannot be mixed with reference generation");
  if (images > 9 || videos > 3 || audio > 3 || images + videos + audio > 12)
    throw new Error("MiniMax accepts up to 9 reference images, 3 videos, 3 audio clips and 12 references total");
  if (options.promptExpansionMode !== undefined && (!max || !["disabled", "balanced", "quality"].includes(options.promptExpansionMode)))
    throw new Error("promptExpansionMode is supported only on H3 Max: disabled, balanced or quality");
  return { modelId, durationSeconds, resolution, aspectRatio,
    mode: frames ? "image-to-video" : images + videos + audio ? "reference-to-video" : "text-to-video",
    inputImageCount: images + frames, referenceVideoCount: videos, referenceAudioCount: audio,
    promptExpansionMode: max ? options.promptExpansionMode ?? "balanced" : undefined };
}

export function qualifyMiniMax(options: MiniMaxSpec, durations: MiniMaxInputDurations = { video: [], audio: [] }) {
  const spec = validateMiniMax(options);
  for (const [values, count] of [[durations.video, spec.referenceVideoCount], [durations.audio, spec.referenceAudioCount]] as const) {
    if (!Array.isArray(values) || values.length !== count || values.some(s => !Number.isFinite(s) || s < 2 || s > 15)
        || values.reduce((a, b) => a + b, 0) > 15)
      throw new Error("Reference clips need measured 2–15 second durations, totaling at most 15 seconds per media type");
  }
  const max = spec.modelId === "MiniMax-H3-Max";
  const rateUsdPerSecond = max ? (spec.resolution === "480P" ? .05 : .08) : (spec.resolution === "2K" ? .13 : .08);
  const referenceVideoRate = max ? (spec.resolution === "480P" ? .0553 : .143) : rateUsdPerSecond;
  // The table does not specify fractional input billing. Reserve rounded-up seconds per clip.
  const reservedReferenceVideoSeconds = durations.video.reduce((n, s) => n + Math.ceil(s), 0);
  const outputMicros = Math.round(spec.durationSeconds * rateUsdPerSecond * 1e6);
  const imageMicros = Math.max(0, spec.inputImageCount - (max ? 2 : 5)) * (max ? 74000 : 40000);
  const videoMicros = Math.round(reservedReferenceVideoSeconds * referenceVideoRate * 1e6);
  return { ...spec, pricingChecked: "2026-10-11", rateUsdPerSecond,
    outputUsd: outputMicros / 1e6, inputImagesUsd: imageMicros / 1e6, inputVideoUsd: videoMicros / 1e6,
    referenceVideoSeconds: durations.video.reduce((a, b) => a + b, 0), reservedReferenceVideoSeconds,
    estimatedUsd: (outputMicros + imageMicros + videoMicros) / 1e6 };
}
