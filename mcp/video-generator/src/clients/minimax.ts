/** Direct MiniMax V2 API. No automatic POST retries, SDK or credential-bearing downloads. */
import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { loadConfig } from "../utils/config.js";
import { resolvePath } from "../utils/paths.js";
import { atomicJson, readLedger, reserveSpend, updateSpend } from "../production/ledger.js";
import { MINIMAX_MODELS, type MiniMaxModel, type MiniMaxSpec } from "../production/minimax-spec.js";
import { prepareMiniMaxRequest } from "../production/minimax-media.js";
export { prepareMiniMaxRequest } from "../production/minimax-media.js";

const API_ROOT = "https://api.minimax.io";
const TASKS_PATH = "/v2/query/video_generation";
const statuses = ["queued", "running", "succeeded", "failed", "cancelled"] as const;
type TaskStatus = typeof statuses[number];
export interface MiniMaxSubmitOptions extends MiniMaxSpec { budgetFile: string; requestId: string }
export interface MiniMaxSubmitResult { provider: "minimax"; operationName: string; model: MiniMaxModel }
export interface MiniMaxPollResult {
  done: boolean; operationName: string; model: MiniMaxModel; status: TaskStatus;
  video?: { uri: string }; error?: string; usage?: Record<string, number>;
  resolution?: string; durationSeconds?: number; aspectRatio?: string; createdAt?: number;
}

export function miniMaxCredentialsConfigured(): boolean {
  const key = process.env.MINIMAX_API_KEY ?? loadConfig().minimaxApiKey;
  return typeof key === "string" && !!key.trim() && !/\s/.test(key.trim());
}
function apiKey(): string {
  const key = process.env.MINIMAX_API_KEY ?? loadConfig().minimaxApiKey;
  if (typeof key !== "string" || !key.trim() || /\s/.test(key.trim()))
    throw new Error("Configure MINIMAX_API_KEY or minimaxApiKey in the ignored data/config.json");
  return key.trim();
}
function taskId(value: unknown): string {
  if (typeof value !== "string" || !/^[A-Za-z0-9_-]{1,128}$/.test(value)) throw new Error("Invalid MiniMax task ID");
  return value;
}
class MiniMaxHttpError extends Error {
  constructor(readonly status: number) {
    const reason: Record<number, string> = { 400: "invalid request", 401: "authentication failed", 402: "insufficient balance",
      403: "access denied", 404: "task not found or expired", 422: "request rejected", 429: "rate limited" };
    super(`MiniMax HTTP ${status}: ${reason[status] ?? "provider request failed"}. No automatic retry.`);
  }
  get rejected() { return [400, 401, 402, 403, 404, 422, 429].includes(this.status); }
}
async function requestJson(endpoint: string, method = "GET", body?: string, key = apiKey()): Promise<any> {
  let response: Response;
  try {
    response = await fetch(API_ROOT + endpoint, { method, redirect: "error", signal: AbortSignal.timeout(120_000),
      headers: { Authorization: `Bearer ${key}`, ...(body ? { "Content-Type": "application/json" } : {}) }, body });
  } catch {
    // Fetch errors and provider response text can echo headers, prompts or signed URLs.
    throw new Error("MiniMax transport failed or timed out; retain the reservation and recover the existing task before another submission");
  }
  if (!response.ok) throw new MiniMaxHttpError(response.status);
  let data;
  try { data = await response.json(); } catch { throw new Error("MiniMax returned invalid JSON; submission outcome may be uncertain"); }
  if (!data || typeof data !== "object" || data.error || data.type === "error"
      || (data.base_resp && data.base_resp.status_code !== 0))
    throw new Error("MiniMax returned an API error or malformed response; no automatic retry");
  return data;
}

function attempt(options: MiniMaxSubmitOptions) {
  if (!options.budgetFile || typeof options.requestId !== "string" || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$/.test(options.requestId))
    throw new Error("MiniMax requires budgetFile and a stable requestId from an authorized production ledger");
  const prepared = prepareMiniMaxRequest(options);
  const budgetFile = resolvePath(options.budgetFile);
  const journalFile = path.join(path.dirname(budgetFile), "operations", `${options.requestId}.json`);
  const entry = readLedger(budgetFile).entries.find(e => e.id === options.requestId);
  if (entry && (entry.category !== "minimax" || entry.fingerprint !== prepared.fingerprint))
    throw new Error("Request ID reused with changed content or provider; preserve the original and use a new attempt ID");
  return { ...prepared, budgetFile, journalFile, entry };
}

