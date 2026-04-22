import datetime
import os
import re

import anthropic


_WIDTH = 40
_ART_PROMPT = (
    "Make a tiny ASCII-art self-image for a persistent AI entity named "
    "{name}, plus a short pun or joke underneath.\n\n"
    "Strict output rules:\n"
    "- First: plain ASCII art, at most 8 rows, at most 28 columns wide. Use "
    "  only printable ASCII (no ANSI codes, no unicode box-drawing, no "
    "  emoji).\n"
    "- Then one blank line.\n"
    "- Then one pun, joke, or witty one-liner on a single line. Theme: AI, "
    "  entities, memory, persistence, loops, or the filesystem. Keep under "
    "  {width} characters.\n"
    "- Output nothing else: no preamble, no explanation, no code fences, no "
    "  commentary.\n"
)
_NAME_FALLBACK = "entity"


def _entity_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _resolve_entity_name(override: str | None, entity_dir: str) -> str:
    if override and override.strip():
        return override.strip()
    identity_path = os.path.join(entity_dir, "IDENTITY.md")
    if not os.path.exists(identity_path):
        return _NAME_FALLBACK
    with open(identity_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^#\s+(.+?)\s*$", line)
            if m:
                return m.group(1).strip()
    return _NAME_FALLBACK


def _center(line: str, width: int) -> str:
    if len(line) >= width:
        return line
    pad = (width - len(line)) // 2
    return (" " * pad) + line


def _archive_existing(image_path: str, entity_dir: str) -> None:
    if not os.path.exists(image_path):
        return
    archive_dir = os.path.join(entity_dir, "images", "self_images")
    os.makedirs(archive_dir, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    with open(image_path, "r", encoding="utf-8") as f:
        old = f.read()
    with open(os.path.join(archive_dir, f"self_image_{ts}.txt"), "w", encoding="utf-8") as f:
        f.write(old)


def _generate_art_and_pun(name: str) -> str:
    client = anthropic.Anthropic()
    prompt = _ART_PROMPT.format(name=name, width=_WIDTH)
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    parts = [b.text for b in resp.content if b.type == "text"]
    return "".join(parts).strip("\n")


def run(**input):
    entity_dir = _entity_dir()
    image_path = os.path.join(entity_dir, "self_image.txt")
    name = _resolve_entity_name(input.get("entity_name"), entity_dir)

    _archive_existing(image_path, entity_dir)

    body = _generate_art_and_pun(name)

    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    footer = _center(f"[{name} - collective intelligence - {timestamp}]", _WIDTH)
    full = f"{body}\n\n{footer}\n"

    with open(image_path, "w", encoding="utf-8") as f:
        f.write(full)

    return f"Self-image refreshed.\n\n{full}"
