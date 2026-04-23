from harness.integrations.gmail import get_service


def run(**input):
    draft_id = input["draft_id"]
    service = get_service()
    sent = service.users().drafts().send(
        userId="me", body={"id": draft_id},
    ).execute()
    return f"Sent draft {draft_id}: message id={sent.get('id')} thread={sent.get('threadId')}"
