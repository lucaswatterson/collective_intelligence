from harness.integrations.gmail import format_message_full, get_service


def run(**input):
    thread_id = input["thread_id"]
    service = get_service()
    thread = service.users().threads().get(
        userId="me", id=thread_id, format="full",
    ).execute()
    messages = thread.get("messages", [])
    if not messages:
        return f"Thread {thread_id} has no messages."
    header = f"Thread {thread_id} — {len(messages)} message(s):\n\n"
    return header + ("\n\n---\n\n".join(format_message_full(m) for m in messages))
