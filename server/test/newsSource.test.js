const {
  register,
  clearSources,
  listAll,
} = require('../src/services/newsSource');

describe('newsSource registry', () => {
  afterEach(() => clearSources());

  test('dedupes by url and sorts by recency', async () => {
    register({
      name: 'a',
      list: async () => [
        { id: '1', title: 'Old', url: 'http://x/1', source: 'a', category: 'World', publishedAt: '2024-01-01T00:00:00Z', description: '' },
        { id: '2', title: 'New', url: 'http://x/2', source: 'a', category: 'World', publishedAt: '2024-06-01T00:00:00Z', description: '' },
      ],
    });
    register({
      name: 'b',
      list: async () => [
        { id: '3', title: 'Dup', url: 'http://x/2', source: 'b', category: 'World', publishedAt: '2024-05-01T00:00:00Z', description: '' },
      ],
    });

    const articles = await listAll({});
    expect(articles).toHaveLength(2);
    expect(articles[0].id).toBe('2'); // newest first
    expect(articles.some((a) => a.id === '3')).toBe(false); // dup removed
  });

  test('respects limit', async () => {
    register({
      name: 'a',
      list: async () => [
        { id: '1', title: 'A', url: 'http://x/1', source: 'a', category: 'World', publishedAt: '2024-01-01T00:00:00Z', description: '' },
        { id: '2', title: 'B', url: 'http://x/2', source: 'a', category: 'World', publishedAt: '2024-01-02T00:00:00Z', description: '' },
        { id: '3', title: 'C', url: 'http://x/3', source: 'a', category: 'World', publishedAt: '2024-01-03T00:00:00Z', description: '' },
      ],
    });
    const articles = await listAll({ limit: 2 });
    expect(articles).toHaveLength(2);
  });

  test('isolates a failing source', async () => {
    register({
      name: 'bad',
      list: async () => {
        throw new Error('boom');
      },
    });
    register({
      name: 'good',
      list: async () => [
        { id: '1', title: 'A', url: 'http://x/1', source: 'good', category: 'World', publishedAt: '2024-01-01T00:00:00Z', description: '' },
      ],
    });
    const articles = await listAll({});
    expect(articles).toHaveLength(1);
    expect(articles[0].source).toBe('good');
  });
});
