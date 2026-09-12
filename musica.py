# -*- coding: utf-8 -*-
"""Música procedural de R-Type ASCII (sense arxius): partitures i arranjaments.

Model de dades (inventat per a aquest mòdul, paral·lel als SFX de ``so.py``)::

    PARTITURA = {
        "nom": {
            "bpm": 132,          # tempo; la negra dura 60/bpm segons
            "lead":  [...],      # melodia principal (veu aguda)
            "bass":  [...],      # baix / ostinato (veu greu)
            "drums": [...],      # percussió (veu de soroll)
        },
    }

Cada veu és una llista de compassos; cada compàs és una llista de
``(figura, altura)`` on:

  * ``figura`` és la durada en negres (1 = negra, 0.5 = corxera,
    2 = blanca, 4 = rodona...).
  * ``altura`` és una nota MIDI (60 = Do central) o ``None`` (= silenci).
    Exemple: ``(0.5, 69)`` = corxera de La4; ``(1, None)`` = silenci de negra.

Només tres veus (``lead``/``bass``/``drums``); si una falta o és buida,
aquella veu calla. Les tres veus sonen SIMULTÀNIES i el bucle és POLIFÒNIC:
cada compàs mescla les tres veus en un sol buffer.

La percussió no fa servir notes MIDI: qualsevol ``altura`` no-None és un
cop (la seva alçada tria el timbre: greu = bombo, mig = caixa, agut = plat).

Conversió nota MIDI -> Hz: la fórmula temperada ``440 * 2**((m-69)/12)``.
Els bucles es generen un sol cop i es guarden a la memòria cau
(``_CACHE``): sonar 40 segons de nivell no resintetitza res.

12 peces (intro + 11 nivells), cada una amb el seu caràcter:
  intro = fanfàrria arcade; 1 = marxa heroica; 2 = fàbrica militant;
  3 = tensió del cap; 4 = misteri de cova; 5 = groove urbà;
  6 = synthwave neó; 7 = riff infernal; 8 = tempesta elèctrica;
  9 = vals glacial; 10 = pols solar; 11 = tambors de jungla.
"""
import math
import threading

import so

RATE = so.RATE

_CACHE = {}
_FIL_ACTUAL = None
_NOM_ACTUAL = None
_ATURA = threading.Event()


def _midi_a_hz(m):
    """Nota MIDI -> Hz (temperament igualat, La4 = 440)."""
    return 440.0 * (2.0 ** ((m - 69) / 12.0))


def _mostra_lead(freq, t, dur):
    a = math.sin(2 * math.pi * freq * t)
    b = math.sin(2 * math.pi * freq * 2 * t) * 0.3
    c = (1.0 if a >= 0 else -1.0) * 0.15
    env = min(1.0, t / 0.01, max(0.0, (dur - t) / (dur * 0.3 + 0.01)))
    return (a + b + c) * 0.55 * env


def _mostra_bass(freq, t, dur):
    a = math.sin(2 * math.pi * freq * t)
    b = math.sin(2 * math.pi * freq * 0.5 * t) * 0.4
    env = min(1.0, t / 0.015, max(0.0, (dur - t) / (dur * 0.25 + 0.01)))
    return (a + b) * 0.6 * env


def _mostra_drum(tipus, t, dur):
    if tipus == 0:
        f = 120 - 70 * (t / max(dur, 0.001))
        return math.sin(2 * math.pi * f * t) * max(0.0, 1 - t / dur)
    if tipus == 1:
        v = math.sin(2 * math.pi * 180 * t) * 0.5
        v += math.sin(2 * math.pi * 1137 * t + 1.3) * 0.3
        v += math.sin(2 * math.pi * 2711 * t + 2.1) * 0.2
        return v * max(0.0, 1 - t / dur)
    v = math.sin(2 * math.pi * 5200 * t) * 0.4
    v += math.sin(2 * math.pi * 7900 * t + 0.7) * 0.3
    return v * max(0.0, 1 - t / dur) * 0.7


def _veu_a_esdeveniments(veu, negra):
    evs = []
    t = 0.0
    for compas in veu:
        for figura, altura in compas:
            dur = figura * negra
            if altura is not None:
                evs.append((t, dur, altura))
            t += dur
    return evs, t


