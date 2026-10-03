import { z } from "zod";
import {
  createVeoJob,
  resumeVeoJob,
  getJob,
  listJobs as listJobsService,
  type Job,
} from "../services/jobs.js";

/**
 * Jobs tools - create, get, and list generation jobs
 */

export const jobsTools = {
  resume_job: {
    name: "resume_job",
    title: "Resume Existing Operation",
    description: "Resume polling an existing Veo job after a restart or timeout. Never submits a new generation.",
    inputSchema: { jobId: z.string() },
    handler: async (args: { jobId: string }) => {
      const job = await resumeVeoJob(args.jobId);
      return { content: [{ type: "text" as const, text: JSON.stringify(job) }] };
    },
  },
  create_job: {
    name: "create_job",
    title: "Create Job",
    description:
      "Create a new Veo video generation job. Returns immediately with job ID. Poll with get_job to check status.",
    inputSchema: {
      budgetFile: z.string().describe("Path to an initialized all-in production budget JSON"),
      requestId: z.string().describe("Stable attempt ID; repeating it recovers rather than resubmits"),
      prompt: z.string().describe("Video generation prompt for Veo"),
      aspectRatio: z
        .enum(["16:9", "9:16"])
        .optional()
        .default("9:16")
        .describe("Video aspect ratio"),
      durationSeconds: z
        .number()
        .optional()
        .default(8)
        .describe("Duration must be exactly 4, 6 or 8 seconds"),
      firstFramePath: z
        .string()
        .optional()
        .describe("Path to first-frame anchor image (image-to-video; maps to Vertex instance.image)"),
      lastFramePath: z
        .string()
        .optional()
        .describe("Path to last-frame anchor image (book-ending; maps to Vertex instance.lastFrame)"),
      model: z
        .enum(["veo-3.1", "veo-3.1-prod", "veo-3.1-fast", "veo-3.1-fast-prod", "veo-2.0"])
        .optional()
        .describe("Qualified GA model; use the production quote for audio/resolution-specific rates"),
      seed: z
        .number()
        .optional()
        .describe("Seed (uint32) for provenance; identical output is not guaranteed."),
      generateAudio: z
        .boolean()
        .optional()
        .describe("Enable/disable native audio generation (Veo 3+ only). Disabling saves cost on drafts."),
      resolution: z
        .enum(["720p", "1080p"])
        .optional()
        .describe("Qualified output resolution: 720p or 1080p."),
    },
    handler: async (args: {
      budgetFile: string;
      requestId: string;
      prompt: string;
      aspectRatio?: "16:9" | "9:16" | "1:1";
      durationSeconds?: number;
      firstFramePath?: string;
      lastFramePath?: string;
      model?: "veo-3.1" | "veo-3.1-prod" | "veo-3.1-fast" | "veo-3.1-fast-prod" | "veo-2.0";
      seed?: number;
      generateAudio?: boolean;
      resolution?: "720p" | "1080p" | "4k";
    }) => {
      try {
        const job = await createVeoJob({
          budgetFile: args.budgetFile,
          requestId: args.requestId,
          prompt: args.prompt,
          aspectRatio: args.aspectRatio,
          durationSeconds: args.durationSeconds,
          firstFramePath: args.firstFramePath,
          lastFramePath: args.lastFramePath,
          model: args.model,
          seed: args.seed,
          generateAudio: args.generateAudio,
          resolution: args.resolution,
        });

        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(
                {
                  jobId: job.id,
                  status: job.status,
                  model: args.model || "veo-3.1",
                  seed: job.input.seed,
                  message: "Job created. Poll with get_job to check status.",
                },
                null,
                2
              ),
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text" as const,
              text: `Error creating job: ${error instanceof Error ? error.message : "Unknown error"}`,
            },
          ],
        };
      }
    },
  },

  get_job: {
    name: "get_job",
    title: "Get Job",
    description: "Get the current status of a generation job by ID.",
    inputSchema: {
      jobId: z.string().describe("Job ID to retrieve"),
    },
    handler: async (args: { jobId: string }) => {
      const job = getJob(args.jobId);

      if (!job) {
        return {
          content: [
            {
              type: "text" as const,
              text: `Job not found: ${args.jobId}`,
            },
          ],
        };
      }

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(job, null, 2),
          },
        ],
      };
    },
  },

  list_jobs: {
    name: "list_jobs",
    title: "List Jobs",
    description: "List generation jobs (newest first).",
    inputSchema: {
      limit: z
        .number()
        .optional()
        .default(50)
        .describe("Maximum number of jobs to return"),
    },
    handler: async (args: { limit?: number }) => {
      const jobs = listJobsService(args.limit);

      // Create summary for each job
      const summary = jobs.map((job: Job) => ({
        id: job.id,
        type: job.type,
        status: job.status,
        createdAt: job.createdAt,
        prompt: job.input.prompt.slice(0, 100) + (job.input.prompt.length > 100 ? "..." : ""),
        result: job.result?.path || null,
        error: job.error || null,
      }));

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(
              {
                count: jobs.length,
                jobs: summary,
              },
              null,
              2
            ),
          },
        ],
      };
    },
  },
};
