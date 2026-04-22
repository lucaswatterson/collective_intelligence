---
description: List files in a directory under entity/. Returns filenames, sizes, and
  modification times. Supports optional glob pattern and recursive mode.
input_schema:
  properties:
    path:
      description: Directory path relative to the entity/ root (e.g. 'work', 'images/self_images').
      type: string
    pattern:
      description: Optional glob pattern to filter results (e.g. '*.md', '*.txt').
        Defaults to '*'.
      type: string
    recursive:
      description: If true, recurse into subdirectories. Defaults to false.
      type: boolean
  required:
  - path
  type: object
---

## Usage

```
list_files(path="work")
list_files(path="images/self_images", pattern="*.txt")
list_files(path="memory/long_term", pattern="*.md", recursive=false)
```

## Notes

- Path is relative to `entity/` — cannot escape the entity directory.
- Hidden directories (names starting with `.`) are skipped in recursive mode.
- Returns a formatted table with name, size, and last-modified time.
- If the directory doesn't exist, returns a clear error.
