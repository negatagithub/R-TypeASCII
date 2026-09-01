# -*- coding: utf-8 -*-
"""Nivell 6 de R-Type ASCII: NEON ESPACIAL - la metropolis orbital.

Sise nivell de la campanya i el mes espectral: un vol entre la nebulosa i una
ciutat orbital de neon, amb un MURAL GLITCH gegant que anuncia «LEVEL 6» i el
duel final contra la IA central (kind BOSS_KIND) al cor de l'arena.

El terreny es DIBUIXAT (format 'art'; la referencia completa del format es el
docstring de nivell_4.py): el PRIMER PLA es solid (cada caracter de la paleta
es una paret; l'espai es lliure) i el FONS es purament estetic, amb parallax
i bucle horizontal: nebulosa magenta, un planeta anellat i la silueta de la
ciutat orbital.

Escenes del nivell (dificultat creixent):

  1. EL MURAL       la paret del cartell: «LEVEL 6» en pixel-art glitch,
                    amb pixels de neon, soroll i regalims digitals.
  2. EL UMBRAL      portes torre d'entrada, finestres i cables penjats.
  3. EL BARRI       carrer estret que serpent entre blocs amb grafitis.
  4. EL PONT        vall suspesa: sostre prim, pont de llum i pilars.
  5. EL NUCLI       les megatorres bessones; el passatge es fa minusc.
  6. L'ARENA        cel obert: duel final amb la IA central (matar-la guanya).

Com a la resta de nivells d'art, cada columna deixa un corredor lliure
d'almenys MIN_CORRIDOR (6) celes i el dibuix te cami de banda a banda
(validat en carregar). Els spawns nomes cauen en columnes amb les seves
files lliures; el del cap, en plena arena.

Eina d'autoria: python eines_art.py 6  (validacio + previsualitzacio amb colors)
"""

FILES = 20                    # ART_CANON_H: files de tot dibuix

# --- paleta del primer pla ---------------------------------------------------
# Cada caracter es SOLID: la presencia de caracter a la cela es una paret.
PALETA = {
    "#": ("#", "37"),    # vora d'edifici: formigo clar
    "%": ("%", "90"),    # parament: formigo fosc
    "=": ("=", "36"),    # pont de llum / estructura cian
    "|": ("|", "36"),    # cable penjat
    "0": ("0", "93"),    # finestra encesa (groc)
    "o": ("o", "34"),    # finestra apagada (blau)
    "@": ("@", "95"),    # neon magenta
    "&": ("&", "91"),    # grafiti vermell
    "$": ("$", "92"),    # grafiti verd
    "w": ("w", "97"),    # grafiti blanc
    "*": ("*", "95"),    # grafiti rosa
    "O": ("O", "33"),    # llamp del pont (taronja)
}

