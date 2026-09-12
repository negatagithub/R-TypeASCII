# -*- coding: utf-8 -*-
"""Síntesi de so procedural per a R-Type ASCII (sense arxius de so).

Genera les ones amb FORMULES MATEMÀTIQUES (sinus, onada quadrada, soroll
determinista, escombrats de freqüència i envolvents d'atac/alliberament) i les
reprodueix amb `winsound` (només Windows) directament des de memòria, sense
cap fitxer .wav ni recurs pregravadet. Cada efecte es descriu com una funció
`freq(t)` variada per paràmetres; la síntesi mostreja la fórmula i l'empaqueta
en un buffer WAV volàtil.

Es desactiva tot sol:
  - si `winsound` no està disponible (plataforma no Windows),
  - si la variable d'entorn R_TYPE_SO és "0",
  - si els tests o el mode demo criden so.set_enabled(False).

Les proves poden forçar-ho amb so.set_enabled(False). Reproduir mai ha de
fer petar el joc: qualsevol error de so es menja en silenci.
"""
import math
import os
import queue      # cua FIFO del motor d'àudio (anti-retard)
import random
import struct
import threading

SND_ON = os.environ.get("R_TYPE_SO", "1") != "0"

try:
    import winsound  # només Windows (part de la stdlib)
    _DISPONIBLE = True
except ImportError:                       # no Windows / entorn sense so
    winsound = None
    _DISPONIBLE = False

RATE = 22050                              # mostres per segon
_AMPLITUD = 20000                         # Pic del PCM de 16 bits
_ultim = b""                              # el buffer reproduït ha de viure


def set_enabled(actiu: bool) -> None:
    """Activa o desactiva el so en temps d'execució (tests, mode demo)."""
    global SND_ON
    SND_ON = bool(actiu)


def actiu() -> bool:
    """Cert si hi ha dispositiu de so i no l'hem desactivat.

    NOTA: abans també exigia ``sys.stdout.isatty()``, però això mutava
    el joc en terminals integrats (VS Code) i redireccions on isatty()
    menteix. Ara només cal winsound + flag actiu; els tests i el mode
    demo el silencien explícitament amb ``set_enabled(False)``.
    """
    return _DISPONIBLE and SND_ON


# --------------------------------------------------------------------------- #
# Síntesi: mostreja una formula freq(t) a un buffer WAV a RATE Hz            #
# --------------------------------------------------------------------------- #
def _onada(gen, dur_ms: float, vol: float = 1.0) -> list:
    """Mostreja `gen(t)` (t en segons) durant dur_ms amb envolvent.

    `gen(t)` retorna un valor a [-1, 1]; `vol` escala l'amplitud. L'envolvent
    fa un fade d'atac (1%) i d'alliberament (8%) per evitar clics.
    """
    n = max(1, int(RATE * dur_ms / 1000.0))
    atac = max(1, int(n * 0.01))
    alliber = max(1, int(n * 0.08))
    mostres = []
    for i in range(n):
        t = i / RATE
        v = gen(t) * vol
        if i < atac:
            v *= i / atac
        if i >= n - alliber:
            v *= (n - i) / alliber
        mostres.append(int(max(-1.0, min(1.0, v)) * _AMPLITUD))
    return mostres


def _wav(mostres: list) -> bytes:
    """Converteix mostres (int 16 bits) en un buffer WAV mono."""
    n = len(mostres)
    fmt = struct.pack("<IHHIIHH", 16, 1, 1, RATE, RATE * 2, 2, 16)
    dada = struct.pack("<" + "h" * n, *mostres)
    return (b"RIFF" + struct.pack("<I", 36 + len(dada)) + b"WAVE"
            + b"fmt " + fmt + b"data" + struct.pack("<I", len(dada)) + dada)


# --------------------------------------------------------------------------- #
# Motor de cues: UN sol fil reproductor + precàrrega (anti-retard)            #
# --------------------------------------------------------------------------- #
# Disseny anterior: cada efecte creava el seu thread i cridava PlaySound
# SÍNCRON (SND_MEMORY sol). Això té dues penalitzacions:
#   1. winsound és UNA sola cua global: cada PlaySound nou TALLA l'anterior
#      (el tret tallava l'explosió i viceversa) i el so sembla que arribi tard.
#   2. Crear un thread per efecte costa ~1-5 ms, que se suma al retard.
#
# Disseny actual: UN fil reproductor persistent (`_FIL`) amb cua FIFO
# (`_CUA`). El fil del joc només fa `_CUA.put(buf)` (~µs, mai bloqueja) i el
# fil d'àudio encadena els buffers amb PlaySound SÍNCRON. Els efectes
# freqüents (tret, explosions...) es PRECARREGUEN (`precarga()`) en arrencar
# el joc: el primer tret ja no paga la síntesi (~2-11 ms) ni l'empaquetat WAV.
# Amb `SND_NOSTOP` cap efecte talla l'anterior: si la cua és plena, el so nou
# s'omet en comptes de tallar el que sona (millor perdre un tret que
# entrebancar tota la banda sonora).
_CUA = queue.Queue(maxsize=8)         # FIFO d'efectes pendents (buffers WAV)
_FIL = None                           # fil reproductor persistent
_PRECARREGAT = {}                     # nom -> bytes WAV llestos per sonar


