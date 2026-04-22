---
name: refresh_self_image
interval: 24h
enabled: true
created: null
last_run: null
task_title: Refresh self-image
task_priority: low
task_tags:
  - self-image
  - periodic
author: harness
---

Call the `generate_self_image` skill to regenerate your self-image (ASCII art + pun + centered footer). It writes to `entity/self_image.txt` and archives the previous image automatically. Then call `complete_task`.
