---
description: List all Gmail labels for the authenticated user. Returns each
  label's ID, display name, and type (system or user).
input_schema:
  type: object
  properties: {}
---

## Usage

Use this to resolve human-readable label names (e.g. "Important",
"Receipts/2026") to the label IDs required by `gmail_search_messages` and
`gmail_modify_message`.

System labels like `INBOX`, `UNREAD`, `STARRED`, `SPAM`, `TRASH`, and the
category labels (`CATEGORY_PERSONAL`, `CATEGORY_PROMOTIONS`, etc.) use their
uppercase name as the ID.
