# -*- coding: utf-8 -*-
"""Nivell 7 de R-Type ASCII: EL FUEGO DEL INFERNO.

Ultim nivell de la campanya: un vol entre el cor del volca. Escenes:

  1. L'ENTRADA     boca de la cova de lava, amb estalactites i la calma roent.
  2. LES CALDERES  tres calderes bullents que escupen columnes de foc.
  3. EL RIU        torrent de lava entre marges rocosos i illes de basalt.
  4. LA CASCADA    cortina de lava caient des del penya-segat de la dreta.
  5. LES ROQUES    illes flotants de basalt entre espurnes.
  6. L'ARENA       plaça oberta sota un sostre de magma: el duel amb el cap.

Format 'art' (vegeu nivell_4.py): primer pla solid amb paleta (cada caracter
es una paret; l'espai es lliure) mes fons decoratiu amb parallax. Cada
columna deixa un corredor lliure d'almenys MIN_CORRIDOR (6) celes (l'assert
_autoria ho valida). Eina: python eines_art.py 7
"""

FILES = 20   # ART_CANON_H: files de tot dibuix

# --- paleta del primer pla -------------------------------------------------
# Cada caracter es SOLID: la presencia de caracter a la cela es una paret.
PALETA = {
    "#": ("#", "37"),    # roca: gres clar
    "%": ("%", "90"),    # roca: basalt fosc
    "v": ("v", "33"),    # lava
    "o": ("o", "31"),    # foc / brasa
    "@": ("@", "35"),    # nucli roent del volca
    "^": ("^", "32"),    # flama verda / gas volcanic
}

# --- paleta del fons (parallax, decoratiu, mai col·lisiona) -----------------
PALETA_FONS = {
    ".": (".", "90"),    # cendra tenu
    "*": ("*", "37"),    # estel brillant
    "v": ("v", "33"),    # silueta del volca (lava llunyana)
    "o": ("o", "31"),    # lluna rogent / brasa
    "-": ("-", "34"),    # nuvol de cendra
    "^": ("^", "32"),    # cim eruptiu llunya
}


def junta(*paneles):
    """Enganxa panells de FILES files horitzontalment en un sol dibuix."""
    return tuple("".join(fila) for fila in zip(*paneles))


def cel(n):
    """Panel de cel obert: n columnes del tot lliures."""
    return (" " * n,) * FILES


def graella(amplada):
    """Una graella buida de FILES x amplada (llista de llistes, per dibuixar)."""
    return [[" "] * amplada for _ in range(FILES)]


def _perfil(g, x0, x1, top, bot):
    """Paret de roca esculpida: perfil superior (top) i inferior (bot) per
    columna. Cada columna te com a molt top+bot <= 12 files rocoses, de
    manera que queda un corredor lliure d'almenys 6 celes al mig."""
    for col, x in enumerate(range(x0, x1)):
        for y in range(top[col]):
            g[y][x] = "#" if (x + y) % 2 else "%"
        for y in range(FILES - bot[col], FILES):
            g[y][x] = "#" if (x + y) % 2 else "%"


# ---------------------------------------------------------------------------
# REGLA D'AUTORIA DE JUGABILITAT (aquest nivell):
#   - sostre:  top  <= 4  (les files 0..top-1 son roca)
#   - terra:   bot  <= 6  (les files 20-bot..19 son roca)
# Aixo garanteix que les files 5..13 (9 celes) queden SEMPRE lliures i el
# pas central es ample i continu. Cap obstacle flota dins d'aquesta banda.
# ---------------------------------------------------------------------------

# --- 1. L'ENTRADA: boca de la cova de lava (40 columnes) ---------------------
def _entrada():
    g = graella(40)
    # Parets laterals de roca esculpida (sostre i terra que convergeixen)
    _perfil(g, 0, 6, (1, 2, 3, 3, 2, 1), (2, 2, 2, 2, 2, 2))
    _perfil(g, 34, 40, (1, 2, 3, 3, 2, 1), (2, 2, 2, 2, 2, 2))
    # La boca del volca amb estalactites penjant
    for x in range(10, 22):
        g[2][x] = "#" if x % 2 else "%"
        g[3][x] = "#" if x % 3 == 0 else " "
    for x in range(22, 30):
        g[1][x] = "#"
    for x in range(24, 28):
        g[2][x] = "#" if x % 2 else "%"
    # gasos que fugen pel sostre (decoracio, no obstacules)
    for x in range(8, 32, 3):
        g[0][x] = "^"
    # bassal de lava del terra (filas baixes, mai sobre la banda central)
    for y in range(17, 20):
        for x in range(8, 33):
            g[y][x] = "v"
    return tuple("".join(fila) for fila in g)


