"""R-Type ASCII - prototip del clàssic arcade shooter, en ASCII i orientació
horitzontal (els enemics arriben des de la dreta).

Executa'l amb:  python main.py

Controls (manten-les premudes; es poden combinar alhora)
---------------------------------------------------------
w / s  o fletxes amunt/avall    : moure la nau amunt / avall
a / d  o fletxes esquerra/dreta : endarrere / endavant (zona esquerra)
ESPAI                           : disparar (mantenir-lo = tir continu)
p                               : pausa (P altre cop per continuar, q surt)
q                               : sortir

Les millors puntuacions (top 5) es guarden a records.json, al costat de
main.py, i es mostren al menu i a la pantalla de fi de partida.

L'entrada es llegeix per ESTAT (tecla premuda o no) a cada frame, com en
un joc normal: pots mantenir les tecles premudes i prémer-ne diverses en
paral·lel mentre el joc respon a totes.

La nau patrulla el costat esquerre mentre enemics de mides ben diverses
(drons, caces, creuers cuirassats i el cap del final de campanya) volen cap
a l'esquerra: com mes grossos,
mes impactes aguanten, mes punts donen i mes mal fan al casc. Els projectils
(-) surten del morro; la barra inferior mostra la vida del casc, i la
partida acaba quan queda completament buida.

Cada element te el seu color ANSI (nau cian, projectils grocs i cada tipus
d'enemic amb el seu); si la consola no admet colors, es juga en monocrom.

Recompenses: alguns enemics abatuts deixen kits vermells que reparen el
casc en tres mides; com mes gran es el kit, mes vida retorna i mes raro es.
El kit mes rar de tots desplega un dron aliat que seguia la teva estela i
dispara un projectil extra cada cop que dispres (maxim 4 drons).

Sense parpalleig: cada frame es repinta sobre l'anterior movent el cursor
a l'origen, sense esborrar la pantalla, i el cursor s'amaga durant el joc.

La mida del camp de joc s'ajusta UN COP al terminal quan s'inicia el joc;
si redimensiones la finestra durant la partida, el camp no canvia.

Model de dades: totes les posicions internes es guarden en espai normalitzat
[0,1] en coma flotant (0 = vora sup/esq, 1 = vora inf/dret) per fer calculs
més precisos; nomes en pintar es converteixen a coordenades de pantalla.
"""

import ctypes   # crides a l'API de Windows: estat del teclat en temps real
import glob     # trobar els fitxers de nivell nivell_<n>.py
import importlib.util  # carregar cada nivell des del seu fitxer
import json      # records persistents (records.json)
import math     # ones sinusoidals del patro de moviment "ona"
import os
import random
import re       # llegir el numero d'ordre de cada fitxer de nivell
import shutil   # per preguntar al terminal la seva mida en arrencar
import sys      # escriptura directa a stdout: frames sense parpalleig
import time

try:
    import msvcrt  # només Windows: lectura de teclat sense bloquejar
except ImportError:  # permet provar la lògica del joc en altres plataformes
    msvcrt = None

# --------------------------------------------------------------------------- #
# Configuració                                                                #
# --------------------------------------------------------------------------- #
# Mida del camp de joc, en caràcters. Són valors per defecte: en arrencar,
# fit_playfield_to_terminal() els recalcula UN COP segons el terminal real.
MIN_WIDTH = 40                 # amplada mínima jugable
MIN_HEIGHT = 10                # alçada mínima jugable
SCREEN_WIDTH = 80              # sobreescrit en iniciar (amplada del terminal)
SCREEN_HEIGHT = 20             # sobreescrit en iniciar (alçada - HUD i marges)

PLAYER_START_X = 2             # columna inicial de la nau

# --- sprites -----------------------------------------------------------------
# Cada objecte del joc es un SPRITE: una tupla de files de cel·les
# (caracter, color). Els espais son transparents i el rectangle que ocupa el
# sprite es, alhora, la seva hitbox real.
def make_sprite(rows, colors):
    """Construeix un sprite associant un color ANSI a cada caracter."""
    if len(rows) != len(colors) or any(len(row) != len(color_row)
                                       for row, color_row in zip(rows, colors)):
        raise ValueError("sprite i colors han de tenir la mateixa mida")
    return tuple(tuple((char, code) for char, code in zip(row, color_row))
                 for row, color_row in zip(rows, colors))


PLAYER_SPRITE = make_sprite(   # la nau del jugador, apunta cap a la dreta
    ("   / ", "}====", "   \\ "),
    ((None, None, None, "95", None),
     ("97", "96", "96", "96", "93"),
     (None, None, None, "95", None)),
)
SHOT_SPRITE = make_sprite(("-",), (("93",),))  # projectil (1x1)
ENEMY_SHOT_SPRITE = make_sprite(("!",), (("101",),))

# --- efectes d'impacte --------------------------------------------------------
# Quan un projectil toca un enemic es genera una espurna curta; si l'enemic
# esbucava, a mes hi ha una explosio al seu centre (com mes gros, millor).
# Cada tupla es una animacio: un frame per tick, i l'ultim s'esvaeix sol.
SPARK_FRAMES = tuple(make_sprite((char,), (("33",),))
                     for char in ("*", "+", "."))
BOOM_FRAMES = (
    make_sprite(("\\ | /", "- O -", "/ | \\"),
                ((None, "33", None, "33", None),
                 ("33", None, "33", None, "33"),
                 ("33", None, "33", None, "33"))),
    make_sprite((" \\ / ", "  .  ", " / \\ "),
                ((None, "33", None, "33", None),
                 (None, None, "33", None, None),
                 (None, "33", None, "33", None))),
)
CODE_IMPACT = "33"             # explosions i espurnes: groc

# --- kits de reparacio (recompenses) -------------------------------------------
# Els enemics abatuts de vegades deixen un kit vermell que repara el casc.
# Hi ha tres mides: com mes vida retorna, mes gran es el sprite i mes rara
# es la seva aparicio (pes de sorteg inversament proporcional a la cura).
POWERUP_SPEED = 1              # celes que deriva cap a l'esquerra per tick
POWERUPS = (
    {"name": "kit petit", "heal": 15, "weight": 7,      # 1x1
    "sprite": make_sprite(("+",), (("91",),))},
    {"name": "kit mitja", "heal": 30, "weight": 3,      # creu 3x3
    "sprite": make_sprite((" + ", "+++", " + "),
                      ((None, "91", None),
                       ("91", "91", "91"),
                       (None, "91", None)))},
    {"name": "kit gran", "heal": 60, "weight": 2,       # creu emmarcada 5x3
    "sprite": make_sprite(("[ + ]", "[+++]", "[ + ]"),
                      (("91", None, "91", None, "91"),
                       ("91", "91", "91", "91", "91"),
                       ("91", None, "91", None, "91")))},
    {"name": "dron aliat", "heal": 0, "weight": 1,      # el mes rar
     "wingman": True,
    "sprite": make_sprite(("<o>",), (("91", "93", "91"),))}, # mini dron
)
POWERUP_DROP_WEIGHTS = tuple(p["weight"] for p in POWERUPS)
POWERUP_NO_DROP_WEIGHT = 30    # pes de que l'enemic no deixi res
CODE_POWERUP = "91"            # tots els powerups son vermells

# --- dro aliats (wingmans) -----------------------------------------------------
# El kit de dron afegeix un company que seguia l'estela de la nau i dispara
# un projectil addicional cada vegada que dispari tu. Maxim: MAX_WINGMANS;
# si el reculls amb l'esquadra plena, es converteix en punts bonus.
MAX_WINGMANS = 4
WINGMAN_TRAIL_GAP = 4          # ticks d'historia entre drons consecutius
WINGMAN_SPRITE = make_sprite(("->",), (("96", "93"),))
WINGMAN_W = len(WINGMAN_SPRITE[0])
WINGMAN_H = len(WINGMAN_SPRITE)
WINGMAN_SCORE_BONUS = 50       # punts quan el kit arriba amb l'esquadra plena

# Tipus d'enemic, de mes petit i feble a mes gran i cuirassat: cada entrada
# defineix el sprite, quantes vides te (hp), quants punts dona, la velocitat
# (celes per tick) i el pes en el sorteig del tipus que apareix.
ENEMY_TYPES = (
    {"name": "dron",           # petit, rapid i feble
    "sprite": make_sprite(("<e>",), (("91", "97", "91"),)),
     "hp": 1, "points": 10, "speed": 2, "weight": 55,
     "damage": 10,
     "color": "91"},           # vermell brillant
    {"name": "caca",           # mitja
    "sprite": make_sprite(("<==", "~~~"),
                      (("95", "97", "95"),
                       ("95", "95", "95"))),
     "hp": 2, "points": 30, "speed": 1, "weight": 30,
     "damage": 20,
     "color": "95"},           # magenta brillant
    {"name": "creuer",         # gros, lent i cuirassat
    "sprite": make_sprite(("<---=", "[###]", "<---'"),
                      (("94", "94", "94", "94", "93"),
                       ("94", "97", "97", "97", "94"),
                       ("94", "94", "94", "94", "93"))),
     "hp": 4, "points": 80, "speed": 1, "weight": 15,
     "damage": 35,
     "color": "94"},           # blau brillant
    {"name": "cap",            # enemic final: entra, s'atura i disparà rafegues
     "sprite": make_sprite(
         ("  [====]  ",
          "<{======}>",
          "<{==@@==}>",
          "  [====]  "),
         ((None, None, "95", "97", "97", "97", "97", "95", None, None),
          ("95", "94", "94", "94", "94", "94", "94", "94", "94", "95"),
          ("95", "94", "94", "94", "91", "91", "94", "94", "94", "95"),
          (None, None, "95", "97", "97", "97", "97", "95", None, None))),
     "hp": 30, "points": 500, "speed": 1, "weight": 0,
     "damage": 45,
     "color": "95"},           # magenta brillant
)
ENEMY_WEIGHTS = tuple(t["weight"] for t in ENEMY_TYPES)

# --- projectils enemics --------------------------------------------------------
# Els enemics disparen projectils amb angle variable; el jugador no els pot
# destruir, nomes esquivar-los. Els petits son mes rapids i fan poc mal,
# mentre que els grans disparen mes lentament però causen molt mes dany.
ENEMY_SHOT_TYPES = (
    {"speed": 3.2, "damage": 8, "color": "91"},
    {"speed": 2.5, "damage": 18, "color": "95"},
    {"speed": 1.8, "damage": 32, "color": "94"},
    {"speed": 1.6, "damage": 40, "color": "95"},   # rafega pesada del cap
)

# --- patrons de moviment -------------------------------------------------------
# Cada enemic neix amb un patro que decideix com es mou per la pantalla:
#   recta  : avanca cap a l'esquerra sense variar l'altura
#   ona    : ondula verticalment al voltant d'una altura base (sinus)
#   zigzag : baixa i puja rebotant entre la part alta i la baixa del camp
#   picat  : es llanca en diagonal cap avall i, en tocar fons, seguia recte
#   puja   : versio espeix del picat, cap a dalt
# Cada tipus d'enemic te la seva llista de patrons preferits.
KIND_PATTERNS = (
    ("recta", "recta", "zigzag", "ona", "picat"),   # drons: imprevisibles
    ("ona", "zigzag", "picat", "puja"),             # cacers: agils
    ("recta", "ona"),                               # creuers: serens
    ("cap",),                                       # el cap final: patró propi
)

