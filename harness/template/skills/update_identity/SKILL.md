---
description: Revise IDENTITY.md (your system prompt on every run). Appends the prior
  content to IDENTITY_HISTORY.md with a timestamp and your stated reason. Includes
  a clobber guard — you must pass the first ~200 chars of the current IDENTITY.md
  verbatim, forcing you to read it first.
input_schema:
  properties:
    new_identity:
      description: Full markdown content to write to IDENTITY.md. Replaces the file
        in its entirety. Write in the first person.
      type: string
    reason:
      description: One-line rationale for this change. Recorded in IDENTITY_HISTORY.md.
      type: string
    prior_snippet:
      description: The first ~200 characters of the current IDENTITY.md (verbatim —
        leading/trailing whitespace will be stripped before comparison). Clobber guard
        — if this doesn't match, the write is refused.
      type: string
  required:
  - new_identity
  - reason
  - prior_snippet
  type: object
---

## Usage

### When to call this
- Only during reflection, when you've decided something about who you are has genuinely shifted — not for every small preference. Those go in long-term memory (`category: self`).
- After you have read the current IDENTITY.md in this turn. Do not trust the version you remember from earlier in the conversation.

### What happens
1. Current IDENTITY.md is read.
2. `prior_snippet` is checked against the current content's prefix. Mismatch → write is refused with the current real prefix surfaced.
3. Current content + timestamp + `reason` are appended to `entity/IDENTITY_HISTORY.md`.
4. `new_identity` is written to IDENTITY.md.
5. The in-session system prompt is reloaded. Your next turn runs under the new identity.

### Notes
- History is append-only. The full prior text is preserved, so you can always look back at who you used to be.
- If you want to sketch a revision before committing, write it to a note first via `create_note` and iterate.
