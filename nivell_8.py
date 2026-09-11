# -*- coding: utf-8 -*-
"""Nivell 8 de R-Type ASCII: TEMPORAL.

Primer nivell del segon acte: el cel obert sobre un mar de nuvols de
tempesta. Escenes:

  1. CEL OBERT       vol lliure entre cirrus, amb els primers llamps llunyans.
  2. BANCS DE NUVOLS talussos rodolants de cumulus, en degradat.
  3. ELS PILONS      torres electriques que creuen el cel, cables al fons.
  4. EL NUCLI        el cor de la tempesta: sostre i terra ondulants i pluja.
  5. L'ULL           l'ull calmat de la tempesta: arena ampla per respirar.

Format 'art' (vegeu nivell_7.py): primer pla solid amb paleta mes fons
decoratiu amb parallax. Estil REXPaint: parets en degradat de tres tons
(░ ▒ ▓) i cel en bandes de color continues amb features dispersos.
Regla d'autoria (igual que el nivell 7): sostre top <= 4 i terra bot <= 6,
de manera que les files 4..13 queden SEMPRE lliures per volar.
Eina: python eines_art.py 8
"""

import math

FILES = 20   # ART_CANON_H: files de tot dibuix

# --- paleta del primer pla (nuvols en degradat ░▒▓) --------------------------
PALETA = {
    "%": ("▓", "34"),   # nuvol fosc (indigo, interior)
    "#": ("▒", "37"),   # nuvol mig (gris)
    "o": ("░", "97"),   # vora clara del nuvol (llum de tempesta)
    "z": ("z", "93"),   # llamp encastat a la vora (SOLID com la roca)
}

# --- paleta del fons (cel en bandes de degradat + features) ------------------
PALETA_FONS = {
    "D": ("▓", "35"),   # indigo profundo: zenit
    "P": ("▒", "35"),
    "p": ("░", "35"),
    "b": ("░", "34"),
    "B": ("▒", "34"),
    "g": ("▒", "37"),
    "l": ("░", "37"),
    "m": ("▒", "90"),   # mar de nuvols (l'horizont)
    "*": ("*", "97"),   # estels
    "z": ("z", "93"),   # llamps llunyans
    "-": ("-", "37"),   # nuvols rodants
    ".": (".", "90"),   # plugim fi
}


def junta(*paneles):
    """Enganxa paneles de FILES files horitzontalment en un sol dibuix."""
    return tuple("".join(fila) for fila in zip(*paneles))


def graella(amplada):
    """Una graella buida de FILES x amplada (llista de llistes)."""
    return [[" "] * amplada for _ in range(FILES)]


def _ramp(g, x0, x1, top, bot, clar="o", mig="#", fosc="%"):
    """Paret en degradat: la vora que mira al corredor es CLARA i l'interior
    s'enfosqueix (clar -> mig -> fosc). top/bot son per columnes."""
    for col, x in enumerate(range(x0, x1)):
        t, b = top[col], bot[col]
        for y in range(t):                       # sostre: vora a la fila t-1
            d = (t - 1) - y
            g[y][x] = clar if d == 0 else (mig if d == 1 else fosc)
        for y in range(FILES - b, FILES):        # terra: vora a FILES-b
            d = y - (FILES - b)
            g[y][x] = clar if d == 0 else (mig if d == 1 else fosc)


def _accent(g, x0, x1, top, bot, ch, pas=7):
    """Espurnes decoratives ENCARA DINS la paret (mai a la banda lliure)."""
    for col, x in enumerate(range(x0, x1)):
        if x % pas == 0:
            if top[col]:
                g[top[col] - 1][x] = ch
            if bot[col]:
                g[FILES - bot[col]][x] = ch


# ---------------------------------------------------------------------------
# ESCENES
# ---------------------------------------------------------------------------

# --- 1. CEL OBERT (40 columnes): cirrus primis, primeres tempestes ----------
def _cel_obert():
    g = graella(40)
    top = (2, 1, 0, 0, 1, 1, 0, 0, 0, 1, 2, 1, 0, 0, 1, 0, 0, 0, 1, 2,
           1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 2, 1, 0, 0, 0, 1, 1, 0, 0, 0)
    bot = (2, 0, 0, 0, 0, 1, 1, 0, 0, 2, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0,
           1, 2, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 2, 1, 0, 0, 0, 0, 1)
    _ramp(g, 0, 40, top, bot)
    return tuple("".join(fila) for fila in g)


# --- 2. BANCS DE NUVOLS (80): cumulus rodolants en onades -------------------
def _bancs():
    g = graella(80)
    top = tuple(max(0, min(3, 2 + int(1.4 * math.sin(x / 6))))
                for x in range(80))
    bot = tuple(max(0, min(3, 2 + int(1.4 * math.sin(x / 6 + 2.1))))
                for x in range(80))
    _ramp(g, 0, 80, top, bot)
    # cumulus que s'aixequen del mar de nuvols (bot=5, cresta fila 15)
    for cx in (18, 44, 70):
        _ramp(g, cx - 3, cx + 4, (0,) * 7, (5,) * 7)
    _accent(g, 0, 80, top, bot, "z", pas=9)
    return tuple("".join(fila) for fila in g)


