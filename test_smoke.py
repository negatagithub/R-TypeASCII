"""Suite de proves headless del motor (main.py): logica pura sense terminal.

No toca la consola real: desactiva els spawns aleatoris, el teclat i els
sleeps, fixa un camp 60x18 i ailla cada estat del mapa de nivell (cap spawn
ni terreny dels fitxers nivell_<n>.py no pot contaminar els tests).
Sortida: una linia PASS/FAIL per comprovacio i, al final, el resum amb codi
d'exit (0 = tot be, 1 = hi ha fallides).
"""
import contextlib
import io
import math
import random
import re
import sys

import main as g

failures = []


def check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    if not cond:
        failures.append(name)


ANSI_RE = re.compile("\x1b\\[[0-9;]*m")


def strip_ansi(s):
    """Elimina els codis de color per poder mesurar text visible."""
    return ANSI_RE.sub("", s)


g.msvcrt = None                       # mode headless
g.clear_screen = lambda: None
g.time.sleep = lambda s: None
g.BASE_SPAWN_CHANCE = 0.0
g.RAMP_PER_MINUTE = 0.0
random.seed(42)

ORIG_W, ORIG_H = g.SCREEN_WIDTH, g.SCREEN_HEIGHT
g.SCREEN_WIDTH, g.SCREEN_HEIGHT = 60, 18

orig_new_state = g.new_state


def quiet(px, py, enemies=None):
    """Estat amb spawn aleatori desactivat i posicio normalitzada controlada.

    Tambe ailla l'estat dels fitxers de nivell: sense aixo, update_world()
    executaria els spawns i el terreny de nivell_<n>.py dins del test (p. ex.
    un dron del mapa apareixia al tick 2 i trencaria qualsevol assercio del
    tipus "enemies == []").
    """
    st = orig_new_state()
    st["map"] = {"name": "TEST", "duration": 10 ** 9,
                 "spawns": (), "terrain_events": ()}
    st["spawn_chance"] = 0.0
    st["player_x"], st["player_y"] = px, py
    if enemies is not None:
        st["enemies"] = enemies
    return st


def mk(kind, x, y, pattern="recta"):
    """Enemic del tipus demanat en posicio normalitzada i patro controlat."""
    en = g.make_enemy(x, kind)
    en["y"] = y
    en["pattern"] = pattern
    return en


def col(c):
    """Columna de pantalla -> posicio normalitzada."""
    return c / g.SCREEN_WIDTH


def row(r):
    """Fila de pantalla -> posicio normalitzada."""
    return r / g.SCREEN_HEIGHT


def isclose(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)


DRONE, FIGHTER, CRUISER = 0, 1, 2

# --- 1. ajust de la mida al terminal -----------------------------------------
try:
    g.shutil.get_terminal_size = lambda: (100, 30)
    g.fit_playfield_to_terminal()
    check("fit uses full terminal", (g.SCREEN_WIDTH, g.SCREEN_HEIGHT) == (98, 25))
    g.shutil.get_terminal_size = lambda: (20, 8)
    g.fit_playfield_to_terminal()
    check("fit respects minimums", (g.SCREEN_WIDTH, g.SCREEN_HEIGHT) == (40, 10))
finally:
    g.shutil.get_terminal_size = lambda: (ORIG_W, ORIG_H)
    g.SCREEN_WIDTH, g.SCREEN_HEIGHT = 60, 18   # mida base d'aquesta suite

# --- 2. espai normalitzat: conversio a cel.les --------------------------------
check("cell_x rounds to column", g.cell_x(col(3)) == 3 and g.cell_x(1.0) == 59)
check("cell_y rounds to row", g.cell_y(row(7)) == 7 and g.cell_y(1.0) == 17)
check("normalized sizes", isclose(g.s_w_n(g.PLAYER_SPRITE), 5 / 60)
      and isclose(g.s_h_n(g.PLAYER_SPRITE), 3 / 18))
