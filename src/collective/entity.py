from collections.abc import Callable
from pathlib import Path
from typing import Any

from collective.client import EntityClient, cached_system
from collective.config import Models, Settings
from collective.memory.store import append_turn, recent_transcripts, start_session
from collective.skills.loader import Skill, discover_skills
from collective.skills.registry import execute, to_anthropic_tools


MUTATING_META_SKILLS = frozenset({"create_skill", "update_skill", "delete_skill"})


WEB_SEARCH_TOOL: dict[str, Any] = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 10,
}

WEB_FETCH_TOOL: dict[str, Any] = {
    "type": "web_fetch_20250910",
    "name": "web_fetch",
    "max_uses": 10,
    "citations": {"enabled": True},
}


COMMIT_IDENTITY_TOOL: dict[str, Any] = {
    "name": "commit_identity",
    "description": (
        "Call this once you have decided who you are and are ready to be born. "
        "Pass the full content of your IDENTITY.md as `identity`. "
        "It will be written to disk and become your system prompt on every "
        "subsequent run. Write in the first person. Include your name, values, "
        "tone, areas of focus, and anything future-you needs to know to act "
        "consistently."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "identity": {
                "type": "string",
                "description": "Full markdown content for IDENTITY.md.",
            }
        },
        "required": ["identity"],
    },
}


class Entity:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = EntityClient(settings)
        self.skills: list[Skill] = []
        self.transcript: Path | None = None
        self.messages: list[dict[str, Any]] = []
        self.system_text: str = ""
        self.in_birth: bool = False

    def needs_birth(self) -> bool:
        path = self.settings.identity_path
        return not path.exists() or not path.read_text(encoding="utf-8").strip()

    def begin_session(self) -> None:
        self.skills = discover_skills(self.settings.skills_dir)
        self.transcript = start_session(self.settings.short_term_dir)

        if self.needs_birth():
            self.in_birth = True
            self.system_text = self.settings.birth_path.read_text(encoding="utf-8")
        else:
            self.in_birth = False
            self.system_text = self.settings.identity_path.read_text(encoding="utf-8")

        self.messages = []
        if not self.in_birth:
            recents = recent_transcripts(self.settings.short_term_dir, limit=4)
            current_marker = f"# Session {self.transcript.stem}"
            recents = [r for r in recents if not r.startswith(current_marker)]
            if recents:
                memory_block = (
                    "Notes from your recent sessions (most recent last):\n\n"
                    + "\n\n---\n\n".join(recents)
                )
                self.messages.append({"role": "user", "content": memory_block})
                self.messages.append(
                    {"role": "assistant", "content": "Recalled. Ready."}
                )

    def turn(self, user_input: str, *, on_text: Callable[[str], None]) -> str:
        assert self.transcript is not None, "Call begin_session() first."
        append_turn(self.transcript, "user", user_input)
        self.messages.append({"role": "user", "content": user_input})

        tools = [WEB_SEARCH_TOOL, WEB_FETCH_TOOL, *to_anthropic_tools(self.skills)]
        if self.in_birth:
            tools = [COMMIT_IDENTITY_TOOL, *tools]

        response = None
        while True:
            response = self.client.stream_turn(
                model=Models.DEFAULT,
                system=cached_system(self.system_text),
                messages=self.messages,
                tools=tools or None,
                on_text=on_text,
            )
            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "pause_turn":
                continue
            if response.stop_reason != "tool_use":
                break

            tool_results = []
            reload_skills = False
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if self.in_birth and block.name == "commit_identity":
                    self._commit_identity(block.input["identity"])
                    result = (
                        "IDENTITY.md saved. You are born. From now on this file "
                        "is your system prompt on every run."
                    )
                else:
                    result = execute(self.skills, block.name, block.input)
                    if block.name in MUTATING_META_SKILLS:
                        reload_skills = True
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )
            self.messages.append({"role": "user", "content": tool_results})

            if reload_skills:
                self.skills = discover_skills(self.settings.skills_dir)
                tools = [WEB_SEARCH_TOOL, WEB_FETCH_TOOL, *to_anthropic_tools(self.skills)]
                if self.in_birth:
                    tools = [COMMIT_IDENTITY_TOOL, *tools]

        final_text = "".join(
            b.text for b in response.content if b.type == "text"
        )
        append_turn(self.transcript, "assistant", final_text)
        return final_text

    def _commit_identity(self, identity_text: str) -> None:
        self.settings.identity_path.write_text(identity_text, encoding="utf-8")
        self.system_text = identity_text
        self.in_birth = False
