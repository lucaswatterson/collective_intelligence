---
description: Send an email from the user's Gmail account via the `gws` CLI. Requires
  `to`, `subject`, and `body`. Supports CC/BCC, HTML bodies, saving as a draft, and
  a dry-run mode that validates without sending. Requires `gws` to be installed and
  authenticated (`gws auth setup`).
input_schema:
  properties:
    to:
      type: string
      description: Recipient email address(es), comma-separated.
    subject:
      type: string
      description: Email subject line.
    body:
      type: string
      description: Email body. Plain text by default. If `html` is true, treat as
        HTML fragment (no <html>/<body> wrapper needed).
    cc:
      type: string
      description: CC address(es), comma-separated. Optional.
    bcc:
      type: string
      description: BCC address(es), comma-separated. Optional.
    html:
      type: boolean
      description: If true, send `body` as HTML. Default false.
    draft:
      type: boolean
      description: If true, save as a draft instead of sending. Default false.
    dry_run:
      type: boolean
      description: If true, validate the request locally without sending or drafting.
        Useful for previewing the exact request before committing. Default false.
  required:
  - to
  - subject
  - body
  type: object
---

## Usage

    send_email(to="alice@example.com", subject="Hello", body="Hi Alice!")
    send_email(to="alice@example.com", subject="Report", body="<b>See below</b>", html=True)
    send_email(to="alice@example.com", subject="Draft", body="WIP", draft=True)
    send_email(to="alice@example.com", subject="Test", body="Test", dry_run=True)

Returns the JSON response from `gws` on success (typically including a message id),
or a clear error string if `gws` is missing, unauthenticated, or rejects the
request.
