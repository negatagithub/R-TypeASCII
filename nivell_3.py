"""Nivell 3 de R-Type ASCII: EL CAP.

Ultim nivell de la campanya i arena del cap final. Els primers instants son
un avanc per un corredor rocos cada cop mes estret i, a partir del tick 540,
el terreny es retira del tot per deixar lloc al duel final.

A l'entrada de l'arena (tick 800) apareix el cap (kind BOSS_KIND): entra per
la dreta, s'atura a pocs celes de la vora i es balanceja disparant trets
dirigits. Te 30 vides i, al caure, completa el nivell immediatament (encara
que quedin ticks de mapa) i pot deixar anar un kit gran de reparacio.

Aquest nivell va ser CONVERTIT AUTOMATICAMENT des de l'antic format
d'elevacions a la v0.6.0: conserva exactament els mateixos perfils de roca,
colors i temps d'entrada de cada columna. El terreny es DIBUIXAT (format
'art'; la referencia completa del format es el docstring de nivell_4.py).
El fons (boira de tempesta vermella, brases i llamps sobre muntanyes
fosques) es purament estetic i avanca mes lent que el primer pla.

Fases d'aquest nivell (dificultat creixent):

  1. L'ABORDATGE   crestes verdes i blaves i la primera porta d'entrada.
  2. LA GORGA      murs alterns i el corredor en S cap a l'arena.
  3. L'ARENA       el pas s'obre: ultimes escortes abans del cap.
  4. EL CAP        a partir del tick 800 entra el cap; matar-lo es l'objectiu.
"""

FILES = 20                    # ART_CANON_H: files de tot dibuix

PALETA = {
    "#": ("#", "37"),
    "%": ("%", "90"),
    "R": ("%", "94"),
    "W": ("#", "95"),
    "Y": ("%", "32"),
    "q": ("%", "35"),
    "r": ("#", "96"),
    "w": ("#", "91"),
    "y": ("#", "92"),
}

PALETA_FONS = {
    ":": (":", "31"),
    "*": ("*", "91"),
    "/": ("/", "93"),
    "^": ("^", "31"),
}


def junta(*paneles):
    """Enganxa panells de 20 files horitzontalment en un sol dibuix."""
    return tuple("".join(fila) for fila in zip(*paneles))


def cel(n):
    """Panel de cel obert: n columnes del tot lliures."""
    return (" " * n,) * FILES


# Roca del tick 30 al 34 (5 columnes)
PANELL_02 = (
    "yYYYy",
    " yYy ",
    "  y  ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
)

# Roca del tick 70 al 74 (5 columnes)
PANELL_04 = (
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "     ",
    "  #  ",
    " #%# ",
    "#%%%#",
)

# Roca del tick 120 al 130 (11 columnes)
PANELL_06 = (
    "rRRRRRRRRRr",
    " rRRRRRRRr ",
    "  rRRRRRr  ",
    "   rrrrr   ",
    "           ",
    "           ",
    "           ",
    "           ",
    "           ",
    "           ",
    "           ",
    "           ",
    "           ",
    "           ",
    "           ",
    "           ",
    "   rrrrr   ",
    "  rRRRRRr  ",
    " rRRRRRRRr ",
    "rRRRRRRRRRr",
)

# Roca del tick 200 al 211 (12 columnes)
PANELL_08 = (
    "yYYYYYy     ",
    " yYYYy      ",
    "  yYy       ",
    "   y        ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "        #   ",
    "       #%#  ",
    "      y%%%# ",
    "     yY%%%%#",
)

# Roca del tick 240 al 251 (12 columnes)
PANELL_10 = (
    "yYYYYYy     ",
    " yYYYy      ",
    "  yYy       ",
    "   y        ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "            ",
    "        #   ",
    "       #%#  ",
    "      y%%%# ",
    "     yY%%%%#",
)

# Roca del tick 300 al 309 (10 columnes)
PANELL_12 = (
    "%%%%%%%%%%",
    "%%%%%%%%%%",
    "%%%%%%%%%%",
    "%%%%%%%%%%",
    "##########",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
)

# Roca del tick 330 al 339 (10 columnes)
PANELL_14 = (
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "          ",
    "##########",
    "%%%%%%%%%%",
    "%%%%%%%%%%",
    "%%%%%%%%%%",
    "%%%%%%%%%%",
)

# Roca del tick 382 al 404 (23 columnes)
PANELL_16 = (
    "rRRRRRRRRRRRr          ",
    " rRRRRRRRRRr           ",
    "  rRRRRRRRr            ",
    "   rRRRRRr             ",
    "    rrrrr              ",
    "                       ",
    "                       ",
    "                       ",
    "                       ",
    "                       ",
    "                       ",
    "                       ",
    "                       ",
    "                       ",
    "                       ",
    "              rrrrr    ",
    "             rRRRRRr   ",
    "            rRRRRRRRr  ",
    "           rRRRRRRRRRr ",
    "          rRRRRRRRRRRRr",
)

# Roca del tick 450 al 457 (8 columnes)
PANELL_18 = (
    "%%%%%%%%",
    "%%%%%%%%",
    "%%%%%%%%",
    "%%%%%%%%",
    "%%%%%%%%",
    "wwwwwwww",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
)

