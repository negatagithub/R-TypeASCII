# -*- coding: utf-8 -*-
"""Nivell 5 de R-Type ASCII: BASTIO URBA - la ciutat en runes i el cap final.

Ultim nivell de la campanya: un vol de cap a cap d'una metropoli abandonada
(amb els seus carrers, edificis, neons i grafitis) que acaba en el duel final
contra el cap (kind BOSS_KIND), que torna per defensar el cor de la ciutat.

El terreny es DIBUIXAT (format 'art'/'fons'; la referencia completa del
format es el docstring de nivell_4.py): el PRIMER PLA dibuixa carrers i
edificis - cada caracter solid de la paleta es una paret de la ciutat; el
FONS es una capa decorativa (cel, silueta llunyana de la ciutat i carretera
amb marques) que avanca mes lent (parallax) i es repeteix en bucle.

Escenes del nivell (dificultat creixent):

  1. L'ENTRADA      cel obert cap a la periferia; porxo i porta amb neons.
  2. EL BARRI       primeres illes de cases amb finestres enceses i tags.
  3. ELS CANYONS    el carrer serpenteja entre blocs alts; tags i neons.
  4. EL MURAL       un mur del bastio amb el grafiti «R-TYPE».
  5. L'AVINGUDA     mes ampla i plena de neons; respira abans del final.
  6. LA PLACETA     ruines baixes i, despres, una placeta del tot oberta.
  7. L'ARENA        el duel amb el cap (ticks finals; matar-lo guanya).

Com a la resta de nivells d'art, cada columna deixa un corredor lliure
d'almenys MIN_CORRIDOR (6) celes i el dibuix te cami de banda a banda
(validat en carregar). Els spawns nomes cauen en columnes amb les seves
files lliures; els de la zona del cap, en plena arena.

Eina d'autoria: python eines_art.py 5  (validacio + previsualitzacio amb colors)
"""

FILES = 20                    # ART_CANON_H: files de tot dibuix

# --- paleta del primer pla ---------------------------------------------------
# Cada caracter es SOLID: la presencia de caracter a la cela es una paret de
# la ciutat (la col·lisio es directa). L'espai es el carrer lliure.
PALETA = {
    "#": ("#", "37"),    # aresta de l'edifici: formigo clar
    "%": ("%", "90"),    # parament: formigo fosc
    "=": ("=", "36"),    # biga de vidre/acer
    "0": ("0", "93"),    # finestra encesa (groc)
    "o": ("o", "34"),    # finestra apagada (blau)
    "@": ("@", "95"),    # cartell de neo (magenta)
    "&": ("&", "91"),    # grafiti vermell
    "$": ("$", "92"),    # grafiti verd
    "w": ("w", "97"),    # grafiti blanc
    "*": ("*", "95"),    # grafiti rosa
}

# --- paleta del fons (parallax, decoratiu, mai col·lisiona) ------------------
# El fons dibuixa el cel, la silueta llunyana de la metropoli, la carretera
# amb marques discontinues i la lluna; els espais del primer pla el deixen
# veure al carrer, donant profunditat a la ciutat.
PALETA_FONS = {
    ".": (".", "90"),    # estel tenu
    "*": ("*", "37"),    # estel brillant
    "o": ("o", "33"),    # llum llunyana encesa / lluna
    "^": ("^", "30"),    # silueta de la ciutat (negre)
    "-": ("-", "33"),    # linia discontinua de la carretera
}


def junta(*paneles):
    """Enganxa panells de FILES files horitzontalment en un sol dibuix."""
    return tuple("".join(fila) for fila in zip(*paneles))


def cel(n):
    """Panel de cel obert: n columnes del tot lliures."""
    return (" " * n,) * FILES


