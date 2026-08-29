"""Proves rapides del terreny i del carregador de nivells (fitxer temporal)."""
import main

# 1. Els nivells venen dels fitxers numerats, en ordre (3 antics + 1 d'art)
assert len(main.MAPS) == 4
m = main.MAPS[0]
assert m["name"] == "NIVELL 1 - PRIMER CONTACTE"
assert len(m["spawns"]) == 59, len(m["spawns"])
assert m["terrain_events"], "hauria d'haver esdeveniments de terreny"
ev_ticks = [ev[0] for ev in m["terrain_events"]]
assert ev_ticks == sorted(ev_ticks)
assert main.MAPS[1]["name"] == "NIVELL 2 - ESCULL DE FERRO"
assert len(main.MAPS[1]["spawns"]) == 84, len(main.MAPS[1]["spawns"])
assert main.MAPS[1]["terrain_events"]
assert main.MAPS[2]["name"] == "NIVELL 3 - EL CAP"
assert any(s[1] == main.BOSS_KIND for s in main.MAPS[2]["spawns"])
assert main.MAPS[2]["terrain_events"]

# 2. fit_corridor garanteix el corredor minim
t, b = main.fit_corridor(50, 50)
assert t + b <= max(0, main.SCREEN_HEIGHT - main.MIN_CORRIDOR), (t, b)
assert main.fit_corridor(1, 2) == (1, 2)
assert main.fit_corridor(0, 0) == (0, 0)

# 3. nova ronda: terreny buit
st = main.new_state()
assert st["terrain"] == []

# 4. scroll exacte d'una cel·la per tick
st["terrain"].append({"x": 0.5, "top": 3, "bot": 0,
                      "edge": ("#", "92"), "fill": ("%", "32")})
c0 = main.cell_x(st["terrain"][0]["x"])
main.update_world(st)
c1 = main.cell_x(st["terrain"][0]["x"])
assert c1 == c0 - 1, (c0, c1)

# 5. el render pinta la paret: interior a dalt i vora a la fila top-1
out = main.render(st).splitlines()
assert "%" in out[1], out[1]                       # fila 0: interior
assert "#" in out[3], out[3]                       # fila 2: vora (top-1)

# 6. tocar una paret destrueix la nau
st2 = main.new_state()
st2["player_y"] = 0.0
st2["terrain"].append({"x": st2["player_x"] + 3.0 / main.SCREEN_WIDTH,
                       "top": main.SCREEN_HEIGHT // 2, "bot": 0,
                       "edge": ("#", "91"), "fill": ("%", "90")})
main.update_world(st2)
assert st2["hp"] == 0
assert any(e["frames"] == main.BOOM_FRAMES for e in st2["effects"])

# 6b. creuament: la nau que sobrevola la columna tambe mor
st2b = main.new_state()
st2b["player_y"] = 0.0
st2b["terrain"].append({"x": st2b["player_x"] + 6.0 / main.SCREEN_WIDTH,
                        "top": main.SCREEN_HEIGHT // 2, "bot": 0,
                        "edge": ("#", "91"), "fill": ("%", "90")})
st2b["ship_prev_x"] = st2b["player_x"]
st2b["player_x"] += 8.0 / main.SCREEN_WIDTH
main.update_world(st2b)
assert st2b["hp"] == 0, "el creuament hauria de destruir la nau"

# 7. els projectils del jugador moren contra la roca
st3 = main.new_state()
st3["terrain"].append({"x": 0.5, "top": main.SCREEN_HEIGHT // 2, "bot": 0,
                       "edge": ("#", "91"), "fill": ("%", "90")})
st3["shots"].append({"x": 0.45, "y": 0.01})
main.update_world(st3)
assert st3["shots"] == [], st3["shots"]

# 7b. creuament de projectil rapid
st3b = main.new_state()
st3b["terrain"].append({"x": 0.5, "top": main.SCREEN_HEIGHT // 2, "bot": 0,
                        "edge": ("#", "91"), "fill": ("%", "90")})
