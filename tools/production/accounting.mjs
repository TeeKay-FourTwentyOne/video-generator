#!/usr/bin/env node
/** Read-only reconciliation of existing ledgers into ignored, itemized reports. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { safePath, sha256 } from './record-schema.mjs';
import { atomicWrite } from './records.mjs';

const requireValue = (test, message) => { if (!test) throw new Error(message); };
const micros = amount => {
  if (amount === null || amount === undefined) return null;
  const n = Math.round(amount * 1e6);
  requireValue(typeof amount === 'number' && Number.isFinite(amount) && amount >= 0 && Number.isSafeInteger(n), 'Invalid accounting amount');
  return n;
};
const sum = values => {
  const n = values.reduce((total, value) => total + value, 0);
  requireValue(Number.isSafeInteger(n), 'Accounting total exceeds integer precision');
  return n;
};

export async function reconcileAccounting(repo, config) {
  requireValue(config && config.schemaVersion === 1 && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(config.projectId) &&
    /^\d{4}-\d{2}-\d{2}$/.test(config.asOf) && Array.isArray(config.sources) && config.sources.length > 0 &&
    Object.keys(config).every(k => ['schemaVersion', 'projectId', 'asOf', 'sources'].includes(k)), 'Invalid local accounting source map');
  requireValue(Number.isFinite(Date.parse(config.asOf)) && new Date(config.asOf).toISOString().slice(0, 10) === config.asOf, 'Invalid accounting date');
  const sources = [], entries = [], allocations = [], sourcePaths = new Set(), operations = new Set();
  for (const source of config.sources) {
    requireValue(source && typeof source.path === 'string' && source.path.startsWith('data/') &&
      ['budget-v1', 'episode-allowances-v1'].includes(source.kind) &&
      Object.keys(source).every(k => ['path', 'kind', 'basisByEntry'].includes(k)) && !sourcePaths.has(source.path), 'Invalid or duplicate accounting source');
    sourcePaths.add(source.path);
    const bytes = await fs.readFile(await safePath(repo, source.path)), ledger = JSON.parse(bytes);
    sources.push({ ...source, sha256: sha256(bytes) });
    if (source.kind === 'budget-v1') {
      requireValue(ledger.schemaVersion === 1 && ledger.currency === 'USD' && Array.isArray(ledger.entries), 'Invalid maintained ledger');
      const bases = source.basisByEntry ?? {};
      requireValue(bases && typeof bases === 'object' && !Array.isArray(bases) && Object.entries(bases).every(([id, basis]) =>
        ['reported-usage', 'invoiced', 'estimate'].includes(basis) && ledger.entries.some(e => e.id === id && e.status === 'reconciled')),
      'Accounting basis must identify reconciled entries and distinguish estimates from charges');
      const ids = new Set();
      for (const entry of ledger.entries) {
        requireValue(typeof entry.id === 'string' && entry.id && !ids.has(entry.id) &&
          typeof entry.category === 'string' && Number.isSafeInteger(entry.reservedMicros) && entry.reservedMicros >= 0 &&
          ['reserved', 'submitted', 'complete', 'failed', 'uncertain', 'reconciled'].includes(entry.status), 'Invalid ledger entry');
        ids.add(entry.id);
        if (entry.operationName) {
          const operation = `${entry.category}:${entry.operationName}`;
          requireValue(!operations.has(operation), 'One provider operation occurs in multiple accounting sources');
          operations.add(operation);
        }
        const reconciled = entry.status === 'reconciled';
        requireValue(!reconciled || typeof entry.evidence === 'string' && entry.evidence.trim(), 'Reconciled entry lacks usage or billing evidence');
        const basis = reconciled ? bases[entry.id] ?? 'reconciled-unclassified' : 'unresolved-reservation';
        const confirmed = ['reported-usage', 'invoiced'].includes(basis);
        entries.push({ sourcePath: source.path, sourceEntryId: entry.id, category: entry.category,
          ...(entry.model ? { model: entry.model } : {}), purpose: entry.note ?? '',
          status: entry.status, basis,
          confirmedMicros: confirmed ? entry.reservedMicros : null,
          estimatedMicros: basis === 'estimate' ? entry.reservedMicros : null,
          unclassifiedMicros: basis === 'reconciled-unclassified' ? entry.reservedMicros : null,
          reservedMicros: reconciled ? 0 : entry.reservedMicros,
          ...(entry.evidence ? { evidence: entry.evidence } : {}) });
      }
    } else {
      requireValue(!source.basisByEntry, 'Legacy invoice/allowance evidence supplies its own accounting basis');
      requireValue(ledger.allocationIsNotBilling === true && Array.isArray(ledger.imageCalls) && Array.isArray(ledger.paidCalls) &&
        ledger.allocations && typeof ledger.allocations === 'object', 'Invalid episode allowance ledger');
      for (const [category, amount] of Object.entries(ledger.allocations)) {
        const amountMicros = micros(amount);
        requireValue(amountMicros !== null, 'Allocation amount is unknown; keep billing unknowns in their entries');
        allocations.push({ sourcePath: source.path, category, amountMicros });
      }
      for (const [index, entry] of [...ledger.imageCalls, ...ledger.paidCalls].entries()) {
        const amount = micros(entry.billedUSD);
        entries.push({ sourcePath: source.path, sourceEntryId: `item-${index + 1}`, category: entry.kind ?? 'images',
          provider: entry.service ?? entry.method, ...(entry.model ? { model: entry.model } : {}),
          purpose: entry.asset ?? entry.kind, basis: amount === null ? 'billing-unknown' : 'invoiced',
          confirmedMicros: amount, reservedMicros: null,
          ...(entry.allowanceUSD !== undefined ? { allowanceMicros: micros(entry.allowanceUSD) } : {}),
          ...(entry.count !== undefined ? { calls: entry.count } : {}),
          ...(entry.reportedCharacterCredits !== undefined ? { usage: { unit: 'character-credits', quantity: entry.reportedCharacterCredits } } : {}) });
      }
    }
  }
  const unknown = entries.filter(e => e.confirmedMicros === null);
  return { schemaVersion: 1, projectId: config.projectId, asOf: config.asOf, currency: 'USD', sources, entries, allocations,
    totals: {
      confirmedMicros: sum(entries.map(e => e.confirmedMicros ?? 0)),
      confirmedTotalIsComplete: unknown.length === 0,
      unresolvedEntries: unknown.length,
      knownReservedMicros: sum(entries.map(e => e.reservedMicros ?? 0)),
      estimatedMicros: sum(entries.map(e => e.estimatedMicros ?? 0)),
      unclassifiedMicros: sum(entries.map(e => e.unclassifiedMicros ?? 0)),
      reservationTotalIsComplete: entries.every(e => e.reservedMicros !== null),
      allocatedMicros: sum(allocations.map(e => e.amountMicros ?? 0)),
    },
    note: 'Derived evidence, not a writable budget or spending authorization. Reconciliation alone does not establish billing; its evidence basis must be reviewed. Reported usage is not necessarily an invoice. Allocations, estimates, account credit and actual charges are different facts.' };
}

export async function writeAccounting(repo, config, { check = false, dryRun = false } = {}) {
  const report = await reconcileAccounting(repo, config);
  const file = `data/accounting/${report.projectId}/summary.json`;
  const bytes = JSON.stringify(report, null, 2) + '\n';
  const before = await fs.readFile(await safePath(repo, file), 'utf8').catch(e => { if (e.code !== 'ENOENT') throw e; });
  const changed = before !== bytes;
  if (check && changed) throw new Error('Local accounting report drift');
  if (changed && !check && !dryRun) {
    if (before) await atomicWrite(repo, `data/accounting/${report.projectId}/history/${sha256(before)}.json`, before);
    await atomicWrite(repo, file, bytes);
  }
  return { path: file, entries: report.entries.length, sources: report.sources.length, changed, written: changed && !check && !dryRun };
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  try {
    const [input, ...flags] = process.argv.slice(2);
    requireValue(input?.startsWith('data/') && flags.every(f => ['--check', '--dry-run'].includes(f)) && flags.length <= 1,
      'Usage: node tools/production/accounting.mjs data/accounting/PROJECT/sources.json [--check|--dry-run]');
    const config = JSON.parse(await fs.readFile(await safePath(process.cwd(), input), 'utf8'));
    console.log(JSON.stringify(await writeAccounting(process.cwd(), config, { check: flags.includes('--check'), dryRun: flags.includes('--dry-run') }), null, 2));
  } catch (error) { console.error(error.message.replaceAll(process.cwd(), '.')); process.exitCode = 1; }
}
