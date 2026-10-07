#!/usr/bin/env node
// Local-only publication guard. Findings never print the matched value.
import {execFileSync} from 'node:child_process';
import {readFileSync, readdirSync, existsSync} from 'node:fs';
import {resolve, join} from 'node:path';
import {pathToFileURL} from 'node:url';

const LIMIT = 2 * 1024 * 1024;
const ZERO = /^0+$/;
const publicEmail = email => /@(?:users\.)?noreply\.github\.com$/i.test(email);
const exampleEmail = email => /@(?:[\w-]+\.)*(?:example\.(?:com|org|net)|invalid|test)$/i.test(email);
const wellFormedEmail = email => /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i.test(email);
const placeholder = value => /^(?:<.*>|\$\{.*\}|YOUR[_-].*|REDACTED|EXAMPLE[_-].*|CHANGEME)$/i.test(value);

// Agent attribution addresses (vendor no-reply mailboxes) are accepted only on a
// well-formed `Co-Authored-By: Name <email>` line of a commit message, and only when
// the repository identity policy lists them. File contents never get this allowance,
// except the policy file itself, which may contain exactly the addresses it lists.
const trailerLine = (text, index, email) => {
  const start = text.lastIndexOf('\n', index - 1) + 1, end = text.indexOf('\n', index);
  const line = text.slice(start, end === -1 ? text.length : end);
  return new RegExp(`^\\s*co-authored-by:\\s*[^<>\\r\\n]{1,80}<${email.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}>\\s*$`, 'i').test(line);
};

