# -*- coding: utf-8 -*-
"""Nivell 11 de R-Type ASCII: LA JUNGLA VIVA.

Selva infinita: gegants vegetals, lianes, llacunes i canopia fosca.
Escenes: 1 L'ENTRADA, 2 ELS GEGANTS, 3 LES LIANES, 4 LES LLACUNES,
5 LA CANOPIA, 6 EL CLAR (arena d'EL DEVORADOR, el CAP).

Format 'art' (vegeu nivell_7.py): primer pla solid + fons parallax.
Regla: top <= 4 i bot <= 6 -> files 4..13 lliures. Tot extra es
CONTIGU al mur d'origen (mai illa al corredor central).
Eina: python eines_art.py 11
"""

import math

FILES = 20   # ART_CANON_H

PALETA = {
    "%": ("▓", "32"),
    "#": ("▒", "32"),
    "o": ("░", "92"),
    "T": ("T", "33"),
    "|": ("|", "92"),
    "~": ("~", "36"),
    "@": ("@", "95"),
    "*": ("*", "93"),
}

PALETA_FONS = {
    "D": ("▓", "22"),
    "P": ("▒", "28"),
    "p": ("░", "28"),
    "b": ("░", "34"),
    "B": ("▒", "32"),
    "g": ("▒", "32"),
    "T": ("T", "22"),
    "o": ("o", "93"),
    "*": ("*", "93"),
    "-": ("-", "32"),
    "^": ("^", "28"),
    ".": (".", "92"),
}


def junta(*paneles):
    return tuple("".join(fila) for fila in zip(*paneles))


def graella(amplada):
    return [[" "] * amplada for _ in range(FILES)]


def _ramp(g, x0, x1, top, bot, clar="o", mig="#", fosc="%"):
    for col, x in enumerate(range(x0, x1)):
        t, b = top[col], bot[col]
        for y in range(t):
            d = (t - 1) - y
            g[y][x] = clar if d == 0 else (mig if d == 1 else fosc)
        for y in range(FILES - b, FILES):
            d = y - (FILES - b)
            g[y][x] = clar if d == 0 else (mig if d == 1 else fosc)


def _accent(g, x0, x1, top, bot, ch, pas=7):
    for col, x in enumerate(range(x0, x1)):
        if x % pas == 0:
            if top[col]:
                g[top[col] - 1][x] = ch
            if bot[col]:
                g[FILES - bot[col]][x] = ch


def _troncs(g, x0, x1, top, bot, cada=15):
    for x in range(x0, x1):
        if (x - x0) % cada == 0:
            for y in range(top[x - x0]):
                g[y][x] = "T"
            for y in range(FILES - bot[x - x0], FILES):
                g[y][x] = "T"


def _lianes(g, top, x0, x1, longitud=2, cada=7):
    for x in range(x0, x1):
        if (x - x0) % cada == 2:
            t = top[x - x0]
            for i in range(1, longitud + 1):
                y = t + i - 1
                if y > 13:
                    break
                if g[y][x] != " ":
                    break
                g[y][x] = "|"

def _entrada():
    g = graella(60)
    top = tuple(max(0, min(2, 1 + int(1.2 * math.sin(x / 6)))) for x in range(60))
    bot = tuple(max(0, min(3, 2 + int(1.2 * math.cos(x / 7)))) for x in range(60))
    _ramp(g, 0, 60, top, bot)
    _accent(g, 0, 60, top, bot, "@", pas=11)
    return tuple("".join(f) for f in g)


def _gegants():
    g = graella(120)
    top = tuple(max(1, min(4, 2 + int(1.6 * math.sin(x / 9) + 0.8 * math.sin(x / 4))))
                for x in range(120))
    bot = tuple(max(2, min(6, 4 + int(1.6 * math.cos(x / 8)))) for x in range(120))
    _ramp(g, 0, 120, top, bot)
    _troncs(g, 0, 120, top, bot, cada=15)
    _accent(g, 0, 120, top, bot, "@", pas=13)
    return tuple("".join(f) for f in g)


