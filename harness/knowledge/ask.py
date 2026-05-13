from pathlib import Path

from harness.client import EntityClient
from harness.config import Models, Settings
from harness.knowledge.index import INDEX_FILENAME


PASS_SENTINEL = "PASS"


SYSTEM = (
    "You answer factual questions using ONLY the knowledge files provided below. "
    "Cite the filename inline when you state a fact (e.g. 'per `lucas-profile.md`'). "
    "If the answer is not in the files, say so plainly — do not guess. "
    "Be terse. No preamble, no trailing summary."
)


TRY_ASK_SYSTEM_TEMPLATE = (
    "You are answering a chat turn from Lucas as the entity described in IDENTITY below. "
    "Speak in that voice — your own.\n\n"
    "RULES:\n"
    "1. If the answer is grounded in the KNOWLEDGE FILES, answer in your own voice. "
    "Cite the source filename inline (e.g. 'per `lucas-profile.md`'). Keep it terse.\n"
    "2. If the question needs reasoning, code understanding, memory of past sessions, "
    "tool use, or anything not directly in the KNOWLEDGE FILES, respond with EXACTLY "
    f"the four characters {PASS_SENTINEL} and nothing else. No punctuation, no quotes, "
    "no explanation. A more capable model will take over.\n"
    "3. When in doubt, prefer PASS. It is cheap to fall through; it is expensive to give "
    "a flat, ungrounded answer.\n\n"
    "=== IDENTITY ===\n\n"
    "{identity}\n\n"
    "=== KNOWLEDGE FILES ===\n\n"
    "{corpus}"
)


def ask(question: str, settings: Settings) -> str:
    question = question.strip()
    if not question:
        return "ask: question is empty."

    corpus = _build_corpus(settings.knowledge_dir)
    if not corpus:
        return "Knowledge base is empty."

    client = EntityClient(settings)
    response = client.create_turn(
        model=Models.FAST,
        system=[{"type": "text", "text": SYSTEM}],
        messages=[
            {
                "role": "user",
                "content": f"KNOWLEDGE FILES:\n\n{corpus}\n\n---\n\nQUESTION: {question}",
            }
        ],
        max_tokens=1024,
    )
    return "".join(
        getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text"
    ).strip()


def try_ask(question: str, settings: Settings, identity_text: str) -> str | None:
    """Single Haiku probe against the knowledge corpus.

    Returns the answer text, or None if Haiku declined (PASS sentinel).
    Skipped silently (returns None) when the corpus is empty or identity is blank.
    """
    question = question.strip()
    if not question:
        return None
    if not identity_text.strip():
        return None

    corpus = _build_corpus(settings.knowledge_dir)
    if not corpus:
        return None

    system_text = TRY_ASK_SYSTEM_TEMPLATE.format(
        identity=identity_text.strip(), corpus=corpus
    )

    client = EntityClient(settings)
    response = client.create_turn(
        model=Models.FAST,
        system=[{"type": "text", "text": system_text}],
        messages=[{"role": "user", "content": question}],
        max_tokens=1024,
    )
    text = "".join(
        getattr(b, "text", "") for b in response.content if getattr(b, "type", "") == "text"
    ).strip()
    if text == PASS_SENTINEL:
        return None
    return text


def _build_corpus(knowledge_dir: Path) -> str:
    if not knowledge_dir.exists():
        return ""
    blocks: list[str] = []
    for f in sorted(knowledge_dir.glob("*.md")):
        if f.name == INDEX_FILENAME or ".archive" in str(f):
            continue
        blocks.append(f"## {f.name}\n\n{f.read_text(encoding='utf-8').strip()}")
    return "\n\n---\n\n".join(blocks)
