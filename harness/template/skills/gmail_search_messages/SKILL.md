---
description: Search Gmail messages using standard Gmail search syntax (e.g. "is:unread",
  "from:alice@example.com newer_than:1d", "label:important"). Returns compact
  summaries with message and thread IDs.
input_schema:
  type: object
  properties:
    query:
      description: Gmail search query string. Empty string lists recent messages.
      type: string
    max_results:
      description: Maximum number of messages to return. Defaults to 20, max 100.
      type: integer
    label_ids:
      description: Optional label IDs to restrict the search to. Use gmail_list_labels to resolve names.
      type: array
      items:
        type: string
  required:
  - query
---

## Usage

Use Gmail's native query syntax. Common operators:
- `is:unread`, `is:starred`, `is:important`
- `from:`, `to:`, `cc:`, `subject:`
- `newer_than:1d`, `older_than:7d`, `after:2026/01/01`
- `has:attachment`, `label:<name>`, `category:primary`

The returned `id` and `threadId` feed directly into `gmail_read_message` and `gmail_read_thread`.