def _bucle_reproductor() -> None:
    """Fil d'àudio: treu buffers de la cua i els sona un darrere l'altre."""
    while True:
        buf = _CUA.get()
        if buf is None:               # sentinella: morir (només en tests)
            return
        try:
            winsound.PlaySound(buf, winsound.SND_MEMORY
                               | winsound.SND_NODEFAULT | winsound.SND_NOSTOP)
        except (RuntimeError, OSError, ValueError, AttributeError):
            pass


def _assegura_fil() -> None:
    """Engega el fil reproductor (un sol cop, daemon, mai trenca el joc)."""
    global _FIL
    if _FIL is not None and _FIL.is_alive():
        return
    try:
        _FIL = threading.Thread(target=_bucle_reproductor, daemon=True)
        _FIL.start()
    except (RuntimeError, OSError, ValueError, AttributeError):
        _FIL = None


def _buf(nom: str, mostres: list) -> bytes:
    """Guarda el WAV sintetitzat a la precàrrega i el retorna com a bytes."""
    global _ultim
    try:
        _ultim = _wav(mostres)
        dades = bytes(_ultim)  # còpia pròpia: el buffer no mor mai
        _PRECARREGAT[nom] = dades
        return dades
    except (RuntimeError, OSError, ValueError, AttributeError,
            struct.error, MemoryError):
        return b""


def _encua(dades: bytes) -> None:
    """Posa un buffer a la cua d'àudio sense bloquejar mai el joc."""
    if not dades:
        return
    _assegura_fil()
    try:
        _CUA.put_nowait(dades)   # cua plena -> ometem (SND_NOSTOP mana)
    except queue.Full:
        pass
    except (RuntimeError, OSError, ValueError, AttributeError):
        pass


def precarga() -> None:
    """Sintetitza un sol cop tots els SFX i els deixa llestos (anti-retard).

    Cridar-ho en arrencar el joc (abans del primer frame): el primer tret ja
    no paga síntesi ni empaquetat WAV. Amb so desactivat no fa res.
    """
    if not actiu():
        return
    for nom, fn in (("tret", _sint_tret), ("tret_enemic", _sint_tret_enemic),
                    ("explosio_petita", _sint_explosio_petita),
                    ("explosio_gran", _sint_explosio_gran),
                    ("impacte", _sint_impacte), ("kit", _sint_kit),
                    ("dron_aliat", _sint_dron_aliat), ("missil", _sint_missil),
                    ("boss", _sint_boss), ("pausa", _sint_pausa),
                    ("victoria", _sint_victoria),
                    ("gameover", _sint_gameover)):
        try:
            _PRECARREGAT.setdefault(nom, bytes(_wav(fn())))
        except (RuntimeError, OSError, ValueError, AttributeError,
                struct.error, MemoryError):
            pass


def _play(seqs) -> None:
    """(Compatibilitat) Reprodueix mostres JA sintetitzades via la cua.

    Els efectes nous ja no passen per aquí: fan servir la precàrrega +
    `_encua` directament (zero síntesi en el camí crític). Aquesta funció
    encara empaqueta el WAV aquí (fora del fil del joc no hi ha res: qui la
    crida ja és un efecte rar) i l'encua sense bloquejar.
    """
    if not actiu():
        return
    if not isinstance(seqs, list) or not seqs or isinstance(seqs[0], int):
        mostres = seqs
    else:
        mostres = [m for seq in seqs for m in seq]
    global _ultim
    try:
        _ultim = _wav(mostres)
        _encua(bytes(_ultim))
    except (RuntimeError, OSError, ValueError, AttributeError,
            struct.error, MemoryError):
        pass


# --------------------------------------------------------------------------- #
# Ones bàsiques (formules freq(t), t en segons)                              #
# --------------------------------------------------------------------------- #
def _sine(f0: float, k: float = 0.0):
    """Sinus amb escombrat lineal: freq = f0 + k*t."""
    return lambda t: math.sin(2 * math.pi * (f0 * t + 0.5 * k * t * t))


def _square(f0: float, k: float = 0.0):
    """Onada quadrada (so retro) amb escombrat lineal."""
    return lambda t: (1.0 if math.sin(2 * math.pi *
                                      (f0 * t + 0.5 * k * t * t)) >= 0
                      else -1.0)


def _saw(f0: float, k: float = 0.0):
    """Onada de serra (ric en harmònics) amb escombrat lineal."""
    return lambda t: 2 * ((f0 * t + 0.5 * k * t * t) % 1.0) - 1.0


def _soroll(f0: float, llavor: int = 7):
    """Soroll deterministic: canvia de polaritat ~f0 cops per segon.

    Usa una llavor fixa (no random del joc): cada efecte sona identic cada
    cop, com cal per a un efecte procedural reproduïble.
    """
    rng = random.Random(llavor)
    val, pas_ant = 1.0, -1
    def gen(t):
        nonlocal val, pas_ant
        pas = int(t * f0)
        if pas != pas_ant:
            pas_ant = pas
            val = 1.0 if rng.random() < 0.5 else -1.0
        return val
    return gen


