"""Nivell 1 de R-Type ASCII: PRIMER CONTACTE.

Cada nivell viu en un fitxer propi numerat (nivell_1.py, nivell_2.py...) al
costat de main.py; el joc els carrega tots en ordre numeric en arrencar.

El diccionari LEVEL admet aquestes claus:

  name     Nom del nivell (es mostra a la pantalla d'introduccio).
  duration Ticks totals del mapa: la partida acaba en arribar-hi.
  spawns   Sequencia de tuples (tick, tipus d'enemic, fila inicial, patro).
           - tipus: 0 dron, 1 caça, 2 creuer
           - fila: alçada inicial normalitzada (0..1), relativa al camp
           - patro: "recta", "ona", "zigzag", "picat" o "puja"
  terrain  Sequencia de segments de paret (opcional). Cada segment:
             "tick"   Tick en que la primera columna entra per la dreta.
             "dalt"   Elevacio EN CEL·LES de la paret superior: UN VALOR PER
                      CADA columna del segment (0 = no hi ha paret).
             "abaix"  El mateix per a la paret inferior.
             "vora"   (caracter, color ANSI) de la superficie de la paret,
                      la cel·la que mira al corredor.
             "cos"    (caracter, color ANSI) de l'interior de la paret.
             "estils" Substitucions puntuals per columna concreta: cada
                      entrada es None o un dict {"vora": (...), "cos": (...)}.
           Les columnes avancen cap a l'esquerra UNA cel·la per tick, aixi
           que segments de ticks consecutius formen parets contigues. Tocar
           una paret amb la nau la destrueix; si un disseny estreny massa el
           pas per al terminal actual, el joc escala les elevacions deixant
           sempre MIN_CORRIDOR celes lliures de corredor.

Aquest nivell dura 1800 ticks (uns 144 segons a 12.5 FPS) i s'estructura en
cinc fases de dificultat creixent:

  1. BENVINGUDA      bumps petits per aprendre la mecanica de les parets.
  2. PRIMERES ROQUES crestes i estalactites alternades, primeres parelles.
  3. EL CANAL EN S   corredor que baixa i puja + porta vermella amb cristall.
  4. LES PINCES      dalt i baix tanquen alhora; murs amb una sola sortida.
  5. ESPRINT FINAL   cadena ritmica de bumps, tunell i gran porta final.

Els enemics no xoquen amb la roca (la sobrevolen), pero el disseny evita
igualment que neixin dins d'una columna emmurallada: cap tick de spawn
coincideix amb una columna de paret.
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
    "name": "NIVELL 1 - PRIMER CONTACTE",
    "duration": 1800,            # 144 segons a 12.5 FPS
    "spawns": (
        # --- FASE 1 · BENVINGUDA: enemics solts, sense pressa (0-400) ------
        (2, 0, 0.18, "recta"),
        (60, 0, 0.72, "ona"),
        (150, 0, 0.52, "recta"),
        (240, 1, 0.35, "zigzag"),
        (330, 0, 0.82, "picat"),
        (345, 2, 0.20, "ona"),
        (390, 0, 0.30, "zigzag"),
        (420, 1, 0.60, "ona"),
        # --- FASE 2 · PRIMERES ROQUES: parelles i petits trios (400-700) ---
        (440, 0, 0.15, "recta"),
        (475, 1, 0.42, "picat"),
        (505, 0, 0.78, "zigzag"),
        (535, 2, 0.45, "ona"),
        (600, 0, 0.25, "recta"),
        (600, 0, 0.75, "recta"),
        (630, 1, 0.50, "recta"),
        (655, 0, 0.30, "zigzag"),
        (655, 0, 0.70, "zigzag"),
        (655, 1, 0.50, "zigzag"),
        # --- FASE 3 · EL CANAL EN S: pressio creixent (700-1000) -----------
        (710, 2, 0.20, "ona"),
        (710, 2, 0.80, "ona"),
        (745, 0, 0.40, "picat"),
        (760, 0, 0.60, "picat"),
        (795, 0, 0.35, "recta"),
        (795, 1, 0.65, "recta"),
        (860, 2, 0.50, "zigzag"),
        (880, 0, 0.25, "ona"),
        (880, 1, 0.75, "ona"),
        (915, 0, 0.30, "picat"),
        (915, 1, 0.70, "picat"),
        (970, 2, 0.50, "recta"),
        # --- FASE 4 · LES PINCES: lluitar en espai estret (1000-1400) ------
        (1040, 0, 0.40, "zigzag"),
        (1040, 1, 0.60, "zigzag"),
        (1075, 0, 0.25, "ona"),
        (1075, 1, 0.75, "ona"),
        (1100, 2, 0.50, "recta"),
        (1145, 0, 0.55, "recta"),
        (1180, 0, 0.25, "recta"),
        (1205, 1, 0.60, "recta"),
        (1260, 2, 0.50, "ona"),
        (1285, 0, 0.35, "recta"),
        (1285, 1, 0.65, "recta"),
        (1310, 0, 0.40, "zigzag"),
        (1310, 1, 0.60, "zigzag"),
        (1375, 2, 0.50, "picat"),
        # --- FASE 5 · ESPRINT FINAL: agitacio maxima (1400-1800) -----------
        (1408, 0, 0.25, "ona"),
        (1408, 1, 0.75, "ona"),
        (1450, 0, 0.50, "recta"),
        (1462, 1, 0.50, "recta"),
        (1520, 2, 0.50, "ona"),
        (1540, 0, 0.35, "zigzag"),
        (1540, 1, 0.65, "zigzag"),
        (1600, 0, 0.25, "ona"),
        (1600, 1, 0.75, "ona"),
        (1630, 2, 0.50, "picat"),
        (1660, 0, 0.40, "recta"),
        (1660, 1, 0.60, "recta"),
        (1730, 2, 0.50, "ona"),
        (1760, 0, 0.30, "recta"),
        (1760, 1, 0.70, "recta"),
    ),
    "terrain": (
        # --- FASE 1 · BENVINGUDA: bumps petits, verds i grisos ---------------
        {"tick": 120, "dalt": bump(3), "abaix": (),
         "vora": ("#", "92"), "cos": ("%", "32")},            # estalactita
        {"tick": 200, "dalt": (), "abaix": bump(3),
         "vora": ("#", "37"), "cos": ("%", "90")},            # bump al terra
        {"tick": 280, "dalt": bump(4), "abaix": (),
         "vora": ("#", "92"), "cos": ("%", "32")},            # estalactita gran
        # --- FASE 2 · PRIMERES ROQUES: alterna dalt i baix -------------------
        {"tick": 380, "dalt": (), "abaix": bump(5),
         "vora": ("#", "37"), "cos": ("%", "90")},            # cresta
        {"tick": 460, "dalt": bump(5), "abaix": (),
         "vora": ("#", "37"), "cos": ("%", "90")},            # estalactita
        {"tick": 560,
         "dalt": fila(bump(4), 9),
         "abaix": fila(5, bump(4), 4),
         "vora": ("#", "37"), "cos": ("%", "90")},            # doble desalineada
        # --- FASE 3 · EL CANAL EN S -------------------------------------------
        {"tick": 680,
         "dalt": fila(2, trapei(5, 2), 7),
         "abaix": fila(9, trapei(5, 2)),
         "vora": ("#", "96"), "cos": ("%", "94")},            # corredor en S
        {"tick": 820,
         "dalt": trapei(6, 4), "abaix": trapei(6, 4),
         "vora": ("#", "91"), "cos": ("%", "90"),
         "estils": (None,) * 7
                   + ({"vora": ("@", "95"), "cos": ("%", "95")},)
                   + (None,) * 7},                            # porta + cristall
        {"tick": 940, "dalt": (), "abaix": bump(3),
         "vora": ("#", "37"), "cos": ("%", "90")},            # respiro
        # --- FASE 4 · LES PINCES ----------------------------------------------
        {"tick": 1020, "dalt": bump(4), "abaix": bump(4),
         "vora": ("#", "95"), "cos": ("%", "35")},            # pinça suau
        {"tick": 1120, "dalt": (7,) * 12, "abaix": (),
         "vora": ("#", "91"), "cos": ("%", "90")},            # mur amb forat I
        {"tick": 1160, "dalt": (), "abaix": (7,) * 12,
         "vora": ("#", "91"), "cos": ("%", "90")},            # mur amb forat II
        {"tick": 1240, "dalt": trapei(6, 4), "abaix": trapei(6, 4),
         "vora": ("#", "95"), "cos": ("%", "35")},            # pinça forta
        {"tick": 1340,
         "dalt": fila(bump(4), 8, bump(4)),
         "abaix": fila(11, bump(4), 4),
         "vora": ("#", "95"), "cos": ("%", "35")},            # serra doble
        # --- FASE 5 · ESPRINT FINAL --------------------------------------------
        {"tick": 1440, "dalt": bump(4), "abaix": (),
         "vora": ("#", "93"), "cos": ("%", "33")},            # cadena ritmica
        {"tick": 1452, "dalt": (), "abaix": bump(4),
         "vora": ("#", "93"), "cos": ("%", "33")},
        {"tick": 1464, "dalt": bump(4), "abaix": (),
         "vora": ("#", "93"), "cos": ("%", "33")},
        {"tick": 1476, "dalt": (), "abaix": bump(4),
         "vora": ("#", "93"), "cos": ("%", "33")},
        {"tick": 1488, "dalt": bump(4), "abaix": (),
         "vora": ("#", "93"), "cos": ("%", "33")},
        {"tick": 1560, "dalt": (5,) * 14, "abaix": (5,) * 14,
         "vora": ("#", "97"), "cos": ("%", "90")},            # tunell blanc
        {"tick": 1680,
         "dalt": trapei(6, 8), "abaix": trapei(6, 8),
         "vora": ("#", "91"), "cos": ("%", "90"),
         "estils": (None,) * 9
                   + ({"vora": ("@", "95"), "cos": ("%", "95")},)
                   + (None,) * 9},                            # gran porta final
    ),
}