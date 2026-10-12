import fs from "fs";
import { CONFIG_PATH } from "./paths.js";

export interface Config {
  anthropicKey?: string;
  googleApiKey?: string;
  elevenLabsKey?: string;
  openaiKey?: string;
  minimaxApiKey?: string;
  runwayApiKey?: string;
  currentProject?: string;
  defaultVoiceId?: string;
  veoServiceAccountPath?: string;
  veoGcsBucket?: string;
  [key: string]: unknown;
}

/**
 * Load configuration from data/config.json
 */
export function loadConfig(): Config {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      const data = fs.readFileSync(CONFIG_PATH, "utf-8");
      return JSON.parse(data);
    }
  } catch {
    // JSON parse errors can contain a snippet of a credential value.
    console.error("Unable to read local configuration; check data/config.json");
  }
  return {};
}

/**
 * Save configuration to data/config.json
 */
export function saveConfig(config: Config): void {
  const serialized = JSON.stringify(config, null, 2);
  const fd = fs.openSync(CONFIG_PATH, "w", 0o600);
  try {
    // `mode` affects new files only; tighten existing files before writing secrets.
    fs.fchmodSync(fd, 0o600);
    fs.writeFileSync(fd, serialized);
  } finally {
    fs.closeSync(fd);
  }
}

/**
 * Update specific config fields (merge with existing)
 */
export function updateConfig(updates: Partial<Config>): Config {
  const current = loadConfig();
  const updated = { ...current, ...updates };
  saveConfig(updated);
  return updated;
}
