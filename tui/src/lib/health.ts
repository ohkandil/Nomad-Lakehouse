import { lookup } from 'node:dns/promises';
import { connect } from 'node:net';

import type { EnvMap } from './env.js';

export type StatusLevel = 'ok' | 'warn' | 'fail' | 'unknown';

export interface ServiceHealth {
  name: string;
  status: StatusLevel;
  endpoint: string;
  ips: string[];
  latencyMs: number | null;
  detail: string;
  hint?: string;
}

export function parseJdbcUri(uri: string): { host: string; port: number } | null {
  const match = /^jdbc:postgresql:\/\/([^:/]+):(\d+)\//.exec(uri);
  if (match === null) return null;
  return { host: match[1], port: Number.parseInt(match[2] ?? '', 10) };
}

export function rollupStatus(statuses: readonly StatusLevel[]): StatusLevel {
  if (statuses.includes('fail')) return 'fail';
  if (statuses.includes('warn')) return 'warn';
  if (statuses.includes('unknown')) return 'unknown';
  return 'ok';
}

async function resolveIps(host: string): Promise<string[]> {
  try {
    const result = await lookup(host, { all: true });
    return result.map((entry) => entry.address);
  } catch {
    return [];
  }
}

export async function tcpCheck(
  host: string,
  port: number,
  timeoutMs = 2000,
): Promise<{ reachable: boolean; latencyMs: number | null; error?: string }> {
  const startedAt = Date.now();
  return new Promise((resolvePromise) => {
    const socket = connect({ host, port });
    const finish = (reachable: boolean, error?: string) => {
      socket.destroy();
      resolvePromise({
        reachable,
        latencyMs: reachable ? Date.now() - startedAt : null,
        error,
      });
    };

    socket.setTimeout(timeoutMs);
    socket.once('connect', () => finish(true));
    socket.once('timeout', () => finish(false, `timed out after ${timeoutMs}ms`));
    socket.once('error', (err: Error) => finish(false, err.message));
  });
}

export async function httpCheck(
  url: string,
  timeoutMs = 2000,
): Promise<{ ok: boolean; statusCode: number | null; latencyMs: number | null; error?: string }> {
  const startedAt = Date.now();
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
    return {
      ok: response.ok,
      statusCode: response.status,
      latencyMs: Date.now() - startedAt,
    };
  } catch (err) {
    return {
      ok: false,
      statusCode: null,
      latencyMs: null,
      error: err instanceof Error ? err.message : String(err),
    };
  }
}

function endpoint(host: string, port: number | string): string {
  return `${host}:${port}`;
}

export async function checkMinioApi(env: EnvMap): Promise<ServiceHealth> {
  const port = env.MINIO_API_PORT ?? '9000';
  const url = `http://localhost:${port}/minio/health/live`;
  const result = await httpCheck(url);
  const ips = await resolveIps('localhost');

  if (result.ok) {
    return {
      name: 'MinIO API',
      status: 'ok',
      endpoint: url,
      ips,
      latencyMs: result.latencyMs,
      detail: `Healthy (HTTP ${result.statusCode})`,
    };
  }
  if (result.statusCode !== null) {
    return {
      name: 'MinIO API',
      status: 'warn',
      endpoint: url,
      ips,
      latencyMs: result.latencyMs,
      detail: `Responded with HTTP ${result.statusCode}`,
      hint: 'Validate the minio container with docker compose ps',
    };
  }
  return {
    name: 'MinIO API',
    status: 'fail',
    endpoint: url,
    ips,
    latencyMs: null,
    detail: `Not reachable: ${result.error ?? 'unknown error'}`,
    hint: 'Run scripts/setup_minio.sh and retry',
  };
}

