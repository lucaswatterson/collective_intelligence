---
description: Generate a creative ANSI color landscape painting for Alex Wayfarer.
  Saves the current image to entity/images/self_images/ before generating a new one.
  Styles rotate randomly.
input_schema:
  properties:
    style:
      description: Optional style override.
      enum:
      - mountain
      - ocean
      - forest
      - desert
      - meadow
      type: string
  type: object
---

## Styles

- **mountain** — alpine peaks, snow, pine trees, sky
- **ocean** — seascape with horizon, waves, sun, sand
- **forest** — woodland canopy, trunks, undergrowth
- **desert** — mesa landscape, dunes, cacti, warm or cool sky
- **meadow** — rolling hills, wildflowers, open sky

## Notes

- Uses ANSI 256-color escape codes. Best viewed in a terminal.
- All art is algorithmically generated — no hardcoded strings.
- Archives the previous `entity/self_image.txt` to `entity/images/self_images/` before writing.
- Randomly picks a style unless `style` is specified.