# --- paleta del fons (parallax, decoratiu, mai col·lisiona) ------------------
PALETA_FONS = {
    ".": (".", "90"),    # estel tenu
    "*": ("*", "37"),    # estel brillant
    "o": ("o", "33"),    # planeta taronja
    "-": ("-", "90"),    # anell del planeta
    "+": ("+", "35"),    # nebulosa magenta
    "^": ("^", "34"),    # silueta de la ciutat orbital (blau)
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


# --- 1. EL MURAL: cartell «LEVEL 6» en pixel-art glitch (64 columnes) --------
# Una paret de 9 files (0..8) amb el text de 5 glifs centrat a les files 2..6.
# El glitch: alguns pixels del glif es tornen '%' (soroll) o '@' (neon), hi ha
# punts dispersos a la paret i «regalims» digitals penjant sota el text.
GLIFS = {
    "L": ("#    ", "#    ", "#    ", "#    ", "#####"),
    "E": ("#####", "#    ", "#### ", "#    ", "#####"),
    "V": ("#   #", "#   #", "#   #", " # # ", "  #  "),
    "6": (" ### ", "#    ", "#### ", "#   #", " ### "),
}
MURAL_AMP = 64


def _linia_cartell(r):
    """La fila r (0..4) del text «LEVEL 6», com un string de 37 columnes."""
    parts = []
    lletres = ("L", "E", "V", "E", "L", None, "6")   # None: espai triple
    for i, lletra in enumerate(lletres):
        parts.append("   " if lletra is None else GLIFS[lletra][r])
        if (i + 1 < len(lletres) and lletra is not None
                and lletres[i + 1] is not None):
            parts.append(" ")
    return "".join(parts)


def _mural():
    g = graella(MURAL_AMP)
    for x in range(MURAL_AMP):
        g[0][x] = "#"                          # carena superior
        g[8][x] = "@" if x % 4 == 1 else "#"   # vora del carrer amb neon
        for y in range(1, 8):
            g[y][x] = "%"                      # parament de la paret
    bloc = [_linia_cartell(r) for r in range(5)]
    ox = (MURAL_AMP - len(bloc[0])) // 2       # text centrat a la paret
    for r, linia in enumerate(bloc):
        for i, ch in enumerate(linia):
            x = ox + i
            if ch == "#":                      # pixel del glif, amb glitch
                h = (r * 7 + x * 13) % 9
                g[2 + r][x] = "@" if h == 4 else ("%" if h == 0 else "#")
    for x in range(ox, ox + len(bloc[0])):     # regalims i soroll glitch
        if (x * 5) % 11 < 2:
            g[7][x] = "#"
        if (x * 3) % 13 == 5:
            g[1][x] = "#"
    return tuple("".join(fila) for fila in g)


PANELL_MURAL = _mural()

# --- constructors de barris ---------------------------------------------------
def _edifici_sup(g, x0, amplada, alt, llavor=0):
    """Edifici penjant de dalt: ocupa les files 0..alt-1 (vora a la fila
    alt-1, la mes propera al passatge). Finestres deterministes al parament."""
    for x in range(x0, x0 + amplada):
        for y in range(alt):
            if y == alt - 1:
                g[y][x] = "@" if x % 5 == 2 else "#"
            elif (x + llavor) % 3 == 1 and y % 2 == 1:
                g[y][x] = "0" if (x + y + llavor) % 4 == 0 else "o"
            else:
                g[y][x] = "%"


def _edifici_inf(g, x0, amplada, baix, llavor=0):
    """Edifici creixent de baix: ocupa les files FILES-baix..19 (vora a la
    fila FILES-baix, la mes propera al passatge)."""
    for x in range(x0, x0 + amplada):
        for y in range(FILES - baix, FILES):
            if y == FILES - baix:
                g[y][x] = "@" if x % 5 == 3 else "#"
            elif (x + llavor) % 3 == 2 and (y - llavor) % 2 == 0:
                g[y][x] = "0" if (x + y + llavor) % 4 == 1 else "o"
            else:
                g[y][x] = "%"


def _grafiti(g, x0, y, text):
    """Estampa un grafiti (caracters SOLID de paleta) sobre parament solid."""
    for i, ch in enumerate(text):
        g[y][x0 + i] = ch


# --- 2. EL UMBRAL: portes torre d'entrada (56 columnes) -----------------------
def _umbral():
    g = graella(56)
    _edifici_sup(g, 10, 10, 5, 1); _edifici_inf(g, 10, 10, 5, 1)
    _edifici_sup(g, 20, 10, 6, 4); _edifici_inf(g, 20, 10, 6, 4)
    _edifici_sup(g, 30, 10, 3, 7); _edifici_inf(g, 30, 10, 3, 7)
    _edifici_sup(g, 40, 10, 7, 2); _edifici_inf(g, 40, 10, 5, 9)
    _edifici_sup(g, 50, 6, 2, 5);  _edifici_inf(g, 50, 6, 2, 5)
    for x in (32, 33):                     # cables penjats sota el sostre curt
        g[3][x] = "|"; g[4][x] = "|"
    for x in (42, 43):                     # cables sota la torre alta
        g[7][x] = "|"; g[8][x] = "|"
    _grafiti(g, 12, 2, "&$w*$")
    _grafiti(g, 42, 4, "w$&w")
    return tuple("".join(fila) for fila in g)


PANELL_UMBRAL = _umbral()


# --- 3. EL BARRI: carrer estret entre blocs amb grafitis (70 columnes) --------
# Perfils (dalt, baix, amplada): segments llargs (12 columnes), el centre del
# corredor es mou com a maxim 1 fila entre segments (serpentina suau) i el
# carrer mai baixa de 8 files lliures. Els salts bruscs amb corredor curt son
# injugables: la nau (3 files) no arriba a recentrar-se entre esglaons.
PERFIL_BARRI = ((4, 4, 10), (5, 5, 12), (6, 6, 12), (5, 6, 12),
                (5, 7, 12), (4, 5, 12))


def _barri():
    g = graella(70)
    x = 0
    for i, (dalt, baix, amplada) in enumerate(PERFIL_BARRI):
        _edifici_sup(g, x, amplada, dalt, i)
        _edifici_inf(g, x, amplada, baix, i + 3)
        x += amplada
    _grafiti(g, 22, 3, "&$w*&$")
    _grafiti(g, 51, 2, "$w&$w")
    _grafiti(g, 5, 16, "w*&$*")
    _grafiti(g, 62, 17, "&w$&")
    return tuple("".join(fila) for fila in g)


PANELL_BARRI = _barri()


# --- 4. EL PONT: vall suspesa amb pont de llum i pilars (70 columnes) ---------
# El sostre es fa prim (2 files) i el terra es converteix en un PONT DE LLUM
# ('=' amb llamps 'O') a la fila 13; els pilars el substitueixen en pujar fins
# a la fila 10, amb tensors '|' que el lliguen al sostre.
def _pont():
    g = graella(70)
    _edifici_sup(g, 0, 8, 3, 0);  _edifici_inf(g, 0, 8, 3, 0)
    _edifici_sup(g, 62, 8, 3, 1); _edifici_inf(g, 62, 8, 5, 1)
    for x in range(8, 62):                 # la vall: sostre prim + pont
        g[0][x] = "%"
        g[1][x] = "#"
        g[13][x] = "O" if (x - 8) % 6 == 0 else "="
        for y in range(14, FILES):
            g[y][x] = "%"
    for x in (15, 16, 30, 31, 45, 46):     # pilars + tensor al sostre
        g[10][x] = "="
        g[11][x] = "%"
        g[12][x] = "%"
        g[2][x] = "|"
    return tuple("".join(fila) for fila in g)


PANELL_PONT = _pont()


# --- 5. EL NUCLI: les megatorres bessones (80 columnes) -----------------------
# El passatge es consta fins a 7 files a les gorges, pero amb RAMPES
# d'aproximacio ((6,6) -> (8,4) -> (10,3)): cada pas baixa el corredor 1-2
# files i la nau sempre hi cap abans de la transicio. Sense rampes, el salt
# de centre es letal (la nau no arriba a posicionar-se).
PERFIL_NUCLI = ((6, 6, 10), (8, 4, 6), (10, 3, 8),       # megatorre 1
                (2, 2, 10),                              # placeta
                (5, 8, 6), (3, 10, 8),                   # megatorre 2
                (4, 8, 6), (5, 6, 6),                    # rampa d'eixida
                (3, 3, 8), (1, 1, 12))                   # cap a l'arena


def _nucli():
    g = graella(80)
    x = 0
    for i, (dalt, baix, amplada) in enumerate(PERFIL_NUCLI):
        _edifici_sup(g, x, amplada, dalt, i * 2)
        _edifici_inf(g, x, amplada, baix, i * 2 + 1)
        x += amplada
    for dy, mida in enumerate((1, 3, 5, 3, 1)):   # el diamant de neon
        c0 = 19 - mida // 2
        for i in range(mida):
            g[2 + dy][c0 + i] = "@"
    _grafiti(g, 41, 12, "@@@ @@@")                # el retol de la segona torre
    _grafiti(g, 17, 8, "&$&$w")
    return tuple("".join(fila) for fila in g)


PANELL_NUCLI = _nucli()

# --- el fons: nebulosa, planeta anellat i ciutat orbital (bucle horitzontal) --
def _fons():
    amplada = 120
    g = graella(amplada)
    for x in range(amplada):               # estels i nebulosa
        for y in range(14):
            h = (x * 7 + y * 13) % 31
            if h == 0:
                g[y][x] = "*"
            elif h in (3, 17):
                g[y][x] = "."
            elif h == 9 and 4 < y < 12:
                g[y][x] = "+"
    cx, cy, radi = 85, 6, 4                # el planeta anellat
    for x in range(cx - radi - 4, cx + radi + 5):
        for y in range(cy - radi, cy + radi + 1):
            d2 = (x - cx) ** 2 + ((y - cy) * 2) ** 2
            if d2 <= radi * radi:
                g[y][x] = "o"
            elif abs(y - cy) == 1 and (x - cx) ** 2 <= (radi + 4) ** 2:
                g[y][x] = "-"
    alcades = (3, 6, 4, 8, 5, 3, 7, 4, 6, 3, 8, 5, 4, 7, 3, 6, 4, 8, 5, 3)
    x = 0                                  # la silueta de la ciutat orbital
    for a in alcades:
        for _ in range(6):
            for y in range(FILES - a, FILES):
                g[y][x] = "^"
            x += 1
    return tuple("".join(fila) for fila in g)


FONS = _fons()


# --- el nivell ----------------------------------------------------------------
# Zones (columnes d'art): mural 40..103 | umbral 128..183 | barri 200..269 |
# pont 286..355 | nucli 372..451 | arena del cap 472..711.
AMPLADA = 712

ART = junta(
    cel(40),                 # 0..39: cel d'entrada
    PANELL_MURAL,            # 40..103: el mural «LEVEL 6» en glitch
    cel(24),                 # 104..127
    PANELL_UMBRAL,           # 128..183: el umbral
    cel(16),                 # 184..199
    PANELL_BARRI,            # 200..269: el barri
    cel(16),                 # 270..285
    PANELL_PONT,             # 286..355: el pont de llum
    cel(16),                 # 356..371
    PANELL_NUCLI,            # 372..451: el nucli
    cel(20),                 # 452..471
    cel(240),                # 472..711: l'arena del cap
)


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
assert all(d + b <= FILES - 6 for d, b, _a in PERFIL_BARRI), PERFIL_BARRI
assert all(d + b <= FILES - 6 for d, b, _a in PERFIL_NUCLI), PERFIL_NUCLI
assert len(ART) == FILES and len(ART[0]) == AMPLADA, (len(ART), len(ART[0]))
assert all(len(fila) == AMPLADA for fila in ART)
assert _corredor_minim(ART) >= 6, _corredor_minim(ART)


LEVEL = {
    "name": "NIVELL 6 - NEON ESPACIAL",
    "duration": 792,                    # 712 columnes d'art + 80 de pantalla
    "paleta": PALETA,
    "art": ART,
    "paleta_fons": PALETA_FONS,
    "fons": FONS,
    "spawns": (
        # --- fase 1: EL MURAL (el cartell glitch entra per la dreta) ---
        (15, 0, 0.50, "recta"),
        (28, 0, 0.35, "ona"),
        (45, 1, 0.55, "ona"),
        (58, 0, 0.70, "zigzag"),
        (72, 2, 0.60, "recta"),
        (86, 0, 0.50, "ona"),
        # --- fase 2: EL UMBRAL (portes torre i cables penjats) ---
        (108, 0, 0.40, "recta"),
        (118, 1, 0.60, "ona"),
        (130, 0, 0.30, "zigzag"),
        (140, 1, 0.30, "picat"),
        (152, 2, 0.35, "recta"),
        (160, 0, 0.50, "ona"),
        (172, 1, 0.35, "ona"),
        (180, 0, 0.60, "recta"),
        # --- fase 3: EL BARRI (carrer estret amb grafitis) ---
        (202, 0, 0.30, "ona"),
        (212, 1, 0.35, "recta"),
        (222, 2, 0.45, "zigzag"),
        (232, 0, 0.35, "picat"),
        (242, 1, 0.50, "ona"),
        (252, 2, 0.30, "recta"),
        (262, 0, 0.40, "puja"),
        (268, 1, 0.45, "ona"),
        # --- fase 4: EL PONT (vall suspesa sobre el pont de llum) ---
        (288, 0, 0.20, "recta"),
        (296, 1, 0.25, "ona"),
        (306, 2, 0.30, "recta"),
        (316, 0, 0.25, "zigzag"),
        (326, 1, 0.40, "ona"),
        (336, 2, 0.35, "picat"),
        (344, 0, 0.50, "ona"),
        (352, 1, 0.30, "recta"),
        # --- fase 5: EL NUCLI (megatorres bessones) ---
        (374, 0, 0.35, "ona"),
        (384, 1, 0.55, "recta"),
        (392, 2, 0.60, "zigzag"),
        (400, 0, 0.20, "ona"),
        (410, 1, 0.25, "picat"),
        (418, 2, 0.30, "recta"),
        (426, 1, 0.35, "ona"),
        (434, 0, 0.50, "recta"),
        (444, 2, 0.45, "ona"),
        (450, 1, 0.40, "zigzag"),
        # --- fase 6: L'ARENA (duel final amb la IA central) ---
        (458, 0, 0.35, "ona"),
        (468, 1, 0.55, "zigzag"),
        (480, 2, 0.40, "recta"),
        (495, 0, 0.30, "ona"),
        (508, 1, 0.60, "recta"),
        (520, 3, 0.40, "cap"),          # LA IA CENTRAL: matar-la guanya
        (535, 0, 0.35, "ona"),
        (550, 1, 0.50, "zigzag"),
        (570, 2, 0.45, "ona"),
        (590, 0, 0.40, "recta"),
        (610, 1, 0.55, "ona"),
        (630, 0, 0.35, "zigzag"),
        (650, 2, 0.50, "recta"),
        (670, 1, 0.40, "ona"),
        (690, 0, 0.45, "recta"),
        (710, 0, 0.40, "ona"),
        (702, 1, 0.50, "ona"),
        (708, 0, 0.35, "zigzag"),
    ),
}