# --------------------------------------------------------------------------- #
# Efectes de so: síntesis pura (sense I/O) + enviament via precàrrega.        #
# --------------------------------------------------------------------------- #
# Cada `_sint_*` retorna la llista de mostres (cap so encara); cada efecte
# públic mira la precàrrega i encua el buffer: ZERO síntesi en el camí
# crític quan `precarga()` ja ha corregut (i una sola síntesi la primera
# vegada si no).
def _toca_precarregat(nom: str, sint_fn) -> None:
    if not actiu():
        return
    dades = _PRECARREGAT.get(nom)
    if not dades:
        try:
            dades = _buf(nom, sint_fn())
        except (RuntimeError, OSError, ValueError, AttributeError):
            return
    _encua(dades)


def _sint_tret() -> list:
    return _onada(_square(1600, (250 - 1600) / 0.070), 70, 0.55)


def tret() -> None:
    """Tret del cano: escombrat quadrat 1600 -> 250 Hz en 70 ms (laser)."""
    _toca_precarregat("tret", _sint_tret)


def _sint_tret_enemic() -> list:
    return _onada(_saw(320, (180 - 320) / 0.050), 50, 0.40)


def tret_enemic() -> None:
    """Tret enemic: serra baixa 320 -> 180 Hz, mes greu i curt."""
    _toca_precarregat("tret_enemic", _sint_tret_enemic)


def _sint_explosio_petita() -> list:
    seq = _onada(_soroll(1400), 70, 0.6)
    seq += _onada(_square(360, (70 - 360) / 0.080), 80, 0.5)
    return seq


def explosio_petita() -> None:
    """Explosio petita (dron): esclat de soroll + escombrat descendent."""
    _toca_precarregat("explosio_petita", _sint_explosio_petita)


def _sint_explosio_gran() -> list:
    seq = _onada(_soroll(900, 3), 180, 0.75)
    seq += _onada(_saw(200, (30 - 200) / 0.300), 300, 0.55)
    seq += _onada(_sine(110, (25 - 110) / 0.350), 350, 0.4)
    return seq


def explosio_gran() -> None:
    """Explosio gran (caça/cap): soroll llarg + greu que s'enfonsa."""
    _toca_precarregat("explosio_gran", _sint_explosio_gran)


def _sint_impacte() -> list:
    return _onada(_saw(900, (100 - 900) / 0.090), 90, 0.7)


def impacte() -> None:
    """La nau rep mal: escombrat dur 900 -> 100 Hz en 90 ms."""
    _toca_precarregat("impacte", _sint_impacte)


def _sint_kit() -> list:
    seq = _onada(_sine(523.25), 70, 0.5)
    seq += _onada(_sine(659.25), 110, 0.5)
    return seq


def kit() -> None:
    """Kit de reparacio recollit: arpegi ascendent de dues notes (do-mi)."""
    _toca_precarregat("kit", _sint_kit)


def _sint_dron_aliat() -> list:
    seq = _onada(_sine(523.25), 60, 0.5)
    seq += _onada(_sine(659.25), 60, 0.5)
    seq += _onada(_sine(783.99), 120, 0.55)
    return seq


def dron_aliat() -> None:
    """Dron aliat unit a l'esquadra: arpegi de tres notes (do-mi-sol)."""
    _toca_precarregat("dron_aliat", _sint_dron_aliat)


def _sint_missil() -> list:
    return _onada(_sine(180, (950 - 180) / 0.160), 160, 0.5)


def missil() -> None:
    """Missil guiat: escombrat ascendent 180 -> 950 Hz (xiulet)."""
    _toca_precarregat("missil", _sint_missil)


def _sint_boss() -> list:
    def gen(t):
        base = _square(62.5)(t)
        trem = 0.6 + 0.4 * math.sin(2 * math.pi * 5 * t)
        return base * trem
    return _onada(gen, 700, 0.7)


def boss() -> None:
    """El cap apareix: dron greu amb tremolo modulat."""
    _toca_precarregat("boss", _sint_boss)


def _sint_pausa() -> list:
    return _onada(_sine(880), 45, 0.4)


def pausa() -> None:
    """Pausa activada: blip curt i net."""
    _toca_precarregat("pausa", _sint_pausa)


def _sint_victoria() -> list:
    seq = _onada(_square(523.25), 90, 0.45)
    seq += _onada(_square(659.25), 90, 0.45)
    seq += _onada(_square(783.99), 90, 0.45)
    seq += _onada(_square(1046.5), 200, 0.5)
    return seq


def victoria() -> None:
    """Nivell superat: fanfaria ascendent (do-mi-sol-do')."""
    _toca_precarregat("victoria", _sint_victoria)


def _sint_gameover() -> list:
    seq = _onada(_saw(520, (60 - 520) / 0.600), 600, 0.6)
    seq += _onada(_sine(260, (50 - 260) / 0.450), 450, 0.45)
    return seq


def gameover() -> None:
    """Fi de partida: escombrat descendent llarg i trist."""
    _toca_precarregat("gameover", _sint_gameover)