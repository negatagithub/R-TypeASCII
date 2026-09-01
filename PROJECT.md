# R-Type ASCII — Documentació tècnica

Aquest és el document tècnic de referència del projecte: arquitectura del
motor, format dels fitxers de nivell, sistema de campanya, proves i registre
de canvis.

- Documentació **d'usuari**: [README.md](README.md)
- Resum de **disseny original** (històric, no reflecteix l'estat actual):
  [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## 1. Fitxers del projecte

| Fitxer | Contingut |
|---|---|
| `main.py` | El motor sencer (1.281 línies): render, entrada, entitats, col·lisions, campanya i CLI |
| `nivell_1.py` | Nivell 1 «PRIMER CONTACTE» (dades pures: `LEVEL`) |
| `nivell_2.py` | Nivell 2 «ESCULL DE FERRO» (dades pures: `LEVEL`) |
| `nivell_3.py` | Nivell 3 «EL CAP» (arena del cap, amb `BOSS_KIND`) |
| `nivell_4.py` | Nivell 4 «GALERIES D'AUTOR» (referència del format d'art) |
| `nivell_5.py` | Nivell 5 «BASTIÓ URBÀ» (final de campanya, art de ciutat) |
| `nivell_<n>.py` | Nous nivells; el carregador els descobreix i ordena pel número |
| `README.md` | Documentació d'usuari |
| `PROJECT.md` | Aquest document |
| `PROJECT_SUMMARY.md` | Resum de disseny original (històric) |
| `_test_terreny.py` | Suite de proves headless (22 blocs): `python _test_terreny.py` |
| `test_smoke.py` | Suite headless del motor (15 blocs): `python test_smoke.py` (codi d'exit 0/1) |

## 2. El motor (`main.py`)

### 2.1 Espai normalitzat
Tota posició i mida viu a l'interval [0..1] en X i en Y, independentment de
la mida del terminal:
- `cell_x()/cell_y()` converteixen a cel·la de pantalla (arrodonint, amb
  límits).
- `s_w_n()/s_h_n()` converteixen mides en cel·les a fraccions.
- `fit_playfield_to_terminal()` fixa la mida del camp UN COP en arrencar:
  mesura el terminal, hi resta 2 columnes i 5 files (HUD i barra d'estat) i
  aplica mínims de 40x10.

### 2.2 Render sense parpelleig
- Doble búfer `_screen` (caràcters) i `_colors` (codis ANSI), pintats amb
  `_plot(char, x, y, code)`.
- `render(state)` composa: HUD superior (punts + ajuda) + camp + barra
  d'estat (casc i percentatge de mapa, amb colors segons la vida).
- Ordre de pintat del camp: **terreny (fons) → projectils → enemics →
  efectes → kits → nau**.
- `draw_frame()`: amb colors, no esborra res — `\x1b[H` i repinta a sobre;
  només el primer frame neteja. Sense colors, fallback `cls`.
- Colors: codis SGR via `paint()`; detecció automàtica en arrencar.

### 2.3 Entrada de teclat
- Camí principal: estat del teclat per frame via `GetAsyncKeyState`
  (ctypes); fallback `_pressed_keys_fallback()` (msvcrt) si no hi ha API.
- Les tecles (`KEY_*`) es tradueixen a accions canòniques (`ACTION_*`).
- `wait_key()` (menús): **buida el buffer del teclat abans de bloquejar-se**.
  Sense això, les pulsacions velles (el dispar sostingut durant les
  animacions) tancaven els menús a l'instant —fix de la sessió 2026-08-27.

### 2.4 Entitats i estat
- `new_state()` crea l'estat de la ronda: `player_x/y`, `ship_prev_x`
  (creuaments de paret), `hp`, `score`, `wingmans`, `trail`, `shots`,
  `enemy_shots`, `missiles` (projectils guiats), `missile_level`,
  `missile_cooldown`, `enemies`, `powerups`, `effects`, `ticks`, `map`,
  `map_progress`, `completed`, `terrain`.
- Sprites: matrius de cel·les `(caràcter, color)` via `make_sprite`.
- Enemics (`ENEMY_TYPES`): dron 3x1 —1 vida, 10 pts, 2 cel·les/tick—,
  caça 3x2 —2 vides, 30 pts, 1 cel·la/tick—, creuer 5x3 —4 vides, 80 pts,
  més lent— i el **cap** (10x4, 30 vides, 500 pts, `BOSS_KIND`), que apareix
  al nivell 3 i torna com a final de campanya al nivell 5. Danys per xoc:
  10/20/35/45.
- Patrons de vol (`KIND_PATTERNS` + `_move_enemy`): `recta`, `ona`
  (sinusoidal), `zigzag` (rebot), `picat` (cap al terra), `puja` i `cap`
  (entra per la dreta, s'atura a `BOSS_STOP_COLS` i oscil·la).
- Cap final: `BOSS_MAX_HP = 30` vides, barra `CAP [..]` a l'HUD
  (`BOSS_BAR_WIDTH`) mentre és viu; derrotar-lo posa `completed` a cert a
  l'instant i pot deixar un kit gran (`BOSS_DROP_KIND`, probabilitat
  `BOSS_DROP_CHANCE`). Els seus trets usen `ENEMY_SHOT_TYPES[3]`. No mor en
  xocar amb la nau: fa 45 de dany i la empeny cap a l'esquerra
  (`BOSS_PUSH_COLS`) sense ser destruït.
- Projectils del jugador a 5 cel·les/tick (`SHOT_SPEED`), cooldown de 2
  ticks; els enemics disparen projectils angulars cap a la nau.
- Kits de reparació: petit +15, mitjà +30, gran +60, dron aliat (fins a
  `MAX_WINGMANS = 4`; amb l'esquadra plena val `WINGMAN_SCORE_BONUS = 50`)
  i missils guiats (fins a `MAX_MISSILES = 7` a l'escena alhora; amb el
  nivell ple val `MISSILE_SCORE_BONUS = 50`). Probabilitats de drop
  7:3:2:1:1.
- Missils guiats: `make_missile` els crea al morro i `_home_missile` els
  reorienta cada tick cap a l'enemic més proper (`MISSILE_SPEED = 6`
  cel·les/tick); surten sols cada `MISSILE_INTERVAL_TICKS = 6.25` ticks
  (500 ms a 12.5 FPS) mentre hi hagi lloc a l'escena.
- Efectes: `SPARK_FRAMES` (espurnes) i `BOOM_FRAMES` (explosions), amb
  envelliment per tick.

### 2.5 Col·lisions
- `rects_overlap` sobre rectangles normalitzats + detecció de **creuament**
  dins del mateix tick (objectes més ràpids que l'amplada d'una cel·la):
  projectil-enemic, projectil-paret i nau-paret (via `ship_prev_x`).
- Els **missils guiats** usen `_swept_hits`: la seva trajectòria diagonal
  i ràpida es mostreja en passos de mitja cel·la per no saltar-se
  enemics prims ni parets.
- Xoc nau-enemic: l'enemic explota i resta el seu dany al casc.
- **Xoc nau-paret: destrucció immediata de la nau.**

### 2.6 Bucle principal
`main()` → `level_from_args()` (CLI) → `fit_playfield_to_terminal()` →
`show_intro()` → bucle de rondes `run_round()` (frames cada
`GAME_TICK = 0.08 s`, ~12.5 FPS) → resultat `quit` / `dead` / `completed`
→ gestió de campanya: `completed` amb nivells pendents passa al següent
IMMEDIATAMENT (sense pausa, pantalla ni tecla; el banner de fi de nivell
anuncia el nom del següent); `dead` → game over on qualsevol tecla repeteix
el nivell (`q` surt); últim `completed` → `show_campaign_complete()` amb
`r` per reiniciar la campanya des del nivell 1.

## 3. Sistema de nivells

### 3.1 Fitxers i càrrega
- Cada nivell és un fitxer `nivell_<n>.py` al costat de `main.py` que exposa
  un diccionari `LEVEL` (dades pures, sense lògica de joc).
- `load_levels()` els descobreix amb `glob`, ordena pel número del nom i els
  valida amb `_normalize_level()`.
- `_normalize_terrain()` aplanà cada segment de terreny en un esdeveniment
  per columna `(tick, dalt, abaix, vora, cos)`, ordenat per tick, perquè
  `update_world` només hagi de comparar ticks.

### 3.2 Format de `LEVEL`
| Clau | Contingut |
|---|---|
| `name` | Nom del nivell (pantalla d'introducció) |
| `duration` | Ticks totals; la ronda acaba en arribar-hi |
| `spawns` | Tuples `(tick, tipus 0/1/2, fila 0..1, patró)` |
| `terrain` | Segments de paret (vegeu 3.3); opcional |
| `art` + `paleta` | Dibuix literal del terreny (vegeu 3.4); opcional, exclusiu amb `terrain` |
| `fons` + `paleta_fons` | Capa de fons decorativa amb parallax (vegeu 3.4); opcional |

Documentació completa del format antic (elevacions) al docstring de
`nivell_1.py`; la del format dibuixat (art i fons), al de `nivell_4.py`.

### 3.3 Terreny per elevacions
- Cada segment defineix `"tick"` (quan la primera columna entra per la
  dreta), `"dalt"` i `"abaix"`: l'elevació EN CEL·LES de CADA columna
  (0 = sense paret).
- Estil de cada segment: `"vora"` (superfície que mira al corredor) i
  `"cos"` (interior), cadascun `(caràcter, color ANSI)`; `"estils"` permet
  substitucions puntuals per columna concreta (cristalls, etc.).
- Les columnes avancen EXACTAMENT 1 cel·la/tick (`terrain_step`), així els
  segments de ticks consecutius queden contigus a la pantalla.
- `fit_corridor()` escala les elevacions si el total deixaria menys de
  `MIN_CORRIDOR = 6` cel·les lliures (protegeix terminals petits).
- `wall_rects()` dona les hitbox normalitzades;
  `draw_terrain_column()` pinta la columna com a fons.

### 3.4 Terreny dibuixat (art i fons)
- Format nou (referència: docstring de `nivell_4.py`): el terreny és un
  dibuix literal de `ART_CANON_H = 20` files; CADA columna del dibuix és una
  columna del nivell i entra per la dreta al seu tick (1 cel·la/tick, com amb
  elevacions; cap `fit_corridor`: la validació ja garanteix el pas).
- `paleta` mapa cada caràcter del dibuix a `(caràcter, color ANSI)`; l'espai
  és cel·la lliure. TOT caràcter de la paleta és sòlid: **la col·lisió és la
  presència/absència de caràcter** a la cela avaluada.
- `_normalize_art()` valida mides (files iguals, `ART_CANON_H`) i paleta, i
  converteix el dibuix en cel·les per columna (`None` = lliure);
  `_validate_art_playable()` comprova corredor mínim (`MIN_CORRIDOR`) per
  columna i un camí BFS de banda a banda, en espai canònic (la càrrega passa
  abans de conèixer el terminal real).
- `_art_row(y)` mostreja la fila canònica a la fila de pantalla
  (nearest-neighbor): render, col·lisions i pilot fan servir LA MATEIXA
  funció, així que el que es pinta és exactament el que col·lisiona.
- `_column_cells()` és el pivot entre formats: retorna cel·les per fila de
  pantalla tant d'una columna d'art com d'una d'elevacions; `terrain_rects()`
  n'extreu hitboxes per trams sòlids (illes flotants i túnels donen tants
  rectangles com trams tingui la columna). Els tres punts de col·lisió
  (nau, trets del jugador i trets enemics) l'usen.
- `fons` + `paleta_fons`: mateixa estructura, capa PURAMENT decorativa;
  avança 1 columna cada `FONS_EVERY = 4` ticks i es repeteix en bucle
  horitzontal (`draw_fons()`, primer pintor del `render()`). Mai col·lisiona
  i els espais del primer pla la deixen veure.
- Pilot automàtic: `_art_column_band()` calcula els RUNS lliures d'una
  columna d'art (illes flotants en parteixen) i tria el que conté la nau;
  `_corridor_free_band()` i `_ticks_until_wall()` entenen els dos formats i
  ignoren el fons.
- Eina d'autoria: `eines_art.py` (valida el nivell i previsualitza l'art amb
  colors sense jugar).

### 3.4 Figures auxiliars (definides a cada fitxer de nivell)
- `bump(h)`: perfil triangular 1..h..1 (amplada 2h−1).
- `trapei(h, pla)`: rampa ascendent + plana de `pla` columnes + rampa
  descendent (amplada 2h+pla−1).
- `fila(*blocs)`: encadena perfils en una fila de columnes; cada enter
  introdueix zeros.

### 3.5 Nivells actuals
| Nivell | Nom | Durada | Spawns | Trams de terreny | Corredor mínim de disseny |
|---|---|---|---|---|---|
| 1 | PRIMER CONTACTE | 1800 ticks (~144 s) | 59 | 21 | 10 cel·les |
| 2 | ESCULL DE FERRO | 1800 ticks (~144 s) | 84 | 30 | 8 cel·les |

Nivell 1 en 5 fases (benvinguda, primeres roques, canal en S, pinces,
esprint final); nivell 2 en 5 fases més dures (porta inicial immediata,
murs de 8-10 files, S doble, serra triple, cadena cada 10 ticks i gola
final amb cristall).

## 4. Campanya i línia de comandes
- `main()` avança `CURRENT_MAP` en completar cada nivell i el següent comença
  immediatament: sense pausa, pantalla intermèdia ni espera de tecles (una
  pulsació accidental no pot tancar el programa entre nivells). En acabar
  l'últim mostra `show_campaign_complete()` i `r` reinicia la campanya des
  del nivell 1. Si la nau mor, qualsevol tecla (menys `q`) repeteix el
  mateix nivell.
- `python main.py [nivell]` — `level_from_args()` valida l'argument: número
  vàlid → nivell inicial (mode testing), `-h/--ajuda` → ús, invàlid →
  llista els nivells disponibles i surt amb codi 1. Sense argument,
  campanya normal.

## 5. Proves
- `_test_terreny.py`: headless (sense terminal interactiu), 12 blocs:
  càrrega i ordre dels nivells, `fit_corridor`, estat nou, scroll del
  terreny (1 cel·la/tick), render de vora/cos, destrucció de la nau per
  contacte i per creuament, projectils (dels dos bàndols) morts contra la
  roca (amb creuament), simulació completa dels dos nivells, garanties de
  disseny de tots els nivells (spawns dins de durada, cap spawn sobre
  paret, corredor mínim), `wait_key` amb buffer brut (consola falsa) i
  `level_from_args` (casos vàlids, invàlids i `-h`).
- `_sim_campanya.py`: headless, substitueix `run_round`/`wait_key`/pantalles
  per stubs i verifica el flux EXACTE de `main()`: pas automàtic entre
  nivells (cap tecla ni pantalla intermèdia), banner amb el nom del nivell
  següent, game over tolerant (qualsevol tecla repeteix, `q` surt) i
  reinici de campanya amb `r`. Fixa `COLOR_ENABLED = False` perquè els
  renders siguin deterministes en qualsevol consola.
- `test_smoke.py`: suite de les primeres iteracions. El seu harness tenia
  un bug (no restaurava la base 60x18) ja corregit; queden 17 FALLs per
  drift amb la mecànica actual, documentats i pendents de modernitzar.

## 6. Limitacions conegudes
- Els enemics sobrevolen la roca: no hi ha col·lisió enemic-paret (només
  visual); el disseny dels nivells evita igualment els naixements sobre
  roca.
- A l'animació de final de nivell el terreny desapareix (la nau surt volant
  per un camp net).
- Si es prem una tecla durant l'animació de final de nivell, es descarta
  (els menús buiden el buffer); el pas al següent nivell és automàtic i no
  demana cap confirmació.
- `test_smoke.py` desactualitzat (vegeu §5).

## 7. Registre de canvis

### 2026-09-01
- **Campanya contínua**: en superar un nivell el següent comença
  immediatament —eliminada la pantalla «NIVELL SUPERAT» que exigia prémer
  `r` (qualsevol altra tecla, p. ex. Retorn, tancava el programa entre
  nivells). El banner de fi de nivell ara anuncia el nom del nivell següent.
- **Game over tolerant**: qualsevol tecla repeteix el nivell; només `q`
  surt (abans, qualsevol tecla que no fos `r` abandonava el joc). La
  pantalla «CAMPANYA COMPLETADA» manté la semàntica `r` = reiniciar.

### 2026-08-30
- **Terreny dibuixat (art)**: nou format de nivell amb dibuix literal a 20
  files; la col·lisió és la presència/absència de caràcter a la cela;
  validació en carregar (corredor mínim per columna + camí BFS de banda a
  banda); nous `_normalize_art()`, `_validate_art_playable()`,
  `_column_cells()`, `terrain_rects()`, `_art_row()`.
- **Fons amb parallax**: capa decorativa (`fons` + `paleta_fons`) que avança
  1 columna cada `FONS_EVERY = 4` ticks i es repeteix en bucle horitzontal;
  `draw_fons()` com a primer pintor del `render()` (de més lluny a més a
  prop, tot als buffers i volcat únic per frame); mai col·lisiona.
- **Nivell 4 nou** (*GALERIES D'AUTOR*): mostra petita del format nou (204
  columnes, 5 escenes, grafiti de roca R-TYPE, fons d'estels i muntanyes);
  el pilot automàtic la completa (`--demo 4`: COMPLETED amb 82/100 de casc).
- **Nivell 5 nou** (*BASTIÓ URBÀ*, final de campanya): 760 columnes d'art de
  **ciutat** —carrers entre blocs amb finestres enceses, tags i neons,
  canyons serpentejants, un **mural de grafiti «R-TYPE»** de 40 columnes i
  una plaça que s'obre a l'arena— amb fons de cel, silueta llunyana i
  carretera amb marques (parallax). El **cap final** (boss del nivell 3)
  torna al tick 505: matar-lo completa la campanya. L'art es genera amb
  petits perfils deterministes (`ciutat()`) i lletres de grafiti de 4x5.
  El pilot l'acaba (`--demo 5`: COMPLETED, abatent el cap).
- **Tests**: la suite passa a 22 blocs: nous blocs 21-22 amb les garanties
  del nivell 5 (el cap neix en cel net, abatre'l compleix el nivell i el
  dibuix sencer de 760 columnes creua el camp).
- **Pilot automàtic adaptat**: `_art_column_band()` (runs lliures per columna,
  illes flotants); `_corridor_free_band()` i `_ticks_until_wall()` entenen
  els dos formats i ignoren el fons.
- **`eines_art.py`**: eina d'autoria (validació + previsualització amb colors).
- **Tests**: 5 blocs nous a `_test_terreny.py` (15-19) i garanties de disseny
  esteses als nivells dibuixats (bloc 9, spawns fora de roca per files).

### 2026-08-27
- **Nivells en fitxers**: el mapa surt de `main.py` i viu a fitxers
  `nivell_<n>.py`; nous `load_levels()`, `_normalize_level()`,
  `_normalize_terrain()`.
- **Terreny per elevacions**: parets a dalt/baix per columna amb vora i cos
  colorits; scroll d'1 cel·la/tick; `fit_corridor()` + `MIN_CORRIDOR = 6`;
  col·lisions nau-paret (destrucció, amb detecció de creuament via
  `ship_prev_x`) i projectils aturats per la roca;
  `draw_terrain_column()` com a capa de fons.
- **Nivell 1 redissenyat**: de 720 a 1800 ticks (arreglat: 45 dels 59
  spawns no es disparaven mai), 5 fases i 21 trams de terreny.
- **Nivell 2 nou**: «ESCULL DE FERRO», 84 spawns i 30 trams, corredors fins
  a 8 cel·les.
- **Campanya**: `main()` avança de nivell en completar-lo; nova
  `show_campaign_complete()`; pantalla de «nivell superat» amb el nom del
  següent.
- **Fix de menús**: `wait_key()` buida el buffer del teclat abans d'esperar
  (les pulsacions velles tancaven el joc en completar un nivell).
- **CLI de testing**: `python main.py [nivell]` amb `level_from_args()` i
  `print_usage()`.
- **Documentació**: README al dia (orientat a l'usuari) i creació d'aquest
  document tècnic; `PROJECT_SUMMARY.md` marcat com a històric.
- **Proves**: `_test_terreny.py` ampliada a 12 blocs (inclosa una consola
  falsa per provar `wait_key` i els casos de CLI); fix del harness de
  `test_smoke.py` (restauració de la base 60x18).

