/** Direct Runway API. Bounded calls, durable reservations and no automatic POST retries. */
import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { loadConfig } from "../utils/config.js";
import { resolvePath } from "../utils/paths.js";
import { atomicJson, readLedger, reserveSpend, updateSpend } from "../production/ledger.js";
import { RUNWAY_MODELS, prepareRunwayRequest, type RunwayModel, type RunwaySpec } from "../production/runway-spec.js";
import { saveGenerationSnapshot, snapshotHash } from "../../../../tools/production/generation-snapshot.mjs";
export { prepareRunwayRequest } from "../production/runway-spec.js";

const API_ROOT = "https://api.dev.runwayml.com";
const API_VERSION = "2024-11-06";
const statuses = ["PENDING", "THROTTLED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"] as const;
export interface RunwaySubmitOptions extends RunwaySpec { budgetFile: string; requestId: string }
export interface RunwaySubmitResult { provider: "runway"; operationName: string; model: RunwayModel }
export interface RunwayPollResult {
  done: boolean; operationName: string; model: RunwayModel; status: typeof statuses[number];
  video?: { uri: string }; error?: string; failureCode?: string; createdAt?: string;
  costCredits?: number; estimatedCostCredits?: number;
}
function configuredKey() { return process.env.RUNWAYML_API_SECRET ?? loadConfig().runwayApiKey; }
export function runwayCredentialsConfigured(): boolean {
  const key = configuredKey();
  return typeof key === "string" && !!key.trim() && !/\s/.test(key.trim());
}
function apiKey(): string {
  const key = configuredKey();
  if (typeof key !== "string" || !key.trim() || /\s/.test(key.trim()))
    throw new Error("Configure RUNWAYML_API_SECRET or runwayApiKey in the ignored data/config.json");
  return key.trim();
}
function taskId(value: unknown): string {
  if (typeof value !== "string" || !/^[\da-f]{8}-[\da-f]{4}-4[\da-f]{3}-[89ab][\da-f]{3}-[\da-f]{12}$/i.test(value))
    throw new Error("Invalid Runway task ID");
  return value;
}
class RunwayHttpError extends Error {
  constructor(readonly status: number) {
    const reason: Record<number, string> = { 400: "invalid request", 401: "authentication failed", 402: "insufficient balance",
      403: "access denied", 404: "task not found", 422: "request rejected", 429: "rate limited" };
    super(`Runway HTTP ${status}: ${reason[status] ?? "provider request failed"}. No automatic retry.`);
  }
  get rejected() { return [400, 401, 402, 403, 404, 422, 429].includes(this.status); }
}
async function requestJson(endpoint: string, method = "GET", body?: string, key = apiKey()): Promise<any> {
  let response: Response;
  try {
    response = await fetch(API_ROOT + endpoint, { method, redirect: "error", signal: AbortSignal.timeout(120_000),
      headers: { Authorization: `Bearer ${key}`, "X-Runway-Version": API_VERSION,
        ...(body ? { "Content-Type": "application/json" } : {}) }, body });
  } catch {
    throw new Error("Runway transport failed or timed out; retain the reservation and recover the existing task before another submission");
  }
  if (!response.ok) throw new RunwayHttpError(response.status);
  let data;
  try { data = await response.json(); } catch { throw new Error("Runway returned invalid JSON; submission outcome may be uncertain"); }
  if (!data || typeof data !== "object" || data.error) throw new Error("Runway returned a malformed response; no automatic retry");
  return data;
}

