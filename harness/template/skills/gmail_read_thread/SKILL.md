---
description: Fetch an entire Gmail thread by ID. Returns all messages in
  chronological order with decoded plaintext bodies.
input_schema:
  type: object
  properties:
    thread_id:
      description: Gmail thread ID (from gmail_search_messages).
      type: string
  required:
  - thread_id
---

## Usage

Use this when context across a multi-message conversation matters. For a
single message use `gmail_read_message`.
