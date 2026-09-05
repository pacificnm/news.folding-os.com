from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.common import find_article, not_found, single_sse_event, sse
from app.clients.ollama import OllamaUnavailableError
from app.db.session import get_db
from app.models import AiResultKind
from app.services import ai, image_cache
from app.services.ai_cache import get_ai_result, set_ai_result
from app.services.news_source import list_all
from app.services.rate_limit import enforce_ai_rate_limit

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("")
async def get_news(category: str | None = None, q: str | None = None, limit: int | None = None) -> dict:
    # No caching here: RssSource.list() only ever reads its already-fetched,
    # background-refreshed snapshot (see app/services/feed_refresh.py) —
    # there's no per-request I/O left to cache.
    take = min(limit or 100, 500)
    articles = await list_all(category=category, q=q, limit=take)
    return {"articles": articles}


@router.get("/{article_id}/image")
async def get_article_image(article_id: str):
    cached = image_cache.get(article_id)
    if cached is None:
        return not_found()
    content, content_type = cached
    return Response(content=content, media_type=content_type, headers={"Cache-Control": "public, max-age=900"})


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
