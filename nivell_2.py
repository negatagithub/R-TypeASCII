"""Nivell 2 de R-Type ASCII: ESCULL DE FERRO.

Segon nivell de la campanya, mes dur que el primer: corredors mes estrets
(minim de 8 celes al pic, contra les 10 del nivell 1), murs de 10 files i
gaire be el doble de densitat d'enemics (84 esdeveniments en 1800 ticks).

El format del diccionari LEVEL es el mateix que el de nivell_1.py (vegeu el
seu docstring per als detalls). Les mateixes figures auxiliars es tornen a
definir aqui perque cada fitxer de nivell sigui autocontingut.

Fases d'aquest nivell (dificultat creixent):

  1. LA PORTA        comencem amb una porta de 10 celes de corredor.
  2. L'ESTRET        murs de 8 files alternats i bumps en cadena rapida.
  3. LA GORGA        corredor en S doble, tunell estret i porta de 8 celes.
  4. L'ESCULL        murs de 10 files, serra triple i la pinca mes cruel.
  5. TEMPESTA FINAL  cadena de bumps cada 10 ticks i la gola final.
"""


def bump(h):
    """Perfil triangular d'amplada 2*h-1: 1, 2, ..., h, ..., 2, 1."""
    return tuple(range(1, h + 1)) + tuple(range(h - 1, 0, -1))


def trapei(h, pla):
    """Puja fins a h, es manté `pla` columnes i torna a baixar."""
    return tuple(range(1, h + 1)) + (h,) * pla + tuple(range(h - 1, 0, -1))


def fila(*blocs):
    """Encadena blocs en una fila de columnes; cada enter introdueix zeros."""
    columnes = []
    for bloc in blocs:
        if isinstance(bloc, int):
            columnes.extend([0] * bloc)
        else:
            columnes.extend(bloc)
    return tuple(columnes)


