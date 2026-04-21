---
description: List long-term memories in entity/memory/long_term/, optionally filtered
  by category or tags. Without filters, returns the contents of INDEX.md.
input_schema:
  properties:
    category:
      description: Optional category filter.
      enum:
      - user
      - self
      - collaboration
      - lesson
      - reference
      type: string
    tags:
      description: Optional tag filter. Returns memories that match ANY supplied tag.
      items:
        type: string
      type: array
  type: object
---

## Usage

- No args → returns INDEX.md verbatim (cheap, pre-rendered).
- With `category` and/or `tags` → returns a filtered listing with title, filename, category, confidence, tags.
