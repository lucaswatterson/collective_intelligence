from datetime import datetime
from pathlib import Path


def start_session(short_term_dir: Path) -> Path:
    short_term_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    path = short_term_dir / f"{stamp}.md"
    path.write_text(f"# Session {stamp}\n\n", encoding="utf-8")
    return path


def append_turn(transcript: Path, role: str, content: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    with transcript.open("a", encoding="utf-8") as f:
        f.write(f"## {role} ({timestamp})\n\n{content.strip()}\n\n")


def recent_transcripts(short_term_dir: Path, limit: int = 3) -> list[str]:
    if not short_term_dir.exists():
        return []
    files = sorted(short_term_dir.glob("*.md"), reverse=True)[:limit]
    return [f.read_text(encoding="utf-8") for f in reversed(files)]
