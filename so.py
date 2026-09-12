# -*- coding: utf-8 -*-
"""Mesclador d'àudio EN TEMPS REAL per a R-Type ASCII (sense arxius de so).

Genera les ones amb FORMULES MATEMÀTIQUES (sinus, onada quadrada, soroll
determinista, escombrats de freqüència i envolvents d'atac/alliberament) i les
reprodueix amb l'API **waveOut** de Windows (`winmm.dll`, via `ctypes`: tot
stdlib, zero paquets externs). Cada efecte es descriu com una funció `freq(t)`
variada per paràmetres; la síntesi mostreja la fórmula UN COP (precàrrega) i
el mesclador la summa al stream en temps real.

Per què no `winsound`? És UN sol canal i no admet so asíncron des de memòria
(`SND_MEMORY + SND_ASYNC` llença RuntimeError): cada so nou tallava l'anterior
i els SFX quedaven desfasats darrere la música. `waveOut` ens dona un stream
continu que un fil mesclador omple de trossos de ~20 ms SUMANT totes les veus:

  * POLIFONIA: trets, explosions i música sonen SIMULTÀNIS (veus independents).
  * TEMPS REAL: un efecte nou entra al tros següent -> se sent en ~20-40 ms.
  * ZERO BLOQUEIG: disparar un efecte només registra una veu (microsegons).

Es desactiva tot sol:
  - si winmm no està disponible (plataforma no Windows),
  - si la variable d'entorn R_TYPE_SO és "0",
  - si els tests o el mode demo criden so.set_enabled(False).

Reproduir mai ha de fer petar el joc: qualsevol error d'àudio es menja en
silenci; sense dispositiu, tot sona com un no-op segur.
"""
import atexit    # tancament net del dispositiu waveOut en sortir
import math
import os
import random
import struct    # només pel _wav llegat; el mesclador empaqueta amb array
import threading
import time      # son del fil mesclador entre trossos

from array import array   # empaquetat PCM rapid (16 bits little-endian)

try:              # API waveOut (winmm.dll): stream d'audio en temps real
    from ctypes import (WinDLL, Structure, byref, c_char_p, c_uint16,
                        c_uint32, c_void_p, cast, sizeof, POINTER)
    _winmm = WinDLL("winmm")
except (OSError, ImportError):            # no Windows / entorn sense so
    _winmm = None

SND_ON = os.environ.get("R_TYPE_SO", "1") != "0"

RATE = 22050                              # mostres per segon
_AMPLITUD = 20000                         # Pic del PCM de 16 bits
_DISPONIBLE = _winmm is not None


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
# Motor EN TEMPS REAL: mesclador polifonic sobre waveOut (winmm via ctypes)   #
# --------------------------------------------------------------------------- #
# Un sol stream d'audio continu: el fil mesclador omple el driver de trossos
# de _CHUNK mostres (~20 ms) barrejant TOTES les veus actives (SFX + musica).
# tret()/musica.sona() nomes REGISTREN una veu (microsegons, mai bloquegen):
# la veu entra al tros seguent i se sent en ~20-40 ms. Cap so talla cap
# altre: es sumen. Sense dispositiu, tot sona com un no-op segur.
_CHUNK = RATE // 50          # 441 mostres = 20 ms (resolucio temporal)
_PROFUNDITAT = 2             # trossos encuats al driver (latencia ~20-40 ms)
_MAX_VEUS = 16               # mes veus no ajuda: totes retallarien de soroll

_PRECARREGAT = {}            # nom -> mostres ja sintetitzades (pre-render)
_VEUS = []                   # veus actives: {buf, pos, vol, loop, tag, acabada}
_LOCK = threading.Lock()     # protegeix _VEUS (fil del joc <-> mesclador)
_PENDENTS = []               # [(WAVEHDR, bytes)] en vol dins el driver
_DISPOSITIU = None           # handle HWAVEOUT (None = encara sense stream)
_FIL_MESCLA = None           # fil mesclador (daemon)


class _WAVEFORMATEX(Structure):
    """WAVEFORMATEX: PCM 22050 Hz, mono, 16 bits."""
    _fields_ = [("wFormatTag", c_uint16), ("nChannels", c_uint16),
                ("nSamplesPerSec", c_uint32), ("nAvgBytesPerSec", c_uint32),
                ("nBlockAlign", c_uint16), ("wBitsPerSample", c_uint16),
                ("cbSize", c_uint16)]


class _WAVEHDR(Structure):
    """WAVEHDR: capcalera d'un tros de PCM en vol dins el driver."""
    _fields_ = [("lpData", c_void_p), ("dwBufferLength", c_uint32),
                ("dwBytesRecorded", c_uint32), ("dwUser", c_void_p),
                ("dwFlags", c_uint32), ("dwLoops", c_uint32),
                ("lpNext", c_void_p), ("reserved", c_void_p)]


