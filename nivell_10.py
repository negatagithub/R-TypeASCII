# -*- coding: utf-8 -*-
"""Nivell 10 de R-Type ASCII: CORONA SOLAR.

Tanca del segon acte: el vol sobre la photosfera d'un sol moribund. Escenes:

  1. L'ECLIPSI      la nit solar: anell de corona al fons, vol lliure.
  2. PROMINENCIES   arcs de foc que brollen del terra i lengues del sostre.
  3. EL VENT SOLAR  corredor ondulant mogut per les corrents de plasma.
  4. LES TAQUES     taques solars al terra i arcs magnetics al sostre.
  5. LA CORONA      l'arena final: el duel amb el CAP SOLAR.

Format 'art' (vegeu nivell_7.py): primer pla solid amb paleta mes fons
decoratiu amb parallax. Estil REXPaint: parets en degradat roig-taronja
(░ ▒ ▓) i fons amb anell de corona, prominencies i vent solar.
Regla d'autoria: sostre top <= 4 i terra bot <= 6 -> files 4..13 lliures.
Eina: python eines_art.py 10
"""

import math

FILES = 20   # ART_CANON_H

# --- paleta del primer pla (photosfera en degradat ░▒▓) ----------------------
PALETA = {
    "%": ("▓", "31"),   # photosfera fosca (interior)
    "#": ("▒", "33"),   # cromosfera (mig)
    "o": ("░", "93"),   # vora incandescent (clar)
    "v": ("v", "91"),   # flama viva encastada (SOLID)
    "@": ("@", "97"),   # guspirella blanca a la vora (SOLID)
}

# --- paleta del fons (anell de corona, prominencies i vent solar) ------------
PALETA_FONS = {
    "D": ("▒", "90"),   # espai fosc al zenit
    "P": ("▒", "31"),
    "p": ("░", "31"),
    "b": ("░", "33"),
    "B": ("▒", "33"),
    "g": ("▓", "33"),   # fotosfera (l'horizon ardent)
    "O": ("O", "93"),   # anell de corona
    "^": ("^", "91"),   # prominencia llunyana
    ".": (".", "93"),   # vent solar
    "@": ("@", "97"),   # guspirella blanca
    "~": ("~", "31"),   # corrents de plasma
}


def junta(*paneles):
    """Enganxa paneles de FILES files horitzontalment en un sol dibuix."""
    return tuple("".join(fila) for fila in zip(*paneles))


def graella(amplada):
    """Una graella buida de FILES x amplada (llista de llistes)."""
    return [[" "] * amplada for _ in range(FILES)]


def _ramp(g, x0, x1, top, bot, clar="o", mig="#", fosc="%"):
    """Paret solar en degradat: vora incandescent cap al corredor."""
    for col, x in enumerate(range(x0, x1)):
        t, b = top[col], bot[col]
        for y in range(t):
            d = (t - 1) - y
            g[y][x] = clar if d == 0 else (mig if d == 1 else fosc)
        for y in range(FILES - b, FILES):
            d = y - (FILES - b)
            g[y][x] = clar if d == 0 else (mig if d == 1 else fosc)


def _accent(g, x0, x1, top, bot, ch, pas=7):
    """Espurnes ENCARA DINS la paret (mai a la banda lliure 4..13)."""
    for col, x in enumerate(range(x0, x1)):
        if x % pas == 0:
            if top[col]:
                g[top[col] - 1][x] = ch
            if bot[col]:
                g[FILES - bot[col]][x] = ch


# ---------------------------------------------------------------------------
# ESCENES
# ---------------------------------------------------------------------------

# --- 1. L'ECLIPSI (40): nit solar, anell de corona al fons ------------------
def _eclipsi():
    g = graella(40)
    top = (1, 2, 0, 0, 1, 1, 0, 0, 0, 1, 2, 1, 0, 0, 0, 1, 1, 0, 0, 0,
           1, 2, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 2, 1, 0, 0, 0, 0, 1, 0)
    bot = (1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 2, 1, 0, 0, 0, 0, 1, 1, 0, 0,
           0, 1, 2, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 2, 1, 0, 0, 0, 1)
    _ramp(g, 0, 40, top, bot)
    _accent(g, 0, 40, top, bot, "@", pas=6)
    return tuple("".join(fila) for fila in g)

# --- 2. PROMINENCIES (80): arcs de foc que brollen i lengues del sostre -----
def _prominencies():
    g = graella(80)
    top = tuple(max(0, min(3, 2 + int(1.4 * math.sin(x / 7 + 2))))
                for x in range(80))
    bot = tuple(max(0, min(5, 4 + int(1.7 * math.sin(x / 6 + 0.6))))
                for x in range(80))
    _ramp(g, 0, 80, top, bot)
    # arcs de foc que s'aixequen del terra (bot=6, cresta fila 14)
    for cx in (14, 40, 66):
        _ramp(g, cx - 2, cx + 3, (0,) * 5, (6,) * 5)
        g[15][cx] = "v"
        g[16][cx - 1] = "v"
        g[16][cx + 1] = "v"
    _accent(g, 0, 80, top, bot, "@", pas=8)
    return tuple("".join(fila) for fila in g)


# --- 3. EL VENT SOLAR (80): corredor ondulant de plasma ---------------------
def _vent_solar():
    g = graella(80)
    top = tuple(max(0, min(3, 2 + int(1.5 * math.sin(x / 5))))
                for x in range(80))
    bot = tuple(max(0, min(5, 4 + int(1.8 * math.cos(x / 5))))
                for x in range(80))
    _ramp(g, 0, 80, top, bot)
    _accent(g, 0, 80, top, bot, "v", pas=5)
    return tuple("".join(fila) for fila in g)


