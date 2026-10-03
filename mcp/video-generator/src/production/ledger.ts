/** Local all-in production budget. Amounts are integer USD microdollars.
 * Reservations survive crashes and failed requests; only evidence-based reconciliation
 * may reduce one. No provider calls and no automatic retry live in this module.
 */
import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";

export interface SpendEntry {
  id: string;
  category: string;
  reservedMicros: number;
  fingerprint: string;
  status: "reserved" | "submitted" | "complete" | "failed" | "uncertain" | "reconciled";
  note: string;
  createdAt: string;
  operationName?: string;
  model?: string;
  seed?: number;
  evidence?: string;
  history: Array<{ at: string; status: string; evidence?: string }>;
}
export interface Ledger {
  schemaVersion: 1;
  currency: "USD";
  limitMicros: number;
  authorization: string;
  entries: SpendEntry[];
}
export function micros(usd: number): number {
  if (!Number.isFinite(usd) || usd < 0 || !Number.isSafeInteger(Math.round(usd * 1e6)))
    throw new Error("USD amount must be finite and nonnegative");
  return Math.round(usd * 1e6);
}
export function atomicJson(filename: string, value: unknown): void {
  const tmp = `${filename}.${randomUUID()}.tmp`;
  const fd = fs.openSync(tmp, "wx", 0o600);
  try { fs.writeFileSync(fd, JSON.stringify(value, null, 2) + "\n"); fs.fsyncSync(fd); }
  finally { fs.closeSync(fd); }
  fs.renameSync(tmp, filename);
}
function locked<T>(filename: string, action: () => T): T {
  const lock = `${filename}.lock`;
  let fd: number;
  try { fd = fs.openSync(lock, "wx", 0o600); }
  catch { throw new Error("Budget is locked; inspect the owning process before recovering a stale lock"); }
  try {
    fs.writeFileSync(fd, JSON.stringify({ pid: process.pid, createdAt: new Date().toISOString() }));
    return action();
  } finally { fs.closeSync(fd); fs.unlinkSync(lock); }
}
export function readLedger(filename: string): Ledger {
  const value = JSON.parse(fs.readFileSync(filename, "utf8")) as Ledger;
  const validMoney = (n: number) => Number.isSafeInteger(n) && n >= 0;
  if (value.schemaVersion !== 1 || value.currency !== "USD" || !validMoney(value.limitMicros)
      || !value.authorization?.trim() || !Array.isArray(value.entries)
      || value.entries.some(e => !e.id || !e.category || !e.fingerprint || !e.note || !validMoney(e.reservedMicros) || !Array.isArray(e.history)
        || !["reserved", "submitted", "complete", "failed", "uncertain", "reconciled"].includes(e.status))
      || !Number.isSafeInteger(value.entries.reduce((s, e) => s + e.reservedMicros, 0))
      || new Set(value.entries.map(e => e.id)).size !== value.entries.length)
    throw new Error("Invalid budget ledger; repair from evidence, never reset it");
  return value;
}
export function budgetSummary(ledger: Ledger) {
  const reservedMicros = ledger.entries.reduce((s, e) => s + e.reservedMicros, 0);
  return { limitUsd: ledger.limitMicros / 1e6, committedUsd: reservedMicros / 1e6,
    remainingUsd: (ledger.limitMicros - reservedMicros) / 1e6, entries: ledger.entries.length };
}
export function createLedger(filename: string, limitUsd: number, authorization: string): Ledger {
  if (!authorization.trim() || limitUsd <= 0) throw new Error("Positive limit and authorization are required");
  fs.mkdirSync(path.dirname(filename), { recursive: true });
  return locked(filename, () => {
    if (fs.existsSync(filename)) throw new Error("Budget already exists; refusing to reset spend");
    const ledger: Ledger = { schemaVersion: 1, currency: "USD", limitMicros: micros(limitUsd), authorization, entries: [] };
    atomicJson(filename, ledger); return ledger;
  });
}
export function reserveSpend(filename: string, input: Pick<SpendEntry, "id" | "category" | "fingerprint" | "note"> & { usd: number }): SpendEntry {
  if (typeof input.id !== 'string' || !/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,95}$/.test(input.id) || !input.note.trim() || !input.fingerprint)
    throw new Error("Reservation needs a stable ID, fingerprint and purpose");
  const amount = micros(input.usd);
  if (!amount) throw new Error("Reservation must be positive");
  return locked(filename, () => {
    const ledger = readLedger(filename);
    if (ledger.entries.some(e => e.id === input.id)) throw new Error("Request ID already reserved; recover the existing operation, never resubmit blindly");
    const used = ledger.entries.reduce((s, e) => s + e.reservedMicros, 0);
    if (used + amount > ledger.limitMicros) throw new Error("Budget exceeded; no request submitted");
    const entry: SpendEntry = { id: input.id, category: input.category, fingerprint: input.fingerprint,
      note: input.note, reservedMicros: amount, status: "reserved", createdAt: new Date().toISOString(), history: [] };
    ledger.entries.push(entry); atomicJson(filename, ledger); return entry;
  });
}
export function updateSpend(filename: string, id: string, changes: Partial<Pick<SpendEntry,
    "status" | "operationName" | "model" | "seed" | "evidence">>): SpendEntry {
  return locked(filename, () => {
    const ledger = readLedger(filename);
    const entry = ledger.entries.find(e => e.id === id);
    if (!entry) throw new Error("Unknown reservation");
    Object.assign(entry, changes);
    entry.history.push({ at: new Date().toISOString(), status: entry.status, evidence: changes.evidence });
    atomicJson(filename, ledger); return entry;
  });
}
export function reconcileSpend(filename: string, id: string, usd: number, evidence: string): SpendEntry {
  if (!evidence.trim()) throw new Error("Reconciliation requires billing or usage evidence");
  return locked(filename, () => {
    const ledger = readLedger(filename);
    const entry = ledger.entries.find(e => e.id === id);
    if (!entry) throw new Error("Unknown reservation");
    const oldMicros = entry.reservedMicros;
    entry.reservedMicros = micros(usd); entry.status = "reconciled"; entry.evidence = evidence;
    entry.history.push({ at: new Date().toISOString(), status: "reconciled",
      evidence: `${oldMicros} -> ${entry.reservedMicros} microUSD: ${evidence}` });
    // Record actual overruns honestly; subsequent reservations will be refused.
    atomicJson(filename, ledger); return entry;
  });
}