def _columna_ciutat(dalt, baix, llavor):
    """Una columna de ciutat: edifici superior de `dalt` files (aresta a la
    fila dalt-1, la mes propera al carrer) i edifici inferior de `baix` files
    (aresta a la fila FILES-baix, la mes propera al carrer). Les `dalt+baix`
    files restants queden lliures: el carrer.

    Les guarnicions (finestres enceses/apagades, cartells de neo i tags de
    grafiti) s'escullen amb `llavor` perque variin de columna a columna de
    manera determinista sense que calgui escriure cada parell de paret.
    """
    cells = []
    for r in range(dalt):
        if r == dalt - 1:
            cells.append("#")
        elif dalt >= 5 and r >= dalt - 3:
            cells.append("0" if (r + llavor) % 3 == 0 else "o")
        elif r % 4 == 0:
            cells.append("=")
        else:
            cells.append("%")
    for _ in range(FILES - dalt - baix):
        cells.append(" ")
    for rr in range(baix):
        if rr == 0:
            cells.append("#")
        elif baix >= 5 and rr <= 2:
            cells.append("o" if (rr + llavor) % 3 == 0 else "0")
        elif rr % 4 == 1:
            cells.append("=")
        else:
            cells.append("%")
    if dalt > 0 and llavor % 5 == 3:
        cells[dalt - 1] = "$"                # tag pintat a l'aresta de dalt
    if baix > 0 and llavor % 6 == 4:
        cells[FILES - baix] = "&"            # tag pintat a l'aresta de baix
    if dalt >= 5 and llavor % 7 == 0:
        cells[dalt - 2] = "@"                # cartell de neo a la facana
    return "".join(cells)


def ciutat(perfil):
    """Converteix un perfil de carrer en un panell de FILES files.

    `perfil` es una llista de parells (dalt, baix): l'alçada en files de
    l'edifici superior i de l'inferior. Cada parell genera UNA columna del
    dibuix: els blocs alts fan el carrer mes estret i les asimetries el
    desplacen amunt o avall (serpentines). Tots els parells han de deixar
    com a minim MIN_CORRIDOR files lliures (dalt + baix <= FILES - 6).
    """
    cols = [_columna_ciutat(d, b, i) for i, (d, b) in enumerate(perfil)]
    return tuple("".join(col[r] for col in cols) for r in range(FILES))
# --- grafitis ----------------------------------------------------------------
# Lletres grans (4 files x 5 columnes) per pintar murals a les parets dels
# edificis. Els traços son TINTA (grafiti) i els buits interiors son mur
# ('%'): tota l'area del mural es solid, com ha de ser dins d'una paret.
GRAFEM = {
    "R": ("RRRRR",
          "R   R",
          "RRRR ",
          "R  R "),
    "-": ("     ",
          "     ",
          "-----",
          "     "),
    "T": ("TTTTT",
          "  T  ",
          "  T  ",
          "  T  "),
    "Y": ("Y   Y",
          " Y Y ",
          "  Y  ",
          "  Y  "),
    "P": ("PPPPP",
          "P   P",
          "PPPPP",
          "P    "),
    "E": ("EEEEE",
          "E    ",
          "EEEE ",
          "EEEEE"),
}
TINTA = {"R": "&", "-": "@", "T": "$", "Y": "w", "P": "*", "E": "@"}


def grafiti(paraula="R-TYPE"):
    """4 files del mural de la paraula, sobre parament de formigo."""
    files = ["", "", "", ""]
    for j, c in enumerate(paraula):
        tinta, formes = TINTA[c], GRAFEM[c]
        for f in range(4):
            files[f] += "".join(tinta if ch != " " else "%" for ch in formes[f])
            if j < len(paraula) - 1:
                files[f] += "%"                    # junta de morter
    return tuple(files)


def _mural():
    """Paret del grafiti: muralla superior (11 files) amb el mural «R-TYPE»
    i edifici baix (3 files), deixant un carrer de 6 files al mig."""
    graf = grafiti()
    total = len(graf[0])                      # 35 celes (6 lletres x 5 + 5 juntes)
    marge = (40 - total) // 2                 # centrat dins els 40 de la paret
    guix = tuple("%" * marge + f + "%" * (40 - marge - total) for f in graf)
    cos = "%" * 40
    aresta = "#" * 40
    finestres = "0%o%" * 10                   # 40 columnes de finestres
    biga = "=%" * 20
    tags = "#&##$#" * 6 + "#&##"              # tag llarg sobre la paret baixa
    carrer = " " * 40

    return (
        cos,                                   #  0: terrat
        aresta,                                #  1: teulada
        finestres,                             #  2: finestres de la facana
        cos,                                   #  3: parament
        guix[0],                               #  4: mural R-TYPE
        guix[1],                               #  5
        guix[2],                               #  6
        guix[3],                               #  7
        cos,                                   #  8: parament
        biga,                                  #  9: bandejada metal·lica
        aresta,                                # 10: aresta de la muralla
        carrer, carrer, carrer, carrer, carrer, carrer,   # 11-16: el carrer
        tags,                                  # 17: aresta de l'edifici baix
        cos,                                   # 18: parament
        finestres,                             # 19: llum de baix
    )

