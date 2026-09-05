import json

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.get("/{article_id}/summarize", dependencies=[Depends(enforce_ai_rate_limit)])
async def summarize_article(article_id: str, db: AsyncSession = Depends(get_db)):
    cached = await get_ai_result(db, article_id, AiResultKind.SUMMARY)
    if cached:
        return cached

    article = await _find_article(article_id)
    if article is None:
        return _not_found()

    result = await ai.summarize(article)
    if result.get("error"):
        return JSONResponse(status_code=503, content=result)

    await set_ai_result(db, article_id, AiResultKind.SUMMARY, result)
    return result


@router.get("/{article_id}/research", dependencies=[Depends(enforce_ai_rate_limit)])
async def research_article(article_id: str, db: AsyncSession = Depends(get_db)):
    cached = await get_ai_result(db, article_id, AiResultKind.RESEARCH)
    if cached:
        return cached

    article = await _find_article(article_id)
    if article is None:
        return _not_found()

    result = await ai.research(article)
    if result.get("error"):
        return JSONResponse(status_code=503, content=result)

    await set_ai_result(db, article_id, AiResultKind.RESEARCH, result)
    return result
