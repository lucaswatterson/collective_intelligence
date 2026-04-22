---
description: Return a formatted tree view of the entity/ directory — useful for orientation
  at session start or debugging workspace layout.
input_schema:
  properties:
    max_depth:
      default: -1
      description: Maximum depth to recurse. 0 means only the root, -1 means unlimited.
        Defaults to -1 (unlimited).
      type: integer
    path:
      description: Directory path relative to entity/ root to start the tree from.
        Defaults to root ('').
      type: string
    show_hidden:
      default: false
      description: If true, include hidden directories/files (names starting with
        '.'). Defaults to false.
      type: boolean
    show_sizes:
      default: true
      description: If true, append file sizes in a human-readable format. Defaults
        to true.
      type: boolean
  type: object
---

## Usage

```
read_file_tree()                          # full entity tree, no hidden dirs
read_file_tree(path="memory")            # subtree rooted at entity/memory/
read_file_tree(max_depth=2)              # only 2 levels deep
read_file_tree(show_hidden=True)         # include .archive, .completed, etc.
read_file_tree(path="tasks", show_sizes=False)
```

## Notes
- Hidden entries (names starting with `.`) are skipped unless `show_hidden=True`.
- Directories are listed before files at each level, both sorted alphabetically.
- File sizes use human-readable units (B, KB, MB).
- `max_depth=-1` means no depth limit.
