import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const TUI_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
export const REPO_ROOT = process.env.NOMAD_LAKEHOUSE_ROOT ?? TUI_ROOT;
export const ENV_PATH = join(REPO_ROOT, '.env');

export type EnvMap = Record<string, string>;

export function parseEnv(content: string): EnvMap {
  const result: EnvMap = {};
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (line === '' || line.startsWith('#')) continue;

    const eqIndex = line.indexOf('=');
    if (eqIndex === -1) continue;

    const key = line.slice(0, eqIndex).trim();
    let value = line.slice(eqIndex + 1).trim();
    if (value.length >= 2 && value[0] === value[value.length - 1] && (value[0] === '"' || value[0] === "'")) {
      value = value.slice(1, -1);
    }
    if (key !== '') result[key] = value;
  }
  return result;
}

export function loadEnvFile(path: string = ENV_PATH): EnvMap {
  try {
    return parseEnv(readFileSync(path, 'utf8'));
  } catch {
    return {};
  }
}

export function serializeEnv(env: EnvMap): string {
  return (
    Object.entries(env)
      .map(([key, value]) => `${key}=${value}`)
      .join('\n') + '\n'
  );
}

export function writeEnvFile(content: string, path: string = ENV_PATH): void {
  writeFileSync(path, content, { encoding: 'utf8', mode: 0o600 });
}

export function mergeEnv(existing: EnvMap, updates: EnvMap): EnvMap {
  const merged: EnvMap = { ...existing };
  for (const [key, value] of Object.entries(updates)) {
    if (value !== '') merged[key] = value;
  }
  return merged;
}
