"""In-memory cache of article thumbnail bytes, warmed by RssSource.refresh()
so a visitor's request never waits on an external image CDN.

Keyed by article id, not URL: GET /api/news/{id}/image only ever serves
bytes THIS process already fetched during a refresh cycle — it never fetches
a caller-supplied URL on request, which would make it an open SSRF proxy.
"""

import asyncio
from urllib.parse import quote

import httpx

FETCH_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
MAX_CONCURRENT_FETCHES = 8
MAX_BYTES = 5 * 1024 * 1024  # a runaway/hostile response shouldn't grow this unbounded

_store: dict[str, tuple[bytes, str]] = {}


async def _fetch(client: httpx.AsyncClient, url: str) -> tuple[bytes, str] | None:
    try:
        resp = await client.get(url, timeout=FETCH_TIMEOUT)
        resp.raise_for_status()
    except httpx.HTTPError:
        return None
    content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
    if not content_type.startswith("image/") or len(resp.content) > MAX_BYTES:
        return None
    return resp.content, content_type


async def warm_all(articles: list[dict]) -> None:
    """Fetches each article's imageUrl and rewrites it in place to the
    proxied `/api/news/{id}/image` path (clearing it on failure). Runs as a
    background task after the article list is already published (see
    RssSource.refresh()) — a dict's `imageUrl` key always exists, so this
    only ever changes a value in place, never a concurrent request's view of
    the list's structure. Until an article's image warms, its original CDN
    URL is what's served — a perfectly fine fallback, not a broken state.
    """
    sem = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)

    async def one(article: dict, client: httpx.AsyncClient) -> None:
        url = article.get("imageUrl")
        if not url:
            return
        async with sem:
            fetched = await _fetch(client, url)
        if fetched:
            _store[article["id"]] = fetched
            article["imageUrl"] = f"/api/news/{quote(article['id'], safe='')}/image"
        else:
            article["imageUrl"] = None

    async with httpx.AsyncClient(headers={"User-Agent": "news.folding-os.com/1.0"}) as client:
        await asyncio.gather(*(one(a, client) for a in articles), return_exceptions=True)

    current_ids = {a["id"] for a in articles}
    for stale_id in [k for k in _store if k not in current_ids]:
        del _store[stale_id]


def get(article_id: str) -> tuple[bytes, str] | None:
    return _store.get(article_id)
