# -*- coding: utf-8 -*-
"""Nivell 9 de R-Type ASCII: ABISS GLACIAL.

Segon acte: la gruta de gel sota la aurora polar. Escenes:

  1. LA BOCA          entrada de la cova, amb neu a les vores.
  2. ESTALACTITES     cims de gel que pengen del sostre i muntanyes a baix.
  3. EL LLAC CONGELAT llisa de gel amb icebergs emergint.
  4. LA CRANERA       cano estret entre dues parets de gel ondulants.
  5. EL COR DE GEL    l'arena final: llac congelat i cor de gel al terra.

Format 'art' (vegeu nivell_7.py): primer pla solid amb paleta mes fons
decoratiu amb parallax. Estil REXPaint: parets de gel en degradat de tres
tons (░ ▒ ▓) i fons en bandes de blaus continues amb aurora i nevada.
Regla d'autoria: sostre top <= 4 i terra bot <= 6 -> files 4..13 lliures.
Eina: python eines_art.py 9
"""

import math

FILES = 20   # ART_CANON_H

# --- paleta del primer pla (gel en degradat ░▒▓) -----------------------------
PALETA = {
    "%": ("▓", "94"),   # gel fosc (interior de la paret)
    "#": ("▒", "96"),   # gel mig
    "o": ("░", "97"),   # vora nevada (clar)
    "*": ("*", "37"),   # neu adherida a la vora (SOLID)
    "O": ("O", "96"),   # cor de gel encastat al terra (arena)
}

# --- paleta del fons (abiss en bandes de degradat + aurora + nevada) ---------
PALETA_FONS = {
    "D": ("▓", "34"),   # blau profundo: zenit de l'abiss
    "P": ("▒", "34"),
    "p": ("░", "94"),
    "b": ("░", "37"),
    "B": ("▒", "37"),
    "g": ("▒", "90"),   # llit de gel (l'horizont)
    "~": ("~", "96"),   # aurora boreal
    "^": ("^", "90"),   # cims de gel llunyans
    ".": (".", "97"),   # nevada
    "*": ("*", "97"),   # estels
    "-": ("-", "37"),   # boira baixa
}


def junta(*paneles):
    """Enganxa paneles de FILES files horitzontalment en un sol dibuix."""
    return tuple("".join(fila) for fila in zip(*paneles))


def graella(amplada):
    """Una graella buida de FILES x amplada (llista de llistes)."""
    return [[" "] * amplada for _ in range(FILES)]


def _ramp(g, x0, x1, top, bot, clar="o", mig="#", fosc="%"):
    """Paret de gel en degradat: vora clara cap al corredor, interior fosca."""
    for col, x in enumerate(range(x0, x1)):
        t, b = top[col], bot[col]
        for y in range(t):
            d = (t - 1) - y
            g[y][x] = clar if d == 0 else (mig if d == 1 else fosc)
        for y in range(FILES - b, FILES):
            d = y - (FILES - b)
            g[y][x] = clar if d == 0 else (mig if d == 1 else fosc)


def _accent(g, x0, x1, top, bot, ch, pas=5):
    """Neu adherida a la vora de la paret (sempre DINS la zona solida)."""
    for col, x in enumerate(range(x0, x1)):
        if x % pas == 0:
            if top[col]:
                g[top[col] - 1][x] = ch
            if bot[col]:
                g[FILES - bot[col]][x] = ch


# ---------------------------------------------------------------------------
# ESCENES
# ---------------------------------------------------------------------------

# --- 1. LA BOCA (40): entrada de la cova, muntanyes de neu a les vores ------
def _boca():
    g = graella(40)
    top = (2, 1, 0, 0, 1, 2, 1, 0, 0, 1, 2, 1, 0, 0, 1, 2, 1, 0, 0, 1,
           2, 1, 0, 0, 0, 1, 2, 1, 0, 0, 1, 2, 1, 0, 0, 0, 1, 1, 0, 0)
    bot = (2, 0, 0, 0, 0, 1, 2, 1, 0, 0, 1, 2, 1, 0, 0, 0, 1, 2, 1, 0,
           0, 1, 2, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 2, 1, 0, 0, 0, 0, 1)
    _ramp(g, 0, 40, top, bot)
    _accent(g, 0, 40, top, bot, "*", pas=5)
    return tuple("".join(fila) for fila in g)


# --- 2. ESTALACTITES (80): cims que pengen i muntanyes de gel a baix --------
def _estalactites():
    g = graella(80)
    top = []
    for x in range(80):
        t = 2 + int(1.4 * math.sin(x / 6))
        if x % 11 == 5:
            t = 4                        # estalactita: cim que baixa més
        top.append(max(0, min(4, t)))
    bot = tuple(max(0, min(5, 4 + int(1.5 * math.sin(x / 7 + 1))))
                for x in range(80))
    _ramp(g, 0, 80, tuple(top), bot)
    _accent(g, 0, 80, tuple(top), bot, "*", pas=6)
    return tuple("".join(fila) for fila in g)

# --- 3. EL LLAC CONGELAT (80): llisa de gel amb icebergs --------------------
def _llac():
    g = graella(80)
    _ramp(g, 0, 80, (0,) * 80, (4,) * 80)          # llisa de gel (16-19)
    for cx in (20, 45, 68):
        _ramp(g, cx - 2, cx + 3, (0,) * 5, (6,) * 5)   # icebergs (14-19)
    _accent(g, 0, 80, (0,) * 80, (4,) * 80, "*", pas=8)
    return tuple("".join(fila) for fila in g)


