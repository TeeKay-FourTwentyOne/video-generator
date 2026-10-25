/** Backup membership and private receipt namespaces. Older sets cover the library. */
import { validateProjectId } from './project-identity.mjs';

export function backupScope(projectId) {
  return projectId === undefined ? { kind: 'library' } : { kind: 'project', projectId: validateProjectId(projectId) };
}

export function validateBackupScope(scope = backupScope()) {
  if (!scope || typeof scope !== 'object' || Array.isArray(scope)
      || !['library', 'project'].includes(scope.kind)
      || Object.keys(scope).some(k => !['kind', ...(scope.kind === 'project' ? ['projectId'] : [])].includes(k)))
    throw new Error('Invalid backup scope');
  if (scope.kind === 'project') validateProjectId(scope.projectId);
  return scope;
}

export function backupStatePath(name, scope = backupScope()) {
  validateBackupScope(scope);
  if (!['plan.json', 'last-sync.json', 'last-backup-set.json'].includes(name)) throw new Error('Invalid backup state filename');
  return `data/clips/cloud/${scope.kind === 'project' ? `projects/${scope.projectId}/` : ''}${name}`;
}
