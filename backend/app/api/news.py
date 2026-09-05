import json

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.ollama import OllamaUnavailableError
from app.db.session import get_db
from app.models import AiResultKind
from app.services import ai, feed_cache
from app.services.ai_cache import get_ai_result, set_ai_result
from app.services.news_source import list_all
from app.services.rate_limit import enforce_ai_rate_limit

router = APIRouter(prefix="/api/news", tags=["news"])


def _not_found() -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": "NOT_FOUND", "message": "Article not found."})


def _cache_key(category: str | None, q: str | None, limit: int | None) -> str:
    return json.dumps({"category": category or "", "q": q or "", "limit": limit or ""})


async def _find_article(article_id: str) -> dict | None:
    articles = await list_all(limit=500)
    return next((a for a in articles if a["id"] == article_id or a["url"] == article_id), None)


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
    article = await _find_article(article_id)
    if article is None:
        return _not_found()
    return article


async def _single_sse_event(event: str, data: dict):
    yield event, data


def _sse(events) -> StreamingResponse:
    async def body():
        async for event, data in events:
            yield f"event: {event}\ndata: {json.dumps(data)}\n\n"

    return StreamingResponse(
        body(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _run_ai_stream(article_id: str, kind: AiResultKind, stream, db: AsyncSession):
    """Adapts an ai.summarize_stream()/research_stream() generator into SSE
    events, persisting the result to the cache once it completes. A failure
    (Ollama down, bad response) becomes a "failed" event rather than an
    exception — the stream has already sent 200 + delta events by the time
    this can happen, so it's too late to fall back to a JSON error response.
    """
    try:
        async for event, payload in stream:
            if event == "done":
                await set_ai_result(db, article_id, kind, payload)
                yield ("done", payload)
            else:
                yield ("delta", {"text": payload})
    except OllamaUnavailableError as exc:
        yield ("failed", {"error": "AI_NOT_CONFIGURED", "message": str(exc)})


@router.get("/{article_id}/summarize", dependencies=[Depends(enforce_ai_rate_limit)])
async def summarize_article(article_id: str, db: AsyncSession = Depends(get_db)):
    cached = await get_ai_result(db, article_id, AiResultKind.SUMMARY)
    if cached:
        return _sse(_single_sse_event("done", cached))

    article = await _find_article(article_id)
    if article is None:
        return _not_found()

    return _sse(_run_ai_stream(article_id, AiResultKind.SUMMARY, ai.summarize_stream(article), db))


@router.get("/{article_id}/research", dependencies=[Depends(enforce_ai_rate_limit)])
async def research_article(article_id: str, db: AsyncSession = Depends(get_db)):
    cached = await get_ai_result(db, article_id, AiResultKind.RESEARCH)
    if cached:
        return _sse(_single_sse_event("done", cached))

    article = await _find_article(article_id)
    if article is None:
        return _not_found()

    return _sse(_run_ai_stream(article_id, AiResultKind.RESEARCH, ai.research_stream(article), db))