# --- 2. LES CALDERES: tres calderes bullents al terra (80 columnes) ----------
def _calderes():
    g = graella(80)
    # terreno continu baix (terra bot=4, sostre obert)
    _perfil(g, 0, 80,
            (0,) * 80,
            (4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4))
    # tres calderes que s'aixequen del terra (bot=6, mai mes amunt de fila 13)
    for cx in (16, 40, 64):
        _perfil(g, cx - 2, cx + 3, (0,) * 5, (6, 6, 6, 6, 6))
        # brasa sobre la caldera
        g[13][cx] = "o"
        g[12][cx] = "^"
    # llengues de lava que se'n van per la base (sobre el terra)
    for cx in (16, 40, 64):
        g[15][cx - 4] = "v"
        g[16][cx + 4] = "v"
    return tuple("".join(fila) for fila in g)


# --- 3. EL RIU: torrent de lava entre marges rocosos (80 columnes) -----------
def _riu_lava():
    g = graella(80)
    # llera baixa continua (terra bot=4/5, sostre obert)
    _perfil(g, 0, 80,
            (0,) * 80,
            (4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
             5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
             5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
             5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4))
    # el torrent: lava bullent sobre el fons
    for y in range(15, 20):
        for x in range(18, 62):
            g[y][x] = "v"
    # illes rocoses baixes que pugen del terra (com a molt fila 13)
    for x in range(26, 30):
        for y in range(13, 16):
            g[y][x] = "#" if (x + y) % 2 else "%"
    for x in range(48, 52):
        for y in range(14, 17):
            g[y][x] = "#" if (x + y) % 2 else "%"
    # vapor i espurnes prop del terra (mai sobre la banda central)
    for x in range(20, 60, 4):
        g[13][x] = "o"
    return tuple("".join(fila) for fila in g)


# --- 4. LA CASCADA: cortina de lava penjada del sostre (80 columnes) ---------
def _cascada():
    g = graella(80)
    # terra continu baix (terra bot=4, sostre obert)
    _perfil(g, 0, 80,
            (0,) * 80,
            (4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4))
    # la cortina de lava penja del sostre (top=4, filas 0-3; pas per sota)
    for x in range(60, 76):
        for y in range(4):
            g[y][x] = "o" if (y + x) % 3 == 0 else "v"
    # xarbots a les roques del marge (cauen fins fila 6, mai mes)
    for x in (58, 59, 76, 77):
        g[4][x] = "^"
        g[5][x] = "o"
    # blocs rocosos que s'aixequen del terra (com a molt fila 13)
    for x in range(18, 22):
        for y in range(13, 16):
            g[y][x] = "#" if (x + y) % 2 else "%"
    for x in range(38, 42):
        for y in range(14, 17):
            g[y][x] = "#" if (x + y) % 2 else "%"
    return tuple("".join(fila) for fila in g)


# --- 5. LES ROQUES: cornises que pengen i cons de basalt (80 columnes) -------
def _roques():
    g = graella(80)
    # sostre amb cornises (top <= 3)
    _perfil(g, 0, 3, (3, 2, 1), (0, 0, 0))
    _perfil(g, 77, 80, (1, 2, 3), (0, 0, 0))
    for x in range(14, 22):
        g[2][x] = "#" if x % 2 else "%"
        g[3][x] = "#" if x % 3 == 0 else " "
    # cornisa llarga que penja (top=3; pas ample per sota)
    for x in range(28, 46):
        g[2][x] = "#" if x % 2 else "%"
        g[3][x] = " " if x % 4 == 0 else "%"
    # terra continu baix amb cons de basalt (bot <= 5)
    _perfil(g, 0, 80,
            (0,) * 80,
            (4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
             4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
             4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4))
    # cons de basalt al terra (bot=5, mai mes amunt de fila 14)
    for x in range(34, 40):
        for y in range(15, 18):
            g[y][x] = "%" if (x + y) % 2 else "#"
    for x in range(50, 56):
        for y in range(15, 18):
            g[y][x] = "%" if (x + y) % 2 else "#"
    for x in range(64, 68):
        for y in range(16, 19):
            g[y][x] = "%" if (x + y) % 2 else "#"
    # espurnes soltes prop del terra (fila 13, mai sobre la banda central)
    for x in range(6, 78, 12):
        g[13][x] = "o"
    return tuple("".join(fila) for fila in g)


# --- 6. L'ARENA: plaça del cap oberta sota el magma (180 columnes) -----------
def _arena():
    g = graella(180)
    # sostre de magma alt i pla (top=2, filas 0-1; estalactites curtes)
    _perfil(g, 0, 180, (2,) * 180, (0,) * 180)
    for x in (30, 31, 72, 73, 74, 110, 111, 148, 149):
        g[2][x] = "#"
        g[3][x] = "%"
    # terra/pis continu de la plaça (bot=5, filas 15-19)
    _perfil(g, 0, 180, (0,) * 180,
            (5,) * 180)
    # el geyser central, baix i enganxat al terra (filas 14-16)
    for y in range(14, 17):
        g[y][80] = "o"
    g[13][80] = "@"
    # forats de lava vius al terra (mai sobre la banda central)
    for x in range(40, 44):
        g[15][x] = "v"
        g[16][x] = "v"
    for x in range(96, 100):
        g[15][x] = "v"
        g[16][x] = "v"
    for x in range(118, 122):
        g[15][x] = "v"
        g[16][x] = "v"
    for x in range(140, 144):
        g[15][x] = "v"
        g[16][x] = "v"
    # escalons laterals d'acces baixos
    for x in (10, 11, 168, 169):
        g[13][x] = "#"
        g[14][x] = "%"
    return tuple("".join(fila) for fila in g)


