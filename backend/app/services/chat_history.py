"""Persistence for the per-article research chat (app/api/chat.py)."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessage


async def get_history(db: AsyncSession, article_id: str) -> list[ChatMessage]:
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.articleId == article_id).order_by(ChatMessage.id)
    )
    return list(result.scalars().all())


async def add_message(
    db: AsyncSession, article_id: str, role: str, content: str, tool_calls_json: str | None = None
) -> None:
    db.add(
        ChatMessage(
            articleId=article_id,
            role=role,
            content=content,
            toolCalls=json.loads(tool_calls_json) if tool_calls_json else None,
        )
    )
    await db.commit()
