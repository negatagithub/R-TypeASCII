"""Proves rapides del terreny i del carregador de nivells (fitxer temporal)."""
import main

# 1. Els nivells venen dels fitxers numerats, en ordre
assert len(main.MAPS) == 3
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
assert len(main.MAPS) == 3, len(main.MAPS)
assert len(main.MAPS[0]["spawns"]) == 59
assert len(main.MAPS[1]["spawns"]) == 84
for idx, mapa in enumerate(main.MAPS, start=1):
    d = mapa["duration"]
    assert max(s[0] for s in mapa["spawns"]) < d, f"nivell {idx}: spawn fora"
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

print("TOT BE: 13 blocs de proves superats")
