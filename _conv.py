# -*- coding: utf-8 -*-
"""Conversor temporal de nivell_1/2/3 al format d'art. S'esborra despres."""
import importlib.util
import math
import os
import random

import main

H = main.ART_CANON_H
FALLBACK = "rRyYwWqQeEtTuUiIoOpPsSdDfFgGhHjJkKlLzZxXvVbBnNmM"


def carrega(num):
    path = os.path.join(main.LEVELS_DIR, "nivell_%d.py" % num)
    spec = importlib.util.spec_from_file_location("_conv_%d" % num, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.LEVEL


def celles_de(top, bot, edge, fill):
    col = []
    for y in range(H):
        if y < top:
            col.append(edge if y == top - 1 else fill)
        elif y >= H - bot:
            col.append(edge if y == H - bot else fill)
        else:
            col.append(None)
    return tuple(col)


def paleta_de(events):
    """Claus de paleta: la parella (caracter, codi) mes frequent de cada
    caracter de dibuix conserva el caracter; la resta, claus de reserva."""
    freq = {}
    for _t, _top, _bot, edge, fill in events:
        for cell in (edge, fill):
            freq[cell] = freq.get(cell, 0) + 1
    ordenats = sorted(freq.items(), key=lambda kv: (-kv[1], repr(kv[0])))
    paleta, usades = {}, set()
    for (char, code), _n in ordenats:
        if char not in usades:
            paleta[(char, code)] = char
            usades.add(char)
    for (char, code), _n in ordenats:
        if (char, code) in paleta:
            continue
        for c in FALLBACK:
            if c not in usades:
                paleta[(char, code)] = c
                usades.add(c)
                break
    return paleta


def panels_de(events, paleta):
    width = max(ev[0] for ev in events) + 1
    # Fusiona events que cauen al mateix tick (segments solapats): l'efecte
    # del codi antic era generar dues columnes a la mateixa x, es a dir, la
    # UNIO de les dues parets. Per tant top/bot resulten del maxim de cada
    # segment, i l'estil es queda amb el primer (tots coincideixen al nivell).
    fusio = {}
    for ev in events:
        t, top, bot, edge, fill = ev
        if t in fusio:
            _t, p_top, p_bot, p_edge, p_fill = fusio[t]
            fusio[t] = (t, max(p_top, top), max(p_bot, bot), p_edge, p_fill)
        else:
            fusio[t] = (t, top, bot, edge, fill)
    events = [fusio[t] for t in sorted(fusio)]
    event_map = {ev[0]: ev for ev in events}
    cols = []
    for t in range(width):
        if t in event_map:
            _t, top, bot, edge, fill = event_map[t]
            cols.append(celles_de(top, bot, edge, fill))
        else:
            cols.append((None,) * H)
    rev = dict(paleta)             # cela (caracter, codi) -> clau de paleta
    panels = []
    i = 0
    while i < width:
        lliure = all(c is None for c in cols[i])
        j = i
        while j < width and all(c is None for c in cols[j]) == lliure:
            j += 1
        if lliure:
            panels.append(("cel", j - i, i, j - 1))
        else:
            rows = ["".join(" " if cols[x][y] is None else rev[cols[x][y]]
                            for x in range(i, j)) for y in range(H)]
            panels.append(("roca", rows, i, j - 1))
        i = j
    return panels, width


def fons1():
    W = 120
    G = [[" "] * W for _ in range(H)]
    random.seed(11)
    for _ in range(55):
        x, y = random.randrange(W), random.randrange(0, 12)
        if G[y][x] == " ":
            G[y][x] = "."
    for _ in range(16):
        x, y = random.randrange(W), random.randrange(0, 10)
        if G[y][x] == " ":
            G[y][x] = "*"
    cx, cy, R = 88, 6, 5
    for y in range(H):
        for x in range(W):
            d2 = (x - cx) ** 2 + ((y - cy) * 2.0) ** 2
            if d2 <= R * R:
                G[y][x] = "o" if d2 > (R - 1.2) ** 2 else "O"
    for x in range(W):
        top = 19 - (3 + int(2.5 * abs(math.sin(x * 0.19 + 0.8)))
                    + int(2.0 * abs(math.sin(x * 0.052))))
        for y in range(max(top, 14), H):
            G[y][x] = "^"
    return (["".join(r) for r in G],
            {".": (".", "90"), "*": ("*", "37"), "O": ("O", "37"),
             "o": ("o", "33"), "^": ("^", "34")})


def fons2():
    W = 128
    G = [[" "] * W for _ in range(H)]
    random.seed(22)
    for y in range(H):
        for x in range(W):
            if (x * 5 + y * 3) % 13 == 0:
                G[y][x] = "'"
    for i in range(7):
        bx = 4 + i * 19
        llarg = 9 + (i * 5) % 7
        for k in range(llarg):
            x, y = bx + k, 2 + k // 2
            if 0 <= x < W and y < 11:
                G[y][x] = "\\" if i % 2 == 0 else "/"
    for x in range(W):
        y = 11 + (x * 7) % 3
        if G[y][x] == " ":
            G[y][x] = "_"
    return (["".join(r) for r in G],
            {"'": ("'", "94"), "\\": ("\\", "90"), "/": ("/", "90"),
             "_": ("_", "33")})


def fons3():
    W = 120
    G = [[" "] * W for _ in range(H)]
    random.seed(33)
    for _ in range(110):
        x, y = random.randrange(W), random.randrange(0, 14)
        if G[y][x] == " ":
            G[y][x] = ":"
    for _ in range(9):
        x, y = random.randrange(W), random.randrange(0, 9)
        if G[y][x] == " ":
            G[y][x] = "*"
    for b in range(4):
        x = 14 + b * 29 + (b * 7) % 9
        y = 0
        while y < 9:
            G[y][x % W] = "/"
            if y % 2 == 1:
                x += 1
            y += 1
    for x in range(W):
        top = 19 - (2 + int(2.2 * abs(math.sin(x * 0.17 + 2.0)))
                    + int(1.6 * abs(math.sin(x * 0.043))))
        for y in range(max(top, 15), H):
            G[y][x] = "^"
    return (["".join(r) for r in G],
            {":": (":", "31"), "*": ("*", "91"), "/": ("/", "93"),
             "^": ("^", "31")})


def esc(s):
    return s.replace("\\", "\\\\")


def emet_panels(panels):
    parts = []
    for idx, p in enumerate(panels, start=1):
        if p[0] == "cel":
            parts.append("        cel(%d)," % p[1])
        else:
            parts.append("        PANELL_%02d," % idx)
    return "\n".join(parts)


def emet_rock_panels(panels):
    blocks = []
    for idx, p in enumerate(panels, start=1):
        if p[0] != "roca":
            continue
        blocks.append(
            "# Roca del tick %d al %d (%d columnes)\nPANELL_%02d = (\n%s\n)"
            % (p[2], p[3], p[3] - p[2] + 1, idx,
               "\n".join('    "%s",' % esc(r) for r in p[1])))
    return "\n\n".join(blocks)


def emet_spawns(spawns, fases):
    lines = []
    fase = 0
    for s in spawns:
        while fase < len(fases) and s[0] >= fases[fase][0]:
            tick, nom = fases[fase]
            lines.append("        # --- %s (des del tick %d) ---" % (nom, tick))
            fase += 1
        lines.append('        (%d, %d, %r, "%s"),' % s)
    return "\n".join(lines)


def escriu(num, doc, fases, fons_fn, nom_fons):
    level = carrega(num)
    events = main._normalize_terrain(level.get("terrain", ()),
                                     "nivell_%d.py" % num)
    paleta = paleta_de(events)
    panels, width = panels_de(events, paleta)
    fons_rows, fons_pal = fons_fn()
    L = []
    L.append('"""%s"""' % doc)
    L.append("")
    L.append("FILES = 20                    # ART_CANON_H: files de tot dibuix")
    L.append("")
    L.append("PALETA = {")
    for (char, code), key in sorted(paleta.items(), key=lambda kv: kv[1]):
        L.append('    "%s": ("%s", "%s"),' % (esc(key), esc(char), code))
    L.append("}")
    L.append("")
    L.append("PALETA_FONS = {")
    for key, (char, code) in fons_pal.items():
        L.append('    "%s": ("%s", "%s"),' % (esc(key), esc(char), code))
    L.append("}")
    L.append("")
    L.append("")
    L.append("def junta(*paneles):")
    L.append('    """Enganxa panells de 20 files horitzontalment en un sol dibuix."""')
    L.append('    return tuple("".join(fila) for fila in zip(*paneles))')
    L.append("")
    L.append("")
    L.append("def cel(n):")
    L.append('    """Panel de cel obert: n columnes del tot lliures."""')
    L.append('    return (" " * n,) * FILES')
    L.append("")
    L.append("")
    L.append(emet_rock_panels(panels))
    L.append("")
    L.append("# Fons: %s (es repeteix en bucle, %d columnes)"
             % (nom_fons, len(fons_rows[0])))
    L.append("FONS = (")
    for r in fons_rows:
        L.append('    "%s",' % esc(r))
    L.append(")")
    L.append("")
    L.append("")
    L.append("LEVEL = {")
    L.append('    "name": %r,' % level["name"])
    L.append('    "duration": %d,' % level["duration"])
    L.append('    "paleta": PALETA,')
    L.append('    "art": junta(')
    L.append(emet_panels(panels))
    L.append("    ),")
    L.append('    "paleta_fons": PALETA_FONS,')
    L.append('    "fons": FONS,')
    L.append('    "spawns": (')
    L.append(emet_spawns(level["spawns"], fases))
    L.append("    ),")
    L.append("}")
    with open("nivell_%d.py" % num, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("nivell_%d.py: %d columnes d'art, %d de fons, paleta de %d claus"
          % (num, width, len(fons_rows[0]), len(paleta)))


DOC1 = """Nivell 1 de R-Type ASCII: PRIMER CONTACTE.

Cada nivell viu en un fitxer propi numerat (nivell_1.py, nivell_2.py...) al
costat de main.py; el joc els carrega tots en ordre numeric en arrencar.

Aquest nivell va ser CONVERTIT AUTOMATICAMENT des de l'antic format
d'elevacions a la v0.6.0: conserva exactament els mateixos perfils de roca,
colors (vora i cos de cada segment) i temps d'entrada de cada columna. El
terreny es DIBUIXAT (format 'art'; la referencia completa del format es el
docstring de nivell_4.py): FILES de dibuix, una columna del dibuix per cada
columna del nivell; tot caracter de PALETA es solid i l'espai es lliure. El
fons (estels, un planeta llunya i muntanyes fosques) es purament estetic i
avanca mes lent que el primer pla.

Dura 1800 ticks (uns 144 segons a 12.5 FPS) en cinc fases de dificultat
creixent:

  1. BENVINGUDA      bumps petits per aprendre la mecanica de les parets.
  2. PRIMERES ROQUES crestes i estalactites alternades, primeres parelles.
  3. EL CANAL EN S   corredor que baixa i puja + porta vermella amb cristall.
  4. LES PINCES      dalt i baix tanquen alhora; murs amb una sola sortida.
  5. ESPRINT FINAL   cadena ritmica de bumps, tunell i gran porta final.

Els enemics no xoquen amb la roca; cap spawn cau sobre una columna amb roca.
"""

FASES1 = [(0, "FASE 1 - BENVINGUDA"),
          (400, "FASE 2 - PRIMERES ROQUES"),
          (700, "FASE 3 - EL CANAL EN S"),
          (1000, "FASE 4 - LES PINCES"),
          (1400, "FASE 5 - ESPRINT FINAL")]

DOC2 = """Nivell 2 de R-Type ASCII: ESCULL DE FERRO.

Segon nivell de la campanya, mes dur que el primer: corredors mes estrets
(minim de 8 celes al pic, contra les 10 del nivell 1), murs de 10 files i
gaire be el doble de densitat d'enemics (84 esdeveniments en 1800 ticks).

Aquest nivell va ser CONVERTIT AUTOMATICAMENT des de l'antic format
d'elevacions a la v0.6.0: conserva exactament els mateixos perfils de roca,
colors (cada estil de vora/cos te la seva clau a PALETA) i temps d'entrada
de cada columna. El terreny es DIBUIXAT (format 'art'; la referencia
completa del format es el docstring de nivell_4.py). El fons (pluja tenu,
bigues trencades i restes de casc enfonsat) es purament estetic i avanca
mes lent que el primer pla.

Fases d'aquest nivell (dificultat creixent):

  1. LA PORTA        comencem amb una porta de 10 celes de corredor.
  2. L'ESTRET        murs de 8 files alternats i bumps en cadena rapida.
  3. LA GORGA        corredor en S doble, tunell estret i porta de cristall.
  4. L'ESCULL        murs de 10 files, serra triple i la pinca mes cruel.
  5. TEMPESTA FINAL  cadena de bumps cada 10 ticks i la gola final.
"""

FASES2 = [(0, "FASE 1 - LA PORTA"),
          (350, "FASE 2 - L'ESTRET"),
          (720, "FASE 3 - LA GORGA"),
          (1100, "FASE 4 - L'ESCULL"),
          (1500, "FASE 5 - TEMPESTA FINAL")]

DOC3 = """Nivell 3 de R-Type ASCII: EL CAP.

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

FASES3 = [(0, "FASE 1 - L'ABORDATGE"),
          (300, "FASE 2 - LA GORGA"),
          (560, "FASE 3 - L'ARENA"),
          (800, "FASE 4 - EL CAP")]

if __name__ == "__main__":
    escriu(1, DOC1, FASES1, fons1, "estels, planeta llunya i muntanyes")
    escriu(2, DOC2, FASES2, fons2, "pluja i restes de ferro")
    escriu(3, DOC3, FASES3, fons3, "tempesta vermella i llamps")

