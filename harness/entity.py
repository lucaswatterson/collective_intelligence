import logging
from collections import Counter
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from harness.client import EntityClient, cached_system
from harness.config import Models, Settings
from harness.memory.store import append_turn, recent_transcripts, start_session
from harness.skills.loader import Skill, discover_skills
from harness.skills.registry import execute, to_anthropic_tools


log = logging.getLogger(__name__)


SKILL_RELOAD_TRIGGERS = frozenset({"create_skill", "update_skill", "delete_skill"})
IDENTITY_RELOAD_TRIGGERS = frozenset({"update_identity"})


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


WORKER_PROMPT_PREFIX = (
    "You are operating autonomously as the worker — not in chat with the human. "
    "Complete the task below end-to-end. If the task produces artifacts, save "
    "them under `entity/work/{slug}/`. Call `complete_task` when finished. If "
    "you cannot finish, use `update_task` to leave a note and set status to "
    "'blocked' (or leave as 'in-progress' if waiting on something). Do not ask "
    "the user questions — make your best judgment and proceed.\n\n"
    "Task file: {filename}\n\n---\n\n{task_body}"
)


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
            recents = recent_transcripts(self.settings.short_term_dir, limit=2)
            current_marker = f"# Session {self.transcript.stem}"
            recents = [r for r in recents if not r.startswith(current_marker)]

            index_path = self.settings.long_term_index_path
            index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""

            parts = []
            if index_text.strip():
                parts.append(
                    "Your long-term memory index. Use `read_memory` to pull any entry in full.\n\n"
                    + index_text
                )
            if recents:
                parts.append(
                    "Recent session transcripts (most recent last):\n\n"
                    + "\n\n---\n\n".join(recents)
                )
            if parts:
                self.messages.append({"role": "user", "content": "\n\n===\n\n".join(parts)})
                self.messages.append(
                    {"role": "assistant", "content": "Recalled. Ready."}
                )

    def turn(
        self,
        user_input: str,
        *,
        on_text: Callable[[str], None],
        on_tool_use: Callable[[str], None] | None = None,
    ) -> str:
        assert self.transcript is not None, "Call begin_session() first."
        append_turn(self.transcript, "user", user_input)
        self.messages.append({"role": "user", "content": user_input})

        final_text = self._run_tool_loop(on_text=on_text, on_tool_use=on_tool_use)
        append_turn(self.transcript, "assistant", final_text)
        return final_text

    def work_on_task(
        self,
        task_path: Path,
        *,
        on_tool_use: Callable[[str], None] | None = None,
    ) -> str:
        """Run an autonomous tool-use loop against a single task file.

        Resets per-task messages and transcript. Injects long-term memory
        index as context. The entity is expected to call `complete_task`
        (or leave progress via `update_task`) as part of the loop.
        """
        self.skills = discover_skills(self.settings.skills_dir)

        if self.needs_birth():
            # Birth is chat-only; worker should not run until identity exists.
            raise RuntimeError(
                "Entity has not been born yet; worker cannot run until IDENTITY.md is committed."
            )
        self.in_birth = False
        self.system_text = self.settings.identity_path.read_text(encoding="utf-8")

        raw = task_path.read_text(encoding="utf-8")
        slug = task_path.stem

        self.transcript = _start_task_session(self.settings.short_term_dir, slug)

        self.messages = []
        index_path = self.settings.long_term_index_path
        if index_path.exists() and index_path.read_text(encoding="utf-8").strip():
            index_text = index_path.read_text(encoding="utf-8")
            self.messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your long-term memory index. Use `read_memory` to pull any "
                        "entry in full.\n\n" + index_text
                    ),
                }
            )
            self.messages.append({"role": "assistant", "content": "Recalled. Ready."})

        prompt = WORKER_PROMPT_PREFIX.format(
            slug=slug, filename=task_path.name, task_body=raw
        )
        append_turn(self.transcript, "user", prompt)
        self.messages.append({"role": "user", "content": prompt})

        final_text = self._run_tool_loop(on_tool_use=on_tool_use)
        append_turn(self.transcript, "assistant", final_text)
        return final_text

    def _run_tool_loop(
        self,
        *,
        on_text: Callable[[str], None] | None = None,
        on_tool_use: Callable[[str], None] | None = None,
    ) -> str:
        def build_tools() -> list[dict[str, Any]]:
            result = [
                WEB_SEARCH_TOOL,
                WEB_FETCH_TOOL,
                *to_anthropic_tools(self.skills),
            ]
            if self.in_birth:
                result = [COMMIT_IDENTITY_TOOL, *result]
            return result

        response = None
        while True:
            tools = build_tools()
            response = self.client.stream_turn(
                model=Models.DEFAULT,
                system=cached_system(self.system_text),
                messages=self.messages,
                tools=tools or None,
                on_text=on_text,
            )
            self.messages.append({"role": "assistant", "content": response.content})

            block_types = Counter(b.type for b in response.content)
            tool_names = [b.name for b in response.content if b.type == "tool_use"]
            log.info(
                "turn: stop_reason=%s blocks=%s tools=%s",
                response.stop_reason,
                dict(block_types),
                tool_names,
            )

            if response.stop_reason == "pause_turn":
                continue
            if response.stop_reason != "tool_use":
                break

            tool_results = []
            reload_skills = False
            reload_identity = False
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if on_tool_use:
                    on_tool_use(block.name)
                if self.in_birth and block.name == "commit_identity":
                    self._commit_identity(block.input["identity"])
                    result = (
                        "IDENTITY.md saved. You are born. From now on this file "
                        "is your system prompt on every run."
                    )
                else:
                    result = execute(self.skills, block.name, block.input)
                    if block.name in SKILL_RELOAD_TRIGGERS:
                        reload_skills = True
                    if block.name in IDENTITY_RELOAD_TRIGGERS:
                        reload_identity = True
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
            if reload_identity and not self.in_birth:
                self.system_text = self.settings.identity_path.read_text(encoding="utf-8")

        return "".join(b.text for b in response.content if b.type == "text")

    def _commit_identity(self, identity_text: str) -> None:
        self.settings.identity_path.write_text(identity_text, encoding="utf-8")
        self.system_text = identity_text
        self.in_birth = False


def _start_task_session(short_term_dir: Path, slug: str) -> Path:
    short_term_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    path = short_term_dir / f"{stamp}_task_{slug}.md"
    path.write_text(f"# Task Session {stamp} · {slug}\n\n", encoding="utf-8")
    return path
