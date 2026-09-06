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

from app.services import image_cache

# Built-in feed list. Each entry maps a feed to a category + source name.
# Reuters/AP both discontinued public RSS access (401 / homepage-not-a-feed,
# confirmed by hand) — replaced with The Guardian and CNN's World feeds,
# which are live and, unlike the old two, actually carry article images.
FEEDS = [
    {"name": "BBC News", "category": "World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "The Guardian", "category": "World", "url": "https://www.theguardian.com/world/rss"},
    {"name": "CNN", "category": "World", "url": "http://rss.cnn.com/rss/cnn_world.rss"},
    {"name": "Yahoo News", "category": "World", "url": "https://news.yahoo.com/rss/topstories"},
    {"name": "NPR", "category": "US", "url": "https://feeds.npr.org/1001/rss.xml"},
    {"name": "TechCrunch", "category": "Tech", "url": "https://techcrunch.com/feed/"},
    {"name": "The Verge", "category": "Tech", "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "Ars Technica", "category": "Tech", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "Hacker News", "category": "Tech", "url": "https://hnrss.org/frontpage"},
    {"name": "BBC Business", "category": "Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml"},
    {"name": "BBC Science", "category": "Science", "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"},
    # Local: Portland, OR. KGW's feed times out consistently and KATU's
    # is a genuinely empty "Untitled RSS Feed" — both dropped after
    # verifying by hand; these three are live with real entries.
    {"name": "OregonLive", "category": "Local", "url": "https://www.oregonlive.com/arc/outboundfeeds/rss/"},
    {"name": "KOIN", "category": "Local", "url": "https://www.koin.com/feed/"},
    {"name": "Oregon Capital Chronicle", "category": "Local", "url": "https://oregoncapitalchronicle.com/feed/"},
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


_IMG_TAG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']')

# BBC's media_thumbnail is a tiny 240x136 RSS-reader-sized image, but the
# width is just a path segment on ichef.bbci.co.uk's image resizer — asking
# for a bigger one (confirmed working up to at least 999px) is a plain URL
# rewrite. Other CDNs seen here don't offer this: the Guardian's thumbnail
# URL is cryptographically signed to its exact 140px width (any other width
# gets a 401), and CNN's are already full-size.
_BBC_ICHEF_RE = re.compile(r"(ichef\.bbci\.co\.uk/ace/standard/)\d+(/)")


def _upsize(url: str) -> str:
    return _BBC_ICHEF_RE.sub(r"\g<1>999\g<2>", url)


def _image_url(entry: dict) -> str | None:
    """Best-effort thumbnail. Not every feed has one (see FEEDS' comment on
    which sources do): media RSS fields first, then a standard RSS
    <enclosure> image link (KOIN uses this — feedparser surfaces it as a
    `links` entry with rel="enclosure"), then the first <img> in whatever
    HTML the entry carries.
    """
    thumb = entry.get("media_thumbnail")
    if thumb:
        return _upsize(thumb[0].get("url"))
    media = entry.get("media_content")
    if media:
        return _upsize(media[0].get("url"))
    for link in entry.get("links") or []:
        if link.get("rel") == "enclosure" and str(link.get("type", "")).startswith("image/"):
            return _upsize(link.get("href"))
    for html in (entry.get("summary"), *(c.get("value", "") for c in entry.get("content") or [])):
        if html:
            match = _IMG_TAG_RE.search(html)
            if match:
                return _upsize(match.group(1))
    return None


def _parse_entries(raw_bytes: bytes, feed: dict) -> list[dict]:
    parsed = feedparser.parse(raw_bytes)
    articles = []
    for entry in parsed.entries:
        # CNN's feed (at least) injects affiliate/sponsored placements
        # (lendingtree.com, fool.com credit-card landing pages, no real
        # publish date) with no `published`/`published_parsed` at all —
        # a real article always has one. Skip rather than fall back to
        # "now", which would make stale ad content look like the newest
        # story in the feed and bury everything real underneath it.
        if not entry.get("published") and not entry.get("published_parsed"):
            continue
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
                "imageUrl": _image_url(entry),
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
        """Holds the last-fetched articles in memory; `.list()` only ever
        filters/slices that snapshot — all the actual feed I/O happens in
        `refresh()`, called on startup and then periodically by
        app/services/feed_refresh.py. This is what makes GET /api/news
        instant instead of paying RSS-fetch latency on every request.
        """

        name = "rss"

        def __init__(self) -> None:
            self._articles: list[dict] = []
            self._warm_task: asyncio.Task | None = None

        async def refresh(self) -> None:
            async with httpx.AsyncClient(headers={"User-Agent": "news.folding-os.com/1.0"}) as client:
                results = await asyncio.gather(
                    *(_fetch_feed(client, f) for f in the_feeds), return_exceptions=True
                )

            articles: list[dict] = []
            for r in results:
                if isinstance(r, list):
                    articles.extend(r)
            self._articles = articles

            # Fire-and-forget: image fetches are slower and flakier than the
            # feeds themselves (a single hanging CDN would otherwise stall
            # feed refresh, and startup, on it). Articles publish immediately
            # with their original CDN image URLs and each one flips to the
            # proxied/cached path in place as it warms — held on self so the
            # task isn't garbage-collected mid-flight.
            self._warm_task = asyncio.create_task(image_cache.warm_all(articles))

        async def list(self, category: str | None = None, q: str | None = None, limit: int | None = None) -> list[dict]:
            # No `limit` slicing here: self._articles is in FEEDS-declaration
            # order (each feed's own entries, concatenated), not sorted by
            # recency — news_source.list_all() does the real global sort
            # across every source before slicing to `limit`. Truncating here
            # first, before that sort, was silently dropping any feed listed
            # late in FEEDS (e.g. Yahoo News) whenever earlier feeds alone
            # already filled the requested limit for a category.
            articles = self._articles
            if category:
                articles = [a for a in articles if a["category"] == category]
            if q:
                needle = q.lower()
                articles = [
                    a for a in articles if needle in a["title"].lower() or needle in a["description"].lower()
                ]
            return articles

    return RssSource()
