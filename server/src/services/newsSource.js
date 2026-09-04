// A NewsSource is any object implementing:
//   list({ category, q, limit }) -> Promise<Article[]>
// where Article = { id, title, url, source, category, publishedAt, description }
//
// Sources are registered into a shared registry; listAll() aggregates,
// dedupes (by url), and sorts them by recency.

const sources = [];

function register(source) {
  if (source && typeof source.list === 'function') {
    sources.push(source);
  }
}

function getSources() {
  return sources;
}

function clearSources() {
  sources.length = 0;
}

async function listAll({ category, q, limit } = {}) {
  const results = await Promise.allSettled(
    sources.map((s) => s.list({ category, q, limit }))
  );

  const articles = [];
  for (const r of results) {
    if (r.status === 'fulfilled' && Array.isArray(r.value)) {
      articles.push(...r.value);
    }
  }

  // Dedupe by url, keep first occurrence.
  const seen = new Set();
  const deduped = articles.filter((a) => {
    if (!a || !a.url || seen.has(a.url)) return false;
    seen.add(a.url);
    return true;
  });

  deduped.sort((a, b) => new Date(b.publishedAt || 0) - new Date(a.publishedAt || 0));

  if (limit && limit > 0) return deduped.slice(0, limit);
  return deduped;
}

module.exports = { register, getSources, clearSources, listAll };
