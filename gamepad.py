"""Suport de gamepad via XInput (Windows).

Aquest modul exposa tres elements:

- ``GAMEPAD_AVAILABLE``: boolea; True si s'ha pogut carregar XInput.
- ``detect_first()`` -> id (0..3) del primer gamepad connectat, o ``None``.
- ``read_actions(gamepad_id)`` -> conjunt d'accions ``ACTION_*`` que el joc
  ja reconeix (definides a ``main``), amb la mateixa semàntica d'ESTAT per
  frame que ``pressed_keys()``: combinables i mantenibles.

Mapa de controls (valors per defecte, raonables):
  Stick esquerre  -> moviment nau (deadzone XInput)
  A               -> dispar          (ACTION_SHOOT)
  B               -> pausa           (ACTION_PAUSE)
  X               -> sortir menus    (ACTION_QUIT)
  Start           -> pausa           (ACTION_PAUSE)
  Back            -> repetir         (ACTION_REPLAY)
  LB / RB         -> (reserva futura)
  Gat L / R       -> (reserva futura)

Sense gamepad connectat, read_actions() retorna un conjunt buit i el joc
seguir funciona només amb teclat.
"""

import ctypes
import ctypes.wintypes as w

# Importem les constants simbòliques d'Accions de main.py. Com a fallback
# (tests independents), es tornen a definir localment.
try:
    from main import (
        ACTION_UP, ACTION_DOWN, ACTION_BACK, ACTION_FORWARD,
        ACTION_SHOOT, ACTION_QUIT, ACTION_REPLAY, ACTION_PAUSE,
    )
except Exception:                                  # pragma: no cover - tests
    ACTION_UP, ACTION_DOWN = "up", "down"
    ACTION_BACK, ACTION_FORWARD = "back", "forward"
    ACTION_SHOOT, ACTION_QUIT = "shoot", "quit"
    ACTION_REPLAY, ACTION_PAUSE = "replay", "pause"


# ---------------------------------------------------------------------------
# Constants d'XInput (msdn: xinput-game-views)
# ---------------------------------------------------------------------------
_XINPUT_ERROR_SUCCESS = 0
_XINPUT_ERROR_NO_CONNECTED = 0x0487

# Mascara de botons (XINPUT_GAMEPAD_*)
_XINPUT_GAMEPAD_A = 0x0001
_XINPUT_GAMEPAD_B = 0x0002
_XINPUT_GAMEPAD_X = 0x0004
_XINPUT_GAMEPAD_Y = 0x0008
_XINPUT_GAMEPAD_LEFT_SHOULDER = 0x0010            # LB
_XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0020           # RB
_XINPUT_GAMEPAD_LEFT_THUMB = 0x0040
_XINPUT_GAMEPAD_RIGHT_THUMB = 0x0080
_XINPUT_GAMEPAD_BACK = 0x0100
_XINPUT_GAMEPAD_START = 0x0200

# Deadzone i llindars (valors recomanats per l'API XInput)
_XINPUT_LEFT_THUMB_DEADZONE = 7848    # ~0.24 de l'escala [-32768, 32767]
_XINPUT_TRIGGER_THRESHOLD = 140      # ~30 % de l'escala [0, 255]


# ---------------------------------------------------------------------------
# Definicions d'estructures compatibles amb la API nativa
# ---------------------------------------------------------------------------
class _XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", w.WORD),
        ("bLeftTrigger", w.BYTE),
        ("bRightTrigger", w.BYTE),
        ("bLeftThumbX", ctypes.c_short),
        ("bLeftThumbY", ctypes.c_short),
        ("bRightThumbX", ctypes.c_short),
        ("bRightThumbY", ctypes.c_short),
    ]


class _XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", w.DWORD),
        ("Gamepad", _XINPUT_GAMEPAD),
    ]


def _load_xinput():
    """Carrega XInputGetState via GetProcAddress.

    A Python 3.14, ``ctypes.WinDLL.__getitem__`` té un bug ('function not
    found' per nom), així que obtenim l'adreça amb GetProcAddress i la
    empaquetam amb CFUNCTYPE.
    Retorna la funció o None.
    """
    kernel = ctypes.windll.kernel32
    kernel.GetProcAddress.restype = ctypes.c_void_p
    kernel.GetProcAddress.argtypes = [w.HMODULE, w.LPCSTR]
    for libname in ("xinput1_4", "xinput1_3", "xinput9_1_6"):
        try:
            lib = ctypes.windll.LoadLibrary(libname)
        except OSError:
            continue
        handle = w.HMODULE(ctypes.cast(lib._handle, ctypes.c_void_p).value)
        addr = kernel.GetProcAddress(handle, w.LPCSTR(b"XInputGetState"))
        if not addr:
            continue
        prototype = ctypes.CFUNCTYPE(ctypes.c_uint, w.DWORD,
                                     ctypes.POINTER(_XINPUT_STATE))
        return prototype(addr)
    return None


_get_state = _load_xinput()
GAMEPAD_AVAILABLE = _get_state is not None


def detect_first():
    """Torna l'identificador (0..3) del primer gamepad connectat, o None.

    Consulta XInputGetState per cada slot fins a trobar-ne un de connectat.
    """
    if _get_state is None:
        return None
    for player in range(4):
        state = _XINPUT_STATE()
        res = _get_state(player, ctypes.byref(state))
        if res == _XINPUT_ERROR_SUCCESS:
            return player
        if res != _XINPUT_ERROR_NO_CONNECTED:
            break
    return None


def read_actions(gamepad_id):
    """Llegeix el gamepad ``gamepad_id`` i retorna un conjunt d'accions.

    Si la lectura falla (control desconnectat, etc.) retorna un conjunt buit.
    El stick esquerre mou la nau mantenint una direcció (deadzone d'XInput);
    el Y està invertit: valor positiu = amunt.
    """
    actions = set()
    if _get_state is None or gamepad_id is None:
        return actions
    state = _XINPUT_STATE()
    res = _get_state(gamepad_id, ctypes.byref(state))
    if res != _XINPUT_ERROR_SUCCESS:
        return actions

    g = state.Gamepad
    buttons = g.wButtons

    # Stick esquerre: Y invertit (valor positiu = amunt).
    threshold = _XINPUT_LEFT_THUMB_DEADZONE
    if g.bLeftThumbX < -threshold:
        actions.add(ACTION_BACK)
    elif g.bLeftThumbX > threshold:
        actions.add(ACTION_FORWARD)
    if g.bLeftThumbY < -threshold:
        actions.add(ACTION_DOWN)
    elif g.bLeftThumbY > threshold:
        actions.add(ACTION_UP)

    # Botons d'acció directa.
    if buttons & _XINPUT_GAMEPAD_A:
        actions.add(ACTION_SHOOT)
    if buttons & _XINPUT_GAMEPAD_B:
        actions.add(ACTION_PAUSE)
    if buttons & _XINPUT_GAMEPAD_X:
        actions.add(ACTION_QUIT)
    if buttons & _XINPUT_GAMEPAD_BACK:
        actions.add(ACTION_REPLAY)
    if buttons & _XINPUT_GAMEPAD_START:
        actions.add(ACTION_PAUSE)
    return actions


def pressed_actions(gamepad_id=None):
    """Aliat de read_actions: nom coherent amb l'API de teclat."""
    return read_actions(gamepad_id)