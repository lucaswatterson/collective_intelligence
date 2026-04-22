from collections.abc import Callable
from typing import Any

import anthropic
from anthropic.types import Message

from collective.config import Models, Settings


class EntityClient:
    def __init__(self, settings: Settings):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def stream_turn(
        self,
        *,
        model: str,
        system: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        on_text: Callable[[str], None] | None = None,
        max_tokens: int = 16000,
    ) -> Message:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        if model in (Models.REASONING, Models.DEFAULT):
            kwargs["thinking"] = {"type": "adaptive"}

        with self._client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                if on_text:
                    on_text(text)
            return stream.get_final_message()

    def create_turn(
        self,
        *,
        model: str,
        system: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 16000,
    ) -> Message:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        if model in (Models.REASONING, Models.DEFAULT):
            kwargs["thinking"] = {"type": "adaptive"}
        return self._client.messages.create(**kwargs)


def cached_system(text: str) -> list[dict[str, Any]]:
    """Wrap a system prompt with an ephemeral cache breakpoint."""
    return [
        {
            "type": "text",
            "text": text,
            "cache_control": {"type": "ephemeral"},
        }
    ]
