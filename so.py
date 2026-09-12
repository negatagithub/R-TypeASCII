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
import random
import struct

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


def _play(seqs) -> None:
    """Reprodueix una o mes seqüencies de mostres concatenades, en silenci
    si so o la plataforma no ho permeten (mai ha de petar el joc)."""
    if not actiu():
        return
    if not isinstance(seqs, list) or not seqs or isinstance(seqs[0], int):
        mostres = seqs
    else:
        mostres = [m for seq in seqs for m in seq]
    global _ultim
    try:
        _ultim = _wav(mostres)
        winsound.PlaySound(_ultim,
                           winsound.SND_MEMORY | winsound.SND_ASYNC
                           | winsound.SND_NODEFAULT)
    except (RuntimeError, OSError, ValueError, AttributeError):
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
# Efectes de so: cada un es una formula (o combinacio) que es reprodueix.    #
# --------------------------------------------------------------------------- #
def tret() -> None:
    """Tret del cano: escombrat quadrat 1600 -> 250 Hz en 70 ms (laser)."""
    _play(_onada(_square(1600, (250 - 1600) / 0.070), 70, 0.55))


def tret_enemic() -> None:
    """Tret enemic: serra baixa 320 -> 180 Hz, mes greu i curt."""
    _play(_onada(_saw(320, (180 - 320) / 0.050), 50, 0.40))


def explosio_petita() -> None:
    """Explosio petita (dron): esclat de soroll + escombrat descendent."""
    seq = _onada(_soroll(1400), 70, 0.6)
    seq += _onada(_square(360, (70 - 360) / 0.080), 80, 0.5)
    _play(seq)


def explosio_gran() -> None:
    """Explosio gran (caça/cap): soroll llarg + greu que s'enfonsa."""
    seq = _onada(_soroll(900, 3), 180, 0.75)
    seq += _onada(_saw(200, (30 - 200) / 0.300), 300, 0.55)
    seq += _onada(_sine(110, (25 - 110) / 0.350), 350, 0.4)
    _play(seq)


def impacte() -> None:
    """La nau rep mal: escombrat dur 900 -> 100 Hz en 90 ms."""
    _play(_onada(_saw(900, (100 - 900) / 0.090), 90, 0.7))


def kit() -> None:
    """Kit de reparacio recollit: arpegi ascendent de dues notes (do-mi)."""
    seq = _onada(_sine(523.25), 70, 0.5)
    seq += _onada(_sine(659.25), 110, 0.5)
    _play(seq)


def dron_aliat() -> None:
    """Dron aliat unit a l'esquadra: arpegi de tres notes (do-mi-sol)."""
    seq = _onada(_sine(523.25), 60, 0.5)
    seq += _onada(_sine(659.25), 60, 0.5)
    seq += _onada(_sine(783.99), 120, 0.55)
    _play(seq)


def missil() -> None:
    """Missil guiat: escombrat ascendent 180 -> 950 Hz (xiulet)."""
    _play(_onada(_sine(180, (950 - 180) / 0.160), 160, 0.5))


def boss() -> None:
    """El cap apareix: dron greu amb tremolo modulat."""
    def gen(t):
        base = _square(62.5)(t)
        trem = 0.6 + 0.4 * math.sin(2 * math.pi * 5 * t)
        return base * trem
    _play(_onada(gen, 700, 0.7))


def pausa() -> None:
    """Pausa activada: blip curt i net."""
    _play(_onada(_sine(880), 45, 0.4))


def victoria() -> None:
    """Nivell superat: fanfaria ascendent (do-mi-sol-do')."""
    seq = _onada(_square(523.25), 90, 0.45)
    seq += _onada(_square(659.25), 90, 0.45)
    seq += _onada(_square(783.99), 90, 0.45)
    seq += _onada(_square(1046.5), 200, 0.5)
    _play(seq)


def gameover() -> None:
    """Fi de partida: escombrat descendent llarg i trist."""
    seq = _onada(_saw(520, (60 - 520) / 0.600), 600, 0.6)
    seq += _onada(_sine(260, (50 - 260) / 0.450), 450, 0.45)
    _play(seq)