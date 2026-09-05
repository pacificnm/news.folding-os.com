"""RSS-based NewsSource. Direct port of the original app's
services/rssSource.js, using `feedparser` in place of the `rss-parser` npm
package.

Field mapping (feedparser's normalized entry -> our Article shape):
  url         entry.link, falling back to entry.get("id") (feedparser
              normalizes both <link> and <guid> onto these)
  description entry.get("summary") (feedparser normalizes <description>/
              <summary> here), falling back to the first <content:encoded>
              block, falling back to the title
  publishedAt entry.get("published_parsed") (a time.struct_time), falling
              back to the raw entry.get("published") string, falling back
              to now
"""

import asyncio
import re
from datetime import UTC, datetime
from time import struct_time

import feedparser
import httpx

# Built-in feed list. Each entry maps a feed to a category + source name.
FEEDS = [
    {"name": "BBC News", "category": "World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "Reuters", "category": "World", "url": "https://www.reutersagency.com/feed/?best-topics=world"},
    {"name": "AP News", "category": "World", "url": "https://apnews.com/hub/world-news.rss"},
    {"name": "NPR", "category": "US", "url": "https://feeds.npr.org/1001/rss.xml"},
    {"name": "TechCrunch", "category": "Tech", "url": "https://techcrunch.com/feed/"},
    {"name": "The Verge", "category": "Tech", "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "Ars Technica", "category": "Tech", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "Hacker News", "category": "Tech", "url": "https://hnrss.org/frontpage"},
    {"name": "BBC Business", "category": "Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml"},
    {"name": "BBC Science", "category": "Science", "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"},
]

_TAG_RE = re.compile(r"<[^>]*>")
_WS_RE = re.compile(r"\s+")


def strip_html(html: str | None) -> str:
    if not html:
        return ""
    text = _TAG_RE.sub(" ", str(html))
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    return _WS_RE.sub(" ", text).strip()


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(s: str) -> str:
    slug = _SLUG_RE.sub("-", s.lower()).strip("-")
    return slug[:80]


def _published_at(entry: dict) -> str:
    parsed: struct_time | None = entry.get("published_parsed")
    if parsed:
        return datetime(*parsed[:6], tzinfo=UTC).isoformat()
    raw = entry.get("published")
    if raw:
        return raw
    return datetime.now(UTC).isoformat()


def _description(entry: dict) -> str:
    summary = entry.get("summary")
    if summary:
        return summary
    content = entry.get("content")
    if content:
        return content[0].get("value", "")
    return entry.get("title", "")


def _parse_entries(raw_bytes: bytes, feed: dict) -> list[dict]:
    parsed = feedparser.parse(raw_bytes)
    articles = []
    for entry in parsed.entries:
        url = entry.get("link") or entry.get("id") or ""
        description = strip_html(_description(entry))
        articles.append(
            {
                "id": f"{feed['name']}:{slugify(url)}",
                "title": strip_html(entry.get("title", "")),
                "url": url,
                "source": feed["name"],
                "category": feed["category"],
                "publishedAt": _published_at(entry),
                "description": description[:500],
            }
        )
    return articles


async def _fetch_feed(client: httpx.AsyncClient, feed: dict) -> list[dict]:
    resp = await client.get(feed["url"], timeout=15.0)
    resp.raise_for_status()
    return await asyncio.to_thread(_parse_entries, resp.content, feed)


def create_rss_source(feeds: list[dict] | None = None):
    the_feeds = feeds if feeds is not None else FEEDS

    class RssSource:
        name = "rss"

        async def list(self, category: str | None = None, q: str | None = None, limit: int | None = None) -> list[dict]:
            wanted = [f for f in the_feeds if not category or f["category"] == category]

            async with httpx.AsyncClient(headers={"User-Agent": "news.folding-os.com/1.0"}) as client:
                results = await asyncio.gather(*(_fetch_feed(client, f) for f in wanted), return_exceptions=True)

            articles: list[dict] = []
            for r in results:
                if isinstance(r, list):
                    articles.extend(r)

            if q:
                needle = q.lower()
                articles = [
                    a for a in articles if needle in a["title"].lower() or needle in a["description"].lower()
                ]

            return articles[: limit or 100]

    return RssSource()