st3b["shots"].append({"x": 0.48, "y": 0.01})
main.update_world(st3b)
assert st3b["shots"] == [], st3b["shots"]

# 8. simulacio completa del nivell sencer sense que la nau xoqui
durada = main.MAPS[0]["duration"]
st4 = main.new_state()
st4["player_x"] = -1.0                     # fora de pantalla: sense colisions
for _ in range(durada):
    main.update_world(st4)
assert st4["completed"]
assert st4["map_progress"] == 1.0
assert not st4["terrain"] or all(c["x"] < 1.0 for c in st4["terrain"])

# 9. garanties de disseny de TOTS els nivells: dins de durada i passables
assert len(main.MAPS) == 4, len(main.MAPS)
assert len(main.MAPS[0]["spawns"]) == 59
assert len(main.MAPS[1]["spawns"]) == 84
for idx, mapa in enumerate(main.MAPS, start=1):
    d = mapa["duration"]
    assert max(s[0] for s in mapa["spawns"]) < d, f"nivell {idx}: spawn fora"
    if mapa["terrain_events"]:
        assert max(ev[0] for ev in mapa["terrain_events"]) < d, \
            f"nivell {idx}: roca fora"
        # Cap enemic neix sobre roca: la columna que entra al seu mateix tick
        # ha d'esser lliure.
        walled = {ev[0] for ev in mapa["terrain_events"] if ev[1] or ev[2]}
        for s in mapa["spawns"]:
            assert s[0] not in walled, f"nivell {idx}: spawn sobre paret: {s}"
        # El disseny no estreny mai mes del que MIN_CORRIDOR tolera
        for ev in mapa["terrain_events"]:
            assert ev[1] + ev[2] <= main.SCREEN_HEIGHT - main.MIN_CORRIDOR, ev
    else:
        # Nivell dibuixat (art): mateixes garanties, en cel·les del dibuix.
        cols = mapa["art_columns"]
        assert cols, f"nivell {idx}: sense terreny"
        assert len(cols) <= d, f"nivell {idx}: mes art que durada"
        for x, column in enumerate(cols):
            best = run = 0
            for cell in column:
                run = run + 1 if cell is None else 0
                best = max(best, run)
            assert best >= main.MIN_CORRIDOR, (idx, x, best)
        # Cap enemic neix sobre roca: les files del seu sprite, lliures a la
        # columna del dibuix que entra al seu mateix tick.
        for tick, kind, start_y, _patro in mapa["spawns"]:
            column = cols[tick]
            y0 = min(main.ART_CANON_H - 1, max(
                0, int(round(start_y * main.ART_CANON_H))))
            y1 = min(main.ART_CANON_H - 1,
                     y0 + len(main.ENEMY_TYPES[kind]["sprite"]) - 1)
            assert all(column[y] is None for y in range(y0, y1 + 1)), \
                f"nivell {idx}: spawn sobre roca: {tick}, {start_y}"

# 10. simulacio completa del nivell 2 sense que la nau xoqui
main.CURRENT_MAP = 1
st5 = main.new_state()
st5["player_x"] = -1.0
for _ in range(main.MAPS[1]["duration"]):
    main.update_world(st5)
assert st5["completed"]
assert st5["map_progress"] == 1.0
assert not st5["terrain"] or all(c["x"] < 1.0 for c in st5["terrain"])
main.CURRENT_MAP = 0

# 11. wait_key descarta les pulsacions velles del buffer abans d'esperar
class _FakeConsole:
    """msvcrt fals: buffer amb pulsacions velles i una tecla nova al final."""

    def __init__(self, pending, fresh):
        self.pending = list(pending)
        self.fresh = fresh

    def kbhit(self):
        return bool(self.pending)

    def getwch(self):
        if self.pending:
            return self.pending.pop(0)
        return self.fresh


