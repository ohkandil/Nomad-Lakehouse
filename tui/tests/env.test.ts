import { describe, expect, it } from 'vitest';

import { mergeEnv, parseEnv, serializeEnv } from '../src/lib/env.js';

describe('parseEnv', () => {
  it('parses key/value pairs and strips quotes', () => {
    const content = 'A=1\nB="two words"\nC=\'single\'\n';
    expect(parseEnv(content)).toEqual({ A: '1', B: 'two words', C: 'single' });
  });

  it('skips comments, blank lines, and lines without =', () => {
    expect(parseEnv('# comment\n\nA=1\nNOVALUE\n')).toEqual({ A: '1' });
  });

  it('preserves values containing = signs', () => {
    expect(parseEnv('URI=jdbc:postgresql://h:5432/db?ssl=true')['URI']).toBe(
      'jdbc:postgresql://h:5432/db?ssl=true',
    );
  });
});

describe('mergeEnv', () => {
  it('overrides existing keys and preserves others', () => {
    expect(mergeEnv({ A: '1', B: '2' }, { B: '3' })).toEqual({ A: '1', B: '3' });
  });

  it('ignores empty-string updates so unset wizard fields do not wipe .env', () => {
    expect(mergeEnv({ A: '1' }, { A: '' })).toEqual({ A: '1' });
  });
});

describe('serializeEnv', () => {
  it('round-trips through parseEnv', () => {
    const env = { A: '1', B: 'x y' };
    expect(parseEnv(serializeEnv(env))).toEqual(env);
  });
});