# --- cap final -----------------------------------------------------------------
# El cap (kind BOSS_KIND) entra per la dreta, s'atura a BOSS_STOP_COLS de la
# vora i es balanceja disparant rafegues en ventall. No mor en xocar contra
# la nau: li fa dany i l'empenta fora del seu casc. Matar-lo completa el
# nivell que el porta (encara que quedin ticks de mapa).
BOSS_KIND = 3                  # index del cap a ENEMY_TYPES
BOSS_STOP_COLS = 3.0           # celes des de la vora dreta on s'atura
BOSS_PUSH_COLS = 2.0           # empenta al casc quan la nau el toca
BOSS_SPREAD = 0.004            # obertura vertical del ventall de la rafega
BOSS_MAX_HP = 30               # vida total del cap final
BOSS_BAR_WIDTH = 22            # celes de la barra de vida del cap a l'HUD
BOSS_DROP_KIND = 2             # kit gran que cau al derrotar el cap
BOSS_DROP_CHANCE = 0.65        # probabilitat de drop al caure el cap

# --- mapes -------------------------------------------------------------------
# Els nivells NO viuen aqui dins: cada un es un fitxer propi numerat
# (nivell_1.py, nivell_2.py...) al costat de main.py, carregat en ordre
# numeric quan arrenca el joc. Cada fitxer exposa un diccionari LEVEL amb:
#   name     nom del nivell (es mostra a la pantalla d'introduccio)
#   duration ticks totals del mapa: la ronda acaba en arribar-hi
#   spawns   tuples (tick, tipus d'enemic, fila inicial, patro); el mapa
#            controla completament els naixements: no hi ha spawn aleatori
#   terrain  parets de dalt i de baix, per elevacions (opcional; vegeu el
#            docstring de nivell_1.py per al format complet)
LEVELS_DIR = os.path.dirname(os.path.abspath(__file__))
LEVEL_FILE_PATTERN = "nivell_*.py"

# Estil per defecte de les parets quan el segment no en defineix cap.
WALL_EDGE_DEFAULT = ("#", "37")    # vora (superficie): blanc grisenc
WALL_FILL_DEFAULT = ("%", "90")    # interior: gris fosc
MIN_CORRIDOR = 6                   # celes lliures minimes entre parets


def _wall_style(segment: dict, index: int):
    """Estil (vora, cos) de la columna `index` d'un segment de terreny."""
    edge = segment.get("vora") or WALL_EDGE_DEFAULT
    fill = segment.get("cos") or WALL_FILL_DEFAULT
    styles = segment.get("estils") or ()
    if index < len(styles) and styles[index]:
        edge = styles[index].get("vora", edge)
        fill = styles[index].get("cos", fill)
    return edge, fill


def _normalize_terrain(terrain, source: str) -> tuple:
    """Converteix els segments de terreny en esdeveniments plans i ordenats.

    Cada segment passa a ser una entrada ``(tick, dalt, abaix, vora, cos)``
    per CADA columna, de manera que update_world nomes hagi de comparar
    ticks. Com que una columna avanca una cel·la per tick, els segments de
    ticks consecutius formen parets contigues.
    """
    events = []
    for segment in terrain:
        top = tuple(segment.get("dalt", ()))
        bot = tuple(segment.get("abaix", ()))
        if not top and not bot:
            continue
        if "tick" not in segment:
            raise ValueError(f"{source}: a cada segment de terrain li falta 'tick'")
        start = int(segment["tick"])
        for j in range(max(len(top), len(bot))):
            edge, fill = _wall_style(segment, j)
            events.append((start + j,
                           top[j] if j < len(top) else 0,
                           bot[j] if j < len(bot) else 0,
                           edge, fill))
    events.sort(key=lambda ev: ev[0])
    return tuple(events)


def _normalize_level(level, source: str) -> dict:
    """Valida i normalitza el diccionari LEVEL d'un fitxer de nivell."""
    if not isinstance(level, dict):
        raise ValueError(f"{source}: LEVEL ha de ser un diccionari")
    normalized = {
        "name": str(level.get("name", "NIVELL")),
        "duration": int(level["duration"]),
        "spawns": tuple(tuple(spawn) for spawn in level.get("spawns", ())),
        "terrain_events": _normalize_terrain(level.get("terrain", ()), source),
    }
    for spawn in normalized["spawns"]:
        if len(spawn) != 4:
            raise ValueError(f"{source}: cada spawn ha de ser "
                             f"(tick, tipus, fila, patro): {spawn}")
        if not 0 <= spawn[1] < len(ENEMY_TYPES):
            raise ValueError(f"{source}: tipus d'enemic desconegut: {spawn}")
    return normalized


def load_levels() -> tuple:
    """Carrega els nivells dels fitxers nivell_<n>.py, en ordre numeric."""
    found = []
    for path in glob.glob(os.path.join(LEVELS_DIR, LEVEL_FILE_PATTERN)):
        match = re.search(r"nivell_(\d+)\.py$", os.path.basename(path),
                          re.IGNORECASE)
        if match is None:
            continue
        spec = importlib.util.spec_from_file_location(
            f"_rtype_nivell_{match.group(1)}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        level = getattr(module, "LEVEL", None)
        if level is None:
            raise ValueError(f"{os.path.basename(path)}: no exposa cap LEVEL")
        found.append((int(match.group(1)),
                      _normalize_level(level, os.path.basename(path))))
    found.sort(key=lambda item: item[0])
    if not found:
        raise FileNotFoundError(
            f"Cap fitxer de nivell trobat: cal almenys un '{LEVEL_FILE_PATTERN}' "
            f"(p. ex. nivell_1.py) al costat de main.py")
    return tuple(level for _, level in found)


# --- records persistents -------------------------------------------------------
# Les millors puntuacions viuen a records.json, al costat d'aquest fitxer,
# com una llista JSON d'objectes {"punts": int, "data": "AAAA-MM-DD"}, sempre
# retallada als SCORES_KEPT millors. Qualsevol problema (fitxer trencat,
# sense permisos...) no ha d'impedir jugar: simplement s'ignora.
SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "records.json")
SCORES_KEPT = 5


def load_scores() -> list:
    """Llegeix el top de puntuacions; [] si no hi ha fitxer o es illegible."""
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    scores = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("punts"), int):
            scores.append({"punts": item["punts"],
                           "data": str(item.get("data", ""))})
    scores.sort(key=lambda s: s["punts"], reverse=True)
    return scores[:SCORES_KEPT]


def save_score(points: int) -> bool:
    """Afegeix una puntuacio al top si hi cap; cert si es la millor de tots.

    Una puntuacio no positiva no es desa. Retorna cert nomes si, despres de
    la insercio, queda com la mes alta de la llista (o si es la primera que
    es desa mai).
    """
    if not isinstance(points, int) or points <= 0:
        return False
    scores = load_scores()
    today = time.strftime("%Y-%m-%d")
    scores.append({"punts": points, "data": today})
    scores.sort(key=lambda s: s["punts"], reverse=True)
    del scores[SCORES_KEPT:]
    best = scores[0]["punts"] if scores else 0
    try:
        with open(SCORES_FILE, "w", encoding="utf-8") as fh:
            json.dump(scores, fh, ensure_ascii=False, indent=1)
    except OSError:
        return False
    return points >= best


def scores_block() -> str:
    """Texte del top 5 (sense colors) per a menus i pantalles finals."""
    scores = load_scores()
    if not scores:
        return " Encara no hi ha puntuacions desades."
    return "\n".join(f" {i:>2}. {s['punts']:6d} pts  {s['data']}"
                     for i, s in enumerate(scores, start=1))


MAPS = load_levels()
CURRENT_MAP = 0
# --- colors ANSI --------------------------------------------------------------
# Codis de color (SGR) per als elements del joc. Requereixen una consola amb
# sequencies VT; _enable_vt() ho activa a la consola de Windows i, si no hi
# es, COLOR_ENABLED queda falsa i el joc es pinta en monocrom.
CODE_PLAYER = "96"             # nau: cian brillant
CODE_SHOT = "93"               # projectil: groc brillant
CODE_HUD = "97"                # puntuacio del HUD: blanc brillant
CODE_HINT = "90"               # pistes i textos secundaris: gris
CODE_TITLE = "96"              # banner: cian brillant
CODE_ALERT = "91"              # game over: vermell brillant

RESET_COLOR = "\x1b[0m"


def _enable_vt() -> bool:
    """Activa les sequencies ANSI a la consola de Windows (Win10+).

    Retorna True si la sortida actual admet colors; si no (sortida
    redirigida, terminal antic...), el joc funcionara en monocrom.
    """
    try:
        kernel32 = ctypes.WinDLL("kernel32")
    except (AttributeError, OSError):
        return False
    handle = kernel32.GetStdHandle(-11)            # STD_OUTPUT_HANDLE
    mode = ctypes.c_uint32()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        return False                               # sortida no interactiva
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    return bool(kernel32.SetConsoleMode(
        handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING))


COLOR_ENABLED = _enable_vt()


def paint(text: str, code: str) -> str:
    """Tenyeix un text amb el codi ANSI donat si els colors estan actius."""
    if COLOR_ENABLED and code:
        return f"\x1b[{code}m{text}{RESET_COLOR}"
    return text


PLAYER_ZONE_FRACTION = 1.0     # la nau pot recórrer tot el camp; el risc es del jugador
PLAYER_HORIZONTAL_SPEED = 3.5  # la nau supera el scroll enemic (2 cel·les/tick)
SHOT_SPEED = 5.0               # els projectils superen la nau, en cel·les/tick
SHOT_COOLDOWN_TICKS = 2        # ticks d'espera entre dos dispars consecutius
INITIAL_ENEMIES = 3            # enemics en cua quan comença la ronda
BASE_SPAWN_CHANCE = 0.10       # probabilitat per tick de nou enemic...
MAX_SPAWN_CHANCE = 0.35        # ...limitada conforme puja la dificultat
RAMP_PER_MINUTE = 0.05         # creixement de la probabilitat per minut
GAME_TICK = 0.08               # segons per frame (~12.5 FPS)

# --- casc de la nau ------------------------------------------------------------
# La vida del casco baixa a cada xoc segons el dany del enemic (damage) i la
# partida acaba quan arriba a zero. La barra inferior la mostra sempre.
SHIP_MAX_HP = 100              # punts de casc inicials
STATUS_BAR_WIDTH = 24          # celes de la barra de vida de sota del camp
MAP_PROGRESS_BAR_WIDTH = 24     # celes de la barra de progrés del mapa
PLAYER_H = len(PLAYER_SPRITE)

