export function snapshotHash(snapshot: Record<string, any>): string;
export function readSnapshot(file: string): Record<string, any>;
export function validateSnapshot(snapshot: Record<string, any>): Record<string, any>;
export function writeSnapshot(file: string, snapshot: Record<string, any>): void;
export function snapshotPath(budgetFile: string, requestId: string): string;
export function saveGenerationSnapshot(budgetFile: string, input: Record<string, any>): Record<string, any>;
export function readGenerationSnapshot(budgetFile: string, requestId: string, expected?: Record<string, any>): Record<string, any> | undefined;
