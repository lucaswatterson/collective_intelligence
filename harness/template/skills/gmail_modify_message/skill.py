from harness.integrations.gmail import get_service


def run(**input):
    message_id = input["message_id"]
    add = list(input.get("add_label_ids") or [])
    remove = list(input.get("remove_label_ids") or [])

    if input.get("archive"):
        if "INBOX" not in remove:
            remove.append("INBOX")

    mark_read = input.get("mark_read")
    if mark_read is True and "UNREAD" not in remove:
        remove.append("UNREAD")
    elif mark_read is False and "UNREAD" not in add:
        add.append("UNREAD")

    if not add and not remove:
        return "No changes requested."

    service = get_service()
    body = {}
    if add:
        body["addLabelIds"] = add
    if remove:
        body["removeLabelIds"] = remove

    updated = service.users().messages().modify(
        userId="me", id=message_id, body=body,
    ).execute()
    labels = ", ".join(updated.get("labelIds", []))
    parts = []
    if add:
        parts.append(f"added: {add}")
    if remove:
        parts.append(f"removed: {remove}")
    return f"Modified {message_id} ({'; '.join(parts)}). Current labels: {labels}"