export function scanText(text, {allowedTrailerEmails = [], allowedEmails = []} = {}) {
  const findings = [];
  const allowed = allowedTrailerEmails.map(e => e.toLowerCase());
  const anywhere = allowedEmails.map(e => e.toLowerCase());
  function check(rule, expression, accept = () => false) {
    for (const match of text.matchAll(expression)) {
      if (!accept(match[1] || match[0], match.index)) findings.push({rule, line: text.slice(0, match.index).split('\n').length});
    }
  }
  check('personal-email', /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi,
    (email, index) => publicEmail(email) || exampleEmail(email) || anywhere.includes(email.toLowerCase())
      || (allowed.includes(email.toLowerCase()) && trailerLine(text, index, email)));
  check('personal-home-path', /(?:\/(?:Users|home)\/|[A-Z]:[\\/]+Users[\\/]+)([^\\/\s"'`<>]+)/gi,
    name => /^(?:user|username|runner|node|app|example|\$USER|%USERNAME%)$/i.test(name));
  check('private-key', /-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----/g);
  check('provider-token', /\b(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{30,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{15,}|(?:AKIA|ASIA)[A-Z0-9]{16})\b/g);
  check('jwt-token', /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g);
  check('literal-credential', /\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|private[_-]?key|secret[_-]?key|auth[_-]?token)["']?\s*[:=]\s*["']([^\s"']{8,})["']/gi, placeholder);
  check('credential-in-url', /https?:\/\/[^\s/@:]+:[^\s/@]+@/gi);
  check('service-account', /["']type["']\s*:\s*["']service_account["']/g);
  check('ssn-like', /\b\d{3}-\d{2}-\d{4}\b/g);
  check('phone-like', /(?<![\w.])(?:\+1[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]\d{3}[ .-]\d{4}(?!\w)/g);
  check('international-phone-like', /(?<!\w)\+\d{1,3}(?:[ -]\d{2,4}){2,4}(?!\d)/g,
    value => { const digits = value.replace(/\D/g, ''); return digits.length < 10 || digits.length > 15; });
  check('street-address-like', /\b\d{1,6}\s+[A-Z][A-Za-z .'-]{2,50}\s(?:Street|St\.|Avenue|Ave\.|Road|Rd\.|Lane|Ln\.|Boulevard|Blvd\.|Drive|Dr\.)\b/g);
  check('private-network-address', /\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b/g);
  check('cloud-bucket-id', /gs:\/\/([a-z0-9][a-z0-9._-]{2,})/gi,
    value => /^(?:example(?:[-.].*)?|your-bucket|bucket-name)$/.test(value));
  return findings;
}

export function scanFile(path, bytes, options = {}) {
  const findings = [];
  if (/(?:^|\/)(?:data|generated-images|node_modules|__pycache__|\.venv[^/]*|venv|\.ssh|\.aws|\.gcloud)(?:\/|$)/i.test(path)
      || /(?:^|\/)(?:\.env(?:\..*)?|id_(?:rsa|ed25519)|.*(?:credentials|service-account).*\.json|config\.json|.*\.log|jobs\.json|data\.zip)$/i.test(path)
      || /\.claude\/(?:settings\.local\.json|plans\/)/.test(path)) findings.push({rule:'private-or-runtime-file', line:1});
  if (bytes.length > LIMIT) return [...findings, {rule:'oversized-file-requires-review', line:1}];
  if (bytes.includes(0) || /\.(?:mp4|mov|mkv|webm|wav|mp3|aac|png|jpe?g|webp|gif|zip|pth|bin)$/i.test(path))
    return [...findings, {rule:'binary-or-generated-asset-requires-review', line:1}];
  return [...findings, ...scanText(bytes.toString('utf8'), options)];
}

function git(args, cwd) {
  try { return execFileSync('git', args, {cwd, maxBuffer:16 * 1024 * 1024, stdio:['ignore','pipe','pipe']}); }
  catch { throw new Error(`Git inspection failed (${args[0]}); details withheld to avoid exposing sensitive values.`); }
}
const lines = bytes => bytes.toString().trim().split('\n').filter(Boolean);
const paths = bytes => bytes.toString().split('\0').filter(Boolean);

/** Repository identity policy: required author/committer identity (the account's public
 * mailbox, GitHub no-reply or not), optional agent attribution addresses allowed on
 * Co-Authored-By trailers, and optional published contact addresses the repository
 * deliberately exposes (a product contact link). Malformed policies fail closed. */
export function loadPolicy(root) {
  const policyPath = join(root,'.githooks','identity.json');
  if (!existsSync(policyPath)) return undefined;
  try {
    const policy = JSON.parse(readFileSync(policyPath,'utf8'));
    if (!policy || typeof policy.name !== 'string'
        || !policy.name.trim() || /[\r\n<>]/.test(policy.name)
        || typeof policy.email !== 'string' || !wellFormedEmail(policy.email)
        || exampleEmail(policy.email)) throw new Error();
    const trailers = policy.attributionTrailers ?? [];
    if (!Array.isArray(trailers) || trailers.some(e => typeof e !== 'string' || !wellFormedEmail(e)
        || publicEmail(e) || exampleEmail(e))) throw new Error();
    const contacts = policy.publishedContacts ?? [];
    if (!Array.isArray(contacts) || contacts.some(e => typeof e !== 'string' || !wellFormedEmail(e)
        || e.toLowerCase() === policy.email.toLowerCase() || trailers.includes(e))) throw new Error();
    return {...policy, attributionTrailers: trailers, publishedContacts: contacts};
  } catch { throw new Error('Invalid repository Git identity policy; details withheld.'); }
}

/** Reviewed assets: exact blob ids a human has inspected (content and embedded metadata) and
 * approved for publication, mapped to a short note. Only the binary and oversized review
 * prompts are released, and only for that exact content; new or changed media is flagged again. */
export function loadReviewedAssets(root) {
  const listPath = join(root,'.githooks','reviewed-assets.json');
  if (!existsSync(listPath)) return {};
  try {
    const reviewed = JSON.parse(readFileSync(listPath,'utf8'));
    if (!reviewed || typeof reviewed !== 'object' || Array.isArray(reviewed)
        || Object.entries(reviewed).some(([id, note]) => !/^[a-f0-9]{40,64}$/.test(id) || typeof note !== 'string')) throw new Error();
    return reviewed;
  } catch { throw new Error('Invalid reviewed-assets list; details withheld.'); }
}
const REVIEW_PROMPTS = new Set(['binary-or-generated-asset-requires-review','oversized-file-requires-review']);

export function audit({cwd = process.cwd(), mode = '--staged', base, input = '', remote = 'origin'}) {
  const root = git(['rev-parse','--show-toplevel'], cwd).toString().trim();
  const expectedIdentity = loadPolicy(root);
  const reviewed = loadReviewedAssets(root);
  const messageOptions = {allowedTrailerEmails: expectedIdentity?.attributionTrailers ?? []};
  // Published contact addresses may appear anywhere; the policy file alone may also contain
  // the identity mailbox and the listed attribution addresses as plain text.
  const published = expectedIdentity?.publishedContacts ?? [];
  const fileOptions = path => path === '.githooks/identity.json'
    ? {allowedEmails: [...published, ...messageOptions.allowedTrailerEmails, ...(expectedIdentity ? [expectedIdentity.email] : [])]}
    : {allowedEmails: published};
  const findings = [], seen = new Set();
  let fileCount = 0, commitCount = 0;
  const add = (scope, path, rows) => findings.push(...rows.map(row => ({scope, path, ...row})));
  function identity(scope, role, name, email) {
    const path = `[${role} metadata]`;
    if (!expectedIdentity) {
      // Without a policy, only public GitHub no-reply addresses are accepted.
      if (!publicEmail(email || '')) add(scope,path,[{rule:'non-noreply-commit-email',line:1}]);
    } else if (name !== expectedIdentity.name || email?.toLowerCase() !== expectedIdentity.email.toLowerCase())
      add(scope,path,[{rule:'unexpected-git-identity',line:1}]);
  }
  function file(ref, path, scope) {
    const object = git(['rev-parse', `${ref}:${path}`], root).toString().trim();
    const key = `${object}:${path}`;
    if (seen.has(key)) return;
    seen.add(key); fileCount++;
    const size = Number(git(['cat-file','-s',object], root));
    const bytes = size > LIMIT ? Buffer.alloc(LIMIT + 1) : git(['cat-file','blob',object], root);
    const rows = scanFile(path, bytes, fileOptions(path));
    add(scope, path, Object.hasOwn(reviewed, object) ? rows.filter(row => !REVIEW_PROMPTS.has(row.rule)) : rows);
  }
  function commits(ids) {
    for (const id of new Set(ids)) {
      commitCount++;
      for (const path of paths(git(['diff-tree','--root','-m','--no-commit-id','--name-only','-r','-z','--diff-filter=ACMRT',id], root))) file(id, path, id.slice(0,12));
      const [authorName, authorEmail, committerName, committerEmail] =
        git(['show','-s','--format=%an%x00%ae%x00%cn%x00%ce',id],root).toString().trimEnd().split('\0');
      identity(id.slice(0,12),'author',authorName,authorEmail);
      identity(id.slice(0,12),'committer',committerName,committerEmail);
      add(id.slice(0,12), '[commit message]', scanText(git(['show','-s','--format=%B',id], root).toString(), messageOptions));
    }
  }
  if (mode === '--staged') {
    for (const path of paths(git(['diff','--cached','--name-only','--diff-filter=ACMRT','-z'], root))) file('',path,'index');
    for (const role of ['AUTHOR','COMMITTER']) {
      const ident = git(['var',`GIT_${role}_IDENT`],root).toString().match(/^(.*) <([^<>]+)>/);
      identity('index',role.toLowerCase(),ident?.[1],ident?.[2]);
    }
  } else if (mode === '--worktree') {
    const files = new Set([...paths(git(['diff','HEAD','--name-only','--diff-filter=ACMRT','-z'],root)), ...paths(git(['ls-files','--others','--exclude-standard','-z'],root))]);
    for (const path of files) { fileCount++; add('worktree',path,scanFile(path,readFileSync(join(root,path)),fileOptions(path))); }
  } else if (mode === '--outgoing') {
    const resolvedBase = git(['rev-parse','--verify',base || '@{upstream}'],root).toString().trim();
    commits(lines(git(['rev-list',`${resolvedBase}..HEAD`],root)));
  } else if (mode === '--pre-push') {
    const ids = [];
    for (const line of input.trim().split('\n').filter(Boolean)) {
      const fields = line.split(/\s+/);
      if (fields.length !== 4 || !/^[a-f0-9]{40,64}$/.test(fields[1]) || !/^[a-f0-9]{40,64}$/.test(fields[3])) throw new Error('Malformed pre-push input; refusing to skip inspection.');
      const [,localSha,,remoteSha] = fields;
      if (ZERO.test(localSha)) continue; // Branch deletion sends no new blobs.
      const range = ZERO.test(remoteSha) ? [localSha,'--not',`--remotes=${remote}`] : [`${remoteSha}..${localSha}`];
      ids.push(...lines(git(['rev-list',...range],root)));
    }
    commits(ids);
  } else throw new Error('Expected --staged, --worktree, --outgoing [base], --pre-push [remote], or --install-hooks.');
  return {fileCount, commitCount, findings};
}

function installHooks() {
  const root = git(['rev-parse','--show-toplevel'],process.cwd()).toString().trim();
  const configured = git(['config','--get-regexp','^core\\.hookspath$|^core\\.repositoryformatversion$'],root).toString();
  const current = configured.split('\n').find(line => line.startsWith('core.hookspath '))?.slice(15);
  if (current && current !== '.githooks') throw new Error('Existing custom hooks detected; integrate the privacy hooks without replacing them.');
  if (!current) {
    const hooks = resolve(root,git(['rev-parse','--git-path','hooks'],root).toString().trim());
    if (existsSync(hooks) && readdirSync(hooks).some(name => !name.endsWith('.sample') && !name.startsWith('.'))) throw new Error('Existing hooks detected; integrate manually without replacing them.');
  }
  git(['config','--local','core.hooksPath','.githooks'],root);
  console.log('Repository-local privacy hooks enabled. Global Git settings unchanged.');
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    const mode = process.argv[2] || '--staged';
    if (mode === '--install-hooks') installHooks();
    else {
      const messageOptions = () => ({allowedTrailerEmails: loadPolicy(git(['rev-parse','--show-toplevel'],process.cwd()).toString().trim())?.attributionTrailers ?? []});
      const report = mode === '--commit-message'
        ? {fileCount:1,commitCount:0,findings:scanText(readFileSync(process.argv[3],'utf8'), messageOptions()).map(row=>({scope:'message',path:'[commit message]',...row}))}
        : audit({mode,base:process.argv[3],remote:process.argv[3],input:mode === '--pre-push' ? readFileSync(0,'utf8') : ''});
      for (const f of report.findings) console.error(`${f.scope} ${f.path}:${f.line}: ${f.rule} [value redacted]`);
      console.log(`Privacy check: ${report.fileCount} file snapshots, ${report.commitCount} outgoing commits, ${report.findings.length} findings.`);
      if (report.findings.length) process.exitCode = 1;
    }
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