check("new state in normalized space",
      isclose(orig_new_state()["player_x"], 2 / 60)
      and isclose(orig_new_state()["player_y"], 0.5))

# --- 3. moviment de la nau (pas fraccional, limits normalitzats) --------------
st = quiet(0.5, 0.5)
g.move_player(st, dy=-1)
check("move up one row step", isclose(st["player_y"], 0.5 - 1 / 18))
g.move_player(st, dy=+1)
check("move down one row step", isclose(st["player_y"], 0.5))
g.move_player(st, dx=-1)
check("move back one col step",
      isclose(st["player_x"], 0.5 - g.PLAYER_HORIZONTAL_SPEED / 60))
g.move_player(st, dx=+1)
check("move forward one col step", isclose(st["player_x"], 0.5))
st = quiet(0.5, 0.0)
g.move_player(st, dy=-1)
check("clamped at top edge", st["player_y"] == 0.0)
maxy = 1.0 - g.s_h_n(g.PLAYER_SPRITE)
st = quiet(0.5, maxy)
g.move_player(st, dy=+1)
check("clamped so sprite fits bottom", isclose(st["player_y"], maxy))
st = quiet(0.9, 0.5)
g.move_player(st, dx=+1)
check("forward capped at right edge",
      isclose(st["player_x"], 1.0 - g.s_w_n(g.PLAYER_SPRITE)))