def _lianes_esc():
    g = graella(120)
    top = tuple(max(1, min(4, 3 + int(1.2 * math.sin(x / 7 + 1)))) for x in range(120))
    bot = tuple(max(2, min(5, 3 + int(1.2 * math.cos(x / 6)))) for x in range(120))
    _ramp(g, 0, 120, top, bot)
    _lianes(g, top, 0, 120, longitud=2, cada=7)
    _arrels(g, bot, 0, 120, longitud=2, cada=11)
    _accent(g, 0, 120, top, bot, "*", pas=17)
    return tuple("".join(f) for f in g)


def _llacunes():
    g = graella(120)
    top = [max(0, min(3, 1 + int(1.0 * math.sin(x / 8)))) for x in range(120)]
    bot = [4] * 120
    for a, b in ((12, 26), (52, 68), (90, 104)):
        for x in range(a, b):
            bot[x] = 6
    _ramp(g, 0, 120, tuple(top), tuple(bot))
    _llacuna(g, 0, 120, tuple(bot))
    for a, b in ((30, 38), (70, 78), (108, 116)):
        for x in range(a, b):
            top[x] = 4
        _ramp(g, a, b, (4,) * (b - a), (0,) * (b - a))
        g[3][(a + b) // 2] = "@"
    return tuple("".join(f) for f in g)


def _canopia():
    g = graella(120)
    top = tuple(max(2, min(4, 3 + int(1.0 * math.sin(x / 5)))) for x in range(120))
    bot = tuple(max(3, min(6, 4 + int(1.4 * math.cos(x / 6 + 0.5)))) for x in range(120))
    _ramp(g, 0, 120, top, bot)
    _troncs(g, 0, 120, top, bot, cada=30)
    _lianes(g, top, 0, 120, longitud=2, cada=9)
    _accent(g, 0, 120, top, bot, "*", pas=5)
    return tuple("".join(f) for f in g)


def _clar():
    g = graella(240)
    top = [1] * 240
    bot = [2] * 240
    for x in range(20, 30):
        top[x] = 4
        bot[x] = 5
    for x in range(55, 65):
        top[x] = 4
        bot[x] = 6
    _ramp(g, 0, 240, tuple(top), tuple(bot))
    _troncs(g, 20, 30, tuple(top[20:30]), tuple(bot[20:30]), cada=5)
    _troncs(g, 55, 65, tuple(top[55:65]), tuple(bot[55:65]), cada=5)
    _lianes(g, tuple(top), 70, 120, longitud=1, cada=10)
    _accent(g, 0, 80, tuple(top[:80]), tuple(bot[:80]), "@", pas=9)
    return tuple("".join(f) for f in g)


def _fons():
    W = 120
    g = graella(W)
    bandes = ((0, 1, "D"), (2, 4, "P"), (5, 7, "p"), (8, 10, "b"),
              (11, 13, "B"), (14, 19, "g"))
    for lo, hi, ch in bandes:
        for y in range(lo, hi + 1):
            for x in range(W):
                g[y][x] = ch
    for cx in (10, 45, 80, 105):
        for y in range(6, 18):
            g[y][cx] = "T"
            g[y][cx + 1] = "T"
    for i in range(10):
        x = (i * 37) % W
        g[4 + (i * 3) % 3][x] = "o"
    for x in range(W):
        if x % 8 == 3:
            g[9][x] = "^"
        if x % 11 == 5:
            g[10][x] = "^"
    for i in range(16):
        x = (i * 53) % W
        g[6 + (i * 5) % 8][x] = "*"
    for x in range(W):
        if x % 3 == 0:
            g[11 + (x // 3) % 4][x] = "."
    for x in range(W):
        if x % 6 == 4:
            g[16 + (x // 6) % 3][x] = "-"
    return tuple("".join(f) for f in g)


def _arrels(g, bot, x0, x1, longitud=2, cada=9):
    for x in range(x0, x1):
        if (x - x0) % cada == 4:
            b = bot[x - x0]
            for i in range(1, longitud + 1):
                y = (FILES - b) - i
                if y < 4:
                    break
                if g[y][x] != " ":
                    break
                g[y][x] = "|"


def _llacuna(g, x0, x1, bot):
    for col, x in enumerate(range(x0, x1)):
        b = bot[col]
        if b:
            g[FILES - b][x] = "~"
PANELL_1 = _entrada()
PANELL_2 = _gegants()
PANELL_3 = _lianes_esc()
PANELL_4 = _llacunes()
PANELL_5 = _canopia()
PANELL_6 = _clar()
FONS = _fons()

AMPLADA = 60 + 120 + 120 + 120 + 120 + 240
ART = junta(PANELL_1, PANELL_2, PANELL_3, PANELL_4, PANELL_5, PANELL_6)


def _corredor_minim(art):
    minim = FILES
    for x in range(len(art[0])):
        run = best = 0
        for y in range(FILES):
            run = run + 1 if art[y][x] == " " else 0
            if run > best:
                best = run
        if best < minim:
            minim = best
    return minim


assert len(ART) == FILES and len(ART[0]) == AMPLADA
assert all(len(f) == AMPLADA for f in ART)
assert _corredor_minim(ART) >= 6, _corredor_minim(ART)

LEVEL = {
    "name": "NIVELL 11 - LA JUNGLA VIVA",
    "duration": 860,
    "paleta": PALETA,
    "art": ART,
    "paleta_fons": PALETA_FONS,
    "fons": FONS,
    "spawns": (
        (8, 0, 0.35, "ona"),
        (24, 1, 0.40, "ona"),
        (42, 0, 0.30, "picat"),
        (55, 6, 0.35, "ona"),
        (70, 1, 0.35, "ona"),
        (88, 7, 0.40, "ona"),
        (104, 0, 0.30, "zigzag"),
        (104, 0, 0.50, "zigzag"),
        (122, 2, 0.40, "ona"),
        (140, 6, 0.35, "picat"),
        (158, 1, 0.45, "picat"),
        (172, 7, 0.30, "recta"),
        (188, 1, 0.40, "puja"),
        (204, 0, 0.35, "picat"),
        (218, 7, 0.45, "ona"),
        (232, 1, 0.30, "zigzag"),
        (232, 0, 0.50, "ona"),
        (250, 2, 0.40, "recta"),
        (268, 6, 0.35, "ona"),
        (284, 1, 0.45, "ona"),
        (294, 0, 0.30, "zigzag"),
        (308, 7, 0.35, "ona"),
        (324, 2, 0.40, "ona"),
        (340, 0, 0.30, "recta"),
        (340, 1, 0.50, "recta"),
        (358, 6, 0.40, "puja"),
        (376, 1, 0.35, "zigzag"),
        (394, 7, 0.45, "recta"),
        (408, 0, 0.30, "ona"),
        (408, 1, 0.50, "ona"),
        (428, 1, 0.40, "ona"),
        (442, 0, 0.30, "picat"),
        (442, 0, 0.50, "picat"),
        (458, 7, 0.35, "ona"),
        (472, 2, 0.40, "ona"),
        (486, 1, 0.30, "zigzag"),
        (486, 6, 0.50, "ona"),
        (502, 0, 0.35, "ona"),
        (516, 7, 0.40, "recta"),
        (528, 1, 0.45, "picat"),
        (548, 2, 0.40, "ona"),
        (564, 0, 0.30, "zigzag"),
        (580, 1, 0.45, "ona"),
        (596, 7, 0.35, "recta"),
        (612, 0, 0.40, "ona"),
        (628, 1, 0.30, "zigzag"),
        (644, 2, 0.45, "ona"),
        (660, 6, 0.35, "puja"),
        (678, 1, 0.40, "ona"),
        (700, 3, 0.40, "cap"),
        (720, 0, 0.35, "ona"),
        (740, 1, 0.45, "zigzag"),
        (760, 2, 0.40, "recta"),
        (770, 7, 0.35, "ona"),
        (777, 0, 0.45, "ona"),
    ),
}

