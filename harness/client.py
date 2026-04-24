from collections.abc import Callable
from typing import Any

import anthropic

from harness.config import Models, Settings


MCP_BETA = "mcp-client-2025-11-20"


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
        mcp_servers: list[dict[str, Any]] | None = None,
        on_text: Callable[[str], None] | None = None,
        max_tokens: int = 32000,
    ) -> Any:
        kwargs = self._build_kwargs(
            model=model,
            system=system,
            messages=messages,
            tools=tools,
            mcp_servers=mcp_servers,
            max_tokens=max_tokens,
        )
        with self._client.beta.messages.stream(**kwargs) as stream:
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
        mcp_servers: list[dict[str, Any]] | None = None,
        max_tokens: int = 32000,
    ) -> Any:
        kwargs = self._build_kwargs(
            model=model,
            system=system,
            messages=messages,
            tools=tools,
            mcp_servers=mcp_servers,
            max_tokens=max_tokens,
        )
        return self._client.beta.messages.create(**kwargs)

    @staticmethod
    def _build_kwargs(
        *,
        model: str,
        system: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        mcp_servers: list[dict[str, Any]] | None,
        max_tokens: int,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
            "betas": [MCP_BETA],
        }
        if tools:
            kwargs["tools"] = tools
        if mcp_servers:
            kwargs["mcp_servers"] = mcp_servers
        if model in (Models.REASONING, Models.DEFAULT):
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": 10000}
        return kwargs


def cached_system(text: str) -> list[dict[str, Any]]:
    """Wrap a system prompt with an ephemeral cache breakpoint."""
    return [
        {
            "type": "text",
            "text": text,
            "cache_control": {"type": "ephemeral"},
        }
    ]