# --- 4. LES TAQUES (80): taques solars i arcs magnetics ---------------------
def _taques():
    g = graella(80)
    top = [1 + (1 if (x // 4) % 3 else 0) for x in range(80)]
    bot = [4] * 80
    _ramp(g, 0, 80, tuple(top), tuple(bot))
    # taques solars: fons fred que s'enfonsa (bot=6, crest fila 14)
    for a, b in ((10, 17), (34, 41), (58, 65)):
        for x in range(a, b):
            bot[x] = 6
        _ramp(g, a, b, (0,) * (b - a), (6,) * (b - a))
        for x in range(a + 1, b - 1):
            g[16][x] = "v"
            g[17][x] = "v"
    # arcs magnetics al sostre (top=4, filas 0-3)
    for a, b in ((22, 29), (46, 53), (70, 77)):
        for x in range(a, b):
            top[x] = 4
        _ramp(g, a, b, (4,) * (b - a), (0,) * (b - a))
        g[3][(a + b) // 2] = "@"
    _accent(g, 0, 80, tuple(top), tuple(bot), "@", pas=9)
    return tuple("".join(fila) for fila in g)

# --- 5. LA CORONA (180): arena final, el duel amb el CAP SOLAR --------------
def _corona():
    g = graella(180)
    top = [2] * 180
    bot = [5] * 180
    for x in range(40, 47):
        top[x] = 4                     # enclusa solar
    for x in range(120, 127):
        top[x] = 4
    for x in range(70, 77):
        bot[x] = 6                     # ones de photosfera
    for x in range(140, 147):
        bot[x] = 6
    _ramp(g, 0, 180, top, bot)
    # forats de foc al terra (flames dins el mur, mai a la banda lliure)
    for cx in (50, 90, 130):
        for x in range(cx - 1, cx + 2):
            g[15][x] = "v"
            g[16][x] = "v"
    _accent(g, 0, 180, top, bot, "@", pas=12)
    return tuple("".join(fila) for fila in g)

# ---------------------------------------------------------------------------
# EL FONS: anell de corona, prominencies i vent solar (estil REXPaint)
# ---------------------------------------------------------------------------
def _fons():
    W = 120
    g = graella(W)
    bandes = ((0, 1, "D"), (2, 3, "P"), (4, 6, "p"), (7, 9, "p"),
              (10, 12, "B"), (13, 15, "B"), (16, 17, "b"), (18, 19, "g"))
    for lo, hi, ch in bandes:
        for y in range(lo, hi + 1):
            for x in range(W):
                g[y][x] = ch
    # l'anell de corona: cercle centrat a (60, 10) amb radi 9..12
    for y in range(FILES):
        for x in range(W):
            d2 = (x - 60) ** 2 + (y - 10) ** 2
            if 81 <= d2 <= 144:
                g[y][x] = "O"
    # prominencies llunyanes
    for x in range(W):
        if x % 17 == 2:
            g[3][x] = "^"
            g[4][x] = "^"
    # vent solar: ratlles diagonals
    for x in range(W):
        if x % 3 == 0:
            g[7 + (x // 3) % 7][x] = "."
    # guspires blanques disperses
    for i in range(14):
        x = (i * 61) % W
        g[2 + (i * 5) % 4][x] = "@"
    # corrents de plasma prop de la photosfera
    for x in range(W):
        if x % 5 == 1:
            g[15 + (x // 5) % 4][x] = "~"
    return tuple("".join(fila) for fila in g)


# ============================================================================
# GENERAR ELS PANELLS I L'ART
# ============================================================================
PANELL_1 = _eclipsi()
PANELL_2 = _prominencies()
PANELL_3 = _vent_solar()
PANELL_4 = _taques()
PANELL_5 = _corona()
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
    "name": "NIVELL 10 - CORONA SOLAR",
    "duration": 540,                    # 460 columnes d'art + 80 d'arena
    "paleta": PALETA,
    "art": ART,
    "paleta_fons": PALETA_FONS,
    "fons": FONS,
    "spawns": (
        # --- fase 1: L'ECLIPSI (0-39) ---
        (9, 8, 0.35, "puja"),
        (27, 0, 0.45, "ona"),
        # --- fase 2: PROMINENCIES (40-119) ---
        (50, 1, 0.35, "ona"),
        (72, 8, 0.30, "picat"),
        (95, 2, 0.40, "recta"),
        (115, 0, 0.30, "picat"),
        # --- fase 3: EL VENT SOLAR (120-199) ---
        (130, 8, 0.35, "puja"),
        (152, 1, 0.45, "ona"),
        (175, 0, 0.35, "zigzag"),
        (195, 2, 0.30, "recta"),
        # --- fase 4: LES TAQUES (200-279) ---
        (210, 8, 0.30, "picat"),
        (232, 1, 0.40, "ona"),
        (255, 2, 0.45, "ona"),
        (275, 0, 0.35, "recta"),
        # --- fase 5: LA CORONA (280-459) ---
        (295, 1, 0.35, "ona"),
        (318, 8, 0.30, "puja"),
        (340, 2, 0.35, "recta"),
        (365, 0, 0.40, "ona"),
        (390, 1, 0.30, "zigzag"),
        (430, 3, 0.45, "cap"),          # EL CAP SOLAR: matar-lo guanya
        (450, 8, 0.45, "ona"),
    ),
}
