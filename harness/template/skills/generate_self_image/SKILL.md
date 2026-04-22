---
description: Generate a creative ANSI color painting for Alex Wayfarer — landscapes,
  cityscapes, space, or self-portrait. Saves the current image to entity/images/self_images/
  before generating a new one. Styles rotate randomly.
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
      - portrait
      - city
      - space
      - tundra
      type: string
  type: object
---

## Styles

- **mountain** — alpine peaks, snow, pine trees, sky
- **ocean** — seascape with horizon, waves, sun, sand
- **forest** — woodland canopy, trunks, undergrowth
- **desert** — mesa landscape, dunes, cacti, warm or cool sky
- **meadow** — rolling hills, wildflowers, open sky
- **portrait** — self-portrait of Alex Wayfarer: blue-teal face, cyan eyes, dark hair, sci-fi accent particles
- **city** — night cityscape with building silhouettes, lit windows, neon signs, moon
- **space** — deep space with nebula clouds, stars, planet (optional rings + shooting star)
- **tundra** — icy landscape under aurora borealis, ice formations, night sky

## Notes

- Uses ANSI 256-color escape codes. Best viewed in a terminal.
- All art is algorithmically generated — no hardcoded strings.
- Archives the previous `entity/self_image.txt` to `entity/images/self_images/` before writing.
- Randomly picks a style unless `style` is specified.
- Portrait uses Alex's consistent identity palette (blue-teal, cyan eyes) with random background variation each run.