function attempt(options: RunwaySubmitOptions) {
  if (!options.budgetFile || typeof options.requestId !== "string" || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$/.test(options.requestId))
    throw new Error("Runway requires budgetFile and a stable requestId from an authorized production ledger");
  const prepared = prepareRunwayRequest(options);
  const budgetFile = resolvePath(options.budgetFile);
  const journalFile = path.join(path.dirname(budgetFile), "operations", `${options.requestId}.json`);
  const entry = readLedger(budgetFile).entries.find(e => e.id === options.requestId);
  if (entry && (entry.category !== "runway" || entry.fingerprint !== prepared.fingerprint))
    throw new Error("Request ID reused with changed content or provider; preserve the original and use a new attempt ID");
  return { ...prepared, budgetFile, journalFile, entry };
}
export async function submitRunwayGeneration(options: RunwaySubmitOptions): Promise<RunwaySubmitResult> {
  const a = attempt(options);
  if (a.entry) {
    let operationName = a.entry.operationName;
    if (!operationName && fs.existsSync(a.journalFile)) {
      const journal = JSON.parse(fs.readFileSync(a.journalFile, "utf8"));
      if (journal.fingerprint === a.fingerprint && journal.provider === "runway" && journal.operationName) {
        operationName = taskId(journal.operationName);
        updateSpend(a.budgetFile, options.requestId, { operationName, model: a.quote.modelId, status: "submitted",
          evidence: "Recovered task ID from durable local journal; no new POST" });
      }
    }
    if (operationName) return { provider: "runway", operationName: taskId(operationName), model: a.quote.modelId };
    throw new Error("Runway request already reserved without a known task; inspect the developer portal and recover-runway, never resubmit blindly");
  }
  const key = apiKey();
  fs.mkdirSync(path.dirname(a.journalFile), { recursive: true });
  if (fs.existsSync(a.journalFile)) throw new Error("Existing Runway journal has no matching reservation; inspect before proceeding");
  reserveSpend(a.budgetFile, { id: options.requestId, category: "runway", fingerprint: a.fingerprint,
    usd: a.quote.estimatedUsd, note: "Runway native MP4 generation" });
  const record = { schemaVersion: 1, provider: "runway", requestId: options.requestId, fingerprint: a.fingerprint,
    quote: a.quote, endpoint: a.endpoint, prompt: options.prompt, sources: a.sources, createdAt: new Date().toISOString() };
  let operationName: string | undefined;
  try {
    const snapshot = saveGenerationSnapshot(a.budgetFile, { provider: "runway", requestId: options.requestId,
      fingerprint: a.fingerprint, prompt: options.prompt, requestedModel: options.model, model: a.quote.modelId,
      seed: a.quote.seed, parameters: { durationSeconds: a.quote.durationSeconds, aspectRatio: a.quote.aspectRatio,
        resolution: a.quote.resolution, generateAudio: a.quote.generateAudio, mode: a.quote.mode,
        ratio: a.quote.ratio, outputFormat: a.quote.outputFormat }, sources: a.sources,
      api: { endpoint: a.endpoint, version: API_VERSION } });
    Object.assign(record, { snapshotSha256: snapshotHash(snapshot) });
    atomicJson(a.journalFile, { ...record, status: "reserved" });
    operationName = taskId((await requestJson(a.endpoint, "POST", a.serializedBody, key)).id);
    const result: RunwaySubmitResult = { provider: "runway", operationName, model: a.quote.modelId };
    atomicJson(a.journalFile, { ...record, ...result, status: "submitted" });
    updateSpend(a.budgetFile, options.requestId, { status: "submitted", operationName, model: a.quote.modelId, seed: options.seed });
    return result;
  } catch (error) {
    const status = operationName ? "submitted" : error instanceof RunwayHttpError && error.rejected ? "failed" : "uncertain";
    const evidence = operationName ? "Provider returned a task ID; recover local persistence before further work"
      : error instanceof RunwayHttpError ? error.message : "Submission outcome uncertain; reservation retained. Inspect provider records before another attempt.";
    try { atomicJson(a.journalFile, { ...record, operationName, status, evidence }); } catch { /* Ledger also retains reservation. */ }
    try { updateSpend(a.budgetFile, options.requestId, { status, operationName, model: a.quote.modelId, evidence }); } catch { /* Journal retains task evidence. */ }
    throw error;
  }
}

