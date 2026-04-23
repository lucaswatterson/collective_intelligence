from harness.integrations.gmail import format_message_summary, get_service


def run(**input):
    query = input.get("query", "")
    max_results = min(int(input.get("max_results") or 20), 100)
    label_ids = input.get("label_ids") or None

    service = get_service()
    req = service.users().messages().list(
        userId="me", q=query, maxResults=max_results, labelIds=label_ids,
    )
    resp = req.execute()
    messages = resp.get("messages", [])
    if not messages:
        return f"No messages matched query: {query!r}"

    summaries = []
    for m in messages:
        full = service.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "To", "Date", "Subject"],
        ).execute()
        summaries.append(format_message_summary(full))
    header = f"{len(summaries)} message(s) for query {query!r}:\n\n"
    return header + "\n\n".join(summaries)