def sintetitzar(peca):
    """Genera el bucle d'una peça (mostres int16). Amb memoria cau."""
    if peca["nom"] in _CACHE:
        return _CACHE[peca["nom"]]
    negra = 60.0 / peca["bpm"]
    ev_lead, dur_l = _veu_a_esdeveniments(peca.get("lead", []), negra)
    ev_bass, dur_b = _veu_a_esdeveniments(peca.get("bass", []), negra)
    ev_drum, dur_d = _veu_a_esdeveniments(peca.get("drums", []), negra)
    total = max(dur_l, dur_b, dur_d, negra)
    n = max(1, int(RATE * total))
    mescla = [0.0] * n
    for t0, dur, nota in ev_lead:
        f = _midi_a_hz(nota)
        i0 = int(t0 * RATE)
        i1 = min(n, i0 + int(dur * RATE))
        for i in range(i0, i1):
            mescla[i] += _mostra_lead(f, (i - i0) / RATE, dur) * 0.5
    for t0, dur, nota in ev_bass:
        f = _midi_a_hz(nota)
        i0 = int(t0 * RATE)
        i1 = min(n, i0 + int(dur * RATE))
        for i in range(i0, i1):
            mescla[i] += _mostra_bass(f, (i - i0) / RATE, dur) * 0.55
    for t0, dur, nota in ev_drum:
        tipus = 0 if nota < 50 else (1 if nota < 70 else 2)
        vol = 0.5 if tipus == 2 else 0.65
        i0 = int(t0 * RATE)
        i1 = min(n, i0 + int(dur * RATE))
        for i in range(i0, i1):
            mescla[i] += _mostra_drum(tipus, (i - i0) / RATE, dur) * vol
    pic = max(0.001, max(abs(v) for v in mescla))
    out = [int(max(-1.0, min(1.0, v / pic * 0.85)) * 20000) for v in mescla]
    _CACHE[peca["nom"]] = out
    return out


def seq(cadena):
    """Notacio compacta: '72:0.5 74:0.5 R:1' -> [(0.5,72),(0.5,74),(1,None)]."""
    out = []
    for tok in cadena.split():
        alt, fig = tok.split(":")
        out.append((float(fig), None if alt == "R" else int(alt)))
    return out


def _bucle_en_fil(buf, marca):
    import winsound
    while not marca.is_set():
        try:
            winsound.PlaySound(bytes(buf), winsound.SND_MEMORY
                               | winsound.SND_NODEFAULT)
        except (RuntimeError, OSError, ValueError, AttributeError):
            return


def sona(nom):
    """Engega el bucle de la peca `nom` (atura l'anterior). No bloqueja."""
    global _FIL_ACTUAL, _NOM_ACTUAL
    atura()
    _NOM_ACTUAL = None
    if not so.actiu() or nom not in PARTITURA:
        return
    try:
        buf = so._wav(sintetitzar(PARTITURA[nom]))
        marca = threading.Event()
        fil = threading.Thread(target=_bucle_en_fil, args=(buf, marca),
                               daemon=True)
        _FIL_ACTUAL = (fil, marca)
        _NOM_ACTUAL = nom
        fil.start()
    except (RuntimeError, OSError, ValueError, AttributeError):
        _FIL_ACTUAL = None
        _NOM_ACTUAL = None


def atura():
    """Atura la musica actual (el so en curs acaba, no en comenca cap de nou)."""
    global _FIL_ACTUAL, _NOM_ACTUAL
    if _FIL_ACTUAL is not None:
        fil, marca = _FIL_ACTUAL
        marca.set()
        _FIL_ACTUAL = None
    _NOM_ACTUAL = None


def actual():
    """Nom de la peca sonant ara mateix (o None)."""
    return _NOM_ACTUAL