# --- 4. dispar, cooldown i viatge de projectils ------------------------------
st = quiet(0.3, 0.5)
g.shoot(st)
nosex = st["player_x"] + g.s_w_n(g.PLAYER_SPRITE)
nosey = st["player_y"] + g.h_n(g.PLAYER_H // 2)
check("shot from nose center",
      len(st["shots"]) == 1 and isclose(st["shots"][0]["x"], nosex)
      and isclose(st["shots"][0]["y"], nosey))
check("cooldown armed", st["shot_cooldown"] == g.SHOT_COOLDOWN_TICKS)
g.shoot(st)
check("cooldown blocks spamming", len(st["shots"]) == 1)
st = quiet(0, 0)
st["shots"] = [{"x": col(10), "y": row(3)}]
g.update_world(st)
check("shot advances SHOT_SPEED columns",
      isclose(st["shots"][0]["x"], col(10 + int(g.SHOT_SPEED))))
st["shots"] = [{"x": col(59), "y": row(3)}]
g.update_world(st)
check("off-screen shot removed", st["shots"] == [])

# --- 5. impactes per creuament en espai normalitzat ----------------------------
st = quiet(0, 0)
st["shots"] = [{"x": col(19), "y": row(6)}]
st["enemies"] = [mk(DRONE, col(20), row(6))]
g.update_world(st)
check("crossing kills small drone", st["shots"] == [] and st["enemies"] == [])
check("drone worth 10", st["score"] == 10)
st = quiet(0, 0)
st["shots"] = [{"x": col(19), "y": row(6)}]
f = mk(FIGHTER, col(22), row(6))
st["enemies"] = [f]
g.update_world(st)
# El tret es rapid (SHOT_SPEED celes/tick): creua el cacic en un sol tick,
# de manera que el solapament i el creuament aterren el mateix cop.
check("fast shot crosses and lands in one tick",
      f["hp"] == 1 and st["shots"] == [])
check("no points until the kill", st["score"] == 0)
st["shots"] = [{"x": f["x"] - 1 / 60, "y": row(6)}]
g.update_world(st)
check("fighter dies on second hit", st["shots"] == [] and st["enemies"] == [])
check("fighter worth 30", st["score"] == 30)
st = quiet(0, 0)
cruiser = mk(CRUISER, col(30), row(5))
st["enemies"] = [cruiser]
for expected_hp in (3, 2, 1):
    st["shots"] = [{"x": cruiser["x"] - 1 / 60, "y": row(5)}]
    g.update_world(st)
    check(f"cruiser holds at {expected_hp} hp",
          st["enemies"] == [cruiser] and cruiser["hp"] == expected_hp)
st["shots"] = [{"x": cruiser["x"] - 1 / 60, "y": row(5)}]
g.update_world(st)
check("cruiser dies after 4 hits", st["enemies"] == [])
check("cruiser worth 80", st["score"] == 80)
st = quiet(0, 0)
st["shots"] = [{"x": col(19), "y": row(3)}]
st["enemies"] = [mk(DRONE, col(20), row(6))]
g.update_world(st)
check("no hit on different row",
      len(st["shots"]) == 1 and len(st["enemies"]) == 1)

# --- 6. velocitats, sortida gradual i col.lisions ------------------------------
st = quiet(0, 0)
d, f = mk(DRONE, col(40), row(2)), mk(FIGHTER, col(40), row(8))
st["enemies"] = [d, f]
g.update_world(st)
check("drone is twice as fast",
      isclose(d["x"], col(38)) and isclose(f["x"], col(39)))
st = quiet(0, 0)
st["enemies"] = [mk(DRONE, col(0), row(4))]
# L'enemic nomes desapareix quan el seu rectangle s'ha sortit del tot:
# amb el morro dins del camp encara es visible (i colisionable).
ticks_alive = 0
while st["enemies"] and ticks_alive < 10:
    g.update_world(st)
    ticks_alive += 1
check("small enemy exits once fully off-screen",
      st["enemies"] == [] and 0 < ticks_alive <= 10)
wide = mk(FIGHTER, col(0), row(4))
st = quiet(0, 0)
st["enemies"] = [wide]
g.update_world(st)
check("wide enemy lingers while visible",
      st["enemies"] == [wide] and wide["x"] < 0.0)
for _ in range(3):
    g.update_world(st)
check("wide enemy exits eventually", st["enemies"] == [])

st = quiet(col(10), row(9))
st["enemies"] = [mk(DRONE, col(14), row(10))]
check("touching rect collides", g.find_collision(st) is not None)
st["enemies"] = [mk(DRONE, col(15), row(10))]
check("one cell apart is safe", g.find_collision(st) is None)
st["enemies"] = [mk(FIGHTER, col(11), row(7))]
check("edge-touching rows safe", g.find_collision(st) is None)
st["enemies"] = [mk(FIGHTER, col(11), row(8))]
check("overlapping rows collide", g.find_collision(st) is not None)
st["enemies"] = [mk(CRUISER, col(18), row(12))]
check("far cruiser is safe", g.find_collision(st) is None)

# --- 7. renderitzat monocrom i colors ----------------------------------------
g.COLOR_ENABLED = False
st = quiet(col(3), row(8))
st["shots"].append({"x": col(15), "y": row(9)})
st["enemies"] = [mk(DRONE, col(30), row(2)),
                 mk(FIGHTER, col(20), row(4)),
                 mk(CRUISER, col(24), row(12))]
text = g.render(st)
lines = text.splitlines()
field = lines[1:-1]
check("hud + field + status height", len(lines) == g.SCREEN_HEIGHT + 2)
check("no escapes when disabled", "\x1b" not in text)
check("row width consistent", all(len(r) == g.SCREEN_WIDTH for r in field))
# La nau te 3 files: ales a dalt i a baix (col 6) i cos amb morro al mig.
check("ship top fin drawn at its cell", field[8][6] == "/")
check("ship body drawn at its cell", field[9][3] == "}")
check("ship nose drawn at its cell", field[9][7] == "=")
check("ship keel drawn at its cell", field[10][6] == "\\")
check("drone drawn", field[2][30] == "<" and field[2][31] == "e")
check("fighter drawn", field[4][20] == "<" and field[5][22] == "~")
check("cruiser drawn", field[12][24] == "<" and field[13][25] == "#")
check("shot drawn", field[9][15] == "-")
g.COLOR_ENABLED = True
colored = g.render(st)
clines = colored.splitlines()
for code in ("96", "93", "91", "95", "94", "97"):
    check(f"color {code} emitted", f"\x1b[{code}m" in colored)
stripped = [strip_ansi(r) for r in clines]
check("colored widths match after strip",
      all(len(r) == g.SCREEN_WIDTH for r in stripped[1:-1]))
check("ship cells painted cyan", "\x1b[96m==" in clines[10])
g.COLOR_ENABLED = False

# --- 8. draw_frame: repintat sense parpalleig ---------------------------------
g.COLOR_ENABLED = True
g._first_frame = True
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    g.draw_frame("FRAME-A")
    g.draw_frame("FRAME-B")
out = buf.getvalue()
check("full clear only on first frame", out.count("\x1b[2J") == 1)
check("frames rehome cursor", out.count("\x1b[H") >= 2)
g.COLOR_ENABLED = False
g._first_frame = True
cls_calls = {"n": 0}
g.clear_screen = lambda: cls_calls.__setitem__("n", cls_calls["n"] + 1)
with contextlib.redirect_stdout(io.StringIO()):
    g.draw_frame("F1")
    g.draw_frame("F2")
check("monochrome fallback clears each frame", cls_calls["n"] == 2)

# --- 9. efectes d'impacte ------------------------------------------------------
st = quiet(0, 0)
st["shots"] = [{"x": col(19), "y": row(6)}]
st["enemies"] = [mk(DRONE, col(20), row(6))]
g.update_world(st)
sparks = [e for e in st["effects"]
          if tuple(e["frames"]) == tuple(g.SPARK_FRAMES)]
booms = [e for e in st["effects"]
         if tuple(e["frames"]) == tuple(g.BOOM_FRAMES)]
# El dron (amplada 3) ja arriba al llindar d'explosio gran: espurna de
# l'impacte + deflagracio al centre de la baixa.
check("drone kill makes one spark and one boom",
      len(sparks) == 1 and len(booms) == 1)
for _ in range(len(g.SPARK_FRAMES)):
    g.update_world(st)
check("effects fade out completely", st["effects"] == [])
st = quiet(0, 0)
fighter = mk(FIGHTER, col(22), row(6))
st["enemies"] = [fighter]
st["shots"] = [{"x": col(15), "y": row(6)}]
g.update_world(st)                       # aproximacio sense contacte
check("approach does not hit yet",
      fighter["hp"] == 2 and len(st["shots"]) == 1)
st["shots"] = [{"x": fighter["x"] - 1 / 60, "y": row(6)}]
g.update_world(st)                       # primer toc (no letal)
sparks = [e for e in st["effects"]
          if tuple(e["frames"]) == tuple(g.SPARK_FRAMES)]
check("non-lethal hit makes one spark",
      len(sparks) == 1 and fighter["hp"] == 1)
ex, ey, ew, eh = g.enemy_rect(fighter)
# Amb el creuament, l'espurna cau on aterra el tret: l'efecte es CENTRA a la
# posicio de l'impacte (per aixo restem mig caracter a l'alçada) i queda dins
# d'un pas de tret (SHOT_SPEED celes) comptat des del davant de l'enemic.
check("spark lands within a shot-step of the enemy",
      isclose(sparks[0]["y"], row(6) - 0.5 / 18)
      and 0 <= sparks[0]["x"] - (ex + ew) <= g.SHOT_SPEED / 60 + 1e-9)
st["shots"] = [{"x": fighter["x"] - 1 / 60, "y": row(6)}]
g.update_world(st)                       # toc letal
booms = [e for e in st["effects"]
         if tuple(e["frames"]) == tuple(g.BOOM_FRAMES)]
check("big enemy death makes big boom",
      len(booms) == 1 and st["enemies"] == [])

# --- 10. patrons de moviment ---------------------------------------------------
st = quiet(0, 0)
floor_row = 1.0 - g.s_h_n(g.ENEMY_TYPES[FIGHTER]["sprite"])
zz = mk(FIGHTER, col(40), floor_row, pattern="zigzag")
zz["vy"] = 1                            # baixa: la vora l'ha de fer rebotar
st["enemies"] = [zz]
g.update_world(st)
check("zigzag bounces off the floor",
      isclose(zz["y"], floor_row) and zz["vy"] == -1)

st = quiet(0, 0)
dv = mk(FIGHTER, col(40), row(2), pattern="picat")
st["enemies"] = [dv]
g.update_world(st)
check("dive drops two rows", isclose(dv["y"], row(4)))
while dv["y"] < floor_row - 1e-9:
    g.update_world(st)
check("dive levels off at the floor", isclose(dv["y"], floor_row))
straight_x = dv["x"]
g.update_world(st)
check("diver goes straight after landing",
      isclose(dv["y"], floor_row) and isclose(dv["x"], straight_x - 1 / 60))

st = quiet(0, 0)
up = mk(FIGHTER, col(40), row(10), pattern="puja")
st["enemies"] = [up]
for _ in range(12):
    g.update_world(st)
check("riser parks at the ceiling", up["y"] == 0.0)

st = quiet(0, 0)
wv = mk(DRONE, col(50), row(8), pattern="ona")
wv.update({"amp": 3 / 18, "base_y": row(8), "phase": 0.0})
st["enemies"] = [wv]
ys = []
for _ in range(24):
    g.update_world(st)
    ys.append(wv["y"])
check("wave stays within amplitude",
      all(abs(y - row(8)) <= (3 / 18 + 1 / 18) for y in ys))
check("wave actually oscillates", len(set(ys)) > 1)
random.seed(11)
okp = True
for _ in range(100):
    en = g.make_enemy(1.5)
    okp = okp and en["pattern"] in g.KIND_PATTERNS[en["kind"]]
check("spawned patterns belong to their kind", okp)

# --- 11. casc, danys ponderats i barra de vida ---------------------------------
check("hull starts full", orig_new_state()["hp"] == g.SHIP_MAX_HP)
st = quiet(col(10), row(9))
st["enemies"] = [mk(DRONE, col(14), row(10))]
g.update_world(st)
check("drone crash deals 10 damage", st["hp"] == g.SHIP_MAX_HP - 10)
check("crashed enemy is destroyed", st["enemies"] == [])
check("crash spawns explosion effect", len(st["effects"]) >= 1)
st = quiet(col(10), row(9))
before = st["hp"]
st["enemies"] = [mk(FIGHTER, col(11), row(8)), mk(DRONE, col(14), row(9))]
g.update_world(st)
check("simultaneous crashes stack damage", st["hp"] == before - 30)
st = quiet(col(10), row(9))
st["hp"] = 5
st["enemies"] = [mk(CRUISER, col(12), row(9))]
g.update_world(st)
check("hull clamps at zero", st["hp"] == 0)


def last_line(hp):
    """Ultima linia del render amb el nivell de casc indicat."""
    s = quiet(0.2, 0.5)
    s["hp"] = hp
    return g.render(s).splitlines()[-1]


w = g.STATUS_BAR_WIDTH
full_line = last_line(g.SHIP_MAX_HP)
half_line = last_line(g.SHIP_MAX_HP // 2)
crit_line = last_line(5)
half_fill = w * (g.SHIP_MAX_HP // 2) // g.SHIP_MAX_HP
check("status bar full", "#" * w in full_line
      and f"{g.SHIP_MAX_HP}/{g.SHIP_MAX_HP}" in full_line)
check("status bar half fill", "#" * half_fill in half_line
      and "-" * (w - half_fill) in half_line)
check("status bar shows numbers", "5/" in crit_line)
g.COLOR_ENABLED = True
check("healthy hull is green", "\x1b[92m" in last_line(g.SHIP_MAX_HP))
check("mid hull is yellow", "\x1b[93m" in last_line(g.SHIP_MAX_HP // 2))
check("critical hull is red", "\x1b[91m" in last_line(5))
g.COLOR_ENABLED = False

# --- 12. powerups: kits de reparacio i dron aliat ------------------------------
check("starts without powerups", orig_new_state()["powerups"] == [])
check("drop weights incl. dron rar", g.POWERUP_DROP_WEIGHTS == (7, 3, 2, 1))
random.seed(5)
check("drops always valid",
      all(g.roll_powerup_drop() in (None, 0, 1, 2, 3) for _ in range(200)))
sp_sprite = g.POWERUPS[0]["sprite"]
bg = g.POWERUPS[2]["sprite"]
k_small = g.make_powerup(0.5, 0.5, 0)
k_big = g.make_powerup(0.5, 0.5, 2)
check("small kit centers at origin",
      isclose(k_small["x"], 0.5 - g.s_w_n(sp_sprite) / 2)
      and isclose(k_small["y"], 0.5 - g.s_h_n(sp_sprite) / 2))
check("large kit centers on its box",
      isclose(k_big["x"], 0.5 - g.s_w_n(bg) / 2)
      and isclose(k_big["y"], 0.5 - g.s_h_n(bg) / 2))

orig_roll = g.roll_powerup_drop
g.roll_powerup_drop = lambda: 2             # sempre cau kit gran
st = quiet(0, 0)
st["shots"] = [{"x": col(15), "y": row(6)}]
fighter = mk(FIGHTER, col(22), row(6))
st["enemies"] = [fighter]
g.update_world(st)                          # aproximacio sense contacte
check("approach leaves hull intact", fighter["hp"] == 2)
st["shots"] = [{"x": fighter["x"] - 1 / 60, "y": row(6)}]
g.update_world(st)                          # primer toc (no letal)
check("first hit wounds but drops nothing yet",
      fighter["hp"] == 1 and st["enemies"] == [fighter]
      and st["powerups"] == [])
st["shots"] = [{"x": fighter["x"] - 1 / 60, "y": row(6)}]
g.update_world(st)                          # toc letal
kits = st["powerups"]
check("killed fighter drops a large kit", len(kits) == 1 and kits[0]["kind"] == 2)
# Recollida: tocar-lo cura fins al maxim del casc.
st["player_x"], st["player_y"] = kits[0]["x"] + g.s_w_n(bg) / 2, kits[0]["y"] + g.s_h_n(bg) / 2
st["hp"] = 70
g.update_world(st)
check("large kit heals up to max", st["powerups"] == [] and st["hp"] == g.SHIP_MAX_HP)
# Kit petit sobre casc mig ple: cura parcial.
st["hp"] = 50
# El kit deriva 1 cela abans de comprovar la recollida: el posem ben endins
# del casc perque el desplacament no el deixi fora de la hitbox.
st["powerups"].append(g.make_powerup(st["player_x"] + 2 / 60,
                                     st["player_y"] + 1 / 18, 0))
g.update_world(st)
check("small kit heals partially", st["hp"] == 65 and st["powerups"] == [])
# Un kit llunya no es recull: deriva cap a l'esquerra i expira.
st["hp"] = g.SHIP_MAX_HP
kit = g.make_powerup(col(40), row(2), 0)
st["powerups"].append(kit)
before_x = kit["x"]                     # make_powerup centra el kit a la cela
g.update_world(st)
check("far kit drifts left",
      isclose(kit["x"], before_x - 1 / 60) and st["hp"] == g.SHIP_MAX_HP)
for _ in range(45):
    g.update_world(st)
check("drifted kit despawns off-screen", st["powerups"] == [])
# Render: kit mitja (creu 3x3) vermell al punt exacte.
st = quiet(col(3), row(8))
st["powerups"].append(g.make_powerup(col(20), row(3), 1))
g.COLOR_ENABLED = True
kit_lines = g.render(st).splitlines()
check("medium kit painted red",
      "\x1b[91m+" in kit_lines[2 + 1] and "\x1b[91m+++" in kit_lines[3 + 1]
      and "\x1b[91m+" in kit_lines[4 + 1])
g.COLOR_ENABLED = False
kit_plain = g.render(st).splitlines()
check("medium kit drawn plain",
      kit_plain[2 + 1][19] == "+" and kit_plain[3 + 1][18:21] == "+++"
      and kit_plain[4 + 1][19] == "+")
g.roll_powerup_drop = orig_roll

# --- 13. drons aliats (wingmans) ------------------------------------------------
check("starts without wingmans", orig_new_state()["wingmans"] == 0)
st = quiet(col(10), row(8))
# Kit de dron que solapa amb la nau: s'uneix a l'esquadra (el kit deriva
# 1 cela abans de la comprobacio, per aixo el centrem una mica endinsat).
st["powerups"].append(g.make_powerup(st["player_x"] + 4 / 60,
                                     st["player_y"] + 1 / 18, 3))
g.update_world(st)
check("dron kit joins the squadron",
      st["wingmans"] == 1 and st["powerups"] == [])
# Cada dron afegeix el seu propi projectil al dispar del jugador.
g.shoot(st)
check("wingman fires its own shot", len(st["shots"]) == 2)
# L'estela: movent la nau cap a la dreta, el dron queda per darrere.
st = quiet(col(5), row(8))
for _ in range(6):
    g.move_player(st, dx=+1)
    g.update_world(st)
wx, _wy = g.wingman_position(st, 0)
check("wingman trails behind a moving ship", wx < st["player_x"] - 1e-9)
# Esquadra plena: el kit extra es converteix en punts bonus.
st = quiet(col(10), row(8))
st["wingmans"] = g.MAX_WINGMANS
before = st["score"]
st["powerups"].append(g.make_powerup(st["player_x"] + 4 / 60,
                                     st["player_y"] + 1 / 18, 3))
g.update_world(st)
check("extra dron converts to bonus points",
      st["wingmans"] == g.MAX_WINGMANS
      and st["score"] == before + g.WINGMAN_SCORE_BONUS)

# --- 14. mode demo: pilot automatic determinista -------------------------------
check("demo level args: plain campaign",
      g.level_from_args(["main.py"]) is None)
check("demo level args: --demo alone",
      g.level_from_args(["main.py", "--demo"]) is None)
check("demo level args: --demo 2",
      g.level_from_args(["main.py", "--demo", "2"]) == 1)
st = quiet(col(8), row(9))
st["enemies"] = [mk(DRONE, col(20), row(9))]
a1 = g.demo_actions(st)
check("demo shoots at an enemy ahead", g.ACTION_SHOOT in a1)
st2 = quiet(col(8), row(9))
st2["enemies"] = [mk(DRONE, col(20), row(9))]
check("demo actions are deterministic", g.demo_actions(st2) == a1)
# Nau centrada i sense amenaces: el pilot no toca res.
st = quiet(col(8), 0.5 - g.s_h_n(g.PLAYER_SPRITE) / 2)
check("demo idles with no threats", g.demo_actions(st) == set())
# Paret de dalt que deixa pas per sota: el pilot baixa cap al corredor.
st = quiet(col(8), row(9))
st["terrain"].append({"x": col(16), "top": 8, "bot": 0,
                      "edge": ("#", "91"), "fill": ("%", "90")})
check("demo ducks under a top wall",
      g.demo_actions(st) == {g.ACTION_DOWN})

# --- resum ----------------------------------------------------------------------
print()
if failures:
    print(f"smoke: {len(failures)} comprovacions fallides:")
    for name in failures:
        print("  FALLA:", name)
    sys.exit(1)
print("smoke: TOT BE")
sys.exit(0)
