"""Simulacio headless del bloc de campanya de main(): cap terminal real.

Substitueix run_round/wait_key i les pantalles per stubs que registren
crides, i comprova el flux EXACTE: pas automatic entre nivells (cap tecla
ni pantalla intermedia), game over tolerant (qualsevol tecla repeteix, q
surt) i reinici de campanya amb 'r' a la pantalla final.
"""
import sys
import main

main.COLOR_ENABLED = False                     # sortida neta sense ANSI
events = []                                    # sequencia observada

main.fit_playfield_to_terminal = lambda: None
main.clear_screen = lambda: None
main.save_score = lambda s: False              # no tocis records.json
main.show_intro = lambda: events.append(
    "intro:%d" % (main.CURRENT_MAP + 1))


def show_game_over_stub(score, completed=False, record=False):
    events.append("pantalla:%s:%d"
                  % ("completat" if completed else "mort", score))


main.show_game_over = show_game_over_stub
main.show_campaign_complete = lambda s, record=False: events.append(
    "pantalla:campanya:%d" % s)

# 1-5 superats, mort al 6 (es repeteix), 6 superat (fi de campanya),
# 'r' la reinicia, mort al nivell 1 i 'q' surt.
resultats = [("completed", 100), ("completed", 200), ("completed", 300),
             ("completed", 400), ("completed", 500),
             ("dead", 40), ("completed", 600),
             ("completed", 650), ("dead", 10)]
tecles = ["x", "r", "q"]                       # x: repetir / r: reiniciar / q: sortir
stat = {"r": 0, "t": 0}


def run_round_stub():
    out, score = resultats[stat["r"]]
    stat["r"] += 1
    events.append("ronda:%d:%s" % (main.CURRENT_MAP + 1, out))
    return out, score


def wait_key_stub():
    tecla = tecles[stat["t"]]
    stat["t"] += 1
    events.append("tecla:%r" % tecla)
    return tecla


main.run_round = run_round_stub
main.wait_key = wait_key_stub

# --- Banner de fi de nivell: ha d'anunciar el nivell seguent -----------
main.CURRENT_MAP = 4                          # acabes el nivell 5 de 6
main.time.sleep = lambda s: None              # sense esperes reals
capturat = []
main.draw_frame = lambda text: capturat.append(text)
main.animate_completion(main.new_state())
assert "_____" in capturat[0]                 # l'art ASCII del banner
assert "Seguent: NIVELL 6 - NEON ESPACIAL" in capturat[0], capturat[0]
main.CURRENT_MAP = 0
print("BANNER OK: la fi de nivell anuncia el nom del nivell seguent.")

sys.argv = ["main.py"]                         # campanya normal, sense CLI
main.main()

esperat = [
    "intro:1",
    # Els cinc primers nivells s'encadenen SENSE cap tecla ni pantalla.
    "ronda:1:completed", "ronda:2:completed", "ronda:3:completed",
    "ronda:4:completed", "ronda:5:completed",
    # Mort al 6: pantalla de game over, qualsevol tecla ('x') repeteix.
    "ronda:6:dead", "pantalla:mort:40", "tecla:'x'",
    "ronda:6:completed",
    # Ultim nivell: pantalla final, 'r' reinicia la campanya des de l'1.
    "pantalla:campanya:600", "tecla:'r'", "intro:1",
    # Reiniciada la campanya, el nivell 1 es torna a completar i avança
    # automàticament al 2; allà la nau mor i 'q' surt del joc.
    "ronda:1:completed", "ronda:2:dead", "pantalla:mort:10", "tecla:'q'",
]
assert events == esperat, "flux inesperat:\n  " + "\n  ".join(events)
print("SIMULACIO OK: pas automatic entre nivells (cap tecla), game over")
print("tolerant i reinici de campanya amb 'r' es comporten com s'esperava.")
