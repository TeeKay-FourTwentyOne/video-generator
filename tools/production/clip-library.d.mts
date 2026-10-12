export const REPO: string;
export function generationMetadata(input?: Record<string, unknown>, source?: string): Record<string, unknown>;
export function importClip(file: string, metadata?: Record<string, unknown>, repo?: string): {
  id: string; sha256: string; path: string; record: { technical: { durationSeconds: number } };
};