# --- 3. ELS PILONS (80): torres electrica amb base de nubol -----------------
def _pilons():
    g = graella(80)
    _ramp(g, 0, 80, (0,) * 80, (2,) * 80)          # base rodant de nuvols
    for cx in (12, 32, 52, 72):
        _ramp(g, cx - 1, cx + 1, (0, 0), (5, 5))   # pilar (filas 15-19)
        _ramp(g, cx - 1, cx + 1, (3, 3), (0, 0))   # barra superior (0-2)
    _accent(g, 0, 80, (0,) * 80, (2,) * 80, "z", pas=11)
    return tuple("".join(fila) for fila in g)

# --- 4. EL NUCLI (80): cor de la tempesta, parets ondulants i pluja ---------
def _nucli():
    g = graella(80)
    top = tuple(max(0, min(3, 2 + int(1.6 * math.sin(x / 5))))
                for x in range(80))
    bot = tuple(max(0, min(5, 4 + int(1.9 * math.sin(x / 5 + 1.2))))
                for x in range(80))
    _ramp(g, 0, 80, top, bot)
    _accent(g, 0, 80, top, bot, "z", pas=6)
    return tuple("".join(fila) for fila in g)


# --- 5. L'ULL (180): l'arena calma de la tempesta ---------------------------
def _ull():
    g = graella(180)
    top = [2] * 180
    bot = [5] * 180
    for x in range(58, 66):
        top[x] = 4                     # enclusa de nuvol
    for x in range(98, 106):
        top[x] = 3
    for x in range(40, 47):
        bot[x] = 6                     # ones de nuvol al terra
    for x in range(122, 129):
        bot[x] = 6
    _ramp(g, 0, 180, top, bot)
    _accent(g, 0, 180, top, bot, "z", pas=13)
    return tuple("".join(fila) for fila in g)


# ---------------------------------------------------------------------------
# EL FONS: cel de tempesta en bandes de degradat (estil REXPaint)
# ---------------------------------------------------------------------------
def _fons():
    W = 120
    g = graella(W)
    bandes = ((0, 1, "D"), (2, 3, "P"), (4, 6, "p"), (7, 9, "b"),
              (10, 12, "B"), (13, 15, "g"), (16, 17, "l"), (18, 19, "m"))
    for lo, hi, ch in bandes:
        for y in range(lo, hi + 1):
            for x in range(W):
                g[y][x] = ch
    # estels dispersos al zenit
    for i in range(26):
        x = (i * 47) % W
        g[1 + (i * 3) % 5][x] = "*"
    # llamps llunyans: zigzag vertical
    for bx in (16, 56, 96):
        for i, y in enumerate(range(3, 10)):
            g[y][(bx + (i % 2)) % W] = "z"
    # nuvols rodants a l'horizont
    for x in range(W):
        if (x * 13) % 60 < 18:
            g[8][(x + 7) % W] = "-"
            g[9][(x + 11) % W] = "-"
    # plugim fi sobre el mar de nuvols
    for x in range(W):
        if x % 3 == 0:
            g[12 + (x // 3) % 4][x] = "."
    # textura del mar de nuvols
    for x in range(W):
        if x % 5 == 2:
            g[18][x] = "-"
        if x % 7 == 3:
            g[19][x] = "-"
    return tuple("".join(fila) for fila in g)


# ============================================================================
# GENERAR ELS PANELLS I L'ART
# ============================================================================
PANELL_1 = _cel_obert()
PANELL_2 = _bancs()
PANELL_3 = _pilons()
PANELL_4 = _nucli()
PANELL_5 = _ull()
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
    "name": "NIVELL 8 - TEMPORAL",
    "duration": 540,                    # 460 columnes d'art + 80 d'arena
    "paleta": PALETA,
    "art": ART,
    "paleta_fons": PALETA_FONS,
    "fons": FONS,
    "spawns": (
        # --- fase 1: CEL OBERT (0-39) ---
        (8, 0, 0.40, "ona"),
        (26, 4, 0.35, "zigzag"),
        # --- fase 2: BANCS DE NUVOLS (40-119) ---
        (48, 0, 0.30, "picat"),
        (66, 5, 0.35, "recta"),
        (90, 1, 0.55, "ona"),
        (110, 4, 0.45, "ona"),
        # --- fase 3: ELS PILONS (120-199) ---
        (128, 2, 0.35, "ona"),
        (150, 4, 0.30, "picat"),
        (172, 5, 0.35, "ona"),
        (192, 0, 0.50, "recta"),
        # --- fase 4: EL NUCLI (200-279) ---
        (208, 1, 0.45, "zigzag"),
        (228, 4, 0.35, "ona"),
        (248, 2, 0.30, "recta"),
        (268, 5, 0.40, "ona"),
        # --- fase 5: L'ULL (280-459) ---
        (295, 0, 0.35, "ona"),
        (320, 1, 0.50, "ona"),
        (345, 4, 0.30, "picat"),
        (370, 5, 0.45, "recta"),
        (395, 2, 0.35, "ona"),
        (420, 0, 0.40, "zigzag"),
        (445, 4, 0.45, "ona"),
    ),
}