export async function submitMiniMaxGeneration(options: MiniMaxSubmitOptions): Promise<MiniMaxSubmitResult> {
  const a = attempt(options);
  if (a.entry) {
    let operationName = a.entry.operationName;
    if (!operationName && fs.existsSync(a.journalFile)) {
      const journal = JSON.parse(fs.readFileSync(a.journalFile, "utf8"));
      if (journal.fingerprint === a.fingerprint && journal.provider === "minimax" && journal.operationName) {
        operationName = taskId(journal.operationName);
        updateSpend(a.budgetFile, options.requestId, { operationName, model: a.quote.modelId, status: "submitted",
          evidence: "Recovered task ID from the durable local submission record; no new POST" });
      }
    }
    if (operationName) return { provider: "minimax", operationName: taskId(operationName), model: a.quote.modelId };
    throw new Error("MiniMax request already reserved without a known task; inspect minimax-tasks and recover-minimax, never resubmit blindly");
  }
  const key = apiKey(); // Missing credentials fail before reserving any money.
  fs.mkdirSync(path.dirname(a.journalFile), { recursive: true });
  if (fs.existsSync(a.journalFile)) throw new Error("Existing MiniMax operation record has no matching reservation; inspect before proceeding");
  reserveSpend(a.budgetFile, { id: options.requestId, category: "minimax", fingerprint: a.fingerprint,
    usd: a.quote.estimatedUsd, note: "MiniMax generation including measured reference inputs" });
  const record = { schemaVersion: 1, provider: "minimax", requestId: options.requestId, fingerprint: a.fingerprint,
    quote: a.quote, prompt: options.prompt, sources: a.sources, createdAt: new Date().toISOString() };
  let operationName: string | undefined;
  try {
    atomicJson(a.journalFile, { ...record, status: "reserved" });
    const data = await requestJson("/v2/video_generation", "POST", a.serializedBody, key);
    operationName = taskId(data.task_id);
    const result: MiniMaxSubmitResult = { provider: "minimax", operationName, model: a.quote.modelId };
    // Persist the task ID before the ledger update, so either record can recover a local crash.
    atomicJson(a.journalFile, { ...record, ...result, status: "submitted" });
    updateSpend(a.budgetFile, options.requestId, { status: "submitted", operationName, model: a.quote.modelId });
    return result;
  } catch (error) {
    const status = operationName ? "submitted" : error instanceof MiniMaxHttpError && error.rejected ? "failed" : "uncertain";
    const evidence = operationName ? "Provider returned a task ID; recover local persistence before further work"
      : "Submission did not complete locally; reservation retained. Inspect provider tasks before another attempt.";
    try { atomicJson(a.journalFile, { ...record, operationName, status, evidence }); } catch { /* Preserve ledger recovery below. */ }
    try { updateSpend(a.budgetFile, options.requestId, { status, operationName, model: a.quote.modelId, evidence }); } catch { /* Journal retains evidence. */ }
    throw error;
  }
}

/** Terminal failure/empty output is never treated as an indefinitely pending task. */
export function interpretMiniMaxTask(raw: unknown, operationName: string): MiniMaxPollResult {
  const task = (raw as { task?: any })?.task;
  if (!task || task.id !== taskId(operationName) || !MINIMAX_MODELS.includes(task.model) || !statuses.includes(task.status)
      || (task.task_type !== undefined && task.task_type !== "generation"))
    throw new Error("Malformed or mismatched MiniMax generation task");
  const usage: Record<string, number> = {};
  for (const k of ["total_seconds", "input_seconds", "output_seconds", "input_image_count", "input_audio_seconds", "total_tokens", "prompt_tokens", "completion_tokens"]) {
    const value = task.usage?.[k];
    if (typeof value === "number" && Number.isFinite(value) && value >= 0) usage[k] = value;
  }
  const result: MiniMaxPollResult = { operationName, model: task.model, status: task.status,
    done: !["queued", "running"].includes(task.status), usage,
    resolution: ["480P", "768P", "2K"].includes(task.resolution) ? task.resolution : undefined,
    durationSeconds: Number.isFinite(task.duration) ? task.duration : undefined,
    aspectRatio: typeof task.ratio === "string" && /^(adaptive|\d{1,2}:\d{1,2})$/.test(task.ratio) ? task.ratio : undefined,
    createdAt: Number.isFinite(task.created_at) ? task.created_at : undefined };
  if (task.status === "failed" || task.status === "cancelled") {
    const code = /^\d{1,6}$/.test(String(task.error?.code)) ? ` (code ${task.error.code})` : "";
    result.error = `MiniMax generation ${task.status}${code}; reservation retained, no automatic retry`;
  } else if (task.status === "succeeded") {
    if (typeof task.content?.url !== "string" || !task.content.url) result.error = "MiniMax completed without a video URL";
    else result.video = { uri: task.content.url };
  }
  return result;
}

export async function pollMiniMaxOperation(operationName: string, model?: string): Promise<MiniMaxPollResult> {
  const result = interpretMiniMaxTask(await requestJson(`${TASKS_PATH}/${taskId(operationName)}`), operationName);
  if (model && result.model !== model) throw new Error("MiniMax task model differs from the reserved model");
  return result;
}

