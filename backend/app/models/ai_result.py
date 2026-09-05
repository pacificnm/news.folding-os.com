import enum
from datetime import datetime

from foldingos_api_core import Base
from sqlalchemy import DateTime, Enum, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class AiResultKind(str, enum.Enum):
    SUMMARY = "SUMMARY"
    RESEARCH = "RESEARCH"


class AiResult(Base):
    """A cached AI-generated summary or research result for one article,
    keyed by the article's own id (a stable hash of its source feed name +
    slugified url — see services/rss_source.py). Articles themselves are
    never persisted (they're re-fetched from RSS on demand and only
    short-TTL cached in-process) — only the AI results are worth persisting,
    since regenerating them costs a real model call.
    """

    __tablename__ = "AiResult"
    __table_args__ = (Index("AiResult_articleId_kind_key", "articleId", "kind", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    articleId: Mapped[str] = mapped_column(String(200))
    kind: Mapped[AiResultKind] = mapped_column(Enum(AiResultKind, name="AiResultKind"))
    payload: Mapped[dict] = mapped_column(JSONB)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
