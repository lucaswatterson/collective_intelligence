import json
import re
from pathlib import Path

from harness.client import EntityClient
from harness.config import Models, Settings, load_settings
from harness.knowledge.index import rebuild_index_if_stale


HAIKU_SYSTEM = (
    "You are a retrieval router for a knowledge base. "
    "You will be given an INDEX of knowledge files and a question. "
    "Return ONLY a JSON array of filenames (from the index) whose contents are "
    "likely to help answer the question. Return [] if nothing is relevant. "
    "Pick at most 3 files. Do not invent filenames."
)


def run(**input) -> str:
    question = input["question"].strip()
    if not question:
        return "query_knowledge: question is empty."

    settings = load_settings()
    knowledge_dir = settings.entity_root / "knowledge"

    if not knowledge_dir.exists():
        return "No knowledge directory found."

    rebuild_index_if_stale(knowledge_dir)
    index_path = knowledge_dir / "INDEX.md"
    if not index_path.exists():
        return "Knowledge base is empty."

    index_text = index_path.read_text(encoding="utf-8")
    if "(empty)" in index_text and not list(knowledge_dir.glob("*.md")):
        return "Knowledge base is empty."

    filenames = _pick_files(settings, index_text, question)
    if not filenames:
        return "No knowledge files appear relevant to that question."

    return _render_files(knowledge_dir, filenames)


def _pick_files(settings: Settings, index_text: str, question: str) -> list[str]:
    client = EntityClient(settings)
    user_msg = (
        f"INDEX:\n{index_text}\n\n"
        f"QUESTION: {question}\n\n"
        "Reply with a JSON array of filenames from the INDEX."
    )
    response = client.create_turn(
        model=Models.FAST,
        system=[{"type": "text", "text": HAIKU_SYSTEM}],
        messages=[{"role": "user", "content": user_msg}],
        max_tokens=512,
    )
    text = "".join(
        getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text"
    ).strip()

    match = re.search(r"\[.*?\]", text, flags=re.DOTALL)
    if not match:
        return []
    try:
        picked = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(picked, list):
        return []
    return [str(name) for name in picked if isinstance(name, str) and name]


def _render_files(knowledge_dir: Path, filenames: list[str]) -> str:
    blocks: list[str] = []
    for name in filenames:
        path = knowledge_dir / name
        if not path.is_file() or ".archive" in str(path) or name == "INDEX.md":
            continue
        try:
            contents = path.read_text(encoding="utf-8")
        except Exception as exc:
            blocks.append(f"## {name}\n\n(could not read: {exc})\n")
            continue
        blocks.append(f"## {name}\n\n{contents.strip()}\n")

    if not blocks:
        return "No knowledge files appear relevant to that question."
    return "\n---\n\n".join(blocks)
