from harness.integrations.gmail import format_message_full, get_service


def run(**input):
    message_id = input["message_id"]
    service = get_service()
    msg = service.users().messages().get(
        userId="me", id=message_id, format="full",
    ).execute()
    return format_message_full(msg)
