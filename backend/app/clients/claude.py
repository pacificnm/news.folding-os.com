"""Claude chat client for JSON-mode tasks (article summarization). This is a
text chat model, not a fact-checking model — it has no independent knowledge
of an article's contents beyond what's given to it. Every caller here must
ground it with the real article text and treat its response as a best-effort
summary/analysis, not a source of truth; nothing from this module should
ever be trusted blindly.
"""

import json
import re
from collections.abc import AsyncIterator

import anthropic

MODEL = "claude-sonnet-5"

_client = anthropic.AsyncAnthropic()

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class ClaudeUnavailableError(Exception):
    pass


def _extract_json(text: str) -> dict:
    cleaned = _JSON_FENCE_RE.sub("", text).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ClaudeUnavailableError("Claude response was not valid JSON") from exc
    if not isinstance(value, dict):
        raise ClaudeUnavailableError("Claude response was not a JSON object")
    return value


async def chat_json(system: str, user: str, timeout_s: float = 60.0) -> dict:
    """Ask the model a question and get back parsed JSON. Raises
    ClaudeUnavailableError on any failure (unreachable, timed out, or a
    non-JSON/malformed response) — callers are expected to catch this and
    fall back to deterministic behavior, not surface it as a hard error to
    the user.
    """
    try:
        response = await _client.with_options(timeout=timeout_s).messages.create(
            model=MODEL,
            max_tokens=1024,
            thinking={"type": "disabled"},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except anthropic.APIError as exc:
        raise ClaudeUnavailableError(f"Claude request failed: {exc}") from exc

    text = "".join(block.text for block in response.content if block.type == "text")
    if not text:
        raise ClaudeUnavailableError("Claude response had no content")
    return _extract_json(text)


async def stream_chat_json(system: str, user: str, timeout_s: float = 90.0) -> AsyncIterator[tuple[str, object]]:
    """Like chat_json, but yields the model's raw text as it's generated for
    display purposes, then a final ("done", parsed_dict) tuple once the
    stream ends. Deltas are text fragments, not incremental JSON — nothing
    should try to parse them until "done".

    Yields ("delta", str) then exactly one ("done", dict). Raises
    ClaudeUnavailableError (before or during the stream) on any failure,
    same contract as chat_json.
    """
    chunks: list[str] = []
    try:
        async with _client.with_options(timeout=timeout_s).messages.stream(
            model=MODEL,
            max_tokens=1024,
            thinking={"type": "disabled"},
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            async for text in stream.text_stream:
                chunks.append(text)
                yield ("delta", text)
    except anthropic.APIError as exc:
        raise ClaudeUnavailableError(f"Claude request failed: {exc}") from exc

    content = "".join(chunks)
    if not content:
        raise ClaudeUnavailableError("Claude response had no content")
    yield ("done", _extract_json(content))
