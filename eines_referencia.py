# -*- coding: utf-8 -*-
"""Harnes temporal: campanya demo headless a 80x20 (canonic). S'esborra."""
import contextlib
import io
import random
import sys

import main

main.SCREEN_WIDTH, main.SCREEN_HEIGHT = 80, 20
main.DEMO_MODE = True
main.DEMO_RENDER_EVERY = 0            # zero frames: maxim rapidesa
inici = int(sys.argv[1]) - 1 if len(sys.argv) > 1 else 0
random.seed(main.DEMO_SEED)
buf = io.StringIO()
for idx in range(inici, len(main.MAPS)):
    main.CURRENT_MAP = idx
    with contextlib.redirect_stdout(buf):
        resultat, punts = main.run_round()
    print(f"{main.MAPS[idx]['name']}: {resultat} - {punts} pts")
    if resultat != "completed":
        break
