"""Per-article research chat: a real conversation with a web_search tool,
replacing the old auto-run "AI Research" call. See app/llm/ for the
Ollama-native tool-calling loop this is built on.
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.common import find_article, not_found, sse
from app.core.config import settings
from app.db.session import get_db
from app.llm import agent
from app.llm.client import LLMClient
from app.llm.tools import get_tools
from app.services import chat_history
from app.services.ai import article_input
from app.services.rate_limit import enforce_ai_rate_limit

router = APIRouter(prefix="/api/news", tags=["chat"])

SYSTEM_TEMPLATE = (
    "You are a research assistant helping a reader dig into a specific news article. "
    "You have the article's text below for context. Use the web_search tool whenever you "
    "need information beyond the article itself — verification, background, updates, "
    "related coverage — rather than relying on stale training knowledge. Be concise and "
    "cite what you find plainly in your answer.\n\nARTICLE:\n{article}"
)


@router.get("/{article_id}/chat")
async def get_chat_history(article_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    messages = await chat_history.get_history(db, article_id)
    return {
        "messages": [
            {"role": m.role, "content": m.content, "toolCalls": m.toolCalls} for m in messages
        ]
    }


class ChatSendBody(BaseModel):
    message: str


@router.post("/{article_id}/chat", dependencies=[Depends(enforce_ai_rate_limit)])
async def send_chat_message(article_id: str, body: ChatSendBody, db: AsyncSession = Depends(get_db)):
    message = body.message.strip()
    if not message:
        raise HTTPException(400, "message must not be empty")

    article = await find_article(article_id)
    if article is None:
        return not_found()

    prior = await chat_history.get_history(db, article_id)
    history = [{"role": m.role, "content": m.content} for m in prior]

    await chat_history.add_message(db, article_id, "user", message)
    history.append({"role": "user", "content": message})

    system = SYSTEM_TEMPLATE.format(article=article_input(article))
    return sse(_run_chat_turn(article_id, system, history, db))


async def _run_chat_turn(article_id: str, system: str, history: list[dict], db: AsyncSession):
    q: asyncio.Queue = asyncio.Queue()
    sentinel = object()
    cancel = asyncio.Event()

    async def emit(name: str, data: dict) -> None:
        q.put_nowait((name, data))

    async def run() -> None:
        try:
            result = await agent.run_turn(
                client=LLMClient(),
                model=settings.ollama_chat_model,
                system=system,
                history=history,
                tools=get_tools(),
                emit=emit,
                cancel=cancel,
            )
            if result.text or result.tool_log:
                await chat_history.add_message(
                    db, article_id, "assistant", result.text, agent.tool_log_json(result)
                )
        finally:
            q.put_nowait(sentinel)

    task = asyncio.create_task(run())
    try:
        while True:
            item = await q.get()
            if item is sentinel:
                break
            yield item
    finally:
        # Client disconnected before the turn finished: let run_turn wind
        # down cooperatively (it checks `cancel` at each round/tool
        # boundary) so the partial answer still gets persisted — using
        # this request's db session, which stays open until this
        # generator returns.
        cancel.set()
        if not task.done():
            await task
