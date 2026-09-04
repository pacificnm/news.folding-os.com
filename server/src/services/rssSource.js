const Parser = require('rss-parser');

// Built-in feed list. Each entry maps a feed to a category + source name.
const FEEDS = [
  { name: 'BBC News', category: 'World', url: 'https://feeds.bbci.co.uk/news/world/rss.xml' },
  { name: 'Reuters', category: 'World', url: 'https://www.reutersagency.com/feed/?best-topics=world' },
  { name: 'AP News', category: 'World', url: 'https://apnews.com/hub/world-news.rss' },
  { name: 'NPR', category: 'US', url: 'https://feeds.npr.org/1001/rss.xml' },
  { name: 'TechCrunch', category: 'Tech', url: 'https://techcrunch.com/feed/' },
  { name: 'The Verge', category: 'Tech', url: 'https://www.theverge.com/rss/index.xml' },
  { name: 'Ars Technica', category: 'Tech', url: 'https://feeds.arstechnica.com/arstechnica/index' },
  { name: 'Hacker News', category: 'Tech', url: 'https://hnrss.org/frontpage' },
  { name: 'BBC Business', category: 'Business', url: 'https://feeds.bbci.co.uk/news/business/rss.xml' },
  { name: 'BBC Science', category: 'Science', url: 'https://feeds.bbci.co.uk/news/science_and_environment/rss.xml' },
];

function stripHtml(html) {
  if (!html) return '';
  return String(html)
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

function slugify(str) {
  return String(str)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);
}

/**
 * RSS-based news source.
 * @param {{ feeds?: Array<{name:string,category:string,url:string}> }} options
 */
function createRssSource({ feeds = FEEDS } = {}) {
  const parser = new Parser({ timeout: 15000 });

  async function fetchFeed(feed) {
    const parsed = await parser.parseURL(feed.url);
    return (parsed.items || []).map((item) => {
      const url = item.link || item.guid || '';
      const description = stripHtml(item.contentSnippet || item.content || item.title || '');
      return {
        id: `${feed.name}:${slugify(url)}`,
        title: stripHtml(item.title || ''),
        url,
        source: feed.name,
        category: feed.category,
        publishedAt: item.isoDate || item.pubDate || new Date().toISOString(),
        description: description.slice(0, 500),
      };
    });
  }

  return {
    name: 'rss',
    async list({ category, q, limit } = {}) {
      const wanted = feeds.filter((f) => !category || f.category === category);
      const results = await Promise.allSettled(wanted.map((f) => fetchFeed(f)));

      const articles = [];
      for (const r of results) {
        if (r.status === 'fulfilled' && Array.isArray(r.value)) {
          articles.push(...r.value);
        }
      }

      if (q) {
        const needle = q.toLowerCase();
        const filtered = articles.filter(
          (a) =>
            a.title.toLowerCase().includes(needle) ||
            a.description.toLowerCase().includes(needle)
        );
        return filtered.slice(0, limit || 100);
      }

      return articles.slice(0, limit || 100);
    },
  };
}

module.exports = { createRssSource, FEEDS, stripHtml, slugify };