if _winmm is not None:      # firmes exactes (segur a 32 i 64 bits)
    for _fn, _args in (
        ("waveOutOpen", (POINTER(c_void_p), c_uint32, POINTER(_WAVEFORMATEX),
                         c_void_p, c_void_p, c_uint32)),
        ("waveOutPrepareHeader", (c_void_p, POINTER(_WAVEHDR), c_uint32)),
        ("waveOutUnprepareHeader", (c_void_p, POINTER(_WAVEHDR), c_uint32)),
        ("waveOutWrite", (c_void_p, POINTER(_WAVEHDR), c_uint32)),
        ("waveOutReset", (c_void_p,)),
        ("waveOutClose", (c_void_p,)),
    ):
        getattr(_winmm, _fn).argtypes = _args
        getattr(_winmm, _fn).restype = c_uint32

_WHDR_DONE = 0x00000001     # el driver ja ha tocat el tros


def _obre_dispositiu():
    """Obre el stream (22050 Hz mono 16 bits) i engega el fil mesclador."""
    global _DISPOSITIU, _FIL_MESCLA
    if _DISPOSITIU is not None or _winmm is None:
        return _DISPOSITIU
    wfx = _WAVEFORMATEX(1, 1, RATE, RATE * 2, 2, 16, 0)
    h = c_void_p()
    try:
        # WAVE_MAPPER = 0xFFFFFFFF, CALLBACK_NULL = 0 (sondeig de WHDR_DONE)
        err = _winmm.waveOutOpen(byref(h), 0xFFFFFFFF, byref(wfx),
                                 None, None, 0)
    except (OSError, ValueError, AttributeError):
        return None
    if err != 0:
        return None
    _DISPOSITIU = h
    try:
        _FIL_MESCLA = threading.Thread(target=_fil_mesclador, daemon=True)
        _FIL_MESCLA.start()
    except (RuntimeError, OSError, ValueError, AttributeError):
        pass
    return _DISPOSITIU


def _tanca_dispositiu() -> None:
    """Reset + Close del stream en sortir del proces (via atexit)."""
    global _DISPOSITIU
    if _DISPOSITIU is None or _winmm is None:
        return
    try:
        _winmm.waveOutReset(_DISPOSITIU)
        _winmm.waveOutClose(_DISPOSITIU)
    except (OSError, ValueError, AttributeError):
        pass
    _DISPOSITIU = None


atexit.register(_tanca_dispositiu)


def _afegeix_veu(buf, vol=1.0, loop=False, tag="sfx") -> bool:
    """Registra una veu al mesclador: NO bloqueja (microsegons).

    Retorna True si sonara. Si ja hi ha _MAX_VEUS, cau la SFX mes antiga
    (la musica, persistent, es protegeix). Sense dispositiu, no-op segur.
    """
    if not actiu() or not buf:
        return False
    with _LOCK:
        if len(_VEUS) >= _MAX_VEUS:
            for i in range(len(_VEUS)):
                if _VEUS[i]["tag"] != "musica":
                    del _VEUS[i]
                    break
            else:
                del _VEUS[0]
        _VEUS.append({"buf": buf, "pos": 0, "vol": float(vol),
                      "loop": bool(loop), "tag": tag, "acabada": False})
    if _DISPOSITIU is None:
        _obre_dispositiu()
    return True


def _mata_veus(tag: str) -> None:
    """Treu totes les veus amb aquell tag (p. ex. canviar de musica)."""
    with _LOCK:
        _VEUS[:] = [v for v in _VEUS if v["tag"] != tag]


def _barreja_tros() -> list:
    """Mescla _CHUNK mostres de TOTES les veus actives (pur, sense I/O).

    Avanca el cursor de cada veu, aplica loop, retira les acabades i retalla
    el pic global: si la suma desborda, es baixa el volum de tot el tros
    (mai clip dur). El fil del joc pot registrar veus mentre aixo corre.
    """
    out = [0] * _CHUNK
    with _LOCK:
        veus = list(_VEUS)
    for v in veus:
        buf, n_buf = v["buf"], len(v["buf"])
        pos, vol = v["pos"], v["vol"]
        i = 0
        while i < _CHUNK:
            n = min(_CHUNK - i, n_buf - pos)
            if n <= 0:
                break
            if vol == 1.0:                    # cas comu: suma d'enters
                for j, s in enumerate(buf[pos:pos + n]):
                    out[i + j] += s
            else:
                for j, s in enumerate(buf[pos:pos + n]):
                    out[i + j] += s * vol
            pos += n
            i += n
            if pos >= n_buf:
                if v["loop"]:
                    pos = 0
                else:
                    break
        v["pos"] = pos
        v["acabada"] = pos >= n_buf and not v["loop"]
    with _LOCK:
        _VEUS[:] = [v for v in _VEUS if not v["acabada"]]
    pic = max(max(out), -min(out))
    if pic > 31000:                           # retall global, mai clip dur
        f = 31000.0 / pic
        return [int(s * f) for s in out]
    return [int(s) for s in out]


