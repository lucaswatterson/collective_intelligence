from datetime import datetime, timezone

from harness.config import load_settings


GUARD_CHARS = 200


def run(**input):
    new_identity = input["new_identity"]
    reason = input["reason"]
    prior_snippet = input["prior_snippet"]

    settings = load_settings()
    identity_path = settings.identity_path
    history_path = settings.identity_history_path

    if not identity_path.exists():
        return "IDENTITY.md does not exist. This skill is for revising an existing identity, not birth."

    current = identity_path.read_text(encoding="utf-8")

    expected = prior_snippet.strip()
    actual_prefix = current.lstrip()[: len(expected)] if expected else ""
    if expected != actual_prefix:
        real_prefix = current.lstrip()[:GUARD_CHARS]
        return (
            "Clobber guard failed — your prior_snippet does not match the current IDENTITY.md prefix. "
            "Read IDENTITY.md first, then retry.\n\n"
            f"Current prefix (first {GUARD_CHARS} chars, stripped):\n\n{real_prefix}"
        )

    ts = datetime.now(timezone.utc).isoformat()
    history_entry = f"## {ts} — {reason.strip()}\n\n{current.rstrip()}\n\n---\n\n"
    if history_path.exists():
        with history_path.open("a", encoding="utf-8") as f:
            f.write(history_entry)
    else:
        history_path.write_text(
            "# IDENTITY history\n\nEach entry preserves the prior IDENTITY.md before it was replaced.\n\n"
            + history_entry,
            encoding="utf-8",
        )

    identity_path.write_text(new_identity, encoding="utf-8")

    return (
        "IDENTITY.md updated. Prior version appended to IDENTITY_HISTORY.md. "
        "The new system prompt takes effect on your next turn."
    )
