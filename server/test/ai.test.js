const { notConfigured, truncate } = require('../src/services/ai');

describe('ai helpers', () => {
  test('notConfigured returns a stable error shape', () => {
    const r = notConfigured();
    expect(r.error).toBe('AI_NOT_CONFIGURED');
    expect(typeof r.message).toBe('string');
  });

  test('truncate caps length', () => {
    const long = 'a'.repeat(5000);
    const out = truncate(long, 100);
    expect(out.length).toBeLessThanOrEqual(101);
    expect(out.endsWith('…')).toBe(true);
  });

  test('truncate leaves short strings intact', () => {
    expect(truncate('short', 100)).toBe('short');
  });
});