def _pendents_vius() -> int:
    """Reintegra els trossos que el driver ja ha tocat; retorna quants queden.

    Només el fil mesclador toca _PENDENTS (sense lock). Amb CALLBACK_NULL
    no hi ha callback: sondegem la bandera WHDR_DONE de cada capcalera.
    """
    if _DISPOSITIU is None:
        return 0
    vius = 0
    for hdr, dada in list(_PENDENTS):
        if hdr.dwFlags & _WHDR_DONE:
            _winmm.waveOutUnprepareHeader(_DISPOSITIU, byref(hdr),
                                          sizeof(_WAVEHDR))
            try:
                _PENDENTS.remove((hdr, dada))
            except ValueError:
                pass
        else:
            vius += 1
    return vius


def _escriu(tros: list) -> None:
    """Empaqueta un tros a PCM 16 bits i l'encua al driver."""
    dades = array("h", tros).tobytes()
    hdr = _WAVEHDR()
    hdr.lpData = cast(c_char_p(dades), c_void_p)
    hdr.dwBufferLength = len(dades)
    if _winmm.waveOutPrepareHeader(_DISPOSITIU, byref(hdr),
                                   sizeof(_WAVEHDR)) != 0:
        return
    if _winmm.waveOutWrite(_DISPOSITIU, byref(hdr), sizeof(_WAVEHDR)) != 0:
        _winmm.waveOutUnprepareHeader(_DISPOSITIU, byref(hdr),
                                      sizeof(_WAVEHDR))
        return
    _PENDENTS.append((hdr, dades))   # refs vives mentre sona dins el driver


def _fil_mesclador() -> None:
    """Fil de sortida: manté _PROFUNDITAT trossos al driver (temps real).

    Un efecte registrat entre mig entra al tros següent: latència màxima
    ~_PROFUNDITAT * _CHUNK (~40 ms), imperceptible davant del tick del joc.
    """
    while _DISPOSITIU is not None:
        vius = _pendents_vius()
        while _DISPOSITIU is not None and _pendents_vius() < _PROFUNDITAT:
            _escriu(_barreja_tros())
        # Amb veus actives anem fins (tros nou cada ~20 ms); en silenci total
        # respirem mes (el driver ja té trossos de zero en cua).
        time.sleep(0.004 if (_VEUS or vius) else 0.02)


def precarga() -> None:
    """Pre-sintetitza els SFX (CPU pura, cap soroll) i escalfa el stream.

    Cridar-ho en arrencar el joc, abans del primer frame: el primer tret ja
    no paga síntesi i waveOutOpen (que pot tardar uns ms) ja ha corregut.
    Renderitzar no sona: es pot cridar amb el so desactivat per provar-ho.
    """
    for nom, fn in (("tret", _sint_tret), ("tret_enemic", _sint_tret_enemic),
                    ("explosio_petita", _sint_explosio_petita),
                    ("explosio_gran", _sint_explosio_gran),
                    ("impacte", _sint_impacte), ("kit", _sint_kit),
                    ("dron_aliat", _sint_dron_aliat), ("missil", _sint_missil),
                    ("boss", _sint_boss), ("pausa", _sint_pausa),
                    ("victoria", _sint_victoria),
                    ("gameover", _sint_gameover)):
        try:
            _PRECARREGAT.setdefault(nom, fn())
        except (RuntimeError, OSError, ValueError, AttributeError,
                struct.error, MemoryError):
            pass
    if actiu():
        _obre_dispositiu()          # pre-escalfament del dispositiu


def _play(seqs) -> None:
    """(Compatibilitat) Registra mostres ja sintetitzades com una veu."""
    if not actiu() or not seqs:
        return
    if isinstance(seqs, list) and not isinstance(seqs[0], int):
        mostres = [m for seq in seqs for m in seq]
    else:
        mostres = seqs
    _afegeix_veu(mostres, tag="sfx")


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
    """Reprodueix un SFX: agafa el pre-render i registra la veu.

    Zero síntesi al camí crític quan precarga() ja ha corregut: registrar
    una veu costa microsegons i sona al tros següent del mesclador.
    """
    dades = _PRECARREGAT.get(nom)
    if not dades:
        try:
            dades = _PRECARREGAT.setdefault(nom, sint_fn())
        except (RuntimeError, OSError, ValueError, AttributeError):
            return
    _afegeix_veu(dades, tag="sfx")


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