export async function listMiniMaxTasks(page = 1, pageSize = 20) {
  if (!Number.isSafeInteger(page) || page < 1 || !Number.isInteger(pageSize) || pageSize < 1 || pageSize > 100)
    throw new Error("Task list requires page >= 1 and pageSize from 1 to 100");
  const data = await requestJson(`${TASKS_PATH}?${new URLSearchParams({ page_num: String(page), page_size: String(pageSize), "filter.task_type": "generation" })}`);
  if (!Array.isArray(data.items) || !Number.isSafeInteger(data.total) || data.total < 0) throw new Error("Malformed MiniMax task list");
  return { page, pageSize, total: data.total, tasks: data.items.map((t: any) => interpretMiniMaxTask({ task: t }, t.id)) };
}

/** Explicit, evidence-backed recovery; the API does not document client idempotency keys. */
export async function recoverMiniMaxOperation(options: MiniMaxSubmitOptions, operationName: string, evidence: string) {
  if (typeof evidence !== "string" || !evidence.trim()) throw new Error("Recovery requires evidence linking the provider task to this attempt");
  taskId(operationName);
  const a = attempt(options);
  if (!a.entry || (a.entry.operationName && a.entry.operationName !== operationName)) throw new Error("No matching unresolved MiniMax reservation");
  if (readLedger(a.budgetFile).entries.some(e => e.id !== options.requestId && e.operationName === operationName))
    throw new Error("MiniMax task is already associated with another reservation");
  const task = await pollMiniMaxOperation(operationName, a.quote.modelId);
  if (task.resolution !== a.quote.resolution || task.durationSeconds !== a.quote.durationSeconds)
    throw new Error("Recovery task parameters differ from the reserved request");
  fs.mkdirSync(path.dirname(a.journalFile), { recursive: true });
  const result: MiniMaxSubmitResult = { provider: "minimax", operationName, model: a.quote.modelId };
  atomicJson(a.journalFile, { ...result, requestId: options.requestId, fingerprint: a.fingerprint, quote: a.quote,
    sources: a.sources, prompt: options.prompt, recoveredAt: new Date().toISOString(), evidence });
  updateSpend(a.budgetFile, options.requestId, { operationName, model: a.quote.modelId, status: "submitted", evidence });
  return result;
}

function outputUrl(uri: string): string {
  let url: URL;
  try { url = new URL(uri); } catch { throw new Error("Invalid MiniMax output URL"); }
  const allowed = ["minimax.io", "minimax.chat", "hailuoai.com"].some(d => url.hostname === d || url.hostname.endsWith("." + d));
  if (url.protocol !== "https:" || url.username || url.password || (url.port && url.port !== "443") || !allowed)
    throw new Error("Unrecognized MiniMax output host; inspect provider evidence before downloading");
  return url.href;
}

/** Exclusive, atomic output; partial downloads are removed and can be fetched again without generating. */
export async function downloadMiniMaxVideo(result: MiniMaxPollResult, output: string): Promise<void> {
  if (!result.done || result.error || !result.video) throw new Error("No successful MiniMax video to download");
  if (fs.existsSync(output)) throw new Error("MiniMax output already exists; refusing to overwrite");
  let uri = outputUrl(result.video.uri);
  let response: Response | undefined;
  for (let redirects = 0; redirects <= 3; redirects++) {
    try { response = await fetch(uri, { redirect: "manual", signal: AbortSignal.timeout(120_000) }); }
    catch { throw new Error("MiniMax download transport failed; poll the existing task to retry retrieval"); }
    if (![301, 302, 303, 307, 308].includes(response.status)) break;
    const location = response.headers.get("location");
    if (!location || redirects === 3) throw new Error("MiniMax download redirect limit reached");
    await response.body?.cancel();
    uri = outputUrl(new URL(location, uri).href);
  }
  const limit = 512 * 1024 * 1024;
  if (!response?.ok || !response.body) throw new Error(`MiniMax download failed (HTTP ${response?.status ?? "unknown"})`);
  if (Number(response.headers.get("content-length")) > limit) { await response.body.cancel(); throw new Error("MiniMax output exceeds the 512 MiB download limit"); }
  const tmp = `${output}.${randomUUID()}.part`;
  const fd = fs.openSync(tmp, "wx", 0o600);
  const reader = response.body.getReader();
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > limit) throw new Error("Download too large");
      fs.writeFileSync(fd, value);
    }
    if (!size) throw new Error("Empty download");
    fs.fsyncSync(fd);
    fs.linkSync(tmp, output); // Atomic no-clobber, including concurrent pollers.
  } catch {
    await reader.cancel().catch(() => {});
    throw new Error("MiniMax download incomplete or output already exists; existing sources preserved");
  } finally { fs.closeSync(fd); fs.unlinkSync(tmp); }
}
