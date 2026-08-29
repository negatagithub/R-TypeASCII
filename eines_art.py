# -*- coding: utf-8 -*-
"""Eina d'autoria del terreny dibuixat: valida i previsualitza un nivell.

Us:
    python eines_art.py                # tots els nivells amb art
    python eines_art.py 4              # nomes el nivell 4
    python eines_art.py 4 5            # varis nivells

Per cada nivell dibuixat (format nou 'art'/'fons', vegeu nivell_4.py):
  1. La validacio completa (mides, paleta, corredors >= MIN_CORRIDOR i cami
     BFS de banda a banda) ja corre en carregar main: si el dibuix es ilegal,
     aquest import falla amb el missatge exacte de l'error.
  2. Comprova que cap spawn neixi sobre cel·les solidas de la seva columna.
  3. Informa del corredor lliure minim del dibuix.
  4. Previsualitza el PRIMER PLA i el FONS amb colors ANSI, sense haver de
     jugar la partida (cada cel·la es pinta amb el seu caracter i color).
"""
import sys

import main


def _max_free_run(column) -> int:
    """Mida del tram lliure mes llarg d'una columna canonica."""
    best = run = 0
    for cell in column:
        run = run + 1 if cell is None else 0
        if run > best:
            best = run
    return best


def check_spawns(mapa) -> int:
    """Spawn sobre roca en nivells d'art: retorna el nombre d'errors."""
    errors = 0
    for tick, kind, start_y, _patro in mapa["spawns"]:
        if tick >= len(mapa["art_columns"]):
            print(f"  !! spawn al tick {tick}: fora del dibuix")
            errors += 1
            continue
        column = mapa["art_columns"][tick]
        sprite = main.ENEMY_TYPES[kind]["sprite"]
        y0 = min(main.ART_CANON_H - 1,
                 max(0, int(round(start_y * main.ART_CANON_H))))
        y1 = min(main.ART_CANON_H - 1, y0 + len(sprite) - 1)
        blocked = [y for y in range(y0, y1 + 1) if column[y] is not None]
        if blocked:
            print(f"  !! spawn al tick {tick} (tipus {kind}): files "
                  f"{blocked} sobre roca")
            errors += 1
    return errors


def preview(columns, titol: str) -> None:
    """Pinta el dibuix fila a fila amb els colors de la seva paleta."""
    print(titol)
    for y in range(main.ART_CANON_H):
        print("  " + "".join(
            " " if column[y] is None
            else main.paint(column[y][0], column[y][1])
            for column in columns))


def main_eina() -> int:
    nums = {int(a) for a in sys.argv[1:] if a.isdigit()}
    vists = 0
    for idx, mapa in enumerate(main.MAPS, start=1):
        if nums and idx not in nums:
            continue
        if mapa.get("art_columns") is None:
            if nums:
                print(f"NIVELL {idx} - {mapa['name']}: format d'elevacions "
                      f"(antic), sense art que previsualitzar.")
            continue
        vists += 1
        fons = len(mapa["fons_columns"]) if mapa["fons_columns"] else 0
        minim = min(_max_free_run(c) for c in mapa["art_columns"])
        print(mapa["name"])
        print(f"  art: {len(mapa['art_columns'])} columnes x "
              f"{main.ART_CANON_H} files | fons: {fons} columnes (bucle) | "
              f"durada: {mapa['duration']} ticks | spawns: "
              f"{len(mapa['spawns'])}")
        print(f"  corredor lliure minim: {minim} celes "
              f"(exigit: {main.MIN_CORRIDOR})")
        errors = check_spawns(mapa)
        print(f"  spawns: " + ("OK" if errors == 0 else f"{errors} errors"))
        preview(mapa["art_columns"], "  --- PRIMER PLA (solid) ---")
        if mapa["fons_columns"]:
            preview(mapa["fons_columns"],
                    "  --- FONS (parallax, decoratiu) ---")
        print()
    if not vists and not nums:
        print("Cap nivell amb art (els nivells 1-3 fan servir el format "
              "antic d'elevacions).")
    return 0


if __name__ == "__main__":
    sys.exit(main_eina())