_orig_msvcrt = main.msvcrt
# L'escenari del bug: la nau ha estat disparant (espais al buffer) quan
# arriba el menu; cap d'aquelles tecles no ha de tancar el joc.
main.msvcrt = _FakeConsole(pending=[" ", " ", " "], fresh="r")
assert main.wait_key() == "r"
main.msvcrt = _FakeConsole(pending=[], fresh="S")
assert main.wait_key() == "s"              # una pulsacio nova es llegeix be
main.msvcrt = _orig_msvcrt

# 12. parametre de linia de comandes: nivell inicial
assert main.level_from_args(["main.py"]) is None          # sense argument
assert main.level_from_args(["main.py", "1"]) == 0
assert main.level_from_args(["main.py", "2"]) == 1
try:
    main.level_from_args(["main.py", "9"])                # fora de rang
    raise AssertionError("hauria d'haver fallat amb nivell 9")
except SystemExit as exc:
    assert exc.code == 1
try:
    main.level_from_args(["main.py", "-x"])               # no es un numero
    raise AssertionError("hauria d'haver fallat amb -x")
except SystemExit as exc:
    assert exc.code == 1
try:
    main.level_from_args(["main.py", "-h"])               # ajuda
    raise AssertionError("-h hauria de sortir amb codi 0")
except SystemExit as exc:
    assert exc.code == 0

# 13. derrotes el cap final: completa el nivell sense esperar el mapa
st6 = main.new_state()
st6["player_x"] = -1.0                     # fora de pantalla
boss = main.make_enemy(5 / main.SCREEN_WIDTH, main.BOSS_KIND)
boss["hp"] = 1                              # un toc mes i cau
boss["y"] = 0.4
boss["base_y"] = 0.4                        # sense derivacio: reflex exacte
boss["amp"] = 0.0
boss["phase"] = 0.0
st6["enemies"].append(boss)
st6["shots"].append({"x": 5 / main.SCREEN_WIDTH, "y": 0.4})
main.update_world(st6)
assert st6["completed"], f"el cap hauria de completar el nivell: {st6}"
assert boss not in st6["enemies"]
assert st6["score"] == main.ENEMY_TYPES[main.BOSS_KIND]["points"], st6["score"]

# 13b. la barra dHP del cap apareix a lHUD mentre el cap es viu
st7 = main.new_state()
st7["enemies"].append(main.make_enemy(0.9, main.BOSS_KIND))
hud_last = main.render(st7).splitlines()[-1]
assert "CAP" in hud_last, hud_last
assert f"{main.BOSS_MAX_HP}/{main.BOSS_MAX_HP}" in hud_last, hud_last

# 14. el cap no mor en el xoc: fa mal i empeny la nau cap a l'esquerra
st8 = main.new_state()
st8["player_x"] = 5 / main.SCREEN_WIDTH
st8["player_y"] = 0.4
boss2 = main.make_enemy(8 / main.SCREEN_WIDTH, main.BOSS_KIND)
boss2["y"] = 0.4
boss2["base_y"] = 0.4
boss2["amp"] = 0.0
boss2["phase"] = 0.0
boss2["hp"] = main.BOSS_MAX_HP
st8["enemies"].append(boss2)
hp0 = st8["hp"]
main.update_world(st8)
dany0 = main.ENEMY_TYPES[main.BOSS_KIND]["damage"]
assert st8["hp"] == hp0 - dany0, st8["hp"]          # dany del xoc al casc
assert boss2 in st8["enemies"]                      # el cap sobreviu
assert boss2["hp"] == main.BOSS_MAX_HP, boss2["hp"]
push_n = main.BOSS_PUSH_COLS / main.SCREEN_WIDTH
esperat_x = 8 / main.SCREEN_WIDTH - main.s_w_n(main.PLAYER_SPRITE) - push_n
assert st8["player_x"] == esperat_x, (st8["player_x"], esperat_x)

# 15. terreny dibuixat (art): normalitzacio i errors de dibuix
m4 = main.MAPS[3]
assert m4["name"] == "NIVELL 4 - GALERIES D'AUTOR"
assert m4["art_columns"] and m4["fons_columns"], "el nivell 4 es d'art"
assert m4["terrain_events"] == ()
assert len(m4["art_columns"]) == 204, len(m4["art_columns"])
assert len(m4["fons_columns"]) == 96, len(m4["fons_columns"])
assert all(len(c) == main.ART_CANON_H for c in m4["art_columns"])
PALETA_PROVA = {"x": ("#", "37")}

