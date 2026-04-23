from harness.integrations.gmail import (
    build_raw_message,
    get_service,
    lookup_message_id_header,
)


def run(**input):
    to = input["to"]
    subject = input["subject"]
    body = input["body"]
    cc = input.get("cc")
    bcc = input.get("bcc")
    in_reply_to_id = input.get("in_reply_to_message_id")
    thread_id = input.get("thread_id")

    service = get_service()

    in_reply_to_header = None
    if in_reply_to_id:
        in_reply_to_header = lookup_message_id_header(service, in_reply_to_id)

    raw = build_raw_message(
        to=to, subject=subject, body=body, cc=cc, bcc=bcc,
        in_reply_to_header=in_reply_to_header,
    )
    payload = {"raw": raw}
    if thread_id:
        payload["threadId"] = thread_id

    sent = service.users().messages().send(userId="me", body=payload).execute()
    return f"Sent message id={sent.get('id')} thread={sent.get('threadId')}"