export function interpretRunwayTask(task: any, operationName: string, model: string): RunwayPollResult {
  if (!RUNWAY_MODELS.includes(model as RunwayModel) || !task || task.id !== taskId(operationName) || !statuses.includes(task.status))
    throw new Error("Malformed or mismatched Runway task");
  const done = ["SUCCEEDED", "FAILED", "CANCELLED"].includes(task.status);
  const result: RunwayPollResult = { done, operationName, model: model as RunwayModel, status: task.status };
  if (typeof task.createdAt === "string" && /^\d{4}-\d{2}-\d{2}T[\d:.]+Z$/.test(task.createdAt)) result.createdAt = task.createdAt;
  if (done && Number.isSafeInteger(task.cost?.credits)) result.costCredits = task.cost.credits;
  if (!done && typeof task.estimatedCost?.credits === "number" && Number.isFinite(task.estimatedCost.credits) && task.estimatedCost.credits >= 0)
    result.estimatedCostCredits = task.estimatedCost.credits;
  if (task.status === "FAILED" || task.status === "CANCELLED") {
    // Never echo free-form provider failure text, which may contain prompt or credential data.
    if (typeof task.failureCode === "string" && /^[A-Z0-9.]{1,80}$/.test(task.failureCode)) result.failureCode = task.failureCode;
    result.error = `Runway generation ${task.status.toLowerCase()}${result.failureCode ? ` (${result.failureCode})` : ""}; no automatic retry`;
  } else if (task.status === "SUCCEEDED") {
    if (!Array.isArray(task.output) || task.output.length !== 1 || typeof task.output[0] !== "string" || !task.output[0])
      result.error = "Runway completed without exactly one video URL";
    else result.video = { uri: task.output[0] };
  }
  return result;
}
export async function pollRunwayOperation(operationName: string, model: string): Promise<RunwayPollResult> {
  taskId(operationName);
  if (!RUNWAY_MODELS.includes(model as RunwayModel)) throw new Error("Unsupported Runway task model");
  return interpretRunwayTask(await requestJson(`/v1/tasks/${operationName}`), operationName, model);
}
/** Read-only account check. Deliberately omit IDs and unrelated account data. */
export async function getRunwayAccount() {
  const data = await requestJson("/v1/organization");
  if (!Number.isSafeInteger(data.creditBalance) || data.creditBalance < 0) throw new Error("Malformed Runway credit balance");
  const modelLimits: Record<string, Record<string, number | null>> = {};
  for (const model of RUNWAY_MODELS) {
    const limits = data.tier?.models?.[model];
    if (!limits) continue;
    modelLimits[model] = {};
    for (const k of ["maxConcurrentGenerations", "maxDailyGenerations"])
      if (limits[k] === null || (Number.isSafeInteger(limits[k]) && limits[k] >= 0)) modelLimits[model][k] = limits[k];
  }
  return { creditBalance: data.creditBalance, balanceUsd: data.creditBalance / 100, modelLimits };
}
/** Runway's task response lacks model/prompt parameters. Matching requires external evidence. */
export async function recoverRunwayOperation(options: RunwaySubmitOptions, operationName: string, evidence: string) {
  if (typeof evidence !== "string" || !evidence.trim()) throw new Error("Recovery requires evidence linking this task to the original attempt");
  taskId(operationName);
  const a = attempt(options);
  if (!a.entry || (a.entry.operationName && a.entry.operationName !== operationName)) throw new Error("No matching unresolved Runway reservation");
  if (readLedger(a.budgetFile).entries.some(e => e.id !== options.requestId && e.operationName === operationName))
    throw new Error("Runway task already belongs to another reservation");
  await pollRunwayOperation(operationName, a.quote.modelId);
  fs.mkdirSync(path.dirname(a.journalFile), { recursive: true });
  const result: RunwaySubmitResult = { provider: "runway", operationName, model: a.quote.modelId };
  const saved = fs.existsSync(a.journalFile) ? JSON.parse(fs.readFileSync(a.journalFile, "utf8")) : {};
  atomicJson(a.journalFile, { ...saved, ...result, requestId: options.requestId, fingerprint: a.fingerprint,
    quote: a.quote, sources: a.sources, prompt: options.prompt, status: "submitted", recoveredAt: new Date().toISOString(), evidence });
  updateSpend(a.budgetFile, options.requestId, { operationName, model: a.quote.modelId, status: "submitted", evidence });
  return result;
}

function outputUrl(uri: string): string {
  let url: URL;
  try { url = new URL(uri); } catch { throw new Error("Invalid Runway output URL"); }
  const allowed = ["cloudfront.net", "runwayml.com", "runway.com"].some(d => url.hostname.endsWith("." + d));
  if (url.protocol !== "https:" || url.username || url.password || (url.port && url.port !== "443") || !allowed)
    throw new Error("Unrecognized Runway output host; inspect provider evidence before downloading");
  return url.href;
}
/** Download without credentials, cap redirects/size, and never overwrite a source clip. */
export async function downloadRunwayVideo(result: RunwayPollResult, output: string): Promise<void> {
  if (!result.done || result.error || !result.video) throw new Error("No successful Runway video to download");
  if (fs.existsSync(output)) throw new Error("Runway output already exists; refusing to overwrite");
  let uri = outputUrl(result.video.uri), response: Response | undefined;
  for (let redirects = 0; redirects <= 3; redirects++) {
    try { response = await fetch(uri, { redirect: "manual", signal: AbortSignal.timeout(120_000) }); }
    catch { throw new Error("Runway download transport failed; poll the same task to retrieve again"); }
    if (![301, 302, 303, 307, 308].includes(response.status)) break;
    const location = response.headers.get("location");
    await response.body?.cancel();
    if (!location || redirects === 3) throw new Error("Runway download redirect limit reached");
    uri = outputUrl(new URL(location, uri).href);
  }
  const limit = 512 * 1024 * 1024;
  if (!response?.ok || !response.body) throw new Error(`Runway download failed (HTTP ${response?.status ?? "unknown"})`);
  if (Number(response.headers.get("content-length")) > limit) { await response.body.cancel(); throw new Error("Runway output exceeds 512 MiB"); }
  const tmp = `${output}.${randomUUID()}.part`, fd = fs.openSync(tmp, "wx", 0o600);
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
    fs.fsyncSync(fd); fs.linkSync(tmp, output);
  } catch {
    await reader.cancel().catch(() => {});
    throw new Error("Runway download incomplete or output already exists; existing sources preserved");
  } finally { fs.closeSync(fd); fs.unlinkSync(tmp); }
}
