from harness.integrations.gmail import get_service


def run(**input):
    query = input.get("query") or None
    max_results = min(int(input.get("max_results") or 20), 100)

    service = get_service()
    resp = service.users().drafts().list(
        userId="me", q=query, maxResults=max_results,
    ).execute()
    drafts = resp.get("drafts", [])
    if not drafts:
        return "No drafts found." + (f" (query: {query!r})" if query else "")

    lines = []
    for d in drafts:
        draft_id = d.get("id")
        msg_stub = d.get("message", {})
        msg_id = msg_stub.get("id")
        thread_id = msg_stub.get("threadId")

        headers = {}
        snippet = ""
        if msg_id:
            msg = service.users().messages().get(
                userId="me", id=msg_id, format="metadata",
                metadataHeaders=["From", "To", "Cc", "Date", "Subject"],
            ).execute()
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            snippet = msg.get("snippet", "")

        lines.append(
            f"draft_id={draft_id} message_id={msg_id} thread={thread_id}\n"
            f"  to:      {headers.get('To', '')}\n"
            f"  cc:      {headers.get('Cc', '')}\n"
            f"  subject: {headers.get('Subject', '')}\n"
            f"  date:    {headers.get('Date', '')}\n"
            f"  snippet: {snippet}"
        )

    header = f"{len(lines)} draft(s)"
    if query:
        header += f" matching {query!r}"
    return header + ":\n\n" + "\n\n".join(lines)
