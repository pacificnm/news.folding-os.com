"""AI summarize for an article. Direct port of the original app's
services/ai.js — same prompt, same truncation, same "never throw, return
{error, message}" contract — only the transport changes (OpenAI -> local
Ollama). The original's defensive JSON-fence-stripping isn't needed here:
`chat_json` (app/clients/ollama.py) already raises OllamaUnavailableError
for a non-JSON/malformed response, using Ollama's own `format: "json"`
constrained decoding rather than a text-based fence strip.

(Research used to live here too, as a second one-shot JSON call. It's now
the interactive chat in app/api/chat.py + app/llm/, which needs multi-turn
history and tool-calling that this module's one-shot pattern can't do.)
"""

from app.clients.ollama import OllamaUnavailableError, chat_json, stream_chat_json

MAX_INPUT_CHARS = 12000


def _truncate(text: str, max_chars: int = MAX_INPUT_CHARS) -> str:
    s = text or ""
    return s if len(s) <= max_chars else s[:max_chars] + "…"


def _not_configured(message: str) -> dict:
    return {"error": "AI_NOT_CONFIGURED", "message": message}


def article_input(article: dict) -> str:
    return _truncate(
        f"Title: {article.get('title', '')}\n\n{article.get('description', '')}\n\n{article.get('contentHtml', '')}"
    )


SUMMARIZE_PROMPT = (
    'You are a news analyst. Return JSON with fields: "summary" (2-3 sentence summary) and '
    '"keyPoints" (array of 3-5 short strings).'
)


def _shape_summary(data: dict) -> dict:
    return {
        "summary": data.get("summary", ""),
        "keyPoints": data.get("keyPoints") if isinstance(data.get("keyPoints"), list) else [],
    }


async def summarize(article: dict) -> dict:
    """Returns {summary, keyPoints} or {error, message}."""
    try:
        data = await chat_json(SUMMARIZE_PROMPT, article_input(article))
    except OllamaUnavailableError as exc:
        return _not_configured(str(exc))
    return _shape_summary(data)


async def summarize_stream(article: dict):
    """Streaming counterpart to summarize(): yields ("delta", str) fragments
    then a final ("done", {summary, keyPoints}). Raises OllamaUnavailableError
    on failure — callers stream this directly to the client and translate a
    caught error into the {error, message} shape at the transport layer.
    """
    async for kind, payload in stream_chat_json(SUMMARIZE_PROMPT, article_input(article)):
        yield (kind, payload if kind == "delta" else _shape_summary(payload))
