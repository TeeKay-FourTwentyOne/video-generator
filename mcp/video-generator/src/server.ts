#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { configTools } from "./tools/config.js";
import { projectsTools } from "./tools/projects.js";
import { jobsTools } from "./tools/jobs.js";
import { generationTools } from "./tools/generation.js";
import { lockingTools } from "./tools/locking.js";
import { executionTools } from "./tools/execution.js";
import { audioTools } from "./tools/audio.js";
import { analysisTools } from "./tools/analysis.js";
import { editingTools } from "./tools/editing.js";
import { assemblyTools } from "./tools/assembly.js";
import { validationTools } from "./tools/validation.js";
import { clipMetadataTools } from "./tools/clip-metadata.js";
import { faceDetectionTools } from "./tools/face-detection.js";
import { songAnalysisTools } from "./tools/song-analysis.js";
import { upscalingTools } from "./tools/upscaling.js";
import { productionTools } from "./tools/production.js";

// Create MCP server
const server = new McpServer({
  name: "video-generator",
  version: "1.0.0",
});

// Tool definition type
interface ToolDef {
  name: string;
  description: string;
  inputSchema: Record<string, z.ZodTypeAny>;
  handler: (args: Record<string, unknown>) => Promise<{
    content: Array<{ type: "text"; text: string }>;
  }>;
}

// Helper to register tools from a tools object
function registerTools(tools: Record<string, ToolDef>) {
  for (const tool of Object.values(tools)) {
    server.registerTool(tool.name, {
      description: tool.description,
      inputSchema: tool.inputSchema,
    }, async (args) => {
      try {
        const result = await tool.handler(args as Record<string, unknown>);
        // Older handlers encode errors as text. Surface them to MCP clients as errors.
        return { ...result, isError: result.content.some(c => /^(Error\b|Job not found:)/.test(c.text)) };
      } catch (error) {
        return { isError: true, content: [{ type: "text" as const,
          text: error instanceof Error ? error.message : "Tool failed" }] };
      }
    });
  }
}

// Keep the default agent surface small. Legacy specialists remain explicitly opt-in.
const profile = process.env.VIDEO_MCP_PROFILE || "production";
if (!["production", "legacy"].includes(profile)) throw new Error("VIDEO_MCP_PROFILE must be production or legacy");
if (profile === "production") {
  registerTools({ get_config: configTools.get_config } as unknown as Record<string, ToolDef>);
} else {
// Register all legacy tool categories
// Phase 3A: Core tools
registerTools(configTools as unknown as Record<string, ToolDef>);
registerTools(projectsTools as unknown as Record<string, ToolDef>);

// Phase 3B: Jobs, generation, locking, execution
registerTools(jobsTools as unknown as Record<string, ToolDef>);
registerTools(generationTools as unknown as Record<string, ToolDef>);
registerTools(lockingTools as unknown as Record<string, ToolDef>);
registerTools(executionTools as unknown as Record<string, ToolDef>);

// Phase 3C: Audio, analysis, editing
registerTools(audioTools as unknown as Record<string, ToolDef>);
registerTools(analysisTools as unknown as Record<string, ToolDef>);
registerTools(editingTools as unknown as Record<string, ToolDef>);

// Phase 3D: Assembly, validation
registerTools(assemblyTools as unknown as Record<string, ToolDef>);
registerTools(validationTools as unknown as Record<string, ToolDef>);

// Clip metadata tools
registerTools(clipMetadataTools as unknown as Record<string, ToolDef>);

// Face detection tools
registerTools(faceDetectionTools as unknown as Record<string, ToolDef>);

// Song analysis tools
registerTools(songAnalysisTools as unknown as Record<string, ToolDef>);

// Upscaling tools
registerTools(upscalingTools as unknown as Record<string, ToolDef>);
}
registerTools(productionTools as unknown as Record<string, ToolDef>);

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Video Generator MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