# --- perfils dels carrers ----------------------------------------------------
# Cada perfil es una llista de parells (dalt, baix): l'alçada en files de
# l'edifici superior i de l'inferior de CADA columna. Cap parell pot sumar
# mes de FILES - MIN_CORRIDOR (14) per garantir el carrer jugable.
# 1. ENTRADA: cel obert, porxo i una porta de neo en doble arc (50 cols).
PERFIL_ENTRADA = (
    [(0, 0)] * 20
    + [(1, 1)] * 4
    + [(0, 0)] * 6
    + [(2, 1), (3, 2), (4, 2), (4, 3), (4, 3), (3, 2), (2, 2), (1, 1)] * 2
    + [(0, 0)] * 4
)

# 2. BARRI: blocs baixos que van creixent; tags i finestres (100 cols).
PERFIL_BARRI = (
    [(3, 3)] * 10 + [(4, 3)] * 10 + [(5, 4)] * 10 + [(4, 4)] * 10
    + [(3, 4)] * 10 + [(4, 5)] * 10 + [(5, 5)] * 10 + [(4, 4)] * 10
    + [(5, 3)] * 10 + [(6, 4)] * 10
)

# 3. CANYONS: els blocs alts estrenyen el carrer i el desplacen amunt/avall
# (la serpentina es llegeix seguint l'aresta blanca dels edificis), amb tags
# i neons; el pas mai baixa de 6 files (90 cols).
PERFIL_CANYO = (
    [(6, 4)] * 8
    + [(7, 4), (7, 5), (8, 5), (8, 6)] * 2     # el carrer baixa
    + [(8, 6)] * 6
    + [(8, 5)] * 6
    + [(7, 6)] * 6
    + [(6, 6)] * 6
    + [(5, 7)] * 6                             # el carrer torna a pujar
    + [(5, 8)] * 6
    + [(6, 8)] * 6
    + [(6, 7)] * 6
    + [(6, 6)] * 6
    + [(5, 5)] * 6
    + [(6, 5)] * 6
    + [(6, 4)] * 6
    + [(5, 4)] * 2
)

# 5. AVINGUDA: ampla, mitjana, plena de neons (70 cols).
PERFIL_AVINGUDA = (
    [(4, 3)] * 8 + [(5, 3)] * 8 + [(4, 4)] * 8 + [(5, 4)] * 8
    + [(3, 3)] * 8 + [(4, 3)] * 8 + [(5, 4)] * 8 + [(3, 4)] * 6
    + [(4, 3)] * 8
)

# 6b. RUINES: blocs trencats i baixos que anuncien la placeta (30 cols).
PERFIL_RUINES = (
    [(2, 1)] * 5 + [(3, 1)] * 5 + [(2, 2)] * 5 + [(3, 2)] * 5
    + [(2, 1)] * 5 + [(3, 1)] * 5
)

# --- fons (parallax, decoratiu, mai col·lisiona) ------------------------------
# Silueta llunyana de la metropoli sota un cel d'estels, amb la lluna i la
# carretera de marques discontinues que es veu pel carrer. 80 columnes,
# repetides en bucle horitzontal mes a poc a poc que el primer pla.
FONS = tuple(
    f + " " * (80 - len(f)) for f in (
        "      .   .       .      .       .     .        .       ",
        "   *      .          .    .          .       .      .   ",
        "         .   o          .            .    .        .    ",
        "   .            .       .     .  .        .       .  .  ",
        "     .       .     .                 .     .        .   ",
        "  ^^^^      ^^^^^      ^^^^       ^^^^^^      ^^^^    ^^",
        " ^oooo^    ^o^^o^^    ^ooooo^    ^^oo^oo^^   ^ooo^   ^o^",
        " ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
        " ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
        " ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
        "                                                         ",
        "                                                         ",
        "                                                         ",
        " ------  ------  ------  ------  ------  ------   ------ ",
        " ---------------------------------------------------------",
        "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
        "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
        "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
        "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
        "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
    )
)


def _muntar():
    """Composa el dibuix sencer del primer pla (760 columnes x 20 files)."""
    paneles = (
        cel(30),                            # cel obert d'entrada
        ciutat(PERFIL_ENTRADA),             # 30..79: porxo i porta de neo
        cel(10),                            # 80..89: respir
        ciutat(PERFIL_BARRI),               # 90..189: barri baix
        ciutat(PERFIL_CANYO),               # 190..279: canyons
        _mural(),                           # 280..319: el mural R-TYPE
        ciutat(PERFIL_AVINGUDA),            # 320..389: l'avinguda
        cel(20),                            # 390..409: la placeta
        ciutat(PERFIL_RUINES),              # 410..439: ruines
        cel(320),                           # 440..759: l'arena del cap
    )
    return junta(*paneles)