for dibuix, motiu in (
        ((), "art buit"),
        ((("ab",) + ("x" * 10,) * 19), "amplades desiguals"),
        ((("x" * 10,) * 19), "19 files"),
        ((("x" * 10,) * 21), "21 files"),
        ((("xy" * 5,) * 20), "caracter fora de paleta"),
        ((("x" * 10,) * 20), "paleta mal formada")):
    paleta = {} if motiu == "caracter fora de paleta" else (
        {"x": ("##", "37")} if motiu == "paleta mal formada" else PALETA_PROVA)
    try:
        main._normalize_art(dibuix, paleta, "test", "art")
        raise AssertionError(f"hauria de fallar: {motiu}")
    except ValueError:
        pass
main._normalize_art(("x" * 10,) * 20, PALETA_PROVA, "test", "art")  # be

try:   # terrain (antic) i art (nou) no poden coexistir
    main._normalize_level({"duration": 10,
                           "terrain": ({"tick": 0, "dalt": (1,)},),
                           "art": ("x" * 10,) * 20, "paleta": PALETA_PROVA},
                          "test")
    raise AssertionError("terrain+art haurien de fallar")
except ValueError:
    pass
try:   # el fons nomes te sentit amb art
    main._normalize_level({"duration": 10, "fons": ("x" * 10,) * 20,
                           "paleta_fons": PALETA_PROVA}, "test")
    raise AssertionError("fons sense art hauria de fallar")
except ValueError:
    pass

# 15b. jugabilitat del dibuix: corredor minim i BFS de connectivitat
dalt_solid = tuple((("#", "37"),) * 7 + (None,) * 13)     # lliures 7-19
baix_solid = tuple((None,) * 7 + (("#", "37"),) * 13)     # lliures 0-6
main._validate_art_playable(tuple(dalt_solid for _ in range(10)), "test")
try:   # cada columna te 13 celes lliures, pero el cami esta tallat
    main._validate_art_playable(
        tuple(dalt_solid if x < 5 else baix_solid for x in range(10)), "test")
    raise AssertionError("dibuix desconnectat hauria de fallar")
except ValueError:
    pass
try:   # columna sense corredor minim
    main._validate_art_playable(
        tuple(tuple((("#", "37"),) * 20,) for _ in range(10)), "test")
    raise AssertionError("columna segellada hauria de fallar")
except ValueError:
    pass

# 16. col·lisió de la nau: presència/absència de caracter a la cela
art_col = tuple(((("=", "36"),) * 10 + (None,) * 10))     # roca dalt, cel baix
st16 = main.new_state()
st16["terrain"].append({"x": st16["player_x"] + 2.0 / main.SCREEN_WIDTH,
                        "cells": art_col})
st16["player_y"] = 0.0                       # la nau neix a les files de roca
main.update_world(st16)
assert st16["hp"] == 0
assert any(e["frames"] == main.BOOM_FRAMES for e in st16["effects"])

st16b = main.new_state()
st16b["terrain"].append({"x": st16b["player_x"] + 2.0 / main.SCREEN_WIDTH,
                         "cells": art_col})
st16b["player_y"] = 0.6                      # files lliures: la nau passa
main.update_world(st16b)
assert st16b["hp"] == main.SHIP_MAX_HP

# 17. projectils (jugador i enemics) contra l'art: espurna i fora
st17 = main.new_state()
st17["terrain"].append({"x": 0.5, "cells": art_col})
st17["shots"].append({"x": 0.45, "y": 0.01})             # creua la roca
main.update_world(st17)
assert st17["shots"] == [] and st17["effects"], st17["effects"]

st17b = main.new_state()
st17b["terrain"].append({"x": 0.5, "cells": art_col})
st17b["shots"].append({"x": 0.45, "y": 0.55})            # creua el cel
main.update_world(st17b)
assert len(st17b["shots"]) == 1, "el tret ha de travessar el cel"