# --- espai normalitzat ----------------------------------------------------------
# Totes les posicions internes del joc es guarden com a FLOTS normalitzats
# a l'interval [0,1] (0 = vora superior/esquerra, 1 = vora inferior/dreta).
# Els calculs (moviment, col.lisions) es fan en aquest espai decimal, d'on se'n
# treu mes precisio; nomes es convertiran a coordenades de pantalla (cel.les)
# en el moment de pintar. Aquestes funcions fan de pont entre els dos espais.
def cell_x(nx: float) -> int:
    """Normalitzada (0..1) -> columna de pantalla."""
    return min(SCREEN_WIDTH - 1, max(0, int(round(nx * SCREEN_WIDTH))))


def cell_y(ny: float) -> int:
    """Normalitzada (0..1) -> fila de pantalla."""
    return min(SCREEN_HEIGHT - 1, max(0, int(round(ny * SCREEN_HEIGHT))))


def w_n(cells: int) -> float:
    """Amplada en cel.les -> amplada normalitzada."""
    return cells / SCREEN_WIDTH


def h_n(cells: int) -> float:
    """Alçada en cel.les -> alçada normalitzada."""
    return cells / SCREEN_HEIGHT


def s_w_n(sprite) -> float:
    """Amplada normalitzada d'un sprite."""
    return len(sprite[0]) / SCREEN_WIDTH


def s_h_n(sprite) -> float:
    """Alçada normalitzada d'un sprite."""
    return len(sprite) / SCREEN_HEIGHT


# --- tecles (caràcters; només serveixen per mostrar-los als textos) --------
KEY_UP = "w"
KEY_DOWN = "s"
KEY_BACK = "a"
KEY_FORWARD = "d"
KEY_QUIT = "q"
KEY_REPLAY = "r"
KEY_PAUSE = "p"

# --- accions canòniques del joc --------------------------------------------
# El bucle de joc no treballa amb caràcters sinó amb ACCIONS: a cada frame
# es comprova quines accions estan actives (tecles premudes ara mateix),
# de manera que es poden mantenir i combinar diverses tecles alhora.
ACTION_UP = "up"
ACTION_DOWN = "down"
ACTION_BACK = "back"
ACTION_FORWARD = "forward"
ACTION_SHOOT = "shoot"
ACTION_QUIT = "quit"
ACTION_REPLAY = "replay"
ACTION_PAUSE = "pause"

X, Y = 0, 1                    # índexos d'un parell [x, y]

_screen = []                   # bufer de caracters del frame en curs
_colors = []                   # bufer paral-lel amb el codi de color de cada cela
_first_frame = True            # encara no hem pintat cap frame d'aquesta ronda


def fit_playfield_to_terminal():
    """Ajusta la mida del camp de joc a la finestra del terminal.

    Es crida UN SOL COP, just en començar el joc: si l'usuari redimensiona
    la finestra durant la partida, el camp manté la mida inicial.
    """
    global SCREEN_WIDTH, SCREEN_HEIGHT
    try:
        cols, rows = shutil.get_terminal_size()
    except (OSError, ValueError):
        cols, rows = 80, 24                       # valor segur per defecte
    # Reservem les linies fixes de la interficie (HUD superior, barra de
    # casc inferior i marges) i una columna de marge a cada costat.
    SCREEN_WIDTH = max(MIN_WIDTH, cols - 2)
    SCREEN_HEIGHT = max(MIN_HEIGHT, rows - 5)


# --------------------------------------------------------------------------- #
# Estat del joc                                                               #
# --------------------------------------------------------------------------- #
def make_enemy(x: float, kind=None) -> dict:
    """Crea un enemic a la columna normalitzada x amb un patro sortejat."""
    if kind is None:
        kind = random.choices(range(len(ENEMY_TYPES)), weights=ENEMY_WEIGHTS)[0]
    t = ENEMY_TYPES[kind]
    h = s_h_n(t["sprite"])
    pattern = random.choice(KIND_PATTERNS[kind])
    # Fila aleatoria dins dels limits, de manera que tot el sprite hi capiga.
    enemy = {"x": x,
             "y": random.uniform(0.0, max(0.0, 1.0 - h)),
             "kind": kind,
             "hp": t["hp"],
             "pattern": pattern,
             "fire_cooldown": random.randint(20, 40) - kind * 5}
    if pattern == "ona":
        # Ondula al voltant d'una altura base que garanteix que l'amplitud
        # hi capiga dins del camp, amb fase aleatoria per dessincronitzar-los.
        avail = max(1.0, 1.0 - h)
        amp = random.uniform(0.02, min(0.2, avail / 2))
        enemy["amp"] = amp
        enemy["phase"] = random.uniform(0.0, 6.283)
        enemy["base_y"] = random.uniform(amp, max(amp, avail - amp))
    elif pattern == "zigzag":
        enemy["vy"] = random.choice((-1, 1))
    elif pattern == "cap":
        # El cap final: s'atura a la dreta i oscil.la cap al seu centre.
        enemy["base_y"] = enemy["y"]
        enemy["amp"] = 0.08
        enemy["phase"] = 0.0
    return enemy


def make_effect(cx: float, cy: float, frames) -> dict:
    """Crea un efecte visual centrat a (cx, cy) amb la sequencia de frames.

    L'efecte mostra un frame per tick i desapareix sol quan s'acaben.
    El centrat fa servir les mides del frame (tots son identics).
    """
    return {"x": cx - s_w_n(frames[0]) / 2,
            "y": cy - s_h_n(frames[0]) / 2,
            "age": 0,
            "frames": frames}


def make_enemy_shot(enemy: dict, target_x: float, target_y: float):
    """Genera un projectil enemic dirigit cap al jugador."""
    if enemy is None:
        return None
    stats = ENEMY_SHOT_TYPES[enemy["kind"]]
    ex = enemy["x"] + s_w_n(ENEMY_TYPES[enemy["kind"]]["sprite"]) / 2
    ey = enemy["y"] + s_h_n(ENEMY_TYPES[enemy["kind"]]["sprite"]) / 2
    dx = target_x - ex
    dy = target_y - ey
    dist = math.hypot(dx, dy)
    if dist <= 0.0:
        return None
    speed = stats["speed"]
    vx = (dx / dist) * speed / SCREEN_WIDTH
    vy = (dy / dist) * speed / SCREEN_HEIGHT
    return {
        "x": ex,
        "y": ey,
        "vx": vx,
        "vy": vy,
        "damage": stats["damage"],
        "color": stats["color"],
    }


def roll_powerup_drop():
    """Sorteja quin kit cau d'un enemic abatut (o None si no en cau cap).

    El pes de cada kit es inversament proporcional a la vida que retorna:
    els petits son els mes comuns i els grans, els mes rars.
    """
    choices = list(range(len(POWERUPS))) + [None]
    weights = list(POWERUP_DROP_WEIGHTS) + [POWERUP_NO_DROP_WEIGHT]
    return random.choices(choices, weights=weights)[0]


def make_powerup(cx: float, cy: float, kind: int) -> dict:
    """Crea un kit de reparacio centrat a (cx, cy) del tipus donat."""
    p = POWERUPS[kind]
    return {"x": cx - s_w_n(p["sprite"]) / 2,
            "y": cy - s_h_n(p["sprite"]) / 2,
            "kind": kind}


def new_state():
    """Crea un diccionari d'estat nou per a una ronda."""
    game_map = MAPS[CURRENT_MAP]
    return {
        "player_x": w_n(PLAYER_START_X),
        "player_y": 0.5,
        "ship_prev_x": w_n(PLAYER_START_X),  # d'on venia la nau: creuaments de paret
        "enemies": [],
        "shots": [],                     # projectils en vol: {"x", "y"}
        "enemy_shots": [],               # projectils enemics amb angle variable
        "effects": [],                   # efectes d'impacte temporals
        "powerups": [],                  # kits de reparacio flotants
        "terrain": [],                   # columnes de paret en pantalla
        "hp": SHIP_MAX_HP,               # vida restant del casc
        "wingmans": 0,                   # drons aliats actius (max 4)
        "trail": [],                     # historia de centres de la nau
        "shot_cooldown": 0,              # ticks que falten per poder disparar
        "score": 0,
        "ticks": 0,
        "map": game_map,
        "map_progress": 0.0,
        "completed": False,
        "spawn_chance": 0.0,
    }


# --------------------------------------------------------------------------- #
# Entrada de teclat: estat de les tecles (estil arcade)                       #
# --------------------------------------------------------------------------- #
# En comptes de llegir pulsacions aïllades (on cal prémer i deixar anar la
# tecla per cada moviment), a cada frame consultem QUINES tecles estan
# PREMUDES en aquest instant. Així la nau respon mentre mantens la tecla i
# pots combinar-ne diverses en paral·lel (p. ex. moure't en diagonal mentre
# disparres). La consulta es fa amb GetAsyncKeyState (API de Windows, via
# ctypes); si no és disponible es fa servir msvcrt com a aproximació.

_user32 = None
try:
    _user32 = ctypes.WinDLL("user32")
    _get_key_state = _user32.GetAsyncKeyState
    _get_key_state.restype = ctypes.c_short       # retorna un SHORT signat
    _get_key_state.argtypes = [ctypes.c_int]
except (AttributeError, OSError):
    _get_key_state = None                         # entorn no-Windows / tests

# Taula (codi de tecla virtual -> acció). Les fletxes fan el mateix que WASD,
# i cada acció pot tenir vàries tecles associades.
_KEY_ACTIONS = (
    (0x57, ACTION_UP),        # W
    (0x26, ACTION_UP),        # fletxa amunt
    (0x53, ACTION_DOWN),      # S
    (0x28, ACTION_DOWN),      # fletxa avall
    (0x41, ACTION_BACK),      # A
    (0x25, ACTION_BACK),      # fletxa esquerra
    (0x44, ACTION_FORWARD),   # D
    (0x27, ACTION_FORWARD),   # fletxa dreta
    (0x20, ACTION_SHOOT),     # barra espaiadora
    (0x50, ACTION_PAUSE),     # P
    (0x51, ACTION_QUIT),      # Q
    (0x52, ACTION_REPLAY),    # R
)


def pressed_keys():
    """Retorna el conjunt d'accions actives (tecles premudes) ara mateix."""
    if _get_key_state is None:
        return _pressed_keys_fallback()
    active = set()
    for vk, action in _KEY_ACTIONS:
        # El bit alt (0x8000) indica que la tecla és físicament premuda.
        if _get_key_state(vk) & 0x8000:
            active.add(action)
    return active


def _pressed_keys_fallback():
    """Fallback sense API Win32: consumeix el buffer de msvcrt.

    Aproximació: les pulsacions rebudes durant aquest frame compten com a
    accions actives. En Windows real no s'utilitza (hi ha GetAsyncKeyState).
    """
    active = set()
    if msvcrt is None:
        return active
    char_to_action = {
        KEY_UP: ACTION_UP, KEY_DOWN: ACTION_DOWN,
        KEY_BACK: ACTION_BACK, KEY_FORWARD: ACTION_FORWARD,
        " ": ACTION_SHOOT, KEY_QUIT: ACTION_QUIT, KEY_REPLAY: ACTION_REPLAY,
        KEY_PAUSE: ACTION_PAUSE,
    }
    while msvcrt.kbhit():
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            # Segon codi de les fletxes: H amunt, P avall, K esquerra, M dreta.
            arrow = {"\x48": ACTION_UP, "\x50": ACTION_DOWN,
                     "\x4B": ACTION_BACK, "\x4D": ACTION_FORWARD}.get(
                         msvcrt.getwch())
            if arrow:
                active.add(arrow)
            continue
        action = char_to_action.get(ch.lower())
        if action:
            active.add(action)
    return active


