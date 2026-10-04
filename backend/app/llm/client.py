"""Streaming chat client backed by the Claude API.

Translates the OpenAI-shaped conversation and tool schema that agent.py and
tools.py build (a legacy of the Ollama OpenAI-compatible endpoint this used
to call) into Claude Messages API calls, and translates Claude's stream
events back into the same Delta shapes — so agent.py and tools.py don't need
to know or care which provider is behind this client.
"""

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import anthropic

MODEL = "claude-sonnet-5"


class LLMError(RuntimeError):
    """Claude request failed; `detail` is a short, user-safe digest."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class ThinkingDelta:
    """Chain-of-thought; not the answer."""

    text: str


@dataclass(frozen=True)
class ToolCallDelta:
    index: int
    id: str | None = None
    name: str | None = None
    arguments_chunk: str = ""


@dataclass(frozen=True)
class DoneDelta:
    finish_reason: str | None


Delta = TextDelta | ThinkingDelta | ToolCallDelta | DoneDelta

ShouldCancel = Callable[[], Awaitable[bool]] | Callable[[], bool]


def _to_claude_messages(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """Convert the OpenAI-shaped convo (system/user/assistant/tool roles,
    OpenAI-style tool_calls) into a Claude system string + messages list.
    """
    system = ""
    out: list[dict[str, Any]] = []
    for m in messages:
        role = m["role"]
        if role == "system":
            system = m.get("content") or ""
        elif role == "user":
            out.append({"role": "user", "content": m.get("content") or ""})
        elif role == "assistant":
            content: list[dict[str, Any]] = []
            if m.get("content"):
                content.append({"type": "text", "text": m["content"]})
            for tc in m.get("tool_calls") or []:
                fn = tc["function"]
                try:
                    tool_input = json.loads(fn["arguments"] or "{}")
                except ValueError:
                    tool_input = {}
                content.append(
                    {"type": "tool_use", "id": tc["id"], "name": fn["name"], "input": tool_input}
                )
            out.append({"role": "assistant", "content": content})
        elif role == "tool":
            out.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": m["tool_call_id"],
                            "content": m["content"],
                        }
                    ],
                }
            )
    return system, out


def _to_claude_tools(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    out = []
    for t in tools:
        fn = t["function"]
        out.append(
            {
                "name": fn["name"],
                "description": fn.get("description", ""),
                "input_schema": fn["parameters"],
            }
        )
    return out


class LLMClient:
    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic()

    async def stream_chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        should_cancel: ShouldCancel | None = None,
    ) -> AsyncIterator[Delta]:
        """Stream one model turn as deltas. Caller iterates to completion.

        `temperature` is accepted for interface compatibility with the prior
        Ollama-backed client but not forwarded — Claude rejects non-default
        sampling parameters.
        """
        system, claude_messages = _to_claude_messages(messages)
        claude_tools = _to_claude_tools(tools)
        tool_index = -1

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "thinking": {"type": "disabled"},
            "messages": claude_messages,
        }
        if system:
            kwargs["system"] = system
        if claude_tools:
            kwargs["tools"] = claude_tools

        try:
            async with self._client.messages.stream(**kwargs) as stream:
                async for event in stream:
                    if should_cancel is not None and await _maybe_cancel(should_cancel):
                        return
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            tool_index += 1
                            yield ToolCallDelta(
                                index=tool_index,
                                id=event.content_block.id,
                                name=event.content_block.name,
                            )
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            yield TextDelta(text=event.delta.text)
                        elif event.delta.type == "thinking_delta":
                            yield ThinkingDelta(text=event.delta.thinking)
                        elif event.delta.type == "input_json_delta":
                            yield ToolCallDelta(index=tool_index, arguments_chunk=event.delta.partial_json)

                final = await stream.get_final_message()
                yield DoneDelta(finish_reason=final.stop_reason)
        except anthropic.APIError as exc:
            raise LLMError(f"Claude request failed: {exc}") from exc


async def _maybe_cancel(should_cancel: ShouldCancel) -> bool:
    result = should_cancel()
    if hasattr(result, "__await__"):
        result = await result  # type: ignore[valid-type]
    return bool(result)
