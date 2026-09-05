"""Postgres-backed replacement for the original app's JSON-file store
(services/store.js) — persists AI results (summary/research) so a repeated
view doesn't re-call the model. Articles themselves are never persisted
here, only their AI results.
"""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AiResult, AiResultKind


async def get_ai_result(db: AsyncSession, article_id: str, kind: AiResultKind) -> dict | None:
    result = await db.execute(
        select(AiResult.payload).where(AiResult.articleId == article_id, AiResult.kind == kind)
    )
    row = result.scalar_one_or_none()
    return row


async def set_ai_result(db: AsyncSession, article_id: str, kind: AiResultKind, payload: dict) -> None:
    stmt = (
        pg_insert(AiResult)
        .values(articleId=article_id, kind=kind, payload=payload)
        .on_conflict_do_update(index_elements=["articleId", "kind"], set_={"payload": payload})
    )
    await db.execute(stmt)
    await db.commit()
