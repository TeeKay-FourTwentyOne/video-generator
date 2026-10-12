import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { scanText, loadPolicy } from '../privacy-check.mjs';

export const schema = JSON.parse(await fs.readFile(new URL('../../docs/schemas/production-record.schema.json', import.meta.url), 'utf8'));
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

export function portablePath(value) {
  return typeof value === 'string' && value.length > 0 && value.split('/').every(part =>
    /^[A-Za-z0-9._-]+$/.test(part) && part !== '.' && part !== '..' && !part.endsWith('.'));
}

export async function safePath(root, relative) {
  if (!portablePath(relative)) throw new Error('Expected a portable relative path without traversal');
  const base = await fs.realpath(root);
  let current = base;
  const parts = relative.split('/');
  for (let i = 0; i < parts.length; i++) {
    current = path.join(current, parts[i]);
    const stat = await fs.lstat(current).catch(error => { if (error.code !== 'ENOENT') throw error; });
    if (stat && (stat.isSymbolicLink() || (i < parts.length - 1 ? !stat.isDirectory() : !stat.isFile() && !stat.isDirectory()))) {
      throw new Error(`Unsafe link or special path: ${relative}`);
    }
  }
  return current;
}

function formatValid(value, format) {
  if (format === 'portable-path') return portablePath(value);
  if (format === 'date') return /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
  if (format === 'public-url') {
    try {
      const u = new URL(value);
      const host = u.hostname.replace(/^www\./, '');
      const query = !u.search || host === 'youtube.com' && u.pathname === '/watch' &&
        [...u.searchParams.keys()].length === 1 && /^[A-Za-z0-9_-]+$/.test(u.searchParams.get('v') ?? '');
      return u.protocol === 'https:' && !u.username && !u.password && query && !u.hash &&
        ['youtube.com', 'youtu.be', 'vimeo.com'].includes(host);
    } catch { return false; }
  }
  throw new Error(`Unsupported schema format: ${format}`);
}

// Only the keywords used by the checked-in schema are implemented. Fail closed
// if that schema gains a constraint this dependency-free validator cannot enforce.
const keywords = new Set(['$schema', 'title', '$defs', '$ref', 'type', 'const', 'enum', 'properties',
  'additionalProperties', 'required', 'items', 'uniqueItems', 'minLength', 'maxLength', 'pattern',
  'format', 'minimum', 'exclusiveMinimum']);
export function validateShape(value, node = schema, location = 'record') {
  for (const key of Object.keys(node)) if (!keywords.has(key)) throw new Error(`Unsupported schema keyword: ${key}`);
  if (node.$ref) {
    if (!node.$ref.startsWith('#/$defs/') || !schema.$defs[node.$ref.slice(8)]) throw new Error('Unsupported schema reference');
    return validateShape(value, schema.$defs[node.$ref.slice(8)], location);
  }
  const fail = rule => { throw new Error(`${location}: ${rule}`); };
  if (Object.hasOwn(node, 'const') && value !== node.const) fail('unexpected constant');
  if (node.enum && !node.enum.includes(value)) fail('unsupported value');
  if (node.type) {
    const valid = node.type === 'object' ? value !== null && typeof value === 'object' && !Array.isArray(value)
      : node.type === 'array' ? Array.isArray(value)
      : node.type === 'integer' ? Number.isSafeInteger(value)
      : node.type === 'number' ? typeof value === 'number' && Number.isFinite(value)
      : typeof value === node.type;
    if (!valid) fail(`expected ${node.type}`);
  }
  if (node.type === 'object') {
    for (const key of node.required ?? []) if (!Object.hasOwn(value, key)) fail(`missing ${key}`);
    for (const key of Object.keys(value)) if (!Object.hasOwn(node.properties, key)) fail('unknown field (value withheld)');
    for (const [key, child] of Object.entries(node.properties)) if (Object.hasOwn(value, key)) validateShape(value[key], child, `${location}.${key}`);
  }
  if (node.type === 'array') {
    value.forEach((item, i) => validateShape(item, node.items, `${location}[${i}]`));
    if (node.uniqueItems && new Set(value.map(v => JSON.stringify(v))).size !== value.length) fail('duplicate items');
  }
  if (typeof value === 'string') {
    if (node.minLength && value.trim().length < node.minLength) fail('empty text');
    if (node.maxLength && value.length > node.maxLength) fail('text too long');
    if (node.pattern && !new RegExp(node.pattern).test(value)) fail('invalid format');
    if (node.format && !formatValid(value, node.format)) fail(`invalid ${node.format}`);
  }
  if (node.minimum !== undefined && value < node.minimum) fail('below minimum');
  if (node.exclusiveMinimum !== undefined && value <= node.exclusiveMinimum) fail('below exclusive minimum');
}

// Positive projection from the schema's allowlist; never serialize a workspace
// manifest and attempt to redact a blacklist of runtime fields afterward.
export function publicProjection(value, node = schema) {
  if (node.$ref) return publicProjection(value, schema.$defs[node.$ref.slice(8)]);
  if (node.type === 'object') return Object.fromEntries(Object.entries(node.properties)
    .filter(([key]) => Object.hasOwn(value, key)).map(([key, child]) => [key, publicProjection(value[key], child)]));
  if (node.type === 'array') return value.map(v => publicProjection(v, node.items));
  return value;
}

export function checkPublicText(text, label, repo) {
  const findings = scanText(text, { allowedEmails: loadPolicy(repo)?.publishedContacts ?? [] });
  if (findings.length) throw new Error(`${label}:${findings[0].line}: ${findings[0].rule} (value withheld)`);
  // A backstop for public prose, not a complete semantic financial/PII audit.
  if (/(?:[$€£]\s*\d|\b(?:USD|EUR|GBP)\s*\d|\d(?:[\d,.]*\d)?\s*(?:USD|EUR|GBP|dollars?|cents?)\b)/i.test(text)) {
    throw new Error(`${label}: financial details belong in ignored data (value withheld)`);
  }
}
