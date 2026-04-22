---
description: Read a file from the entity directory by relative path. Returns the file
  contents as a string.
input_schema:
  properties:
    path:
      description: File path relative to the entity/ root
      type: string
  required:
  - path
  type: object
---

## Usage

Read any text file under `entity/`. Useful for loading work artifacts like READMEs before processing them.

```
read_file(path="work/my-task/README.md")
```
