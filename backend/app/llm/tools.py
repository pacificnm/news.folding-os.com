"""Tools exposed to the research-chat model. Ported from
chat.folding-os.com/backend/app/llm/tools.py, trimmed to just web_search —
news has no repo/sandbox tools to expose.

Handler contract: `async def handler(arguments: dict, ctx: ToolContext) -> str`.
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx

from app.core.config import settings

MAX_RESULTS = 6
MAX_SNIPPET_CHARS = 400
SearchTimeout = httpx.Timeout(15.0, connect=5.0)

Emit = Callable[[str, dict], Awaitable[None]]
Handler = Callable[[dict, "ToolContext"], Awaitable[str]]


@dataclass
class ToolContext:
    """Runtime context handed to every tool handler.

    - `emit`: push incremental `tool_output` events (streaming tools only)
    - `index`: this call's index within the current turn
    - `cancel`: user-abort signal — long-running handlers must observe it
    """

    emit: Emit
    index: int
    cancel: asyncio.Event


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict  # JSON Schema for the arguments object
    handler: Handler
    #: True if the handler streams its own `tool_output` increments while running.
    streams: bool = False

    def to_openai(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


async def web_search(arguments: dict, _ctx: ToolContext) -> str:
    """Query self-hosted SearXNG (JSON API) and format the top hits."""
    query = str(arguments.get("query") or "").strip()
    if not query:
        return "error: missing 'query'"
    url = f"{settings.searxng_url.rstrip('/')}/search"
    try:
        async with httpx.AsyncClient(timeout=SearchTimeout) as client:
            res = await client.get(url, params={"q": query, "format": "json"})
            res.raise_for_status()
            rows = res.json().get("results") or []
    except httpx.HTTPError as exc:
        return f"web search unavailable ({exc.__class__.__name__}); answer from knowledge instead"

    if not rows:
        return f"no results for: {query}"

    lines: list[str] = []
    for i, row in enumerate(rows[:MAX_RESULTS], start=1):
        title = str(row.get("title") or row.get("url") or "untitled").strip()
        link = str(row.get("url") or "")
        snippet = " ".join(str(row.get("content") or "").split())
        if len(snippet) > MAX_SNIPPET_CHARS:
            snippet = snippet[:MAX_SNIPPET_CHARS].rstrip() + "…"
        lines.append(f"{i}. {title} — {link}")
        if snippet:
            lines.append(f"   {snippet}")
    return "\n".join(lines)


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="web_search",
            description=(
                "Search the web (self-hosted SearXNG) for current information relevant to "
                "the article being discussed: background, verification, related coverage, "
                "updates since the article was published. Returns the top 6 titles, URLs "
                "and snippets, which cannot be fetched further."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (a few words)."}
                },
                "required": ["query"],
            },
            handler=web_search,
        ),
    ]


def parse_tool_arguments(raw: str) -> dict:
    """Model-provided arguments arrive as a (streamed) JSON string."""
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except ValueError:
        return {"_parse_error": raw[:200]}
    return value if isinstance(value, dict) else {"value": value}
