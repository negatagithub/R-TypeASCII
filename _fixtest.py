"""Fix temporal: repara l'indentació del bloc de spawns a _test_terreny.py."""
import subprocess, sys

p = "_test_terreny.py"
s = open(p, encoding="utf-8").read()

old = (
    '                for tick, kind, start_y, _patro in mapa["spawns"]:\n'
    '            if tick >= len(cols):\n'
    "                continue          # fora de l'art: boss arena buida, sense roca\n"
    '            column = cols[tick]'
)
new = (
    '        for tick, kind, start_y, _patro in mapa["spawns"]:\n'
    '            if tick >= len(cols):\n'
    "                continue          # fora de l'art: arena buida, sense roca\n"
    '            column = cols[tick]'
)

assert old in s, "patro vell no trobat"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("FIX OK")