# ---------------------------------------------------------------------------
# PARTITURES (12 peces: intro + 11 nivells). Cada compas = 4 negres.
# ---------------------------------------------------------------------------
PARTITURA = {
    "intro": {
        "nom": "intro", "bpm": 112,
        "lead": [seq("72:1 76:1 79:1 84:1"), seq("79:1 76:1 72:2"),
                 seq("74:1 77:1 81:1 86:1"), seq("81:2 79:2")],
        "bass": [seq("48:1 48:1 55:1 55:1"), seq("53:1 53:1 55:2"),
                 seq("50:1 50:1 57:1 57:1"), seq("53:2 55:2")],
        "drums": [seq("40:1 60:1 40:1 60:1"), seq("40:1 60:1 80:2")],
    },
    "nivell_1": {
        "nom": "nivell_1", "bpm": 132,
        "lead": [seq("72:0.5 74:0.5 76:1 79:1 76:1"),
                 seq("81:0.5 79:0.5 76:1 74:1 72:1"),
                 seq("72:0.5 74:0.5 76:1 79:1 81:1"),
                 seq("79:2 76:2")],
        "bass": [seq("48:1 48:1 48:1 48:1"), seq("53:1 53:1 53:1 53:1"),
                 seq("45:1 45:1 45:1 45:1"), seq("43:2 43:2")],
        "drums": [seq("40:1 60:1 40:1 60:1"), seq("40:1 40:1 60:2")],
    },
    "nivell_2": {
        "nom": "nivell_2", "bpm": 140,
        "lead": [seq("69:0.5 69:0.5 72:0.5 69:0.5 67:1 65:1"),
                 seq("69:0.5 69:0.5 72:0.5 74:0.5 76:2"),
                 seq("77:0.5 76:0.5 74:0.5 72:0.5 74:1 69:1"),
                 seq("67:2 65:2")],
        "bass": [seq("45:0.5 45:0.5 45:0.5 45:0.5 45:0.5 45:0.5 45:1"),
                 seq("41:0.5 41:0.5 41:0.5 41:0.5 41:0.5 41:0.5 41:1"),
                 seq("43:0.5 43:0.5 43:0.5 43:0.5 43:0.5 43:0.5 43:1"),
                 seq("45:2 44:2")],
        "drums": [seq("40:0.5 60:0.5 40:0.5 60:0.5 40:0.5 60:0.5 80:1"),
                  seq("40:0.5 60:0.5 40:0.5 60:0.5 40:1 60:1")],
    },
    "nivell_3": {
        "nom": "nivell_3", "bpm": 100,
        "lead": [seq("62:2 63:2"), seq("62:1 R:1 58:2"),
                 seq("62:2 63:2"), seq("65:3 R:1")],
        "bass": [seq("38:2 38:2"), seq("38:2 41:2"),
                 seq("36:2 36:2"), seq("41:2 43:2")],
        "drums": [seq("40:2 40:2"), seq("60:1 60:1 80:2")],
    },
    "nivell_4": {
        "nom": "nivell_4", "bpm": 96,
        "lead": [seq("76:2 79:1 81:1"), seq("79:2 76:1 74:1"),
                 seq("76:2 72:1 74:1"), seq("72:4")],
        "bass": [seq("45:2 41:2"), seq("43:2 40:2"),
                 seq("45:2 41:2"), seq("43:4")],
        "drums": [seq("60:2 80:2"), seq("R:4")],
    },
    "nivell_5": {
        "nom": "nivell_5", "bpm": 104,
        "lead": [seq("72:0.5 75:0.5 79:0.5 75:0.5 72:1 70:1"),
                 seq("72:0.5 75:0.5 79:0.5 82:0.5 81:1 79:1"),
                 seq("77:0.5 81:0.5 79:0.5 77:0.5 75:1 74:1"),
                 seq("75:2 72:2")],
        "bass": [seq("48:1 R:0.5 48:0.5 55:1 55:1"),
                 seq("46:1 R:0.5 46:0.5 53:1 53:1"),
                 seq("45:1 R:0.5 45:0.5 52:1 52:1"),
                 seq("43:2 43:2")],
        "drums": [seq("40:1 60:0.5 60:0.5 40:1 80:1"),
                  seq("40:1 60:0.5 60:0.5 40:1 60:1")],
    },
    "nivell_6": {
        "nom": "nivell_6", "bpm": 118,
        "lead": [seq("81:0.5 79:0.5 76:0.5 79:0.5 84:2"),
                 seq("79:0.5 76:0.5 74:0.5 76:0.5 79:2"),
                 seq("81:0.5 84:0.5 86:0.5 84:0.5 81:1 79:1"),
                 seq("76:4")],
        "bass": [seq("45:1 45:1 45:1 45:1"), seq("41:1 41:1 41:1 41:1"),
                 seq("43:1 43:1 43:1 43:1"), seq("43:1 43:1 41:2")],
        "drums": [seq("40:1 60:1 80:1 60:1"), seq("40:1 60:1 80:1 80:1")],
    },
    "nivell_7": {
        "nom": "nivell_7", "bpm": 150,
        "lead": [seq("64:0.5 64:0.5 65:0.5 64:0.5 62:1 64:1"),
                 seq("62:0.5 62:0.5 63:0.5 62:0.5 60:2"),
                 seq("64:0.5 64:0.5 65:0.5 67:0.5 69:1 67:1"),
                 seq("65:2 63:2")],
        "bass": [seq("40:1 40:1 40:1 40:1"), seq("40:1 40:1 38:1 38:1"),
                 seq("40:1 40:1 40:1 40:1"), seq("43:1 42:1 41:1 40:1")],
        "drums": [seq("40:1 40:1 60:1 40:1"), seq("40:1 40:1 60:1 60:1")],
    },
    "nivell_8": {
        "nom": "nivell_8", "bpm": 138,
        "lead": [seq("74:0.5 R:0.5 77:0.5 R:0.5 81:1 79:1"),
                 seq("77:0.5 R:0.5 74:0.5 R:0.5 72:2"),
                 seq("74:0.5 R:0.5 77:0.5 R:0.5 81:1 84:1"),
                 seq("86:2 84:2")],
        "bass": [seq("50:2 48:2"), seq("45:2 43:2"),
                 seq("50:2 48:2"), seq("45:2 47:2")],
        "drums": [seq("40:0.5 40:0.5 60:1 80:0.5 80:0.5 80:1"),
                  seq("40:0.5 40:0.5 60:1 60:1 80:1")],
    },
    "nivell_9": {
        "nom": "nivell_9", "bpm": 90,
        "lead": [seq("84:1 81:1 79:1 76:1"), seq("81:1 79:1 76:1 74:1"),
                 seq("79:1 76:1 74:1 72:1"), seq("76:1 74:1 72:2")],
        "bass": [seq("48:1 45:1 43:1 41:1"), seq("41:1 38:1 36:1 34:1"),
                 seq("38:1 36:1 34:1 31:1"), seq("36:1 34:1 31:2")],
        "drums": [seq("80:1 R:1 60:1 R:1"), seq("80:1 R:1 80:1 R:1")],
    },
    "nivell_10": {
        "nom": "nivell_10", "bpm": 128,
        "lead": [seq("76:0.5 79:0.5 81:0.5 79:0.5 76:0.5 79:0.5 84:1"),
                 seq("81:0.5 79:0.5 76:0.5 79:0.5 74:2"),
                 seq("76:0.5 79:0.5 81:0.5 84:0.5 86:1 84:1"),
                 seq("81:2 79:2")],
        "bass": [seq("43:1 43:1 43:1 43:1"), seq("41:1 41:1 41:1 41:1"),
                 seq("40:1 40:1 40:1 40:1"), seq("41:2 43:2")],
        "drums": [seq("40:1 60:1 40:1 60:1"), seq("40:1 60:1 80:1 80:1")],
    },
    "nivell_11": {
        "nom": "nivell_11", "bpm": 120,
        "lead": [seq("72:1 74:1 76:1 74:1"), seq("76:1 79:1 76:1 74:1"),
                 seq("72:1 74:1 76:1 79:1"), seq("81:2 79:2")],
        "bass": [seq("43:1 43:1 45:1 45:1"), seq("41:1 41:1 43:1 43:1"),
                 seq("40:1 40:1 41:1 41:1"), seq("43:2 43:2")],
        "drums": [seq("40:0.5 40:0.5 60:1 40:0.5 40:0.5 60:1"),
                  seq("40:0.5 40:0.5 60:1 80:1 60:1")],
    },
}

