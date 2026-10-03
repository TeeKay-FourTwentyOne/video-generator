import { z } from "zod";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { PROJECT_ROOT } from "../utils/paths.js";

const run = promisify(execFile);
/** MCP and shell use the same implementation; no second orchestration engine. */
async function invoke(args: string[]) {
  const { stdout } = await run(process.execPath, [path.join(PROJECT_ROOT, "tools/production/film.mjs"), ...args],
    { cwd: PROJECT_ROOT, maxBuffer: 4 * 1024 * 1024 });
  return { content: [{ type: "text" as const, text: stdout }] };
}
const workspace = z.string().describe("Project-local workspace under data/workspace");
export const productionTools = {
  production_doctor: {
    name: "production_doctor", description: "Inspect local prerequisites and credential presence. No network calls or installations.",
    inputSchema: {}, handler: async () => invoke(["doctor"]),
  },
  production_init: {
    name: "production_init", description: "Create a local workspace and all-in ledger from the user's explicit spend authorization. Never resets an existing budget.",
    inputSchema: { workspace, limitUsd: z.number().positive(), authorization: z.string().min(1) },
    handler: async (a: { workspace: string; limitUsd: number; authorization: string }) => invoke(["init", a.workspace, String(a.limitUsd), a.authorization]),
  },
  production_status: {
    name: "production_status", description: "Read the all-in budget and reservation states. Local only.",
    inputSchema: { workspace }, handler: async (a: { workspace: string }) => invoke(["status", a.workspace]),
  },
  production_plan: {
    name: "production_plan", description: "Validate the film plan and quote qualified Veo shots. No provider calls or spend.",
    inputSchema: { workspace }, handler: async (a: { workspace: string }) => invoke(["plan", a.workspace]),
  },
  production_submit: {
    name: "production_submit", description: "Submit one authorized planned shot after an atomic budget reservation. Stable request IDs prevent duplicate paid submissions.",
    inputSchema: { workspace, shotId: z.string() },
    handler: async (a: { workspace: string; shotId: string }) => invoke(["submit", a.workspace, a.shotId]),
  },
  production_poll: {
    name: "production_poll", description: "Poll once and retrieve an existing shot operation. Saves source hash and metadata. Never generates or resubmits.",
    inputSchema: { workspace, shotId: z.string() },
    handler: async (a: { workspace: string; shotId: string }) => invoke(["poll", a.workspace, a.shotId]),
  },
  production_image: {
    name: "production_image", description: "Generate one planned anchor through the existing Google provider, with a prior ledger reservation. No automatic retries.",
    inputSchema: { workspace, requestFile: z.string().describe("Workspace-relative JSON request, with promptFile, refs, id, aspectRatio and output") },
    handler: async (a: { workspace: string; requestFile: string }) => invoke(["image", a.workspace, a.requestFile]),
  },
  production_assemble: {
    name: "production_assemble", description: "Render a new local edit version from source hashes and accepted frame ranges. Refuses existing output versions.",
    inputSchema: { workspace, version: z.string() },
    handler: async (a: { workspace: string; version: string }) => invoke(["assemble", a.workspace, a.version]),
  },
  production_review: {
    name: "production_review", description: "Build a local native-resolution review player with shot navigation and delivery evidence.",
    inputSchema: { workspace, version: z.string() },
    handler: async (a: { workspace: string; version: string }) => invoke(["review", a.workspace, a.version]),
  },
};