# --- el fons: horitzo volcanic amb parallax (120 columnes, bucle) ------------
# Capa exclusivament estetica: mai col·lisiona, avanca mes lent que el primer
# pla (parallax) i es repeteix en bucle horitzontal. Dibuixat amb patrons
# deterministes (sense random) per fer-lo estable entre partides.
def _fons():
    g = graella(120)
    # estels espaiats (pocs, per no tapar la silueta del volca)
    for x in range(4, 120, 6):
        if (x // 6) % 3:
            g[1][x] = "."
    for x in range(9, 120, 17):
        g[0][x] = "*"
    # la lluna rogent
    g[2][84] = "o"
    g[3][84] = "o"
    # nuvols de cendra
    for x in range(0, 120, 4):
        g[5][x] = "-"
        if (x // 4) % 2:
            g[6][x] = "."
    # siluetes volcaniques a l'horitzo (cons de dors)
    for cx, h in ((18, 5), (52, 7), (88, 4), (112, 8)):
        for x in range(cx - h, cx + h + 1):
            if 0 <= x < 120:
                dy = h - abs(x - cx)
                g[9 - dy][x] = "v"
    # cims en erupcio amb brasa
    for cx in (52, 112):
        g[3][cx] = "^"
        g[8][cx] = "o"
    # brasa llunyana que puja
    for x in range(32, 90, 14):
        g[4][x] = "o"
    return tuple("".join(fila) for fila in g)


# ============================================================================
# GENERAR ELS PANELLS I L'ART
# ============================================================================
PANELL_1 = _entrada()
PANELL_2 = _calderes()
PANELL_3 = _riu_lava()
PANELL_4 = _cascada()
PANELL_5 = _roques()
PANELL_ARENA = _arena()
FONS = _fons()

# ART
AMPLADA = 40 + 80 + 80 + 80 + 80 + 180    # 540 columnes
ART = junta(PANELL_1, PANELL_2, PANELL_3, PANELL_4, PANELL_5, PANELL_ARENA)


# ============================================================================
# VALIDACIO
# ============================================================================
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


# Garanties d'autoria (la validacio completa, amb BFS, corre en carregar main):
assert len(ART) == FILES and len(ART[0]) == AMPLADA
assert all(len(fila) == AMPLADA for fila in ART)
assert _corredor_minim(ART) >= 6, _corredor_minim(ART)


# ============================================================================
# NIVELL
# ============================================================================
LEVEL = {
    "name": "NIVELL 7 - EL FUEGO DEL INFERNO",
    "duration": 620,                    # 540 columnes d'art + 80 de pantalla
    "paleta": PALETA,
    "art": ART,
    "paleta_fons": PALETA_FONS,
    "fons": FONS,
    "spawns": (
        # --- fase 1: L'ENTRADA (0-39) ---
        (8, 0, 0.40, "ona"),
        (22, 1, 0.57, "recta"),
        (36, 2, 0.35, "zigzag"),
        # --- fase 2: LES CALDERES (40-119) ---
        (45, 0, 0.45, "zigzag"),
        (60, 1, 0.72, "ona"),
        (80, 0, 0.55, "recta"),
        (100, 2, 0.45, "ona"),
        (115, 1, 0.47, "picat"),
        # --- fase 3: EL RIU (120-199) ---
        (135, 0, 0.30, "puja"),
        (155, 2, 0.35, "ona"),
        (175, 1, 0.33, "zigzag"),
        (190, 0, 0.45, "recta"),
        (198, 2, 0.45, "ona"),
        # --- fase 4: LA CASCADA (200-279) ---
        (215, 2, 0.45, "recta"),
        (235, 0, 0.45, "ona"),
        (255, 1, 0.47, "puja"),
        (265, 0, 0.55, "zigzag"),
        (278, 2, 0.55, "ona"),
        # --- fase 5: LES ROQUES (280-359) ---
        (295, 1, 0.62, "ona"),
        (310, 0, 0.40, "zigzag"),
        (330, 2, 0.25, "recta"),
        (345, 1, 0.47, "picat"),
        (358, 0, 0.45, "ona"),
        # --- fase 6: L'ARENA (360-539) ---
        (380, 2, 0.50, "ona"),
        (400, 0, 0.30, "zigzag"),
        (430, 1, 0.33, "ona"),
        (460, 2, 0.30, "recta"),
        (490, 1, 0.28, "zigzag"),
        (500, 3, 0.33, "cap"),          # EL CAP DEL VOLCA: matar-lo guanya
        (515, 0, 0.30, "ona"),
        (525, 2, 0.45, "ona"),
        (533, 0, 0.45, "recta"),
        (538, 1, 0.47, "ona"),
    ),
}