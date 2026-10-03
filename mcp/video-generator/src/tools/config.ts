import { z } from "zod";
import { loadConfig, updateConfig, type Config } from "../utils/config.js";

/** Report presence only. An allowlist misses historical aliases and future secrets. */
export function configurationSummary(config: Config): Record<string, boolean> {
  return Object.fromEntries(Object.entries(config).map(([key, value]) => [key, value !== undefined && value !== null && value !== ""]));
}

/**
 * Config tools - get and save configuration
 */

export const configTools = {
  get_config: {
    name: "get_config",
    title: "Get Configuration",
    description: "Report configured field names and presence only. Never returns credential values.",
    inputSchema: {
      includeKeys: z
        .boolean()
        .optional()
        .default(false)
        .describe("Deprecated and ignored: credential values are never returned"),
    },
    handler: async (args: { includeKeys?: boolean }) => {
      const config = loadConfig();

      const safeConfig = configurationSummary(config);

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(safeConfig, null, 2),
          },
        ],
      };
    },
  },

  save_config: {
    name: "save_config",
    title: "Save Configuration",
    description: "Update configuration fields. Merges with existing config.",
    inputSchema: {
      updates: z
        .record(z.string(), z.any())
        .describe("Configuration fields to update (key-value pairs)"),
    },
    handler: async (args: { updates: Record<string, unknown> }) => {
      const updated = updateConfig(args.updates);

      const safeConfig = configurationSummary(updated);

      return {
        content: [
          {
            type: "text" as const,
            text: `Configuration updated:\n${JSON.stringify(safeConfig, null, 2)}`,
          },
        ],
      };
    },
  },
};