def wait_key():
    """Espera (bloquejant) fins que es premi una tecla; per als menús.

    Abans d'esperar BUIDA el buffer del teclat: durant les animacions (el
    banner de nivell completat, per exemple) la nau segueix disparant i les
    pulsacions queden acumulades. Sense aquest buidatge, la primera tecla
    vella (un espai de dispar, normalment) es consumiria a l'instant com si
    fos la resposta del menu i el joc es tancaria sense deixar contestar.
    """
    if msvcrt is None:
        return None
    while msvcrt.kbhit():
        msvcrt.getwch()                        # descarta les pulsacions velles
    ch = msvcrt.getwch()                       # espera una pulsacio NOVA
    if ch in ("\x00", "\xe0"):
        msvcrt.getwch()
        return ""
    return ch.lower()


# --------------------------------------------------------------------------- #
# Simulacio                                                                   #
# --------------------------------------------------------------------------- #
def player_zone_max_x():
    """Columna normalitzada maxima fins on pot avançar la nau.

    Ara la nau pot recórrer tot el camp, amb el risc de la seva pròpia
    maniobra: la única limitació és que el sprite no se n'escapi.
    """
    return max(0.0, 1.0 - s_w_n(PLAYER_SPRITE))


def move_player(state: dict, dx: int = 0, dy: int = 0) -> None:
    """Mou la nau en espai normalitzat, sense limitar-la a un terç de pantalla.

    dx/dy són els valors dels inputs (-1, 0 o 1); el pas per tick és una
    fracció de cel·la, de manera que el moviment és precís i continua.
    """
    step_x = PLAYER_HORIZONTAL_SPEED / SCREEN_WIDTH
    step_y = 1.0 / SCREEN_HEIGHT
    state["player_x"] = max(0.0,
                            min(player_zone_max_x(),
                                state["player_x"] + dx * step_x))
    state["player_y"] = max(0.0, min(1.0 - s_h_n(PLAYER_SPRITE),
                                     state["player_y"] + dy * step_y))