LEVEL = {
    "name": "NIVELL 2 - ESCULL DE FERRO",
    "duration": 1800,            # 144 segons a 12.5 FPS
    "spawns": (
        # --- FASE 1 · LA PORTA: marxa alta desde el primer minut (0-350) ---
        (5, 1, 0.30, "zigzag"),
        (25, 0, 0.70, "ona"),
        (85, 0, 0.25, "picat"),
        (110, 1, 0.55, "recta"),
        (110, 0, 0.30, "recta"),
        (140, 2, 0.50, "ona"),
        (185, 0, 0.60, "zigzag"),
        (215, 1, 0.40, "picat"),
        (265, 0, 0.35, "recta"),
        (265, 1, 0.65, "recta"),
        (300, 2, 0.20, "ona"),
        (330, 0, 0.75, "ona"),
        # --- FASE 2 · L'ESTRET: murs profunds i cadena rapida (350-720) ----
        (360, 0, 0.20, "recta"),
        (360, 1, 0.70, "zigzag"),
        (400, 0, 0.85, "recta"),
        (415, 0, 0.15, "ona"),
        (447, 2, 0.30, "recta"),
        (470, 1, 0.35, "picat"),
        (470, 0, 0.20, "ona"),
        (510, 2, 0.50, "ona"),
        (530, 0, 0.30, "recta"),
        (530, 1, 0.70, "recta"),
        (555, 0, 0.50, "zigzag"),
        (615, 1, 0.25, "ona"),
        (615, 0, 0.75, "ona"),
        (640, 2, 0.50, "recta"),
        (668, 0, 0.50, "recta"),
        (678, 1, 0.50, "recta"),
        (688, 0, 0.50, "picat"),
        (698, 1, 0.50, "recta"),
        # --- FASE 3 · LA GORGA: S doble i tunels (720-1100) -----------------
        (720, 2, 0.35, "recta"),
        (720, 2, 0.65, "recta"),
        (733, 0, 0.50, "ona"),
        (770, 0, 0.30, "picat"),
        (790, 1, 0.60, "zigzag"),
        (810, 0, 0.40, "recta"),
        (810, 1, 0.60, "recta"),
        (835, 2, 0.25, "ona"),
        (835, 1, 0.75, "ona"),
        (855, 0, 0.35, "picat"),
        (900, 2, 0.50, "zigzag"),
        (920, 0, 0.30, "recta"),
        (920, 1, 0.70, "recta"),
        (945, 0, 0.50, "ona"),
        (965, 1, 0.40, "picat"),
        (965, 0, 0.60, "picat"),
        (985, 2, 0.50, "ona"),
        # --- FASE 4 · L'ESCULL: roca profunda per totes bandes (1100-1500) --
        (1100, 0, 0.30, "zigzag"),
        (1100, 1, 0.70, "zigzag"),
        (1130, 2, 0.50, "recta"),
        (1155, 0, 0.85, "ona"),
        (1195, 0, 0.15, "ona"),
        (1215, 1, 0.50, "recta"),
        (1240, 0, 0.40, "picat"),
        (1271, 1, 0.50, "recta"),
        (1288, 0, 0.50, "ona"),
        (1300, 2, 0.30, "recta"),
        (1300, 1, 0.70, "recta"),
        (1355, 0, 0.50, "recta"),
        (1355, 1, 0.50, "ona"),
        (1385, 2, 0.50, "zigzag"),
        (1410, 0, 0.35, "recta"),
        (1410, 1, 0.65, "recta"),
        (1448, 0, 0.25, "ona"),
        (1448, 1, 0.75, "ona"),
        (1470, 2, 0.50, "picat"),
        (1470, 0, 0.35, "recta"),
        # --- FASE 5 · TEMPESTA FINAL (1500-1800) -----------------------------
        (1510, 0, 0.30, "ona"),
        (1510, 1, 0.70, "ona"),
        (1529, 0, 0.50, "recta"),
        (1539, 1, 0.50, "recta"),
        (1549, 2, 0.50, "recta"),
        (1595, 0, 0.35, "picat"),
        (1615, 1, 0.65, "picat"),
        (1630, 2, 0.50, "ona"),
        (1665, 0, 0.50, "recta"),
        (1665, 1, 0.50, "ona"),
        (1695, 2, 0.35, "ona"),
        (1695, 0, 0.65, "ona"),
        (1730, 0, 0.30, "recta"),
        (1730, 1, 0.70, "recta"),
        (1755, 2, 0.50, "ona"),
        (1785, 0, 0.40, "recta"),
        (1785, 1, 0.60, "recta"),
    ),
    "terrain": (
        # --- FASE 1 · LA PORTA: estreta desde el primer minut -----------------
        {"tick": 60, "dalt": trapei(6, 3), "abaix": trapei(6, 3),
         "vora": ("#", "91"), "cos": ("%", "90")},            # porta inicial
        {"tick": 170, "dalt": bump(5), "abaix": (),
         "vora": ("#", "37"), "cos": ("%", "90")},            # serra al cel
        {"tick": 250, "dalt": (), "abaix": bump(5),
         "vora": ("#", "37"), "cos": ("%", "90")},            # serra al terra
        # --- FASE 2 · L'ESTRET: murs de 8 files i cadena rapida ---------------
        {"tick": 380, "dalt": (8,) * 14, "abaix": (),
         "vora": ("#", "91"), "cos": ("%", "90")},            # mur I: a terra
        {"tick": 430, "dalt": (), "abaix": (8,) * 14,
         "vora": ("#", "91"), "cos": ("%", "90")},            # mur II: al cel
        {"tick": 490, "dalt": bump(6), "abaix": fila(6, bump(6)),
         "vora": ("#", "96"), "cos": ("%", "94")},            # doble gran
        {"tick": 590, "dalt": bump(6), "abaix": bump(6),
         "vora": ("#", "95"), "cos": ("%", "35")},            # pinca
        {"tick": 660, "dalt": bump(4), "abaix": (),
         "vora": ("#", "96"), "cos": ("%", "94")},            # cadena rapida
        {"tick": 670, "dalt": (), "abaix": bump(4),
         "vora": ("#", "91"), "cos": ("%", "90")},
        {"tick": 680, "dalt": bump(4), "abaix": (),
         "vora": ("#", "96"), "cos": ("%", "94")},
        {"tick": 690, "dalt": (), "abaix": bump(4),
         "vora": ("#", "91"), "cos": ("%", "90")},
        {"tick": 700, "dalt": bump(4), "abaix": (),
         "vora": ("#", "96"), "cos": ("%", "94")},
        # --- FASE 3 · LA GORGA: S doble, tunell i porta de cristall ------------
        {"tick": 740,
         "dalt": fila(3, trapei(6, 2), 8),
         "abaix": fila(11, trapei(6, 2)),
         "vora": ("#", "96"), "cos": ("%", "94")},            # corredor en S doble
        {"tick": 880, "dalt": (6,) * 12, "abaix": (6,) * 12,
         "vora": ("#", "97"), "cos": ("%", "90")},            # tunell estret
        {"tick": 1000, "dalt": trapei(7, 4), "abaix": trapei(7, 4),
         "vora": ("#", "91"), "cos": ("%", "90"),
         "estils": (None,) * 8
                   + ({"vora": ("@", "95"), "cos": ("%", "95")},)
                   + (None,) * 8},                            # porta de cristall
        # --- FASE 4 · L'ESCULL: roca profunda per totes bandes -----------------
        {"tick": 1120, "dalt": (10,) * 10, "abaix": (),
         "vora": ("#", "91"), "cos": ("%", "90")},            # mur alt I
        {"tick": 1180, "dalt": (), "abaix": (10,) * 10,
         "vora": ("#", "91"), "cos": ("%", "90")},            # mur profund II
        {"tick": 1250, "dalt": bump(5), "abaix": (),
         "vora": ("#", "95"), "cos": ("%", "35")},            # serra triple
        {"tick": 1262, "dalt": (), "abaix": bump(5),
         "vora": ("#", "95"), "cos": ("%", "35")},
        {"tick": 1274, "dalt": bump(5), "abaix": (),
         "vora": ("#", "95"), "cos": ("%", "35")},
        {"tick": 1330, "dalt": trapei(7, 4), "abaix": trapei(7, 4),
         "vora": ("#", "95"), "cos": ("%", "35")},            # pinca maxima
        {"tick": 1420,
         "dalt": fila(bump(5), 6, bump(5)),
         "abaix": fila(10, bump(5), 5),
         "vora": ("#", "95"), "cos": ("%", "35")},            # serra doble gran
        # --- FASE 5 · TEMPESTA FINAL -------------------------------------------
        {"tick": 1520, "dalt": bump(5), "abaix": (),
         "vora": ("#", "93"), "cos": ("%", "33")},            # cadena densa
        {"tick": 1530, "dalt": (), "abaix": bump(5),
         "vora": ("#", "93"), "cos": ("%", "33")},
        {"tick": 1540, "dalt": bump(5), "abaix": (),
         "vora": ("#", "93"), "cos": ("%", "33")},
        {"tick": 1550, "dalt": (), "abaix": bump(5),
         "vora": ("#", "93"), "cos": ("%", "33")},
        {"tick": 1560, "dalt": bump(5), "abaix": (),
         "vora": ("#", "93"), "cos": ("%", "33")},
        {"tick": 1570, "dalt": (), "abaix": bump(5),
         "vora": ("#", "93"), "cos": ("%", "33")},
        {"tick": 1640, "dalt": trapei(7, 6), "abaix": trapei(7, 6),
         "vora": ("#", "91"), "cos": ("%", "90"),
         "estils": (None,) * 9
                   + ({"vora": ("@", "95"), "cos": ("%", "95")},)
                   + (None,) * 9},                            # gola final
        {"tick": 1740, "dalt": bump(4), "abaix": bump(4),
         "vora": ("#", "93"), "cos": ("%", "33")},            # ultim ressalt
    ),
}