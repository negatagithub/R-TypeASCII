"""Nivell 3 de R-Type ASCII: EL CAP.

Ultim nivell de la campanya i arena del cap final. Els primers instants son un
avanç per un corredor rocos cada cop mes estret i, a partir del tick 540, el
terreny es retira del tot per deixar lloc al duel final.

A l'entrada de l'arena (tick 800) apareix el cap (kind BOSS_KIND): entra per
la dreta, s'atura a pocs celes de la vora i es balanceja disparant trets
dirigits. Te 30 vides i, al caure, completa el nivell immediatament (encara
que quedin ticks de mapa) i pot deixar anar un kit gran de reparacio.

El format del diccionari LEVEL es el mateix que el de nivell_1.py (vegeu el
seu docstring per als detalls). Les mateixes figures auxiliars es tornen a
definir aqui perque cada fitxer de nivell sigui autocontingut.

Fases d'aquest nivell (dificultat creixent):

  1. L'ABORDATGE   crestes baixes i la primera porta d'entrada.
  2. LA GORGA      murs alterns i el corredor en S cap a l'arena.
  3. L'ARENA       el pas s'obre: ultimes escortes abans del cap.
  4. EL CAP        a partir del tick 800 entra el cap; matar-lo es l'objectiu.
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
    "name": "NIVELL 3 - EL CAP",
    "duration": 1500,            # 120 segons a 12.5 FPS
    "spawns": (
        # --- FASE 1 · L'ABORDATGE: marxa baixa, sense pressa (0-300) --------
        (15, 0, 0.30, "zigzag"),
        (45, 1, 0.55, "ona"),
        (58, 0, 0.20, "picat"),
        (90, 1, 0.45, "recta"),
        (96, 0, 0.65, "recta"),
        (110, 2, 0.35, "ona"),
        (140, 0, 0.25, "ona"),
        (185, 1, 0.60, "zigzag"),
        (218, 0, 0.40, "picat"),
        (228, 1, 0.30, "recta"),
        (260, 0, 0.50, "ona"),
        (272, 1, 0.70, "recta"),
        # --- FASE 2 · LA GORGA: murs alterns i el canal en S (300-560) -------
        (310, 2, 0.25, "recta"),
        (315, 0, 0.45, "recta"),
        (322, 1, 0.65, "zigzag"),
        (350, 0, 0.25, "ona"),
        (360, 1, 0.35, "picat"),
        (366, 0, 0.55, "ona"),
        (412, 0, 0.30, "recta"),
        (418, 2, 0.45, "ona"),
        (430, 1, 0.40, "zigzag"),
        (438, 0, 0.60, "recta"),
        (465, 1, 0.30, "ona"),
        (470, 0, 0.70, "picat"),
        (512, 2, 0.40, "ona"),
        (520, 0, 0.30, "picat"),
        (528, 1, 0.60, "recta"),
        # --- FASE 3 · L'ARENA: el pas s'obre; ultimes escortes (560-800) -----
        (565, 0, 0.20, "zigzag"),
        (580, 1, 0.30, "ona"),
        (596, 0, 0.60, "recta"),
        (610, 2, 0.50, "ona"),
        (626, 0, 0.35, "picat"),
        (640, 1, 0.25, "ona"),
        (660, 2, 0.55, "ona"),
        (680, 0, 0.40, "recta"),
        (700, 1, 0.65, "zigzag"),
        (720, 0, 0.30, "ona"),
        (740, 2, 0.50, "ona"),
        (770, 0, 0.45, "picat"),
        (785, 1, 0.35, "ona"),
        # --- FASE 4 · EL CAP: entra el cap final (800+) ----------------------
        (800, 3, 0.40, "cap"),
        (812, 1, 0.60, "recta"),   # escort solemne just darrere el cap
    ),
    "terrain": (
        # --- FASE 1 · L'ABORDATGE: crestes verdes i blaves -------------------
        {"tick": 30, "dalt": bump(3), "abaix": (),
         "vora": ("#", "92"), "cos": ("%", "32")},            # estalactita
        {"tick": 70, "dalt": (), "abaix": bump(3),
         "vora": ("#", "37"), "cos": ("%", "90")},            # cresta
        {"tick": 120, "dalt": trapei(4, 4), "abaix": trapei(4, 4),
         "vora": ("#", "96"), "cos": ("%", "94")},            # porta d'entrada
        {"tick": 200, "dalt": bump(4), "abaix": (),
         "vora": ("#", "92"), "cos": ("%", "32")},            # cadena I
        {"tick": 205, "dalt": (), "abaix": bump(4),
         "vora": ("#", "37"), "cos": ("%", "90")},            # cadena II
        {"tick": 240, "dalt": bump(4), "abaix": (),
         "vora": ("#", "92"), "cos": ("%", "32")},            # cadena III
        {"tick": 245, "dalt": (), "abaix": bump(4),
         "vora": ("#", "37"), "cos": ("%", "90")},            # cadena IV
        # --- FASE 2 · LA GORGA: murs alterns i el canal en S -----------------
        {"tick": 300, "dalt": (5,) * 10, "abaix": (),
         "vora": ("#", "37"), "cos": ("%", "90")},            # mur alt I
        {"tick": 330, "dalt": (), "abaix": (5,) * 10,
         "vora": ("#", "37"), "cos": ("%", "90")},            # mur profund II
        {"tick": 380,
         "dalt": fila(2, trapei(5, 4), 8),
         "abaix": fila(12, trapei(5, 4)),
         "vora": ("#", "96"), "cos": ("%", "94")},            # corredor en S
        {"tick": 450, "dalt": (6,) * 8, "abaix": (),
         "vora": ("#", "91"), "cos": ("%", "90")},            # tunell I
        {"tick": 490, "dalt": (), "abaix": (6,) * 8,
         "vora": ("#", "91"), "cos": ("%", "90")},            # tunell II
        {"tick": 540, "dalt": bump(4), "abaix": bump(4),
         "vora": ("#", "95"), "cos": ("%", "35")},            # porta final
        # --- FASE 3 · L'ARENA: aqui es retira el terreny ---------------------
        # (cap esdeveniment de roca mes enlla del 540: el duel contra el cap
        #  es lluita en un camp net i ample.)
    ),
}