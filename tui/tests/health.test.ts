import { describe, expect, it } from 'vitest';

import { parseJdbcUri, rollupStatus } from '../src/lib/health.js';

describe('parseJdbcUri', () => {
  it('parses host and port from a jdbc uri', () => {
    expect(parseJdbcUri('jdbc:postgresql://postgres:5432/iceberg')).toEqual({
      host: 'postgres',
      port: 5432,
    });
  });

  it('returns null for missing or malformed uris', () => {
    expect(parseJdbcUri('')).toBeNull();
    expect(parseJdbcUri('jdbc:postgresql://localhost/iceberg')).toBeNull();
    expect(parseJdbcUri('postgresql://postgres:5432/iceberg')).toBeNull();
  });
});

describe('rollupStatus', () => {
  it('fail wins over everything', () => {
    expect(rollupStatus(['ok', 'warn', 'fail'])).toBe('fail');
  });

  it('warn beats unknown and ok', () => {
    expect(rollupStatus(['ok', 'unknown', 'warn'])).toBe('warn');
  });

  it('unknown beats ok', () => {
    expect(rollupStatus(['ok', 'unknown'])).toBe('unknown');
  });

  it('all ok rolls up to ok', () => {
    expect(rollupStatus(['ok', 'ok'])).toBe('ok');
  });
});
