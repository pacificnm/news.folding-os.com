const { stripHtml, slugify } = require('../src/services/rssSource');

describe('rssSource helpers', () => {
  test('stripHtml removes tags and decodes entities', () => {
    expect(stripHtml('<p>Hello&nbsp;world</p> &amp; more')).toBe('Hello world & more');
    expect(stripHtml('')).toBe('');
    expect(stripHtml(null)).toBe('');
  });

  test('slugify normalizes a url', () => {
    expect(slugify('Hello, World! 2024')).toBe('hello-world-2024');
    expect(slugify('---a---b---')).toBe('a-b');
  });
});
