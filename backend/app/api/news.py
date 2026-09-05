import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.common import find_article, not_found, single_sse_event, sse
from app.clients.ollama import OllamaUnavailableError
from app.db.session import get_db
from app.models import AiResultKind
from app.services import ai, feed_cache
from app.services.ai_cache import get_ai_result, set_ai_result
from app.services.news_source import list_all
from app.services.rate_limit import enforce_ai_rate_limit

router = APIRouter(prefix="/api/news", tags=["news"])


def _cache_key(category: str | None, q: str | None, limit: int | None) -> str:
    return json.dumps({"category": category or "", "q": q or "", "limit": limit or ""})


@router.get("")
async def get_news(category: str | None = None, q: str | None = None, limit: int | None = None) -> dict:
    take = min(limit or 100, 500)
    key = _cache_key(category, q, take)

    articles = feed_cache.get(key)
    if articles is None:
        articles = await list_all(category=category, q=q, limit=take)
        feed_cache.put(key, articles)
    return {"articles": articles}


@router.get("/{article_id}")
async def get_article(article_id: str):
    article = await find_article(article_id)
    if article is None:
        return not_found()
    return article


async def _run_summarize_stream(article_id: str, article: dict, db: AsyncSession):
    """Adapts ai.summarize_stream() into SSE events, caching the result once
    it completes. A failure (Ollama down, bad response) becomes a "failed"
    event rather than an exception — the stream has already sent 200 + delta
    events by the time this can happen, so it's too late to fall back to a
    JSON error response.
    """
    try:
        async for event, payload in ai.summarize_stream(article):
            if event == "done":
                await set_ai_result(db, article_id, AiResultKind.SUMMARY, payload)
                yield ("done", payload)
            else:
                yield ("delta", {"text": payload})
    except OllamaUnavailableError as exc:
        yield ("failed", {"error": "AI_NOT_CONFIGURED", "message": str(exc)})


@router.get("/{article_id}/summarize", dependencies=[Depends(enforce_ai_rate_limit)])
async def summarize_article(article_id: str, db: AsyncSession = Depends(get_db)):
    cached = await get_ai_result(db, article_id, AiResultKind.SUMMARY)
    if cached:
        return sse(single_sse_event("done", cached))

    article = await find_article(article_id)
    if article is None:
        return not_found()

    return sse(_run_summarize_stream(article_id, article, db))
