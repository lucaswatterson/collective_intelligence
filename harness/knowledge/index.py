from pathlib import Path
from typing import Any

import yaml


INDEX_FILENAME = "INDEX.md"


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except Exception:
        fm = {}
    if not isinstance(fm, dict):
        fm = {}
    return fm, parts[2]


def _gist(fm: dict[str, Any], body: str) -> str:
    gist = fm.get("gist")
    if not gist:
        for line in body.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("---"):
                gist = stripped
                break
    gist = str(gist or "").strip()
    if len(gist) > 120:
        gist = gist[:117] + "..."
    return gist


def _knowledge_files(knowledge_dir: Path) -> list[Path]:
    return sorted(
        f for f in knowledge_dir.glob("*.md")
        if f.name != INDEX_FILENAME and ".archive" not in str(f)
    )


def rebuild_index(knowledge_dir: Path) -> None:
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    index_path = knowledge_dir / INDEX_FILENAME

    lines = ["# Knowledge Index", ""]
    files = _knowledge_files(knowledge_dir)
    if not files:
        lines.append("(empty)")
    else:
        for f in files:
            try:
                fm, body = _parse_frontmatter(f.read_text(encoding="utf-8"))
            except Exception:
                fm, body = {}, ""
            title = str(fm.get("title", f.stem))
            gist = _gist(fm, body)
            suffix = f" — {gist}" if gist and gist != title else ""
            lines.append(f"- [{f.name}]({f.name}) — {title}{suffix}")

    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def rebuild_index_if_stale(knowledge_dir: Path) -> None:
    if not knowledge_dir.exists():
        return
    index_path = knowledge_dir / INDEX_FILENAME
    files = _knowledge_files(knowledge_dir)
    if not index_path.exists():
        rebuild_index(knowledge_dir)
        return
    index_mtime = index_path.stat().st_mtime
    if any(f.stat().st_mtime > index_mtime for f in files):
        rebuild_index(knowledge_dir)
