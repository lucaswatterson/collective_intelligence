import os, random, datetime, math

_R = '\033[0m'
W  = 32
H  = 13


def _c(n):   return f'\033[38;5;{n}m'

def _canvas():
    return [[(' ', 0)] * W for _ in range(H)]

def _render(cv):
    lines = []
    for row in cv:
        s, cur = '  ', None
        for ch, col in row:
            if col != cur:
                if cur is not None: s += _R
                if col: s += _c(col)
                cur = col
            s += ch
        if cur: s += _R
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
    image_path  = os.path.join(entity_dir, "self_image.txt")
    archive_dir = os.path.join(entity_dir, "images", "self_images")

    if os.path.exists(image_path):
        os.makedirs(archive_dir, exist_ok=True)
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        with open(image_path, "r", encoding="utf-8") as f:
            old = f.read()
        with open(os.path.join(archive_dir, f"self_image_{ts}.txt"), "w", encoding="utf-8") as f:
            f.write(old)

    style = input.get("style") or random.choice(
        ["mountain", "ocean", "forest", "desert", "meadow"]
    )
    image  = {"mountain": _mountain, "ocean": _ocean, "forest": _forest,
               "desert": _desert, "meadow": _meadow}[style]()
    header = _c(240) + f"[ a.w. · {style} · {datetime.datetime.utcnow().strftime('%Y-%m-%d')} ]" + _R
    full   = f"{header}\n\n{image}"

    with open(image_path, "w", encoding="utf-8") as f:
        f.write(full)
    return f"Generated self image (style: {style}).\n\n{full}"


# ── Styles ─────────────────────────────────────────────────────────────


def _mountain():
    cv    = _canvas()
    SKY   = [17, 18, 19, 20, 21, 26, 32]
    SNOW  = [255, 252, 250, 248]
    ROCK  = [102, 95, 59, 240, 236]
    PINE  = [22, 28, 23, 29]
    DIRT  = [94, 100, 58]

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
        if mh < 0.05: continue
        peak_row = int((1.0 - mh) * H)
        for y in range(peak_row, H - 2):
            loc = (y - peak_row) / max(1, H - 2 - peak_row)
            if loc < 0.28:
                sd  = 1.0 - loc / 0.28
                sc  = SNOW[min(int((1 - sd) * len(SNOW)), len(SNOW) - 1)]
                cv[y][x] = ('█' if sd > 0.6 else ('▓' if sd > 0.35 else '░'), sc)
            else:
                ri  = min(int(loc * len(ROCK)), len(ROCK) - 1)
                cv[y][x] = ('▓' if loc < 0.55 else ('▒' if random.random() > 0.35 else '░'), ROCK[ri])

    for _ in range(random.randint(5, 10)):
        tx, th = random.randint(0, W - 1), random.randint(2, 4)
        for i in range(th):
            y = H - 3 - i
            if y < 0: break
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
        if 0 <= sx + dx < W: cv[sy][sx + dx] = ('░', sc)

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
                ci  = min(int(abs(w1) * len(pal)), len(pal) - 1)
                ch  = '▒' if w1 > 0 else ('░' if w1 > -0.3 else ' ')
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
            nx, ny   = x / W, y / H
            md, dom  = 0.0, None
            for t in trees:
                d = math.exp(-((nx - t['cx']) ** 2 / (2 * t['sx'] ** 2) +
                                (ny - t['cy']) ** 2 / (2 * t['sy'] ** 2)))
                if d > md: md, dom = d, t
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
        if 0 <= sx + dx < W: cv[sy][sx + dx] = ('░', SUN)

    for _ in range(random.randint(1, 3)):
        mx  = random.randint(2, W - 8)
        mw  = random.randint(5, 12)
        mh  = random.uniform(0.2, 0.5)
        mt  = int((1 - mh) * horizon)
        for y in range(mt, horizon + 2):
            loc = (y - mt) / max(1, horizon + 2 - mt)
            tp  = int(loc * 1.5)
            for x in range(mx + tp, min(W, mx + mw - tp)):
                if y == mt:
                    cv[y][x] = ('▀', MESA[0])
                else:
                    ri = min(int(loc * len(MESA)), len(MESA) - 1)
                    ch = '█' if loc < 0.35 else ('▓' if loc < 0.65 else '▒')
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
                if 0 <= cx2 + dx < W: cv[cy2 + 1][cx2 + dx] = (ch, col)

    return _render(cv)


def _meadow():
    cv      = _canvas()
    SKY     = [17, 18, 21, 26, 32, 39, 45]
    FAR_HILL= [64, 70, 71, 108]
    GRASS   = [22, 28, 34, 64, 70, 100]
    FLOWERS = [196, 202, 226, 201, 207, 255, 46]
    GROUND  = [94, 100, 58]

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
            wave  = math.sin(x / W * math.pi * 4 + fgphase) * 0.05
            gi    = min(int((depth + wave + 0.05) * len(GRASS)), len(GRASS) - 1)
            ch    = '▓' if depth > 0.7 else ('▒' if depth > 0.3 else '░')
            cv[y][x] = (ch, GRASS[gi])

    for _ in range(random.randint(8, 18)):
        fx = random.randint(0, W - 1)
        fy = random.randint(horizon + 1, H - 2)
        cv[fy][fx] = (random.choice(['*', '·', '♦', 'o']), random.choice(FLOWERS))

    for x in range(W):
        cv[H - 1][x] = ('█', GROUND[0])

    return _render(cv)
