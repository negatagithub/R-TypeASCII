# -*- coding: utf-8 -*-
"""Nivell 12 de R-Type ASCII: GRUTA VERMELLA.

Darrera cambra de la campanya: un llarg passadis subterrani tallat a la roca
vermellosa i marronosa, definit de principi a fi amb degradats de tons propers
(mateixes densitats de trama amb variants de color) i un fons discret de
cendra i mineral que avanca mes lent (parallax) sense robar protagonisme.

Escenes:
  1. L'ENTRADA      boca estreta que s'obre a la roca.
  2. ELS ESTRETS    galeria baixa amb estalactites i estalagmites.
  3. ELS CRISTALLS  veta rica en cristalls vermells i quars daurat.
  4. LA CAMBRA      catedral de roca amb pilars que pengen del sostre.
  5. LA SORTIDA     la claror del final, amb cristalls que s'il.luminen.

Format 'art' (vegeu nivell_4.py): primer pla solid + fons parallax.
La paleta es volgudament homogènia: tres densitats de trama (▓ fosc, ▒ mig,
░ clar) per cada familia de color (ambre, vermell, rocam fosc, molsa) per
crear degradats continus a les parets. Els trams estrets (escena 2) baixen
el sostre i pugen el terra fins a deixar el corredor minim de MIN_CORRIDOR
celes; la cambra (escena 4) s'eixampla i només els pilars del sostre la
trenquen.
Eina: python eines_art.py 12
"""

import math

FILES = 20   # ART_CANON_H

# --- paleta del primer pla ---------------------------------------------------
# 'molts colors semblants entre si': cada familia te tres densitats de tramat
# (fosc interior, mig, superficie clara) amb tons propers, mes accents minerals.
PALETA = {
    "b": ("\u2593", "30"),    # rocam fosc: interior (slate)
    "c": ("\u2592", "30"),    # rocam fosc: mig
    "d": ("\u2591", "30"),    # rocam fosc: superficie
    "e": ("\u2593", "31"),    # vermell: interior
    "f": ("\u2592", "31"),    # vermell: mig
    "g": ("\u2591", "31"),    # vermell: superficie
    "h": ("\u2593", "32"),    # molsa: interior fosca
    "i": ("\u2592", "32"),    # molsa: mig
    "j": ("\u2591", "92"),    # molsa: superficie lluminosa
    "k": ("\u2593", "33"),    # ambre/marro: interior
    "l": ("\u2592", "33"),    # ambre/marro: mig
    "m": ("\u2591", "33"),    # ambre/marro: superficie
    "o": ("@", "91"),         # cristall vermell brillant
    "n": ("*", "93"),         # quars daurat
    "p": ("~", "33"),         # veta de mineral a la paret
}

# Families de degradat, rotades lentament al llarg del dibuix: el mateix mur
# canvia de to de manera gradual en lloc de fer salts bruscos entre escenes.
# Ordenades de mes clar a mes fosca perque _pintar pugui degradar amb elles.
MURS = (
    ("m", "l", "k"),    # ambre: superficie, mig, fosc
    ("g", "f", "e"),    # vermell
    ("d", "c", "b"),    # rocam fosc
    ("j", "i", "h"),    # molsa
)

# --- paleta del fons (parallax, decoratiu, mai col.lisiona) ------------------
# El fons es LLEUGER: gairebe tot espai (el negre del terminal), amb nomes
# elements puntuals esparsos. Cap capa solida: els sprites del primer pla amb
# fons negre queden nets en passar per davant.
PALETA_FONS = {
    "X": ("\u2591", "31"),    # taca de roca llunyana (molt esparsa)
    "*": ("*", "91"),         # guspira
    "~": ("~", "90"),         # degoteig
    ".": (".", "33"),         # polsim mineral
}
def junta(*paneles):
    """Enganxa panells de 20 files horitzontalment en un sol dibuix."""
    return tuple("".join(fila) for fila in zip(*paneles))