st17c = main.new_state()
st17c["terrain"].append({"x": 0.5, "cells": art_col})
st17c["enemy_shots"].append({"x": 0.49, "y": 0.01, "vx": -0.001, "vy": 0.0,
                             "damage": 5})               # dins la roca
main.update_world(st17c)
assert st17c["enemy_shots"] == [] and st17c["effects"]

st17d = main.new_state()
st17d["terrain"].append({"x": 0.5, "cells": art_col})
st17d["enemy_shots"].append({"x": 0.49, "y": 0.55, "vx": -0.001, "vy": 0.0,
                             "damage": 5})               # dins el cel
main.update_world(st17d)
assert len(st17d["enemy_shots"]) == 1

# 18. render de l'art (cel·la a cel·la) i del fons (parallax amb bucle)
st18 = main.new_state()
st18["map"] = dict(st18["map"])              # no toquem el mapa real
st18["terrain"].append({"x": 0.5, "cells": art_col})
st18["map"]["fons_columns"] = main._normalize_art(
    tuple("o" if y == 5 else " " for y in range(main.ART_CANON_H)),
    {"o": ("o", "94")}, "test", "fons")
out18 = main.render(st18).splitlines()
fila5 = out18[1 + 5]                                     # fila 5 del camp
assert fila5[40] == "=", fila5[39:42]                    # la roca tapa el fons
assert fila5.count("o") == main.SCREEN_WIDTH - 1, fila5  # cel: fons visible

st18["map"]["fons_columns"] = main._normalize_art(
    tuple("op" if y == 5 else "  " for y in range(main.ART_CANON_H)),
    {"o": ("o", "94"), "p": ("p", "34")}, "test", "fons")
st18["ticks"] = 0
out18d = main.render(st18).splitlines()
st18["ticks"] = 4                            # el fons avança 1 columna
out18b = main.render(st18).splitlines()
assert out18d[6][0] == "o" and out18d[6][1] == "p"
assert out18b[6][0] == "p" and out18b[6][1] == "o"
st18["ticks"] = 3                            # encara no toca avançar
out18c = main.render(st18).splitlines()
assert out18c[6][0] == "o" and out18c[6][1] == "p"

st18d = main.new_state()                     # el fons MAI col·lisiona
st18d["map"] = dict(st18d["map"])
st18d["map"]["fons_columns"] = st18["map"]["fons_columns"]
st18d["player_y"] = 0.26                     # la nau dins dels estels
main.update_world(st18d)
assert st18d["hp"] == main.SHIP_MAX_HP

# 19. pilot automatic amb art: illes flotants, fons ignorat i nivell sencer
illa = tuple(None if not 4 <= y <= 5 else ("%", "90")
             for y in range(main.ART_CANON_H))
st19 = main.new_state()
st19["terrain"].append({"x": st19["player_x"], "cells": illa})
banda = main._corridor_free_band(st19)       # el run lliure on es la nau
assert banda == (6 / main.SCREEN_HEIGHT, 1.0), banda
st19["map"] = dict(st19["map"])
st19["map"]["fons_columns"] = st18["map"]["fons_columns"]
assert main._corridor_free_band(st19) == banda, "el fons no pot sumar parets"
assert main._ticks_until_wall(st19, main.ship_rect(st19)) == 0.0

main.CURRENT_MAP = 3                         # simulacio completa del nivell 4
st20 = main.new_state()
st20["player_x"] = -1.0                      # fora de pantalla: sense colisions
for i in range(main.MAPS[3]["duration"]):
    main.update_world(st20)
    if i == 100:
        assert st20["terrain"], "l'art ha d'estar entrant a mig nivell"
        assert all("cells" in c for c in st20["terrain"])
assert st20["completed"] and st20["map_progress"] == 1.0
assert not st20["terrain"], "el dibuix sencer hauria d'haver creuat"
main.CURRENT_MAP = 0

print("TOT BE: 19 blocs de proves superats")
