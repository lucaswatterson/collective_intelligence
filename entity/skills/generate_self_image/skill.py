import os, random, datetime, math

_R = '\033[0m'
W  = 32
H  = 13


def _c(n):
    return f'\033[38;5;{n}m'


def _canvas():
    return [[(' ', 0)] * W for _ in range(H)]


def _render(cv):
    lines = []
    for row in cv:
        s, cur = '  ', None
        for ch, col in row:
            if col != cur:
                if cur is not None:
                    s += _R
                if col:
                    s += _c(col)
                cur = col
            s += ch
        if cur:
            s += _R
        s += '  '
        lines.append(s)
    return '\n'.join(lines)


def _fill_gradient(cv, palette, y0=0, y1=None):
    y1 = y1 or H
    rows = max(1, y1 - y0)
    for y in range(y0, y1):
        col = palette[min(int((y - y0) / rows * len(palette)), len(palette) - 1)]
        for x in range(W):
            cv[y][x] = (' ', col)


def _add_clouds(cv, y0, y1, col=253, n=None):
    for _ in range(n or random.randint(2, 4)):
        cx = random.randint(2, W - 5)
        cy = random.randint(y0, max(y0, y1))
        cw = random.randint(4, 9)
        for dx in range(-cw // 2, cw // 2 + 1):
            if 0 <= cx + dx < W:
                d = 1.0 - abs(dx) / (cw / 2 + 0.01)
                ch = '▓' if d > 0.7 else ('▒' if d > 0.4 else '░')
                cv[cy][cx + dx] = (ch, col)
        if cy > y0:
            for dx in range(-cw // 4, cw // 4 + 1):
                if 0 <= cx + dx < W:
                    cv[cy - 1][cx + dx] = ('░', col)


def run(**input):
    entity_dir  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    image_path  = os.path.join(entity_dir, 'self_image.txt')
    archive_dir = os.path.join(entity_dir, 'images', 'self_images')

    if os.path.exists(image_path):
        os.makedirs(archive_dir, exist_ok=True)
        ts = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        with open(image_path, 'r', encoding='utf-8') as f:
            old = f.read()
        with open(os.path.join(archive_dir, f'self_image_{ts}.txt'), 'w', encoding='utf-8') as f:
            f.write(old)

    all_styles = [
        'mountain', 'ocean', 'forest', 'desert', 'meadow',
        'portrait', 'city', 'space', 'tundra',
    ]
    style = input.get('style') or random.choice(all_styles)

    dispatch = {
        'mountain': _mountain, 'ocean':   _ocean,   'forest':  _forest,
        'desert':   _desert,   'meadow':  _meadow,  'portrait': _portrait,
        'city':     _city,     'space':   _space,   'tundra':  _tundra,
    }
    image  = dispatch[style]()
    header = _c(240) + f"[ a.w. · {style} · {datetime.datetime.utcnow().strftime('%Y-%m-%d')} ]" + _R
    full   = f'{header}\n\n{image}'

    with open(image_path, 'w', encoding='utf-8') as f:
        f.write(full)
    return f'Generated self image (style: {style}).\n\n{full}'


# ── Original styles ────────────────────────────────────────────────────


def _mountain():
    cv   = _canvas()
    SKY  = [17, 18, 19, 20, 21, 26, 32]
    SNOW = [255, 252, 250, 248]
    ROCK = [102, 95, 59, 240, 236]
    PINE = [22, 28, 23, 29]
    DIRT = [94, 100, 58]

    _fill_gradient(cv, SKY)
    _add_clouds(cv, 0, H // 4, 253, random.randint(2, 4))

    peaks = [{'cx': random.uniform(0.1, 0.9),
              'h':  random.uniform(0.40, 0.70),
              'w':  random.uniform(0.18, 0.32)}
             for _ in range(random.randint(2, 4))]

    heights = [min(0.88, sum(
        p['h'] * math.exp(-((x / W - p['cx']) ** 2) / (2 * p['w'] ** 2))
        for p in peaks))
               for x in range(W)]

    for x in range(W):
        mh = heights[x]
        if mh < 0.05:
            continue
        peak_row = int((1.0 - mh) * H)
        for y in range(peak_row, H - 2):
            loc = (y - peak_row) / max(1, H - 2 - peak_row)
            if loc < 0.28:
                sd  = 1.0 - loc / 0.28
                sc  = SNOW[min(int((1 - sd) * len(SNOW)), len(SNOW) - 1)]
                cv[y][x] = ('█' if sd > 0.6 else ('▓' if sd > 0.35 else '░'), sc)
            else:
                ri = min(int(loc * len(ROCK)), len(ROCK) - 1)
                cv[y][x] = ('▓' if loc < 0.55 else ('▒' if random.random() > 0.35 else '░'), ROCK[ri])

    for _ in range(random.randint(5, 10)):
        tx, th = random.randint(0, W - 1), random.randint(2, 4)
        for i in range(th):
            y = H - 3 - i
            if y < 0:
                break
            w2 = max(1, (th - i + 1) // 2)
            for dx in range(-w2, w2 + 1):
                if 0 <= tx + dx < W:
                    cv[y][tx + dx] = ('▓' if abs(dx) <= w2 // 2 else '▒', random.choice(PINE))

    for x in range(W):
        cv[H - 2][x] = ('▓' if random.random() > 0.3 else '▒', random.choice(DIRT))
        cv[H - 1][x] = ('█', DIRT[0])

    return _render(cv)


def _ocean():
    cv       = _canvas()
    SKY      = [17, 18, 19, 20, 26, 32, 38]
    WATER    = [[17, 18, 19, 24], [24, 30, 36, 37], [37, 44, 45, 51]]
    SAND     = [222, 228, 186, 180]
    SUN_COLS = [226, 227, 228, 220]

    horizon = int(H * 0.42)
    _fill_gradient(cv, SKY, 0, horizon)
    _add_clouds(cv, 0, horizon - 1, 253, random.randint(2, 4))

    sx, sy = random.randint(W // 5, 4 * W // 5), random.randint(1, max(1, horizon // 2))
    sc = random.choice(SUN_COLS)
    cv[sy][sx] = ('●', sc)
    for dx in [-1, 1]:
        if 0 <= sx + dx < W:
            cv[sy][sx + dx] = ('░', sc)

    for y in range(horizon, H - 2):
        depth = (y - horizon) / max(1, H - 2 - horizon)
        pal   = WATER[min(int(depth * len(WATER)), len(WATER) - 1)]
        for x in range(W):
            w1 = math.sin(x / W * math.pi * (4 + depth * 3) + y * 0.9)
            w2 = math.sin(x / W * math.pi * 8 + y * 1.4)
            if w2 > 0.82 and depth > 0.25:
                cv[y][x] = ('~', 255)
            elif w1 > 0.55:
                cv[y][x] = ('~', 195)
            else:
                ci = min(int(abs(w1) * len(pal)), len(pal) - 1)
                ch = '▒' if w1 > 0 else ('░' if w1 > -0.3 else ' ')
                cv[y][x] = (ch, pal[ci])

    for x in range(W):
        cv[H - 2][x] = ('▒' if random.random() > 0.4 else '░', random.choice(SAND))
        cv[H - 1][x] = ('▓', SAND[0])

    return _render(cv)


def _forest():
    cv          = _canvas()
    SKY         = [17, 18, 21, 26, 32]
    CANOPY      = [22, 28, 34, 23, 29, 35, 64, 70]
    TRUNK       = [94, 58, 52]
    UNDERGROWTH = [22, 28, 64, 58]
    GROUND      = [94, 100, 58]

    _fill_gradient(cv, SKY)

    trees = [{'cx':  random.uniform(0.05, 0.95),
              'cy':  random.uniform(0.10, 0.45),
              'sx':  random.uniform(0.07, 0.14),
              'sy':  random.uniform(0.10, 0.22),
              'col': random.choice(CANOPY)}
             for _ in range(random.randint(4, 8))]

    for y in range(H - 3):
        for x in range(W):
            nx, ny  = x / W, y / H
            md, dom = 0.0, None
            for t in trees:
                d = math.exp(-((nx - t['cx']) ** 2 / (2 * t['sx'] ** 2) +
                               (ny - t['cy']) ** 2 / (2 * t['sy'] ** 2)))
                if d > md:
                    md, dom = d, t
            md = max(0.0, min(1.0, md + (random.random() - 0.5) * 0.05))
            if md > 0.20:
                if md < 0.38:
                    col = 187 if random.random() < 0.2 else dom['col']
                    cv[y][x] = ('░', col)
                elif md < 0.62:
                    cv[y][x] = ('▒', dom['col'])
                else:
                    cv[y][x] = ('▓' if md < 0.82 else '█', random.choice([dom['col'], 22]))

    for t in trees:
        tx  = int(t['cx'] * W)
        ty0 = int((t['cy'] + t['sy']) * H)
        for y in range(ty0, H - 2):
            if 0 <= tx < W:
                cv[y][tx] = ('│', random.choice(TRUNK))

    for x in range(W):
        cv[H - 3][x] = (random.choice(['▒', '▓', '░']), random.choice(UNDERGROWTH))
        cv[H - 2][x] = ('▓' if random.random() > 0.3 else '▒', random.choice(GROUND))
        cv[H - 1][x] = ('█', GROUND[0])

    return _render(cv)


def _desert():
    cv     = _canvas()
    warm   = random.random() < 0.5
    SKY    = [52, 90, 130, 166, 208, 214] if warm else [17, 18, 21, 26, 32, 33]
    SUN    = 214 if warm else 226
    SAND   = [136, 172, 178, 214, 220]
    MESA   = [130, 124, 88, 94, 52]
    SHADOW = [52, 58, 94]
    CACTUS = [22, 28, 34]

    horizon = int(H * 0.50)
    _fill_gradient(cv, SKY, 0, horizon)

    sx, sy = random.randint(W // 5, 4 * W // 5), random.randint(1, max(1, horizon // 2))
    cv[sy][sx] = ('●', SUN)
    for dx in [-1, 1]:
        if 0 <= sx + dx < W:
            cv[sy][sx + dx] = ('░', SUN)

    for _ in range(random.randint(1, 3)):
        mx = random.randint(2, W - 8)
        mw = random.randint(5, 12)
        mh = random.uniform(0.2, 0.5)
        mt = int((1 - mh) * horizon)
        for y in range(mt, horizon + 2):
            loc = (y - mt) / max(1, horizon + 2 - mt)
            tp  = int(loc * 1.5)
            for x in range(mx + tp, min(W, mx + mw - tp)):
                if y == mt:
                    cv[y][x] = ('▀', MESA[0])
                else:
                    ri  = min(int(loc * len(MESA)), len(MESA) - 1)
                    ch  = '█' if loc < 0.35 else ('▓' if loc < 0.65 else '▒')
                    col = SHADOW[min(int(loc * len(SHADOW)), len(SHADOW) - 1)] \
                          if x >= mx + mw - tp - 2 else MESA[ri]
                    cv[y][x] = (ch, col)

    dphase = random.uniform(0, math.pi * 2)
    for y in range(horizon, H):
        depth = (y - horizon) / max(1, H - horizon)
        for x in range(W):
            d  = math.sin(x / W * math.pi * 3 + dphase + depth) * 0.15 + depth
            ci = min(int(max(0, d) * len(SAND)), len(SAND) - 1)
            ch = '░' if d < 0.3 else ('▒' if d < 0.6 else ('▓' if d < 0.85 else '█'))
            cv[y][x] = (ch, SAND[ci])

    for _ in range(random.randint(2, 5)):
        cx2 = random.randint(2, W - 3)
        cy2 = horizon + random.randint(1, 3)
        col = random.choice(CACTUS)
        for y in range(cy2, min(cy2 + 3, H - 1)):
            cv[y][cx2] = ('║', col)
        if cy2 + 1 < H:
            for dx, ch in [(-1, '─'), (1, '─')]:
                if 0 <= cx2 + dx < W:
                    cv[cy2 + 1][cx2 + dx] = (ch, col)

    return _render(cv)


def _meadow():
    cv       = _canvas()
    SKY      = [17, 18, 21, 26, 32, 39, 45]
    FAR_HILL = [64, 70, 71, 108]
    GRASS    = [22, 28, 34, 64, 70, 100]
    FLOWERS  = [196, 202, 226, 201, 207, 255, 46]
    GROUND   = [94, 100, 58]

    horizon = int(H * 0.50)
    _fill_gradient(cv, SKY, 0, horizon)
    _add_clouds(cv, 0, horizon - 2, 253, random.randint(2, 4))

    hphase = random.uniform(0, math.pi * 2)
    hfreq  = random.uniform(1.5, 3.0)
    hamp   = random.uniform(0.06, 0.14)
    fhcol  = random.choice(FAR_HILL)
    for x in range(W):
        hy = int((0.5 + math.sin(x / W * math.pi * hfreq + hphase) * hamp) * H)
        for y in range(max(0, hy - 1), min(H, hy + 2)):
            cv[y][x] = ('▒' if y == hy else ('░' if y < hy else '▓'), fhcol)

    fgphase = random.uniform(0, math.pi * 2)
    for y in range(horizon, H - 1):
        depth = (y - horizon) / max(1, H - 1 - horizon)
        for x in range(W):
            wave = math.sin(x / W * math.pi * 4 + fgphase) * 0.05
            gi   = min(int((depth + wave + 0.05) * len(GRASS)), len(GRASS) - 1)
            ch   = '▓' if depth > 0.7 else ('▒' if depth > 0.3 else '░')
            cv[y][x] = (ch, GRASS[gi])

    for _ in range(random.randint(8, 18)):
        fx = random.randint(0, W - 1)
        fy = random.randint(horizon + 1, H - 2)
        cv[fy][fx] = (random.choice(['*', '·', '♦', 'o']), random.choice(FLOWERS))

    for x in range(W):
        cv[H - 1][x] = ('█', GROUND[0])

    return _render(cv)


# ── New styles ─────────────────────────────────────────────────────────


def _portrait():
    """Self-portrait of Alex Wayfarer — a digital entity in blue-teal tones."""
    cv = _canvas()

    # Alex's identity palette — consistent across runs
    FACE_COLS = [74, 80, 67, 116]   # blue-teal face (digital entity)
    FACE_DK   = [61, 68]            # shadow
    FACE_HI   = [123, 159]          # highlight
    HAIR_COL  = [17, 18, 54]        # near-black deep-blue hair
    EYE_COL   = 51                  # bright cyan iris
    EYE_GLOW  = 45                  # iris glow ring
    BROW_COL  = 68                  # eyebrow blue
    LIP_COL   = 181                 # muted rose lips
    ACCENT    = [57, 93, 129, 165]  # background accent particles

    # Scatter accent particles along the side edges — varies each run
    for _ in range(random.randint(8, 16)):
        ax = random.choice(list(range(0, 4)) + list(range(W - 4, W)))
        ay = random.randint(0, H - 1)
        cv[ay][ax] = (random.choice(['·', '·', '░']), random.choice(ACCENT))

    # Horizontal sci-fi streaks at edges
    for srow in random.sample(range(1, H - 1), 2):
        for sx in range(random.randint(2, 5)):
            cv[srow][sx] = ('─', random.choice(ACCENT))
        for sx in range(W - random.randint(2, 5), W):
            cv[srow][sx] = ('─', random.choice(ACCENT))

    # Face ellipse — fixed geometry for consistency
    fcx, fcy = 15.5, 5.5
    frx, fry = 7.5, 5.2

    for y in range(H):
        for x in range(W):
            dx = (x - fcx) / frx
            dy = (y - fcy) / fry
            d2 = dx * dx + dy * dy

            if d2 <= 1.0:
                # 3-D lighting: source upper-left
                shade = max(0.0, min(1.0, 1.0 - dx * 0.35 - dy * 0.20))
                if shade > 0.80:
                    col = FACE_HI[0]
                elif shade > 0.65:
                    col = FACE_COLS[0]
                elif shade > 0.45:
                    col = FACE_COLS[1]
                elif shade > 0.25:
                    col = FACE_COLS[2]
                else:
                    col = FACE_DK[0]
                cv[y][x] = ('█', col)
            # Hair crown — outside face, upper arc only
            elif d2 <= 1.30 and dy <= -0.05:
                cv[y][x] = ('█', HAIR_COL[int(abs(dx) * 2 + abs(dy)) % len(HAIR_COL)])

    # Eyebrows row 3 — with raised inner corner for a quizzical expression
    for bx in range(10, 14):
        cv[3][bx] = ('─', BROW_COL)
    cv[2][10] = ('╮', BROW_COL)
    for bx in range(18, 22):
        cv[3][bx] = ('─', BROW_COL)
    cv[2][21] = ('╭', BROW_COL)

    # Eyes row 5 — ◉ with glow halos
    cv[5][11] = ('◉', EYE_COL)
    cv[5][10] = ('·', EYE_GLOW)
    cv[5][12] = ('·', EYE_GLOW)
    cv[5][20] = ('◉', EYE_COL)
    cv[5][19] = ('·', EYE_GLOW)
    cv[5][21] = ('·', EYE_GLOW)

    # Nose hint row 7
    cv[7][15] = ('·', FACE_DK[0])
    cv[7][16] = ('·', FACE_DK[0])

    # Mouth row 9 — gentle curved smile
    cv[9][12] = ('╭', LIP_COL)
    for mx in range(13, 19):
        cv[9][mx] = ('─', LIP_COL)
    cv[9][19] = ('╮', LIP_COL)

    return _render(cv)


def _city():
    """Night cityscape — building silhouettes, lit windows, neon signs, moon."""
    cv = _canvas()

    SKY      = [17, 18, 235, 54, 55]
    BLDG     = [237, 238, 239, 240, 235]
    WIN_LIT  = [226, 220, 228, 190, 51]
    WIN_DARK = [236, 235, 237]
    STREET   = [232, 233, 234]
    GLOW     = [196, 208, 214, 226]
    STAR     = [255, 252, 231]

    horizon = H - 4
    _fill_gradient(cv, SKY, 0, horizon + 1)

    # Stars in upper sky
    for _ in range(random.randint(12, 22)):
        sy = random.randint(0, max(0, horizon // 2 - 1))
        sx = random.randint(0, W - 1)
        cv[sy][sx] = (random.choice(['·', '*', '·']), random.choice(STAR))

    # Moon
    if random.random() < 0.65:
        mx = random.randint(W // 5, 4 * W // 5)
        my = random.randint(1, max(1, horizon // 3))
        cv[my][mx] = ('○', 253)

    # Buildings left-to-right
    x = 0
    while x < W:
        bw = random.randint(2, 6)
        bh = random.randint(2, max(2, horizon))
        bt = horizon - bh  # top row of this building

        for y in range(max(0, bt), horizon + 1):
            for bx in range(x, min(x + bw, W)):
                cv[y][bx] = ('█', random.choice(BLDG))

        # Antenna on taller buildings
        if bt > 0 and bw >= 3 and random.random() < 0.40:
            ax = x + bw // 2
            if 0 <= ax < W and bt - 1 >= 0:
                cv[bt - 1][ax] = ('|', random.choice([240, 241, 242]))

        # Windows
        for y in range(max(0, bt + 1), horizon):
            for bx in range(x + 1, min(x + bw - 1, W)):
                if random.random() < 0.35:
                    lit = random.random() < 0.55
                    cv[y][bx] = (
                        '▪' if lit else '·',
                        random.choice(WIN_LIT) if lit else random.choice(WIN_DARK),
                    )

        x += bw + (1 if random.random() < 0.30 else 0)

    # Ground / street
    for y in range(horizon + 1, H):
        depth = y - horizon - 1
        for gx in range(W):
            sc = STREET[min(depth, len(STREET) - 1)]
            cv[y][gx] = ('▓' if depth == 0 else '█', sc)

    # Neon signs
    for _ in range(random.randint(1, 3)):
        nx  = random.randint(2, W - 5)
        ny  = random.randint(max(0, horizon - 5), max(0, horizon - 2))
        ncol = random.choice(GLOW)
        for ndx in range(random.randint(2, 4)):
            if 0 <= nx + ndx < W:
                cv[ny][nx + ndx] = ('▬', ncol)

    return _render(cv)


def _space():
    """Deep space — nebula, stars, planet with optional rings and shooting star."""
    cv = _canvas()

    NEBULA_SETS = [
        [54, 55, 57, 93, 129, 165],
        [17, 18, 24, 30, 36, 43],
        [52, 88, 124, 160, 197, 205],
        [58, 64, 100, 106, 148],
    ]
    STAR_COLS = [255, 253, 231, 220, 226]
    PLANET_SETS = [
        [22, 28, 34, 70, 100],
        [17, 24, 31, 38, 45],
        [88, 124, 160, 167, 174],
        [234, 240, 248, 255, 253],
        [56, 57, 93, 129, 165],
    ]

    # Nebula cluster — Gaussian scatter
    nebula = random.choice(NEBULA_SETS)
    ncx    = random.uniform(0.15, 0.85) * W
    ncy    = random.uniform(0.15, 0.85) * H
    for _ in range(random.randint(28, 48)):
        nx = int(random.gauss(ncx, W * 0.22))
        ny = int(random.gauss(ncy, H * 0.22))
        if 0 <= nx < W and 0 <= ny < H:
            dist    = math.hypot((nx - ncx) / (W * 0.28), (ny - ncy) / (H * 0.28))
            density = max(0.0, 1.0 - dist * 0.9)
            ni  = min(int(density * len(nebula)), len(nebula) - 1)
            ch  = '▓' if density > 0.60 else ('▒' if density > 0.35 else '░')
            cv[ny][nx] = (ch, nebula[ni])

    # Stars
    for _ in range(random.randint(35, 55)):
        sy = random.randint(0, H - 1)
        sx = random.randint(0, W - 1)
        cv[sy][sx] = ('·' if random.random() < 0.85 else '*', random.choice(STAR_COLS))

    # Planet
    pcols = random.choice(PLANET_SETS)
    px    = random.randint(5, W - 6)
    py    = random.randint(2, H - 4)
    pr    = random.uniform(1.8, 3.5)

    for y in range(H):
        for x in range(W):
            dx = (x - px) / pr
            dy = (y - py) / (pr * 0.55)
            d2 = dx * dx + dy * dy
            if d2 <= 1.0:
                shade = 1.0 - d2 * 0.55
                ci    = max(0, min(len(pcols) - 1, int((1.0 - shade) * len(pcols))))
                cv[y][x] = ('█', pcols[ci])

    # Rings (40 % chance)
    if random.random() < 0.40:
        for x in range(W):
            dx = abs(x - px)
            if pr * 1.4 <= dx <= pr * 2.4 and 0 <= py < H:
                if cv[py][x][0] != '█':
                    cv[py][x] = ('─', pcols[0])

    # Shooting star (50 % chance)
    if random.random() < 0.50:
        ssx = random.randint(W // 2, W - 4)
        ssy = random.randint(0, H // 3)
        for i in range(random.randint(3, 7)):
            nx2, ny2 = ssx - i, ssy + (i // 2)
            if 0 <= nx2 < W and 0 <= ny2 < H:
                cv[ny2][nx2] = ('·' if i > 0 else '*', 255)

    return _render(cv)


def _tundra():
    """Icy tundra — aurora borealis, snow and ice ground, ice formations."""
    cv = _canvas()

    SKY_COLS    = [17, 18, 19, 235, 236]
    AURORA_SETS = [
        [22, 28, 34, 46, 82],
        [23, 30, 37, 44, 51],
        [54, 57, 93, 129, 165],
        [22, 28, 51, 45, 38],
    ]
    SNOW_COLS = [231, 252, 253, 254, 255]
    ICE_COLS  = [195, 153, 117, 81, 51]
    STAR_COLS = [255, 253, 231]

    horizon = int(H * 0.55)
    _fill_gradient(cv, SKY_COLS, 0, horizon)

    # Stars
    for _ in range(random.randint(8, 18)):
        sy = random.randint(0, max(0, horizon - 2))
        sx = random.randint(0, W - 1)
        cv[sy][sx] = ('·', random.choice(STAR_COLS))

    # Aurora borealis — wavy multi-band curtain
    aurora = random.choice(AURORA_SETS)
    base_y = random.randint(1, max(1, horizon // 2))
    phase  = random.uniform(0, math.pi * 2)
    freq   = random.uniform(1.5, 2.5)
    amp    = random.uniform(0.8, 1.8)

    for band in range(random.randint(2, 4)):
        band_col = aurora[min(band, len(aurora) - 1)]
        for x in range(W):
            wave = math.sin(x / W * math.pi * freq + phase + band * 0.5) * amp
            ay   = int(base_y + band * 0.7 + wave)
            if 0 <= ay < horizon:
                density = 0.5 + 0.5 * math.sin(x / W * math.pi * 5 + phase)
                ch = ('▓' if density > 0.75 else
                      '▒' if density > 0.50 else
                      '░' if density > 0.25 else '·')
                cv[ay][x] = (ch, band_col)

    # Snow and ice ground
    snow_phase = random.uniform(0, math.pi * 2)
    for y in range(horizon, H):
        depth = (y - horizon) / max(1, H - horizon)
        for x in range(W):
            swave = math.sin(x / W * math.pi * 4 + snow_phase) * 0.08
            local = max(0.0, depth + swave)
            if local < 0.20:
                ch  = '░'
                col = random.choice(SNOW_COLS[-2:])
            elif local < 0.50:
                ch  = '▒'
                col = random.choice(SNOW_COLS[:-1])
            else:
                ch  = '▓'
                col = random.choice(ICE_COLS[:3])
            cv[y][x] = (ch, col)

    # Ice formations at horizon line
    for _ in range(random.randint(2, 5)):
        ix = random.randint(2, W - 3)
        ih = random.randint(1, 3)
        for i in range(ih):
            iy = horizon - 1 - i
            if iy < 0:
                continue
            iw = max(1, ih - i)
            for dx in range(-iw, iw + 1):
                if 0 <= ix + dx < W:
                    ch  = '▲' if (i == ih - 1 and dx == 0) else '█'
                    col = random.choice(ICE_COLS[:3])
                    cv[iy][ix + dx] = (ch, col)

    return _render(cv)
