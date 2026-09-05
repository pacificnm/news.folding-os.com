"""Local Ollama server. This is a text chat model, not a fact-checking
model — it has no independent knowledge of an article's contents beyond
what's given to it. Every caller here must ground it with the real article
text and treat its response as a best-effort summary/analysis, not a source
of truth; nothing from this module should ever be trusted blindly.
"""

import json

import httpx

from app.core.config import settings


class OllamaUnavailableError(Exception):
    pass


async def chat_json(system: str, user: str, timeout_s: float = 60.0):
    """Ask the model a question and get back parsed JSON. Raises
    OllamaUnavailableError on any failure (not configured, unreachable,
    timed out, or a non-JSON/malformed response) — callers are expected to
    catch this and fall back to deterministic behavior, not surface it as a
    hard error to the user.
    """
    if not settings.ollama_base_url:
        raise OllamaUnavailableError("OLLAMA_BASE_URL is not configured")

    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "format": "json",
                    "stream": False,
                },
            )
    except httpx.HTTPError as exc:
        raise OllamaUnavailableError(f"Ollama request failed: {exc}") from exc

    if resp.status_code != 200:
        raise OllamaUnavailableError(f"Ollama returned {resp.status_code}")

    data = resp.json()
    content = (data.get("message") or {}).get("content")
    if not content:
        raise OllamaUnavailableError("Ollama response had no content")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise OllamaUnavailableError("Ollama response was not valid JSON") from exc


async def stream_chat_json(system: str, user: str, timeout_s: float = 90.0):
    """Like chat_json, but yields the model's raw text as it's generated for
    display purposes, then a final ("done", parsed_dict) tuple once the
    stream ends. Deltas are text fragments, not incremental JSON — nothing
    should try to parse them until "done", since Ollama's JSON-mode output
    is only valid JSON once the full response has arrived.

    Yields ("delta", str) then exactly one ("done", dict). Raises
    OllamaUnavailableError (before or during the stream) on any failure,
    same contract as chat_json.
    """
    if not settings.ollama_base_url:
        raise OllamaUnavailableError("OLLAMA_BASE_URL is not configured")

    chunks: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            async with client.stream(
                "POST",
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "format": "json",
                    "stream": True,
                },
            ) as resp:
                if resp.status_code != 200:
                    raise OllamaUnavailableError(f"Ollama returned {resp.status_code}")
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    piece = json.loads(line)
                    delta = (piece.get("message") or {}).get("content", "")
                    if delta:
                        chunks.append(delta)
                        yield ("delta", delta)
                    if piece.get("done"):
                        break
    except httpx.HTTPError as exc:
        raise OllamaUnavailableError(f"Ollama request failed: {exc}") from exc

    content = "".join(chunks)
    if not content:
        raise OllamaUnavailableError("Ollama response had no content")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise OllamaUnavailableError("Ollama response was not valid JSON") from exc
    yield ("done", parsed)