# --- 4. LA CRANERA (80): cano estret entre dues parets de gel ---------------
def _cranera():
    g = graella(80)
    top = tuple(max(0, min(4, 3 + int(1.2 * math.sin(x / 5.5))))
                for x in range(80))
    bot = tuple(max(0, min(6, 5 + int(1.2 * math.cos(x / 5.5))))
                for x in range(80))
    _ramp(g, 0, 80, top, bot)
    _accent(g, 0, 80, top, bot, "*", pas=7)
    return tuple("".join(fila) for fila in g)


# --- 5. EL COR DE GEL (180): arena final sobre el llac congelat -------------
def _cor_gel():
    g = graella(180)
    top = [2] * 180
    bot = [5] * 180
    for x in range(30, 33):
        top[x] = 4                     # estalactites curtes
    for x in range(80, 83):
        top[x] = 4
    for x in range(130, 133):
        top[x] = 4
    for x in range(55, 61):
        bot[x] = 6                     # ones de gel al terra
    for x in range(115, 121):
        bot[x] = 6
    _ramp(g, 0, 180, top, bot)
    # el cor de gel: nuclis brillants encastats al llit (sempre dins el mur)
    for x in (90, 91):
        g[17][x] = "O"
        g[18][x] = "O"
    _accent(g, 0, 180, top, bot, "*", pas=12)
    return tuple("".join(fila) for fila in g)


# ---------------------------------------------------------------------------
# EL FONS: abiss glacial en bandes de degradat + aurora + nevada
# ---------------------------------------------------------------------------
def _fons():
    W = 120
    g = graella(W)
    bandes = ((0, 1, "D"), (2, 4, "P"), (5, 7, "p"), (8, 10, "b"),
              (11, 13, "B"), (14, 19, "g"))
    for lo, hi, ch in bandes:
        for y in range(lo, hi + 1):
            for x in range(W):
                g[y][x] = ch
    # estels al zenit
    for i in range(18):
        x = (i * 53) % W
        g[(i * 2) % 4][x] = "*"
    # aurora boreal: ones de llum
    for x in range(W):
        if (x // 6) % 4 == 0:
            g[3 + (x // 6) % 4][x] = "~"
    # cims de gel llunyans
    for x in range(W):
        if x % 9 == 3:
            g[14][x] = "^"
        if x % 13 == 5:
            g[15][x] = "^"
    # nevada
    for x in range(W):
        if x % 2 == 0:
            g[5 + (x // 2) % 10][x] = "."
    # boira baixa sobre el llit
    for x in range(W):
        if x % 6 == 4:
            g[16 + (x // 6) % 3][x] = "-"
    return tuple("".join(fila) for fila in g)


# ============================================================================
# GENERAR ELS PANELLS I L'ART
# ============================================================================
PANELL_1 = _boca()
PANELL_2 = _estalactites()
PANELL_3 = _llac()
PANELL_4 = _cranera()
PANELL_5 = _cor_gel()
FONS = _fons()

AMPLADA = 40 + 80 + 80 + 80 + 180          # 460 columnes
ART = junta(PANELL_1, PANELL_2, PANELL_3, PANELL_4, PANELL_5)


def _corredor_minim(art):
    """El corredor lliure mes estret de tot el dibuix (garantia d'autoria)."""
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
assert all(len(fila) == AMPLADA for fila in ART)
assert _corredor_minim(ART) >= 6, _corredor_minim(ART)

# ============================================================================
# NIVELL
# ============================================================================
LEVEL = {
    "name": "NIVELL 9 - ABISS GLACIAL",
    "duration": 540,                    # 460 columnes d'art + 80 d'arena
    "paleta": PALETA,
    "art": ART,
    "paleta_fons": PALETA_FONS,
    "fons": FONS,
    "spawns": (
        # --- fase 1: LA BOCA (0-39) ---
        (10, 6, 0.30, "picat"),
        (28, 0, 0.45, "ona"),
        # --- fase 2: ESTALACTITES (40-119) ---
        (52, 7, 0.35, "ona"),
        (70, 1, 0.50, "zigzag"),
        (92, 6, 0.35, "puja"),
        (112, 0, 0.35, "recta"),
        # --- fase 3: EL LLAC CONGELAT (120-199) ---
        (132, 2, 0.40, "ona"),
        (155, 6, 0.30, "picat"),
        (175, 7, 0.35, "ona"),
        (195, 1, 0.45, "ona"),
        # --- fase 4: LA CRANERA (200-279) ---
        (210, 0, 0.30, "zigzag"),
        (230, 6, 0.40, "ona"),
        (250, 2, 0.35, "recta"),
        (270, 7, 0.45, "ona"),
        # --- fase 5: EL COR DE GEL (280-459) ---
        (295, 1, 0.35, "ona"),
        (320, 6, 0.30, "picat"),
        (345, 7, 0.40, "ona"),
        (370, 0, 0.45, "ona"),
        (395, 2, 0.30, "recta"),
        (420, 6, 0.35, "puja"),
        (445, 1, 0.40, "ona"),
    ),
}