def graella(amplada):
    """Taula buida de FILES files i `amplada` columnes."""
    return [[" "] * amplada for _ in range(FILES)]


def _estil(x):
    """Familia de degradat (superficie, mig, fosc) per a la columna x.

    Rota lentament al llarg del dibuix: en lloc de canviar de truc entre
    escenes, el color de la roca evoluciona de manera continua.
    """
    i = (x // 90) % len(MURS)
    return MURS[i]


def _pintar(g, x0, x1, top, bot, cristall_cada=13, veta_cada=7,
            estrella_cada=23):
    """Pinta les parets d'una escena entre x0 (inclos) i x1 (exclos).

    `top[i]` son les celes de sostre a la columna x0+i i `bot[i]` les de
    terra. Cada columna pinta la roca en tres trams (superficie mes clara,
    mig i fosc) triant la familia `_estil`; els accents afegeixen cristalls,
    quars i vetes de mineral sobre la paret (mai envaeixen el corredor).
    """
    for col, x in enumerate(range(x0, x1)):
        cl, mig, fosc = _estil(x)
        t, b = top[col], bot[col]
        for y in range(t):                       # sostre: de dalt a baix
            g[y][x] = fosc if y < t - 2 else (mig if y < t - 1 else cl)
        for y in range(FILES - b, FILES):        # terra: de baix a dalt
            d = y - (FILES - b)
            g[y][x] = fosc if d > 1 else (mig if d > 0 else cl)
        if cristall_cada and x % cristall_cada == 0:
            if t:
                g[t - 1][x] = "o"                # cristall penjat del sostre
            if b:
                g[FILES - b][x] = "o"            # cristall dret al terra
        if estrella_cada and x % estrella_cada == 0 and t:
            g[t - 1][x] = "n"                    # quars daurat incrustat
        if veta_cada and x % veta_cada == 0 and t >= 2:
            g[t - 2][x] = "p"                    # veta mineral al mur


def _entrada():
    """Boca estreta que s'obre a la roca vermella."""
    W = 60
    g = graella(W)
    top = tuple(max(4, min(6, 5 + int(1.3 * math.sin(x / 5))))
                for x in range(W))
    bot = tuple(max(4, min(6, 5 + int(1.3 * math.cos(x / 6))))
                for x in range(W))
    _pintar(g, 0, W, top, bot, cristall_cada=15, veta_cada=7)
    return tuple("".join(f) for f in g)


def _estrets():
    """Galeria baixa: sostre i terra enganxats, estalactites i estagmites."""
    W = 80
    g = graella(W)
    top = tuple(max(5, min(7, 6 + int(1.6 * math.sin(x / 4))))
                for x in range(W))
    bot = tuple(max(5, min(6, 5 + int(1.6 * math.cos(x / 5))))
                for x in range(W))
    _pintar(g, 0, W, top, bot, cristall_cada=11, veta_cada=5)
    return tuple("".join(f) for f in g)
def _cristalls():
    """Veta rica en cristalls vermells i quars daurat."""
    W = 80
    g = graella(W)
    top = tuple(max(4, min(6, 5 + int(1.4 * math.sin(x / 7 + 1))))
                for x in range(W))
    bot = tuple(max(4, min(7, 5 + int(1.4 * math.cos(x / 6))))
                for x in range(W))
    _pintar(g, 0, W, top, bot, cristall_cada=9, estrella_cada=17, veta_cada=0)
    return tuple("".join(f) for f in g)


def _cambra():
    """Catedral de roca amb pilars que pengen del sostre."""
    W = 120
    g = graella(W)
    top = [max(2, min(5, 3 + int(1.6 * math.sin(x / 9)))) for x in range(W)]
    bot = [4] * W
    for a, b in ((40, 46), (96, 102)):          # pilars penjants (sostre=6)
        for x in range(a, b):
            top[x] = 6
        for x in range(a - 2, a):
            top[x] = min(6, top[x] + 1)
        for x in range(b, b + 2):
            top[x] = min(6, top[x] + 1)
    _pintar(g, 0, W, tuple(top), tuple(bot), cristall_cada=13,
            estrella_cada=29, veta_cada=0)
    return tuple("".join(f) for f in g)


def _sortida():
    """La claror del final, amb cristalls que s'il.luminen."""
    W = 80
    g = graella(W)
    top = tuple(max(4, min(6, 5 + int(1.2 * math.sin(x / 6 + 2))))
                for x in range(W))
    bot = tuple(max(4, min(6, 5 + int(1.3 * math.cos(x / 7))))
                for x in range(W))
    _pintar(g, 0, W, top, bot, cristall_cada=9, estrella_cada=13, veta_cada=0)
    return tuple("".join(f) for f in g)


def _fons():
    """Fons lleuger: negre del terminal amb elements puntuals esparsos.

    Gairebe tot son espais: nomes hi ha guspires, degoteigs, polsim i tres
    taques de roca llunyana molt separades. El fons mai es una capa solida,
    aixi els sprites que porten fons negre queden nets en passar per davant.
    """
    W = 90
    g = graella(W)
    for x in range(W):                            # elements puntuals
        if x % 7 == 2:
            g[3 + (x // 7) % 4][x] = "*"          # guspira
        if x % 11 == 5:
            g[15 + (x // 11) % 3][x] = "~"        # degoteig de la volta
        if x % 13 == 9:
            g[12 + (x // 13) % 3][x] = "."        # polsim mineral
    for x in (23, 58, 82):                        # taques de roca llunyana
        for y in range(5, 8):
            if (x + y) % 3:
                g[y][x] = "X"
    return tuple("".join(f) for f in g)


PANELL_1 = _entrada()
PANELL_2 = _estrets()
PANELL_3 = _cristalls()
PANELL_4 = _cambra()
PANELL_5 = _sortida()
FONS = _fons()

AMPLADA = 60 + 80 + 80 + 120 + 80                # 420 columnes d'art
ART = junta(PANELL_1, PANELL_2, PANELL_3, PANELL_4, PANELL_5)

# --- garanties de jugabilitat (mides, paleta i corredor minim) ---------------
def _corredor_minim(art):
    """Mida del tram lliure mes llarg de cada columna (el mes petit de tots)."""
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
    "name": "NIVELL 12 - GRUTA VERMELLA",
    "duration": 500,               # 420 columnes d'art + 80 de pantalla
    "paleta": PALETA,
    "art": ART,
    "paleta_fons": PALETA_FONS,
    "fons": FONS,
    "spawns": (
        (8, 0, 0.40, "ona"),
        (20, 8, 0.35, "puja"),
        (34, 1, 0.45, "zigzag"),
        (48, 0, 0.35, "picat"),
        (62, 2, 0.45, "recta"),
        (76, 8, 0.40, "puja"),
        (92, 0, 0.45, "ona"),
        (106, 1, 0.35, "ona"),
        (120, 2, 0.40, "ona"),
        (134, 0, 0.35, "zigzag"),
        (148, 8, 0.35, "puja"),
        (162, 1, 0.45, "picat"),
        (178, 0, 0.40, "ona"),
        (192, 2, 0.45, "ona"),
        (206, 0, 0.35, "picat"),
        (220, 8, 0.40, "puja"),
        (234, 1, 0.35, "zigzag"),
        (248, 0, 0.45, "ona"),
        (262, 2, 0.40, "ona"),
        (276, 0, 0.35, "picat"),
        (290, 8, 0.40, "puja"),
        (304, 1, 0.40, "ona"),
        (318, 0, 0.45, "zigzag"),
        (332, 2, 0.35, "recta"),
        (346, 0, 0.40, "ona"),
        (358, 8, 0.35, "puja"),
        (368, 1, 0.45, "ona"),
        (378, 0, 0.40, "picat"),
        (388, 2, 0.45, "recta"),
        (395, 3, 0.40, "cap"),
        (398, 8, 0.40, "puja"),
        (406, 0, 0.35, "ona"),
    ),
}