# Roca del tick 490 al 497 (8 columnes)
PANELL_20 = (
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "        ",
    "wwwwwwww",
    "%%%%%%%%",
    "%%%%%%%%",
    "%%%%%%%%",
    "%%%%%%%%",
    "%%%%%%%%",
)

# Roca del tick 540 al 546 (7 columnes)
PANELL_22 = (
    "WqqqqqW",
    " WqqqW ",
    "  WqW  ",
    "   W   ",
    "       ",
    "       ",
    "       ",
    "       ",
    "       ",
    "       ",
    "       ",
    "       ",
    "       ",
    "       ",
    "       ",
    "       ",
    "   W   ",
    "  WqW  ",
    " WqqqW ",
    "WqqqqqW",
)

# Fons: tempesta vermella i llamps (es repeteix en bucle, 120 columnes)
FONS = (
    ":             /                :                 :/ *     *  : : :           /                    :*    /               ",
    "         : :  /            :                  :   /          ::              /   :      :               /    :       *  ",
    "*       :    : /                         :         /                     :    /                         */              ",
    " :             /                            :      /                       *  / :      :                 /    :         ",
    "                /                                   /                          /                      :   /   :  :      ",
    ":      :        /                 ::                /           :  *           /            :  :     : :  /    :        ",
    "                 /                 :  :         : :  /          :        *      /     :          :        :/            ",
    " :               /  :            : ::            :   /       :              :   /:              :          /            ",
    "                  /            :      ::              /                    :     / :   :                    /       :  :",
    "          :              :          :   :                                                    : :            :   :: :    ",
    "               :       :            :     :                        :       :          :                               : ",
    "                                                                                :                           : :      : :",
    "                      :                 ::             :  :            :                         :                      ",
    "               :                              :                                      :   :      :       :      :        ",
    "                                                                                                                        ",
    "^             ^^^^^^^^^     ^^^^^^^^^^^^^      ^^^^^^^^^^^           ^^^^^              ^^^^^^^^^     ^^^^^^^^^^^^^     ",
    "^^^^      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^     ^^^^^^^^^^^^^      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
    "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
    "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
    "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
)


LEVEL = {
    "name": 'NIVELL 3 - EL CAP',
    "duration": 1500,
    "paleta": PALETA,
    "art": junta(
        cel(30),
        PANELL_02,
        cel(35),
        PANELL_04,
        cel(45),
        PANELL_06,
        cel(69),
        PANELL_08,
        cel(28),
        PANELL_10,
        cel(48),
        PANELL_12,
        cel(20),
        PANELL_14,
        cel(42),
        PANELL_16,
        cel(45),
        PANELL_18,
        cel(32),
        PANELL_20,
        cel(42),
        PANELL_22,
    ),
    "paleta_fons": PALETA_FONS,
    "fons": FONS,
    "spawns": (
        # --- FASE 1 - L'ABORDATGE (des del tick 0) ---
        (15, 0, 0.3, "zigzag"),
        (45, 1, 0.55, "ona"),
        (58, 0, 0.2, "picat"),
        (90, 1, 0.45, "recta"),
        (96, 0, 0.65, "recta"),
        (110, 2, 0.35, "ona"),
        (140, 0, 0.25, "ona"),
        (185, 1, 0.6, "zigzag"),
        (218, 0, 0.4, "picat"),
        (228, 1, 0.3, "recta"),
        (260, 0, 0.5, "ona"),
        (272, 1, 0.7, "recta"),
        # --- FASE 2 - LA GORGA (des del tick 300) ---
        (310, 2, 0.25, "recta"),
        (315, 0, 0.45, "recta"),
        (322, 1, 0.65, "zigzag"),
        (350, 0, 0.25, "ona"),
        (360, 1, 0.35, "picat"),
        (366, 0, 0.55, "ona"),
        (412, 0, 0.3, "recta"),
        (418, 2, 0.45, "ona"),
        (430, 1, 0.4, "zigzag"),
        (438, 0, 0.6, "recta"),
        (465, 1, 0.3, "ona"),
        (470, 0, 0.7, "picat"),
        (512, 2, 0.4, "ona"),
        (520, 0, 0.3, "picat"),
        (528, 1, 0.6, "recta"),
        # --- FASE 3 - L'ARENA (des del tick 560) ---
        (565, 0, 0.2, "zigzag"),
        (580, 1, 0.3, "ona"),
        (596, 0, 0.6, "recta"),
        (610, 2, 0.5, "ona"),
        (626, 0, 0.35, "picat"),
        (640, 1, 0.25, "ona"),
        (660, 2, 0.55, "ona"),
        (680, 0, 0.4, "recta"),
        (700, 1, 0.65, "zigzag"),
        (720, 0, 0.3, "ona"),
        (740, 2, 0.5, "ona"),
        (770, 0, 0.45, "picat"),
        (785, 1, 0.35, "ona"),
        # --- FASE 4 - EL CAP (des del tick 800) ---
        (800, 3, 0.4, "cap"),
        (812, 1, 0.6, "recta"),
    ),
}
