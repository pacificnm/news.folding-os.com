"""SSE helpers and article lookup shared by app/api/news.py and app/api/chat.py."""

import json

from fastapi.responses import JSONResponse, StreamingResponse

from app.services.news_source import list_all


def not_found() -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": "NOT_FOUND", "message": "Article not found."})


async def find_article(article_id: str) -> dict | None:
    articles = await list_all(limit=500)
    return next((a for a in articles if a["id"] == article_id or a["url"] == article_id), None)


async def single_sse_event(event: str, data: dict):
    yield event, data


def sse(events) -> StreamingResponse:
    async def body():
        async for event, data in events:
            yield f"event: {event}\ndata: {json.dumps(data)}\n\n"

    return StreamingResponse(
        body(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
