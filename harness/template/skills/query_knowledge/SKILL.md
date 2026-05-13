---
description: Ask a question and retrieve relevant facts from entity/knowledge/. Uses Haiku to pick the most relevant files from the knowledge index and returns their full contents so you can answer with grounded information.
input_schema:
  type: object
  properties:
    question:
      type: string
      description: A natural-language question whose answer may be in the knowledge base.
  required: [question]
---

## When to use

- The user asked something factual that might be covered by curated knowledge (preferences, project facts, references, "ground truth" the human has dropped into `entity/knowledge/`).
- Use this **before** answering from prior knowledge or guessing — knowledge files are authoritative.

## When not to use

- For self-derived recollection or session continuity — use `manage_memory` (action `read`/`list`) for that. Knowledge is human-curated ground truth; memory is what you've learned about yourself and your collaborators.
- For project artifacts you've produced — those live under `notes/`, `work/`, or `files/`.

## Behavior

- The skill auto-rebuilds `knowledge/INDEX.md` if it is missing or out of date.
- If no files appear relevant, you'll get back a short "no match" message and should answer without the knowledge base.
- Returned content includes the filename of each cited file; quote it when you reference a fact so the human can audit.
