"""A NewsSource is anything implementing:
    async def list(category, q, limit) -> list[dict]
where Article = { id, title, url, source, category, publishedAt, description }

Sources are registered into a shared registry; list_all() aggregates,
dedupes (by url), and sorts them by recency. Direct port of the original
app's services/newsSource.js.
"""

import asyncio
from datetime import datetime

_sources: list = []


def register(source) -> None:
    if source is not None and hasattr(source, "list"):
        _sources.append(source)


def get_sources() -> list:
    return _sources


def clear_sources() -> None:
    _sources.clear()


def _published_at(article: dict) -> datetime:
    raw = article.get("publishedAt")
    if not raw:
        return datetime.min
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min


async def list_all(category: str | None = None, q: str | None = None, limit: int | None = None) -> list[dict]:
    results = await asyncio.gather(
        *(s.list(category=category, q=q, limit=limit) for s in _sources), return_exceptions=True
    )

    articles: list[dict] = []
    for r in results:
        if isinstance(r, list):
            articles.extend(r)

    seen: set[str] = set()
    deduped = []
    for a in articles:
        url = a.get("url") if a else None
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(a)

    deduped.sort(key=_published_at, reverse=True)

    if limit and limit > 0:
        return deduped[:limit]
    return deduped