ART = _muntar()

# Garanties d'autoria: les columnes perfilades mai no estrenyen el carrer
# per sota del minim (dalt + baix <= FILES - MIN_CORRIDOR) i tots els
# panells que formen ART tenen les FILES files de la mateixa amplada.
assert all(d + b <= 14
           for perfil in (PERFIL_ENTRADA, PERFIL_BARRI, PERFIL_CANYO,
                          PERFIL_AVINGUDA, PERFIL_RUINES)
           for d, b in perfil), "cap carrer pot baixar de 6 files lliures"
assert len(ART) == FILES and len(ART[0]) == 760, (len(ART), len(ART[0]))

# --- el nivell ----------------------------------------------------------------
LEVEL = {
    "name": "NIVELL 5 - BASTIO URBA",
    "duration": 840,                    # 760 columnes d'art + 80 de pantalla
    "paleta": PALETA,
    "art": ART,
    "paleta_fons": PALETA_FONS,
    "fons": FONS,
    "spawns": (
        # --- fase 1: L'ENTRADA (dalt del cel obert, cap a la porta) ---
        (10, 0, 0.50, "recta"),
        (28, 0, 0.35, "ona"),
        (45, 1, 0.55, "ona"),
        (58, 0, 0.70, "zigzag"),
        (72, 2, 0.40, "recta"),
        # --- fase 2: EL BARRI (carrers baixos, finestres i tags) ---
        (95, 0, 0.40, "ona"),
        (105, 1, 0.55, "ona"),
        (120, 2, 0.45, "recta"),
        (132, 0, 0.35, "zigzag"),
        (145, 1, 0.60, "puja"),
        (158, 0, 0.50, "recta"),
        (170, 1, 0.40, "ona"),
        (182, 0, 0.60, "zigzag"),
        # --- fase 3: ELS CANYONS (carrer serpent de blocs alts) ---
        (195, 1, 0.45, "ona"),
        (205, 0, 0.50, "zigzag"),
        (215, 2, 0.40, "ona"),
        (228, 1, 0.50, "recta"),
        (236, 0, 0.45, "ona"),
        (248, 1, 0.40, "zigzag"),
        (258, 0, 0.50, "recta"),
        (268, 2, 0.45, "ona"),
        # --- fase 4: EL MURAL (carrer al peu del grafiti R-TYPE) ---
        (288, 0, 0.55, "ona"),
        (300, 1, 0.60, "recta"),
        (312, 0, 0.68, "ona"),
        # --- fase 5: L'AVINGUDA (ampla; la calma abans del final) ---
        (325, 0, 0.35, "ona"),
        (335, 1, 0.50, "zigzag"),
        (345, 2, 0.40, "ona"),
        (355, 0, 0.60, "recta"),
        (368, 1, 0.45, "ona"),
        (378, 0, 0.55, "zigzag"),
        # --- fase 6: LA PLACETA I LES RUINES ---
        (392, 0, 0.45, "ona"),
        (402, 1, 0.55, "recta"),
        (415, 0, 0.40, "zigzag"),
        (425, 2, 0.55, "ona"),
        (432, 0, 0.48, "ona"),
        # --- fase 7: L'ARENA (duel amb el cap final) ---
        (445, 0, 0.35, "ona"),
        (458, 1, 0.55, "zigzag"),
        (470, 2, 0.40, "ona"),
        (485, 0, 0.60, "recta"),
        (500, 1, 0.50, "ona"),
        (505, 3, 0.35, "cap"),          # EL CAP FINAL (defensant la ciutat)
        (522, 0, 0.35, "ona"),
        (540, 1, 0.45, "zigzag"),
        (560, 0, 0.50, "ona"),
        (580, 2, 0.40, "recta"),
        (600, 1, 0.55, "ona"),
        (620, 0, 0.60, "zigzag"),
        (640, 0, 0.45, "ona"),
        (660, 1, 0.35, "zigzag"),
        (680, 2, 0.55, "ona"),
        (700, 0, 0.50, "recta"),
        (720, 0, 0.40, "ona"),
        (740, 1, 0.60, "ona"),
        (755, 0, 0.45, "recta"),
    ),
}