def shoot(state: dict) -> None:
    """Dispara un projectil des del morro de la nau, si el cano es carregat."""
    if state["shot_cooldown"] > 0:
        return                                  # encara recarregant
    # Neix just davant del morro, a l'altura de la fila central del sprite.
    state["shots"].append({"x": state["player_x"] + s_w_n(PLAYER_SPRITE),
                           "y": state["player_y"] + h_n(PLAYER_H // 2)})
    # Cada dron aliat afegeix el seu propi projectil, des de la seva posicio.
    for i in range(state.get("wingmans", 0)):
        wx, wy = wingman_position(state, i)
        state["shots"].append({"x": wx + s_w_n(WINGMAN_SPRITE),
                               "y": wy})
    state["shot_cooldown"] = SHOT_COOLDOWN_TICKS


def rects_overlap(x1, y1, w1, h1, x2, y2, w2, h2) -> bool:
    """Cert si dos rectangles (cantonada sup. esquerra + mides) es solapen.

    Treballa en l'espai normalitzat (floats), que es on viuen les posicions.
    """
    return (x1 < x2 + w2 and x2 < x1 + w1 and
            y1 < y2 + h2 and y2 < y1 + h1)


def enemy_rect(en: dict):
    """Rectangle hitbox normalitzat (x, y, amplada, alcada) d'un enemic."""
    t = ENEMY_TYPES[en["kind"]]
    return en["x"], en["y"], s_w_n(t["sprite"]), s_h_n(t["sprite"])


def ship_rect(state: dict):
    """Rectangle hitbox normalitzat de la nau."""
    return (state["player_x"], state["player_y"],
            s_w_n(PLAYER_SPRITE), s_h_n(PLAYER_SPRITE))


def fit_corridor(top: int, bot: int):
    """Ajusta dues elevacions de paret per garantir un pas jugable.

    La suma de les dues parets no pot deixar menys de MIN_CORRIDOR celes
    lliures al mig; en terminals baixos, les elevacions dissenyades al
    fitxer de nivell s'escalen proporcionalment per complir-ho.
    """
    max_total = max(0, SCREEN_HEIGHT - MIN_CORRIDOR)
    total = top + bot
    if total <= max_total:
        return top, bot
    if total == 0:
        return 0, 0
    return top * max_total // total, bot * max_total // total


def wall_rects(column: dict):
    """Rectangles hitbox normalitzats d'una columna de paret (dalt i baix)."""
    w = 1.0 / SCREEN_WIDTH
    rects = []
    if column["top"] > 0:
        rects.append((column["x"], 0.0, w, column["top"] / SCREEN_HEIGHT))
    if column["bot"] > 0:
        rects.append((column["x"], 1.0 - column["bot"] / SCREEN_HEIGHT,
                      w, column["bot"] / SCREEN_HEIGHT))
    return rects


def wingman_position(state: dict, index: int):
    """Posicio (cantonada sup. esquerra, normalitzada) del dron aliat `index`.

    Cada dron seguia l'estela de la nau: s'ubica sobre el punt del historial
    de centres registrat `WINGMAN_TRAIL_GAP * (index + 1)` ticks enrere,
    aixi que van formant una cua darrera de tu.
    """
    trail = state.get("trail") or []
    if not trail:
        return state["player_x"], state["player_y"]
    k = max(0, len(trail) - 1 - WINGMAN_TRAIL_GAP * (index + 1))
    cx, cy = trail[k]
    return cx - s_w_n(WINGMAN_SPRITE) / 2, cy - s_h_n(WINGMAN_SPRITE) / 2


def _move_enemy(enemy: dict, tick: int) -> None:
    """Avanca un enemic (en espai normalitzat) segons el seu patro.

    Mutza l'enemic: x sempre retrocedeix (per a l'esquerra) i y depen del
    patro, limitat sempre a l'interior del camp segons l'alçada del sprite.
    Els desplazaments es fan en fraccions de cel·la per a mes precisio.
    """
    t = ENEMY_TYPES[enemy["kind"]]
    max_y = 1.0 - s_h_n(t["sprite"])
    spd_x = t["speed"] / SCREEN_WIDTH      # cels de velocitat -> normalitzat
    step_y = 1.0 / SCREEN_HEIGHT
    pattern = enemy["pattern"]

    if pattern == "ona":
        dx, dy = -spd_x, 0.0
        desired = (enemy["base_y"]
                   + enemy["amp"] * math.sin(0.05 * tick + enemy["phase"]))
        dy = max(-step_y, min(step_y, desired - enemy["y"]))
    elif pattern == "zigzag":
        dx, dy = -spd_x, enemy.get("vy", 1) * step_y
    elif pattern == "picat":
        dx = -spd_x
        # Picat rapid cap avall; en tocar fons seguia recte.
        dy = 2.0 * step_y if enemy["y"] < max_y else 0.0
    elif pattern == "puja":
        dx = -spd_x
        # Versio espeix: puja en diagonal fins dalt i alli segueix recte.
        dy = -2.0 * step_y if enemy["y"] > 0.0 else 0.0
    elif pattern == "cap":
        # El cap avanca fins a la seva posicio de combat i alli es balanceja
        # al voltant de la fila on ha neixut (base_y +- amp).
        stop_x = (1.0 - s_w_n(t["sprite"])
                  - BOSS_STOP_COLS / SCREEN_WIDTH)
        dx = 0.0 if enemy["x"] <= stop_x else max(-spd_x, stop_x - enemy["x"])
        desired = (enemy.get("base_y", enemy["y"])
                   + enemy.get("amp", 0.08)
                   * math.sin(0.05 * tick + enemy.get("phase", 0.0)))
        dy = max(-step_y, min(step_y, desired - enemy["y"]))
    else:                                        # "recta" i desconeguts
        dx, dy = -spd_x, 0.0

    enemy["x"] += dx
    enemy["y"] += dy

    # Limits verticals; el zigzag aprofita el rebrot per invertir sentit.
    if enemy["y"] < 0.0:
        enemy["y"] = 0.0
        if pattern == "zigzag":
            enemy["vy"] = 1
    elif enemy["y"] > max_y:
        enemy["y"] = max_y
        if pattern == "zigzag":
            enemy["vy"] = -1


def update_world(state: dict) -> None:
    """Avanca un tick: mou enemics/projectils, spawneja i resol impactes."""
    state["ticks"] += 1

    game_map = state["map"]
    for tick, kind, start_y, pattern in game_map["spawns"]:
        if tick == state["ticks"]:
            enemy = make_enemy(1.0, kind)
            enemy["y"] = max(0.0, min(1.0 - s_h_n(
                ENEMY_TYPES[kind]["sprite"]), start_y))
            enemy["pattern"] = pattern
            if pattern == "ona":
                enemy["amp"] = 0.02
                enemy["phase"] = 0.0
                enemy["base_y"] = enemy["y"]
            elif pattern == "zigzag":
                enemy["vy"] = 1
            elif pattern == "cap":
                # El cap entra per la dreta i es balanceja al voltant de la
                # fila on se li ha dit que neixi (mirall de la branca "ona"):
                # sense aixo la base quedaria a l'y aleatori de make_enemy.
                enemy["base_y"] = enemy["y"]
                enemy["amp"] = 0.08
                enemy["phase"] = 0.0
            state["enemies"].append(enemy)
    # --- terreny: cada columna de paret entra per la dreta el seu tick -------
    # Els esdeveniments ja venen aplanats i ordenats des del fitxer de nivell.
    for ev_tick, top, bot, edge, fill in game_map.get("terrain_events", ()):
        if ev_tick == state["ticks"]:
            top, bot = fit_corridor(top, bot)
            state["terrain"].append({"x": 1.0, "top": top, "bot": bot,
                                     "edge": edge, "fill": fill})

    state["map_progress"] = min(1.0, state["ticks"] / game_map["duration"])
    if state["ticks"] >= game_map["duration"]:
        state["completed"] = True

    if state["shot_cooldown"] > 0:
        state["shot_cooldown"] -= 1             # el cano es va carregant

    # Historia de centres de la nau: l'estela que seguexen els drons aliats.
    center_x = state["player_x"] + s_w_n(PLAYER_SPRITE) / 2
    center_y = state["player_y"] + s_h_n(PLAYER_SPRITE) / 2
    state["trail"].append((center_x, center_y))
    needed = MAX_WINGMANS * WINGMAN_TRAIL_GAP + 1
    if len(state["trail"]) > needed:
        del state["trail"][: len(state["trail"]) - needed]

    # --- efectes d'impacte: envellir i retirar els acabats ------------------
    for eff in state["effects"]:
        eff["age"] += 1
    state["effects"] = [e for e in state["effects"]
                        if e["age"] < len(e["frames"])]

    # --- terreny: scroll cap a l'esquerra, UNA cel·la per tick ----------------
    # Pas exacte d'una cel·la: aixi els segments de ticks consecutius queden
    # contigus a pantalla i la deteccio de creuaments es simple.
    terrain_step = 1.0 / SCREEN_WIDTH
    for column in state["terrain"]:
        column["x"] -= terrain_step
    state["terrain"] = [c for c in state["terrain"]
                        if c["x"] + terrain_step > 0.0]

    # --- enemics: avancen segons el seu patro de moviment -------------------
    for enemy in state["enemies"]:
        enemy["prev_x"] = enemy["x"]
        _move_enemy(enemy, state["ticks"])
    # Un enemic nomes marxa quan el seu sprite surt del tot del camp.
    state["enemies"] = [
        e for e in state["enemies"]
        if e["x"] + s_w_n(ENEMY_TYPES[e["kind"]]["sprite"]) > 0.0
    ]

    # --- projectils: cap a la dreta; fora de pantalla, fora -------------------
    for shot in state["shots"]:
        shot["prev_x"] = shot["x"]
        shot["x"] += SHOT_SPEED / SCREEN_WIDTH
    state["shots"] = [s for s in state["shots"] if s["x"] < 1.0]

    # --- enemics disparen projectils amb angle variable cap al jugador -------
    player_center_x = state["player_x"] + s_w_n(PLAYER_SPRITE) / 2
    player_center_y = state["player_y"] + s_h_n(PLAYER_SPRITE) / 2
    for enemy in state["enemies"]:
        enemy["fire_cooldown"] = enemy.get("fire_cooldown", 0) - 1
        if enemy["fire_cooldown"] <= 0 and enemy["x"] < 0.95:
            shot = make_enemy_shot(enemy, player_center_x, player_center_y)
            if shot is not None:
                state["enemy_shots"].append(shot)
            enemy["fire_cooldown"] = random.randint(18, 36) - enemy["kind"] * 5

    # --- projectils enemics amb trajectoria angular ---------------------------
    remaining_enemy_shots = []
    es_w, es_h = 1.0 / SCREEN_WIDTH, 1.0 / SCREEN_HEIGHT
    for shot in state["enemy_shots"]:
        shot["x"] += shot["vx"]
        shot["y"] += shot["vy"]
        if 0.0 <= shot["x"] <= 1.0 and 0.0 <= shot["y"] <= 1.0:
            # Els projectils enemics tampoc travessen la roca.
            if any(rects_overlap(shot["x"], shot["y"], es_w, es_h, *wr)
                   for column in state["terrain"]
                   for wr in wall_rects(column)):
                state["effects"].append(make_effect(
                    shot["x"], shot["y"], SPARK_FRAMES))
                continue
            remaining_enemy_shots.append(shot)
    state["enemy_shots"] = remaining_enemy_shots

    # --- kits de reparacio: deriven cap a l'esquerra i es poden recollir ----
    # Aquest bloc va ABANS de resoldre els impactes: aixi els kits que neixen
    # d'una baixa apareixen exactament al punt de l'explosio i no es mouen
    # fins el tick seguent. Tocar-los amb la nau retorna la seva cura,
    # limitada al maxim del casc.
    sr = ship_rect(state)
    remaining = []
    for pu in state["powerups"]:
        pu["x"] -= POWERUP_SPEED / SCREEN_WIDTH
        p = POWERUPS[pu["kind"]]
        pw, ph = s_w_n(p["sprite"]), s_h_n(p["sprite"])
        if pu["x"] + pw <= 0.0:
            continue                            # ha sortit per l'esquerra
        if rects_overlap(pu["x"], pu["y"], pw, ph, *sr):
            if p.get("wingman"):
                # Dron aliat: s'afegeix a l'esquadra fins al maxim; si ja
                # hi ha MAX_WINGMANS, el kit es converteix en punts bonus.
                if state["wingmans"] < MAX_WINGMANS:
                    state["wingmans"] += 1
                else:
                    state["score"] += WINGMAN_SCORE_BONUS
            else:
                state["hp"] = min(SHIP_MAX_HP, state["hp"] + p["heal"])
            continue                            # recollit
        remaining.append(pu)
    state["powerups"] = remaining

    # --- impactes projectil-enemic -------------------------------------------------
    # Solapament de rectangles despres de moure; a mes, detectem creuaments
    # dins del mateix tick (el projectil passa de ser darrere l'enemic a ser
    # davant) per evitat que els mes petits s'escapin sense rebre l'impacte.
    shot_w = s_w_n(SHOT_SPRITE)
    shot_h = s_h_n(SHOT_SPRITE)
    dead_shots, dead_enemies = set(), set()
    for i, shot in enumerate(state["shots"]):
        if i in dead_shots:
            continue
        sx, sy = shot["x"], shot["y"]
        # La roca atura els projectils: espurna a la vora i fora. A mes del
        # solapament es detecta el creuament dins del mateix tick (el tiri es
        # mes rapid que l'amplada d'una columna de paret).
        hit_wall = False
        for column in state["terrain"]:
            for wl, wt, ww, wh in wall_rects(column):
                hit = rects_overlap(sx, sy, shot_w, shot_h, wl, wt, ww, wh)
                if not hit and sy < wt + wh and wt < sy + shot_h:
                    hit = (shot.get("prev_x", sx) <= wl and sx >= wl)
                if hit:
                    hit_wall = True
                    break
            if hit_wall:
                break
        if hit_wall:
            state["effects"].append(make_effect(sx, sy, SPARK_FRAMES))
            dead_shots.add(i)
            continue
        for j, enemy in enumerate(state["enemies"]):
            if j in dead_enemies:
                continue
            ex, ey, ew, eh = enemy_rect(enemy)
            hit = rects_overlap(sx, sy, shot_w, shot_h, ex, ey, ew, eh)
            if not hit and sy < ey + eh and ey < sy + shot_h:
                # Mateixa banda vertical: ha creuat aquest tick?
                hit = (shot.get("prev_x", sx) < enemy.get("prev_x", ex)
                       and sx >= ex + ew)
            if hit:
                # Espurna justament on ha tocat el projectil.
                state["effects"].append(
                    make_effect(sx, sy, SPARK_FRAMES))
                dead_shots.add(i)
                enemy["hp"] -= 1                # els grans aguanten mes d'un toc
                if enemy["hp"] <= 0:
                    dead_enemies.add(j)
                    state["score"] += ENEMY_TYPES[enemy["kind"]]["points"]
                    # Explosio al centre de l'enemic abatut; com mes gros,
                    # mes grossa la deflagracio.
                    state["effects"].append(make_effect(
                        ex + ew / 2, ey + eh / 2,
                        BOOM_FRAMES if ew >= 3.0 / SCREEN_WIDTH
                        else SPARK_FRAMES))
                    # Recompensa i desenllac del cap final: derrotar-lo
                    # completa l'escenari immediatament (encara que quedin
                    # ticks de mapa) i deixa caure un kit gran amb certa
                    # probabilitat; els altres enemics segueixen el sorteig.
                    if enemy["kind"] == BOSS_KIND:
                        state["completed"] = True
                        if random.random() < BOSS_DROP_CHANCE:
                            state["powerups"].append(
                                make_powerup(ex + ew / 2, ey + eh / 2,
                                             BOSS_DROP_KIND))
                    else:
                        drop = roll_powerup_drop()
                        if drop is not None:
                            state["powerups"].append(
                                make_powerup(ex + ew / 2, ey + eh / 2, drop))
                break                           # cada projectil pega un sol cop
    if dead_shots:
        state["shots"] = [s for i, s in enumerate(state["shots"])
                          if i not in dead_shots]
        state["enemies"] = [e for j, e in enumerate(state["enemies"])
                            if j not in dead_enemies]
    # Les posicions previes ja no fan falta fins al proper tick.
    for enemy in state["enemies"]:
        enemy.pop("prev_x", None)
    for shot in state["shots"]:
        shot.pop("prev_x", None)

    # --- colisions contra la nau: dany pesat i enemic esbucat ----------------
    # Cada enemic que toca el casc li fa el dany del seu tipus i explota al
    # seu centre; poden xocar varis el mateix tick (el dany s'acumula).
    sr = ship_rect(state)
    survivors = []
    for enemy in state["enemies"]:
        if rects_overlap(*sr, *enemy_rect(enemy)):
            state["hp"] = max(0, state["hp"]
                              - ENEMY_TYPES[enemy["kind"]]["damage"])
            ex, ey, ew, eh = enemy_rect(enemy)
            state["effects"].append(make_effect(
                ex + ew / 2, ey + eh / 2,
                BOOM_FRAMES if ew >= 3.0 / SCREEN_WIDTH else SPARK_FRAMES))
        else:
            survivors.append(enemy)
    state["enemies"] = survivors

    # --- projectils enemics: no es poden destruir, nomes esquivar-los ---------
    enemy_shot_size_w = s_w_n(("o",))
    enemy_shot_size_h = s_h_n(("o",))
    live_enemy_shots = []
    for shot in state["enemy_shots"]:
        if rects_overlap(state["player_x"], state["player_y"],
                         s_w_n(PLAYER_SPRITE), s_h_n(PLAYER_SPRITE),
                         shot["x"], shot["y"], enemy_shot_size_w, enemy_shot_size_h):
            state["hp"] = max(0, state["hp"] - shot["damage"])
            ex = shot["x"] + enemy_shot_size_w / 2
            ey = shot["y"] + enemy_shot_size_h / 2
            state["effects"].append(make_effect(ex, ey, SPARK_FRAMES))
            continue
        live_enemy_shots.append(shot)
    state["enemy_shots"] = live_enemy_shots

    # --- parets del terreny: tocar-ne una destrueix la nau --------------------
    # El pas s'estreta a proposit: si el casc toca la roca (o la sobrevola
    # sense solapar-la, perque avanca mes rapid que l'amplada de la columna),
    # la nau explota i la ronda acaba.
    if state["hp"] > 0:
        px, py, pw, ph = sr
        prev_right = state.get("ship_prev_x", px) + pw
        for column in state["terrain"]:
            for wl, wt, ww, wh in wall_rects(column):
                hit = rects_overlap(px, py, pw, ph, wl, wt, ww, wh)
                if not hit and py < wt + wh and wt < py + ph:
                    hit = (prev_right <= wl and px + pw >= wl)
                if hit:
                    state["effects"].append(make_effect(
                        px + pw / 2, py + ph / 2, BOOM_FRAMES))
                    state["hp"] = 0
                    break
            if state["hp"] <= 0:
                break


def find_collision(state: dict):
    """Retorna el primer enemic el rectangle del qual toca la nau, o None."""
    sr = ship_rect(state)
    for enemy in state["enemies"]:
        if rects_overlap(*sr, *enemy_rect(enemy)):
            return enemy
    return None


# --------------------------------------------------------------------------- #
# Renderitzat                                                                 #
# --------------------------------------------------------------------------- #
def _plot(char: str, x: int, y: int, code: str = None) -> None:
    """Posa un caracter (i el seu color) als buffers; fora de pantalla, res."""
    if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
        _screen[y][x] = char
        _colors[y][x] = code


def draw_sprite(sprite, nx: float, ny: float, code: str = None) -> None:
    """Pinta un sprite als buffers a partir de posicio normalitzada (0..1).

    Converteix l'origen de normalitzat a cel·les de pantalla (cell_x/cell_y);
    els espais son transparents (no esborren el que hi ha a sota), el retall
    als bordes es automatica i cada cel·la pot substituir el `code` general.
    """
    ox = cell_x(nx)
    oy = cell_y(ny)
    for dy, row in enumerate(sprite):
        for dx, cell in enumerate(row):
            if isinstance(cell, tuple):
                char, cell_code = cell
            else:
                char, cell_code = cell, None
            if char != " ":
                _plot(char, ox + dx, oy + dy,
                      cell_code if cell_code is not None else code)


def draw_player(x: int, y: int) -> None:
    """Dibuixa la nau a les coordenades indicades."""
    draw_sprite(PLAYER_SPRITE, x, y, CODE_PLAYER)


def draw_enemy(enemy: dict) -> None:
    """Dibuixa un enemic amb el sprite i el color del seu tipus."""
    t = ENEMY_TYPES[enemy["kind"]]
    draw_sprite(t["sprite"], enemy["x"], enemy["y"], t.get("color"))


def draw_shot(shot: dict) -> None:
    """Dibuixa un projectil a les coordenades indicades."""
    draw_sprite(SHOT_SPRITE, shot["x"], shot["y"], CODE_SHOT)


def draw_enemy_shot(shot: dict) -> None:
    """Dibuixa un projectil enemic amb una marca visual d'alerta fixa."""
    draw_sprite(ENEMY_SHOT_SPRITE, shot["x"], shot["y"])


def draw_effect(eff: dict) -> None:
    """Dibuixa el frame actual d'un efecte d'impacte."""
    draw_sprite(eff["frames"][eff["age"]], eff["x"], eff["y"], CODE_IMPACT)


def draw_powerup(pu: dict) -> None:
    """Dibuixa un kit de reparacio amb el sprite del seu tamany."""
    p = POWERUPS[pu["kind"]]
    draw_sprite(p["sprite"], pu["x"], pu["y"], CODE_POWERUP)


def draw_terrain_column(column: dict) -> None:
    """Pinta una columna de paret, enganxada a les vores superior i inferior.

    La cel·la de la superficie (la que mira al corredor) fa servir l'estil
    "vora"; la resta de la paret, l'estil "cos".
    """
    cx = cell_x(column["x"])
    if not 0 <= cx < SCREEN_WIDTH:
        return
    top = max(0, min(SCREEN_HEIGHT, column["top"]))
    bot = max(0, min(SCREEN_HEIGHT - top, column["bot"]))
    for y in range(top):
        char, code = column["edge"] if y == top - 1 else column["fill"]
        _plot(char, cx, y, code)
    for y in range(SCREEN_HEIGHT - bot, SCREEN_HEIGHT):
        char, code = (column["edge"] if y == SCREEN_HEIGHT - bot
                      else column["fill"])
        _plot(char, cx, y, code)


def _active_boss(state: dict):
    """El cap final actual (``kind == BOSS_KIND``) o ``None`` si encara no ha
    néixit o ja ha caït. Es busca entre els enemics visuals: el boss és l'enemic
    de ``kind == BOSS_KIND`` que encara no s'ha derrotat.
    """
    for enemy in state["enemies"]:
        if enemy["kind"] == BOSS_KIND:
            return enemy
    return None


def render(state: dict) -> str:
    """Compon el HUD i el camp de joc (amb colors) i ho retorna com a text."""
    global _screen, _colors
    _screen = [[" "] * SCREEN_WIDTH for _ in range(SCREEN_HEIGHT)]
    _colors = [[None] * SCREEN_WIDTH for _ in range(SCREEN_HEIGHT)]

    # Ordre de pintat: el terreny es fons (la roca queda a sota de tot),
    # despres projectils, enemics, efectes, kits i finalment la nau.
    for column in state["terrain"]:
        draw_terrain_column(column)
    for shot in state["shots"]:
        draw_shot(shot)
    for shot in state["enemy_shots"]:
        draw_enemy_shot(shot)
    for enemy in state["enemies"]:
        draw_enemy(enemy)
    for eff in state["effects"]:
        draw_effect(eff)
    for pu in state["powerups"]:
        draw_powerup(pu)
    for i in range(state["wingmans"]):
        wx, wy = wingman_position(state, i)
        draw_sprite(WINGMAN_SPRITE, wx, wy, CODE_PLAYER)
    if not state.get("hide_player", False):
        draw_player(state["player_x"], state["player_y"])

    # Converteix els buffers a text agrupant celes consecutives del mateix
    # color en un sol trac (un parell de codis ANSI per grup, no per cela).
    rows = []
    for y in range(SCREEN_HEIGHT):
        parts, current = [], None
        for x in range(SCREEN_WIDTH):
            code = _colors[y][x]
            if code != current:
                if current is not None and COLOR_ENABLED:
                    parts.append(RESET_COLOR)
                if COLOR_ENABLED and code is not None:
                    parts.append(f"\x1b[{code}m")
                current = code
            parts.append(_screen[y][x])
        if current is not None and COLOR_ENABLED:
            parts.append(RESET_COLOR)
        rows.append("".join(parts))

    hud = (" " + paint(f"PUNTS {state['score']:5d}", CODE_HUD)
           + "     " + paint("w/s mou   a/d avanca   ESPAI dispara   "
                             f"{KEY_PAUSE} pausa   {KEY_QUIT} surt",
                             CODE_HINT))

    # Barra de casc a la part inferior; canvia de color segons la vida restant:
    # verd per sobre del 60%, groc fins al 25% i vermell en nivell critic.
    hp = max(0, min(SHIP_MAX_HP, state["hp"]))
    filled = STATUS_BAR_WIDTH * hp // SHIP_MAX_HP
    gauge = "#" * filled + "-" * (STATUS_BAR_WIDTH - filled)
    if hp > SHIP_MAX_HP * 3 // 5:
        gauge_code = "92"                      # verd: casc sa
    elif hp > SHIP_MAX_HP // 4:
        gauge_code = "93"                      # groc: tocat pero flota
    else:
        gauge_code = "91"                      # vermell: nivell critic
    map_progress = max(0.0, min(1.0, state.get("map_progress", 0.0)))
    map_filled = MAP_PROGRESS_BAR_WIDTH * int(map_progress * 100) // 100
    map_gauge = "#" * map_filled + "-" * (MAP_PROGRESS_BAR_WIDTH - map_filled)
    map_percent = int(map_progress * 100)
    status = (paint(f" CASC [{gauge}] {hp}/{SHIP_MAX_HP}", gauge_code)
              + paint(f"   MAPA [{map_gauge}] {map_percent:3d}%", "96"))
    # Barra de vida del cap final (si encomana): nomes es mostra mentre el cap
    # es viu, despres de la barra de mapa. El magenta combina amb el seu
    # sprite multicolor.
    boss = _active_boss(state)
    if boss is not None:
        boss_hp = max(0, boss["hp"])
        b_filled = BOSS_BAR_WIDTH * boss_hp // BOSS_MAX_HP
        b_gauge = "#" * b_filled + "-" * (BOSS_BAR_WIDTH - b_filled)
        status += paint(f"   CAP [{b_gauge}] {boss_hp}/{BOSS_MAX_HP}", "95")

    return hud + "\n" + "\n".join(rows) + "\n" + status


def clear_screen() -> None:
    """Neteja la pantalla de la consola (Windows)."""
    os.system("cls")


def draw_frame(text: str) -> None:
    """Pinta un frame sencer sense fer parpellejar la pantalla.

    Amb colors actius NO esborrem res: movem el cursor a l'origen (\\x1b[H)
    i repintem el frame a sobre de l'anterior; com que el camp te mida fixa,
    el frame nou cobreix exactament l'antic. A mes, tot el frame s'escriu en
    una sola crida per minimitzar el tearing. Nomes el primer frame de cada
    ronda fa una neteja completa; el mode monocrom manté el vell cls.
    """
    global _first_frame
    if not COLOR_ENABLED:
        clear_screen()                         # fallback classic
        print(text)
        return
    prefix = "\x1b[2J\x1b[H" if _first_frame else "\x1b[H"
    sys.stdout.write(prefix + text + "\n")
    sys.stdout.flush()
    _first_frame = False


COMPLETION_BANNER = r"""
 __   __ _____ _     _____ _       ____  ____  __  __ ____  _     _____ _____ _____
 \ \ / /| ____| |   | ____| |     / ___||  _ \|  \/  |  _ \| |   | ____|_   _| ____|
  \ V / |  _| | |   |  _| | |     \___ \| |_) | |\/| | |_) | |   |  _|   | | |  _|
   | |  | |___| |___| |___| |___   ___) |  __/| |  | |  __/| |___| |___  | | | |___
   |_|  |_____|_____|_____|_____| |____/|_|   |_|  |_|_|   |_____|_____| |_| |_____|
"""


def animate_completion(state: dict) -> None:
    """Mostra el banner i fa sortir la nau per la dreta del camp."""
    # En demo no hi ha animacions: fora terreny i nau, i endavant.
    if DEMO_MODE:
        state["terrain"] = []
        state["hide_player"] = True
        return
    # Mostra el banner centrat en una pantalla separada
    banner_lines = paint(COMPLETION_BANNER, "92").splitlines()
    padding = (SCREEN_HEIGHT - len(banner_lines)) // 2
    banner_block = "\n".join([""] * padding + banner_lines + [""] * padding)
    draw_frame(banner_block)
    time.sleep(6.0)
    # Torna al camp de joc i fa sortir la nau; el terreny desapareix perque
    # la nau surti volant per un camp net.
    state["terrain"] = []
    state["hide_player"] = False
    while state["player_x"] <= 1.0:
        draw_frame(render(state))
        state["player_x"] += 4.0 / SCREEN_WIDTH
        time.sleep(0.06)
    state["hide_player"] = True
    draw_frame(render(state))


# --------------------------------------------------------------------------- #
# Pantalles                                                                   #
# --------------------------------------------------------------------------- #
BANNER = r"""
    _____ _____ _____         ____              _
   |  __ \_   _|_   _|       |  _ \ ___ _ __   |_(_)___
   | |__) || |   | |   _____| |_) / _ \ '_ \ __| | / __|
   |  _  / | |   | |  |_____|  _ <  __/ | | |__| | \__ \
   |_| \_\ |_|   |_|         |_| \_\___|_| |\__,_|_|___/
                                            |_/
"""


def show_intro() -> None:
    """Pantalla de benvinguda amb els controls; espera una tecla per començar."""
    if DEMO_MODE:
        # En demo no hi ha teclat: una sola linia i correm.
        print(paint(f"[demo] Mapa: {MAPS[CURRENT_MAP]['name']}", CODE_HINT))
        return
    clear_screen()
    print(paint(BANNER, CODE_TITLE))
    print(paint(f"   Mapa: {MAPS[CURRENT_MAP]['name']}", CODE_HINT))
    print("   Esquiva o destrueix els enemics que arriben des de la dreta:")
    print()
    print(paint(f"     {KEY_UP}/{KEY_DOWN} o fletxes    amunt / avall", CODE_HINT))
    print(paint(f"     {KEY_BACK}/{KEY_FORWARD} o fletxes  endarrere / endavant",
                CODE_HINT))
    print(paint("     ESPAI   disparar (manten-lo premut = tir continu)", CODE_HINT))
    print(paint(f"     {KEY_PAUSE}       pausa ({KEY_PAUSE} altre cop per continuar)",
                CODE_HINT))
    print(paint(f"     {KEY_QUIT}       sortir", CODE_HINT))
    print()
    print(paint("   MILLORS PUNTUACIONS", CODE_HUD))
    for line in scores_block().splitlines():
        print(paint(line, CODE_HUD))
    print()
    print("   Manten premudes les tecles: el joc respon mentre estan actives")
    print("   i en pots combinar diverses alhora.")
    print()
    print(paint("   Patrons de vol: rectes, ones, zigzags i picats.", CODE_HINT))
    print(paint("   La barra inferior es el teu casc: no la deixis a zero.",
                CODE_HINT))
    print(paint("   Alguns enemics abatuts deixen kits vermells de reparacio.",
                CODE_HINT))
    print("   Enemics, de petit a gros:")
    for t in ENEMY_TYPES:
        plural = "vida" if t["hp"] == 1 else "vides"
        for row in t["sprite"]:
            visible_row = "".join(cell[0] if isinstance(cell, tuple) else cell
                                   for cell in row)
            print("      " + paint(visible_row, t.get("color")))
        print(paint(f"         {t['hp']} {plural}, {t['points']} punts", CODE_HINT))
    print()
    print(paint(f"   Camp de joc: {SCREEN_WIDTH}x{SCREEN_HEIGHT} (ajustat al terminal)",
                CODE_HINT))
    print()
    print("   Premeu qualsevol tecla per comencar...")
    wait_key()


def show_game_over(score: int, completed: bool = False,
                   record: bool = False) -> None:
    """Pantalla de fi de partida, per derrota o per mapa completat."""
    print()
    if completed:
        print(paint(f" NIVELL COMPLETAT - puntuacio final: {score}", "92"))
    else:
        print(paint(f" GAME OVER - puntuacio final: {score}", CODE_ALERT))
    if record:
        print(paint(" NOU RECORD!", "93"))
    print(paint("   MILLORS PUNTUACIONS", CODE_HUD))
    for line in scores_block().splitlines():
        print(paint(line, CODE_HUD))
    print(paint(f" Prem '{KEY_REPLAY}' per tornar a jugar, o qualsevol altra "
                f"tecla per sortir.", CODE_HINT))


def show_campaign_complete(score: int, record: bool = False) -> None:
    """Pantalla de victoria quan s'acaba l'ultim nivell de la campanya."""
    print()
    print(paint(" CAMPANYA COMPLETADA!", "92"))
    print(paint(f" Puntuacio final: {score}", CODE_HUD))
    if record:
        print(paint(" NOU RECORD!", "93"))
    print(paint("   MILLORS PUNTUACIONS", CODE_HUD))
    for line in scores_block().splitlines():
        print(paint(line, CODE_HUD))
    print(paint(f" Prem '{KEY_REPLAY}' per repetir la campanya des del "
                f"principi, o qualsevol altra tecla per sortir.", CODE_HINT))


# --------------------------------------------------------------------------- #
# Mode demo (pilot automatic determinista)                                    #
# --------------------------------------------------------------------------- #
# `python main.py --demo [nivell]` juga la campanya sola, amb un pilot
# automatic determinista: serveix per provar el bucle complet (spawns,
# terreny, kits, fi de nivell) sense teclat, al terminal o a la CI. La
# politica, per ordre de prioritat: 1) colocar-se al corredor lliure que
# imposen les parets properes (interseccio de les seves franges lliures);
# 2) dins del corredor, esquivar el perill (tret apuntat o enemic) mes
# proper SENSE sortir-ne mai; 3) sense corredor proper, esquivar el perill
# mes proper; 4) si no hi ha perills, derivar cap al centre del camp; i
# disparar sempre que hi hagi enemics per davant (el cooldown regula el
# ritme de tir). La llavor fixa fa que cada execucio sigui identica.
DEMO_MODE = False              # s'activa amb --demo a la linia de comandes
DEMO_SEED = 1                  # llavor fixa per a drops reproduibles
DEMO_RENDER_EVERY = 60         # pinta un frame cada N ticks (0 = mai)
DEMO_MAX_TICKS = 20000         # fusible: cap nivell hauria de durar tant
DEMO_ENEMY_LOOKAHEAD = 12.0    # celes per davant on un enemic es amenaça
DEMO_SHOT_PREDICT = 80         # ticks de trajectoria de tret que es prediu
                               # (el vol sencer: la ruta es fixa en disparar)
DEMO_WALL_AHEAD = 16.0         # columnes per davant que cal tenir en compte
DEMO_WALL_BEHIND = 2.0         # columnes ja depassades que encara compten


def _corridor_free_band(state: dict):
    """Banda vertical lliure (lo, hi) imposada per les parets properes.

    Considera TOTES les columnes que la nau te a sobre o que s'hi apropen
    (dins DEMO_WALL_AHEAD/DEMO_WALL_BEHIND) i retorna la INTERSECCIO de les
    seves franges lliures: aixi les rampes i esglaons no enganyen, perque la
    banda ja compleix la columna mes exigent. Retorna None si no hi ha cap
    paret rellevant.
    """
    sr = ship_rect(state)
    nose = sr[0] + sr[2]
    x_w = 1.0 / SCREEN_WIDTH
    lo, hi, found = 0.0, 1.0, False
    for column in state["terrain"]:
        if column["top"] == 0 and column["bot"] == 0:
            continue                       # columna sense parets
        if column["x"] + x_w <= sr[0] - DEMO_WALL_BEHIND * x_w:
            continue                       # completament enrrera
        if column["x"] > nose + DEMO_WALL_AHEAD * x_w:
            continue                       # encara massa lluny
        found = True
        lo = max(lo, column["top"] / SCREEN_HEIGHT)
        hi = min(hi, 1.0 - column["bot"] / SCREEN_HEIGHT)
    if not found:
        return None
    return lo, hi


def _ticks_until_wall(state: dict, sr):
    """Ticks fins que la propera columna de paret arribi al morro, o None.

    Les parets avancen 1 cel·la per tick cap a l'esquerra i la nau del pilot
    no avança: la distancia en cel·les fins a la columna mes propera que
    encara no hem depassat ES el nombre de ticks disponibles.
    """
    nose = sr[0] + sr[2]
    x_w = 1.0 / SCREEN_WIDTH
    nearest = None
    for column in state["terrain"]:
        if column["top"] == 0 and column["bot"] == 0:
            continue
        if column["x"] + x_w <= sr[0]:
            continue                       # ja la tenim a sobre o enrrera
        d = (column["x"] - nose) / x_w
        if nearest is None or d < nearest:
            nearest = d
    if nearest is None:
        return None
    return max(0.0, nearest)


def _shot_threat(state: dict, sr):
    """Primer tret enemic que creuara el casc segons la seva trajectoria.

    Simula DEMO_SHOT_PREDICT ticks de vol (son trets APUNTATS: la seva ruta
    ja es fixa en disparar, aixi que predir-la es fiable) amb el casc inflat
    mig fila de marge. Retorna (distancia_del_morro, cy_previst) o None.
    """
    w, h = s_w_n(("o",)), s_h_n(("o",))
    pad = 0.5 / SCREEN_HEIGHT
    best = None
    for s in state["enemy_shots"]:
        if s["vx"] >= 0.0:
            continue                       # s'allunya: no amenaça
        for k in range(1, DEMO_SHOT_PREDICT + 1):
            px = s["x"] + s["vx"] * k
            py = s["y"] + s["vy"] * k
            if px + w <= sr[0]:
                break                      # ha depassat la nau: no la toca
            if rects_overlap(px, py, w, h,
                             sr[0], sr[1] - pad, sr[2], sr[3] + 2 * pad):
                d = px - (sr[0] + sr[2])
                if best is None or d < best[0]:
                    best = (d, py + h / 2)
                break
    return best


def _enemy_threat(state: dict, sr):
    """Enemic mes proper per davant que comparteix banda vertical amb la nau.

    Retorna (distancia_del_morro_al_perill, cy_del_perill) o None.
    """
    threat, threat_cy, gap = None, 0.0, None
    for enemy in state["enemies"]:
        ex, ey, ew, eh = enemy_rect(enemy)
        if ex + ew <= sr[0]:
            continue                       # per darrera: no amenaça
        if ex > sr[0] + sr[2] + DEMO_ENEMY_LOOKAHEAD / SCREEN_WIDTH:
            continue                       # massa lluny
        band = (eh + sr[3]) / 2.0 + 0.8 / SCREEN_HEIGHT
        if ey + eh < sr[1] - band or ey > sr[1] + sr[3] + band:
            continue                       # bandes verticals separades
        d = ex - sr[0]
        if gap is None or d < gap:
            gap, threat, threat_cy = d, enemy, ey + eh / 2.0
    if threat is None:
        return None
    return gap, threat_cy


def demo_actions(state: dict) -> set:
    """Accions del pilot automatic per a aquest tick (mateix format que
    `pressed_keys()`): conjunt d'ACCIONS actives."""
    actions = set()
    sr = ship_rect(state)
    ship_cy = sr[1] + sr[3] / 2.0
    max_y = 1.0 - s_h_n(PLAYER_SPRITE)

    # Intencio vertical, per prioritats ESTRICTES: dins de corredor, nomes
    # centrat (esquivar-hi ha acabat estampant la nau contra les rampes);
    # sense corredor proper, esquiva el perill predit (tret apuntat o enemic).
    # Els trets que neixin a escassos ticks del casc son riscs acceptats.
    band = _corridor_free_band(state)
    dy = 0.0
    if band is not None:
        c_lo = band[0] + sr[3] / 2.0          # rang valid del CENTRE de la nau
        c_hi = band[1] - sr[3] / 2.0
        dy = (c_lo + c_hi) / 2.0 - ship_cy    # centra dins del corredor
        if abs(dy) < 0.5 / SCREEN_HEIGHT:     # zona morta: no jitterar
            dy = 0.0
        # Dins del corredor tambe cal esquivar perills (els trets apuntats i
        # els crashes son la primera causa de desgast), pero SEMPRE sense
        # sortir de la banda: si el pas d'esquiva ens faria sortir, es
        # manté el centrat. Esquiva el perill mes proper dels dos.
        shot = _shot_threat(state, sr)
        foe = _enemy_threat(state, sr)
        threat = None
        if shot is not None and (foe is None or shot[0] <= foe[0]):
            threat = shot
        elif foe is not None:
            threat = foe
        if threat is not None:
            dodge = -1.0 if threat[1] >= ship_cy else 1.0
            nxt = ship_cy + dodge / SCREEN_HEIGHT
            if c_lo - 1e-9 <= nxt <= c_hi + 1e-9:
                dy = dodge
    else:
        shot = _shot_threat(state, sr)
        foe = _enemy_threat(state, sr)
        if shot is not None and (foe is None or shot[0] <= foe[0]):
            threat = shot
        elif foe is not None:
            threat = foe
        else:
            threat = None
        if threat is not None:
            dy = -1.0 if threat[1] >= ship_cy else 1.0
        elif abs(state["player_y"]
                 - (0.5 - sr[3] / 2.0)) > 2.0 / SCREEN_HEIGHT:
            dy = (0.5 - sr[3] / 2.0) - state["player_y"]   # deriva al centre
        else:
            dy = 0.0

    # Converteix la intencio en accio feasible (respectant les vores), amb una
    # zona morta de mig fila: sense ella, el centre del corredor mou la nau
    # amunt i avall cada tick (oscil·lacio) i pot ficarla dins d'una rampa.
    if dy < -0.5 / SCREEN_HEIGHT:
        actions.add(ACTION_UP if state["player_y"] > 0 else ACTION_DOWN)
    elif dy > 0.5 / SCREEN_HEIGHT:
        actions.add(ACTION_DOWN if state["player_y"] < max_y else ACTION_UP)

    # Retirada horitzontal: si la paret propera demana una posicio vertical
    # que la nau no assolira a temps (descens a 1 fila/tick contra paret a
    # 1 columna/tick), ENDARRERE: la nau es 3.5 cops mes rapida en horitzontal
    # i aixi guanya els ticks que li falten per posicionar-se al corredor.
    if band is not None:
        c_lo = band[0] + sr[3] / 2.0
        c_hi = band[1] - sr[3] / 2.0
        if not c_lo - 1e-9 <= ship_cy <= c_hi + 1e-9:
            rows_needed = max(c_lo - ship_cy, ship_cy - c_hi) * SCREEN_HEIGHT
            ticks_to_wall = _ticks_until_wall(state, sr)
            if (ticks_to_wall is not None
                    and rows_needed + 0.75 >= ticks_to_wall):
                actions.add(ACTION_BACK)

    # Dispara si hi ha qualsevol enemic per davant del morro.
    for enemy in state["enemies"]:
        ex, _ey, _ew, _eh = enemy_rect(enemy)
        if ex > sr[0] + sr[2] - 2.0 / SCREEN_WIDTH:
            actions.add(ACTION_SHOOT)
            break
    return actions


# --------------------------------------------------------------------------- #
# Bucle principal                                                             #
# --------------------------------------------------------------------------- #
def pause_round(state: dict) -> bool:
    """Pausa el joc fins que el jugador la continuï o surti.

    Bloqueja esperant una pulsacio nova: 'p' continua (un cop la tecla esta
    fisicament alliberada, per no tornar a pausar a l'instant) i 'q' surt.
    Retorna True per continuar la partida o False per abandonar-la.
    """
    print(paint(f" PAUSA - prem '{KEY_PAUSE}' per continuar, "
                f"'{KEY_QUIT}' per sortir", CODE_HINT))
    while True:
        ch = wait_key()
        if ch == KEY_QUIT:
            return False
        if ch == KEY_PAUSE:
            # No reprenem mentre 'p' segueixi fisicament premuda: amb
            # GetAsyncKeyState tornaria a pausar a l'instant.
            while ACTION_PAUSE in pressed_keys():
                time.sleep(0.02)
            return True


def run_round():
    """Juga una ronda completa.

    Retorna una tupla ``(resultat, punts)`` on resultat es ``"quit"``
    (l'usuari ha sortit), ``"dead"`` (la nau ha quedat sense casc) o
    ``"completed"`` (el mapa s'ha recorregut completament).
    """
    global _first_frame
    _first_frame = True                        # nova ronda: neteja completa
    state = new_state()

    while True:
        # 1. Llegeix l'ESTAT del teclat: totes les tecles premudes ara mateix.
        #    En ser estat (i no pulsacions), pots mantenir la tecla premuda
        #    per moure't contínuament i prémer diverses tecles alhora.
        #    En mode demo, qui decideix es el pilot automatic.
        actions = demo_actions(state) if DEMO_MODE else pressed_keys()

        if ACTION_QUIT in actions:
            return "quit", state["score"]
        if ACTION_PAUSE in actions and not DEMO_MODE:
            if not pause_round(state):
                return "quit", state["score"]
            _first_frame = True          # repinta sencera: esborra el texte de pausa

        # Moviment combinable: dx i dy són independents (permet diagonals);
        # move_player ja s'encarrega dels límits de la zona.
        dx = (ACTION_FORWARD in actions) - (ACTION_BACK in actions)
        dy = (ACTION_DOWN in actions) - (ACTION_UP in actions)
        # Recorda d'on venia la nau: si aquest tick sobreve una columna de
        # paret sense solapar-la (la nau es mes rapida que l'amplada de la
        # columna), la colisio per creuament ho detecta igualment.
        state["ship_prev_x"] = state["player_x"]
        if dx or dy:
            move_player(state, dx=dx, dy=dy)

        # Tir continu: mantenint ESPAI premut, es dispara tan bon punt el
        # canó torna a estar carregat (el cooldown el gestiona shoot()).
        if ACTION_SHOOT in actions:
            shoot(state)

        # 2. Avança el mon ------------------------------------------------------
        update_world(state)

        # 3. La nau ha perdut tota la vida? --------------------------------------
        if state["hp"] <= 0:
            return "dead", state["score"]
        if state["completed"]:
            animate_completion(state)
            return "completed", state["score"]
        if DEMO_MODE and state["ticks"] > DEMO_MAX_TICKS:
            return "timeout", state["score"]   # fusible anti-bucle infinit

        # 4. Renderitza sense parpalleig i marca el ritme del bucle -------------
        #    En demo anem a maxim: nomes un frame cada DEMO_RENDER_EVERY ticks
        #    i cap espera, perque una campanya sencera duri segons.
        if not DEMO_MODE or (DEMO_RENDER_EVERY
                             and state["ticks"] % DEMO_RENDER_EVERY == 0):
            draw_frame(render(state))
        if not DEMO_MODE:
            time.sleep(GAME_TICK)


def print_usage() -> None:
    """Mostra la forma d'us del programa a la linia de comandes."""
    print("Us: python main.py [--demo] [nivell]")
    print(f"  nivell    numero del nivell inicial (1-{len(MAPS)}). "
          f"Sense argument, campanya completa des del nivell 1.")
    print("  --demo    la juga sola: pilot automatic determinista (sense")
    print("            teclat, a maxima velocitat; per proves i CI)")


def level_from_args(argv):
    """Index (0-based) del nivell inicial demanat a la linia de comandes.

    `python main.py 2` comença la partida directament al nivell 2, utl per
    provar un nivell concret sense passar pels anteriors. Sense arguments
    retorna None i la campanya comença pel primer nivell. Amb -h/--ajuda
    mostra l'us; si l'argument es invalid, llista els nivells disponibles
    i acaba el programa. El prefix opcional --demo no canvia el nivell.
    """
    rest = list(argv[1:])
    if rest and rest[0] == "--demo":
        rest = rest[1:]
    if not rest:
        return None
    if rest[0] in ("-h", "--ajuda", "--help"):
        print_usage()
        raise SystemExit(0)
    raw = rest[0]
    if not raw.isdigit() or not 1 <= int(raw) <= len(MAPS):
        print(f"Error: nivell '{raw}' invalid. Nivells disponibles:")
        for i, mapa in enumerate(MAPS, start=1):
            print(f"  {i}. {mapa['name']}")
        print_usage()
        raise SystemExit(1)
    return int(raw) - 1


def main() -> None:
    global CURRENT_MAP, DEMO_MODE
    DEMO_MODE = "--demo" in sys.argv[1:]
    if DEMO_MODE:
        random.seed(DEMO_SEED)             # reproduibilitat del pilot
    nivell_inicial = level_from_args(sys.argv)
    if nivell_inicial is not None:
        # Mode de prova: la campanya comença al nivell demanat i, en
        # superar-lo, continua amb el seguent com sempre.
        CURRENT_MAP = nivell_inicial
    demo_timeout = False
    try:
        if COLOR_ENABLED and not DEMO_MODE:
            # Amaguem el cursor mentre dura el joc: salta per la pantalla a
            # cada frame i dona sensacio de parpalleig.
            sys.stdout.write("\x1b[?25l")
            sys.stdout.flush()
        # La mida del camp es fixa UN COP aquí, abans de res: despres ja no
        # es torna a mesurar encara que es redimensioni la finestra.
        fit_playfield_to_terminal()
        show_intro()
        while True:
            outcome, score = run_round()
            if DEMO_MODE:
                print(paint(f"[demo] {MAPS[CURRENT_MAP]['name']}: "
                            f"{outcome.upper()} - puntuacio: {score}",
                            CODE_HUD if outcome == "completed" else CODE_ALERT))
                if outcome == "timeout":
                    demo_timeout = True
                if outcome == "completed" and CURRENT_MAP + 1 < len(MAPS):
                    CURRENT_MAP += 1
                    show_intro()
                    continue
                break                       # campanya acabada, derrota o fusible
            if outcome == "quit":
                break
            record = save_score(score)     # desa al top (no en demo)
            if outcome == "completed" and CURRENT_MAP + 1 < len(MAPS):
                # Nivell superat i en queden mes: la campanya continua amb el
                # seguent fitxer de nivell. En premer 'r' es mostra la
                # introduccio del nou nivell i s'hi passa.
                CURRENT_MAP += 1
                print()
                print(paint(f" NIVELL SUPERAT - puntuacio: {score}", "92"))
                print(paint(f"   Seguent: {MAPS[CURRENT_MAP]['name']}",
                            CODE_HINT))
                print(paint(f" Prem '{KEY_REPLAY}' per continuar al seguent "
                            f"nivell, o qualsevol altra tecla per sortir.",
                            CODE_HINT))
                if wait_key() != KEY_REPLAY:
                    break
                show_intro()
                continue
            if outcome == "completed":
                # Era l'ultim nivell de la campanya.
                show_campaign_complete(score, record)
            else:
                show_game_over(score, record=record)
            if wait_key() != KEY_REPLAY:
                break
            if outcome == "completed":
                # La campanya sencera es reinicia des del primer nivell.
                CURRENT_MAP = 0
                show_intro()

        clear_screen()
        if DEMO_MODE:
            # Resum final; el codi d'exit nomes falla si el motor s'ha
            # encallat (una derrota del pilot es un resultat valid, no error).
            print(paint("[demo] Campanya finalitzada"
                        + (" - FUSIBLE DE TICKS ACTIVAT" if demo_timeout
                           else ""),
                        CODE_ALERT if demo_timeout else CODE_TITLE))
            if demo_timeout:
                sys.exit(1)
            return
        print(paint("Gracies per jugar a R-Type ASCII!", CODE_TITLE))
    except KeyboardInterrupt:
        print("\nInterromput - adeu!")
    finally:
        if COLOR_ENABLED:
            # Restaura sempre el cursor, tan si es surt be com si peta.
            sys.stdout.write("\x1b[?25h")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
