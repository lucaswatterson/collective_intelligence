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
    message = {"raw": raw}
    if thread_id:
        message["threadId"] = thread_id

    draft = service.users().drafts().create(
        userId="me", body={"message": message},
    ).execute()
    msg = draft.get("message", {})
    return (
        f"Draft created id={draft.get('id')} "
        f"message_id={msg.get('id')} thread={msg.get('threadId')}"
    )
