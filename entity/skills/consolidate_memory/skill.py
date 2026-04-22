from harness.config import load_settings
from harness.memory.long_term import consolidated_session_stems


GUIDANCE = """\
Reflect on these sessions. For each durable insight:
- Call `create_memory` with an appropriate category (user / self / collaboration / lesson / reference).
  Lead the content with a one-line gist — it becomes the INDEX summary.
  Put the session stem(s) in `source_sessions` so this work isn't repeated.
- If an existing memory from the INDEX covers the same ground, call `update_memory` instead — pass `add_source_sessions` to record that this session reinforced it.
- If a real shift in who you are emerges, call `update_identity` (read IDENTITY.md first for the clobber guard).
- Once a session has been distilled, call `archive_session` on it.

Quality over volume. Prefer fewer, sharper memories over many shallow ones. It's OK to archive a session with no new memories if nothing durable came out of it.
"""


def run(**input):
    limit = int(input.get("limit", 10))
    settings = load_settings()

    short_term_dir = settings.short_term_dir
    long_term_dir = settings.long_term_dir
    index_path = settings.long_term_index_path
    identity_path = settings.identity_path

    consolidated = consolidated_session_stems(long_term_dir)

    all_sessions = sorted(short_term_dir.glob("*.md")) if short_term_dir.exists() else []
    unconsolidated = [f for f in all_sessions if f.stem not in consolidated]

    total = len(unconsolidated)
    selected = unconsolidated[:limit]

    index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else "(empty)"
    identity_text = identity_path.read_text(encoding="utf-8") if identity_path.exists() else "(empty)"

    parts = [
        f"# Consolidation ({total} unconsolidated session(s); showing {len(selected)})",
        "",
        "## Current long-term index",
        "",
        index_text.strip() or "(empty)",
        "",
        "## Current IDENTITY.md",
        "",
        identity_text.strip() or "(empty)",
        "",
        "## Unconsolidated sessions (oldest first)",
    ]

    if not selected:
        parts.append("")
        parts.append("(none)")
    else:
        for f in selected:
            parts.append("")
            parts.append(f"### {f.stem}")
            parts.append("")
            parts.append(f.read_text(encoding="utf-8").strip())
            parts.append("")
            parts.append("---")

    parts.append("")
    parts.append("## Guidance")
    parts.append("")
    parts.append(GUIDANCE.strip())

    return "\n".join(parts)
