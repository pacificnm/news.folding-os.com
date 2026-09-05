from datetime import datetime

from foldingos_api_core import Base
from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class ChatMessage(Base):
    """One message in an article's research chat. Ordered by `id` (a single
    thread per article — no branching or editing, so no separate sequence
    column is needed, unlike a multi-conversation chat app).
    """

    __tablename__ = "ChatMessage"
    __table_args__ = (Index("ChatMessage_articleId_idx", "articleId"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    articleId: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    toolCalls: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