async function checkTcpService(
  name: string,
  env: EnvMap,
  rawHost: string,
  rawPort: string,
  fallbackPort: number,
  hintFail: string,
  hintUnknown: string,
): Promise<ServiceHealth> {
  const port = Number.parseInt(rawPort, 10) || fallbackPort;
  const candidates = rawHost === 'postgres' ? ['localhost', rawHost] : [rawHost];
  const lastError = { message: 'unknown error', host: rawHost };

  for (const candidate of candidates) {
    const result = await tcpCheck(candidate, port);
    if (result.reachable) {
      return {
        name,
        status: 'ok',
        endpoint: endpoint(candidate, port),
        ips: await resolveIps(candidate),
        latencyMs: result.latencyMs,
        detail: 'TCP reachable',
      };
    }
    lastError.message = result.error ?? lastError.message;
    lastError.host = candidate;
  }

  if (rawHost === '') {
    return {
      name,
      status: 'unknown',
      endpoint: '-',
      ips: [],
      latencyMs: null,
      detail: 'No host configured',
      hint: hintUnknown,
    };
  }

  return {
    name,
    status: 'fail',
    endpoint: endpoint(rawHost, port),
    ips: await resolveIps(rawHost),
    latencyMs: null,
    detail: `Unable to reach ${lastError.host}: ${lastError.message}`,
    hint: hintFail,
  };
}

export async function checkMinioConsole(env: EnvMap): Promise<ServiceHealth> {
  return checkTcpService(
    'MinIO Console',
    env,
    'localhost',
    env.MINIO_CONSOLE_PORT ?? '',
    9001,
    'Ensure the minio container is running (docker compose ps)',
    'Set MINIO_CONSOLE_PORT in .env',
  );
}

export async function checkPostgresCatalog(env: EnvMap): Promise<ServiceHealth> {
  const jdbc = parseJdbcUri(env.CATALOG_JDBC_URI ?? '');
  if (jdbc === null) {
    return checkTcpService(
      'PostgreSQL Catalog',
      env,
      env.POSTGRES_PORT !== undefined ? 'localhost' : '',
      env.POSTGRES_PORT ?? '',
      5432,
      'Ensure docker engine is running and postgres service is healthy',
      'Set CATALOG_JDBC_URI or POSTGRES_PORT in .env',
    );
  }
  return checkTcpService(
    'PostgreSQL Catalog',
    env,
    jdbc.host,
    String(jdbc.port),
    5432,
    'Ensure docker engine is running and postgres service is healthy',
    'Set CATALOG_JDBC_URI or POSTGRES_PORT in .env',
  );
}

export async function checkDashboardUpstream(env: EnvMap): Promise<ServiceHealth> {
  const upstream = env.DASHBOARD_UPSTREAM ?? '';
  const match = /^(?:(\d{1,3}(?:\.\d{1,3}){3})|([\w.-]+)):(\d+)$/.exec(upstream);
  if (match === null) {
    return {
      name: 'Admin Dashboard',
      status: 'unknown',
      endpoint: upstream === '' ? '-' : upstream,
      ips: [],
      latencyMs: null,
      detail: 'DASHBOARD_UPSTREAM is not configured or invalid',
      hint: 'Set DASHBOARD_UPSTREAM in .env (e.g. 127.0.0.1:8088)',
    };
  }
  const host = match[1] ?? match[2] ?? upstream.split(':')[0];
  const port = Number.parseInt(match[3] ?? '8088', 10);
  return checkTcpService(
    'Admin Dashboard',
    env,
    host,
    String(port),
    8088,
    'Start the dashboard: python3 -m uvicorn dashboard.app:app --host 127.0.0.1 --port 8088',
    'Set DASHBOARD_UPSTREAM in .env',
  );
}

export async function collectServiceHealth(env: EnvMap): Promise<{
  overall: StatusLevel;
  services: ServiceHealth[];
  collectedAt: Date;
}> {
  const services = await Promise.all([
    checkMinioApi(env),
    checkMinioConsole(env),
    checkPostgresCatalog(env),
    checkDashboardUpstream(env),
  ]);
  return {
    overall: rollupStatus(services.map((service) => service.status)),
    services,
    collectedAt: new Date(),
  };
}
