# R-Type ASCII

[![Proves](https://github.com/negatagithub/R-TypeASCII/actions/workflows/tests.yml/badge.svg)](https://github.com/negatagithub/R-TypeASCII/actions/workflows/tests.yml)
[![Llicència: MIT](https://img.shields.io/badge/lic%C3%A8ncia-MIT-blue.svg)](LICENSE)

Prototip del clàssic arcade shooter **R-Type**, renderitzat íntegrament en
ASCII art dins del terminal de Windows, amb **orientació horitzontal**: la
nau navega per l'esquerra mentre els enemics arriben volant des de la dreta.

## Requisits

- Windows 10/11 (teclat via `msvcrt`; colors via seqüències ANSI que
  s'activen automàticament en arrencar —si el terminal no les admet, es
  juga en monocrom)
- Python 3.8+ — no cal cap paquet extern (`os`, `ctypes`, `msvcrt`, `random`,
  `shutil`, `time`; només `shutil`/`ctypes` fan servir la stdlib de Windows)

## Com jugar

```
python main.py [nivell]         # partida normal
python main.py --demo           # demo: pilot automatic (no guarda records)
python main.py --demo 2         # demo del nivell 2
```

| Argument | Descripció |
|----------|------------|
| *(cap)* | Campanya completa, des del nivell 1 |
| `2` | Comença directament al nivell indicat —útil per provar un nivell concret sense passar pels anteriors; en superar-lo, la campanya continua amb el següent |
| `--demo [nivell]` | **Mode demo**: un pilot automàtic determinista juga en headless (sense teclat ni esperes); amb nivell, comença allà |
| `-h` | Mostra l'ús del programa i els nivells disponibles |

| Tecla | Acció |
|-------|-------|
| `w` / `s` o fletxes ↑ ↓ | Moure la nau amunt / avall |
| `a` / `d` o fletxes ← → | Moure la nau endarrere / endavant |
| `ESPAI` | Disparar (mantenir-lo premut = tir continu) |
| `p` | Pausa: congela la partida; `p` altre cop continua, `q` surt |
| `q` | Sortir |
| `r` | A la pantalla «Campanya completada»: repetir la campanya des del nivell 1 |

L'entrada es llegeix per **estat del teclat** a cada frame (via
`GetAsyncKeyState`): pots mantenir les tecles premudes i combinar-ne diverses
alhora —moviment en diagonal mentre disparres— com en un joc d'arcade.

Els enemics arriben en quatre mides —drons petits, caces mitjans, creuers
cuirassats i el cap final del nivell 3— i els projectils (`-`) els destrueixen;
cada tipus val punts diferents i els mes grossos aguantan varios impactes. Quan un enemic toca
la nau li resta vida al casc segons la seva mida, i la partida s'acaba si
la barra inferior queda buida. El nivell 1 segueix un mapa temporitzat i
acaba quan s'han recorregut tots els seus ticks.

### Mode demo

Amb `--demo` la partida la juga sola un **pilot automàtic determinista**
(llavor fixa: cada execució és idèntica). Va a màxima velocitat —un frame
pintat de cada 60, cap espera— i una campanya sencera dura un parell de
segons. La política del pilot: col·locar-se al corredor lliure que imposen
les parets properes, esquivar-hi (sense sortir-ne) el tret o enemic més
proper, i disparar quan té algú per davant. S'usa per fumigar el bucle
complet del joc al terminal o a la CI.

## Mecàniques

- **Orientació horitzontal** — la nau apunta cap a la dreta i es pot moure
  per tot el camp; els enemics entren pel costat dret.
- **Enemics de diverses mides** — drons (3x1, ràpids, 1 vida, 10 pts),
  caces (3x2, 2 vides, 30 pts) i creuers (5x3, lents, 4 vides, 80 pts).
  Cada sprite ocupa el seu rectangle: la mida forma part del repte.
- **Cap final (nivell 3)** — el `cap` (10x4, **30 vides**, 500 pts) entra
  per la dreta, s'atura i es balanceja disparant trets dirigits. La barra
  `CAP` de la línia d'estat en mostra la vida i, en caure, el nivell es
  completa a l'instant (no cal arribar al 100% del mapa) i pot deixar un
  kit gran de reparació. No mor si el toques: cada xoc resta 45 punts al
  casc i **empeny la nau cap enrere, fora del seu casc** (`BOSS_PUSH_COLS`).
- **Sprites multicolor** — cada cel·la del sprite defineix el seu caràcter i
  el seu color ANSI, de manera que una mateixa nau pot combinar cian, blanc,
  groc i altres tons. Els projectils, enemics, efectes, kits i HUD també
  mantenen els seus colors; si el terminal no admet ANSI, es veu en monocrom.
- **Patrons de moviment** — cada enemic neix amb un patro predefinit:
  recta, ona sinusoidal, zigzag rebotant, picat en diagonal o pujada;
  cada tipus d'enemic combina els seus patrons caracteristics.
- **Casc i barra de vida** — la nau te **100 punts de casc**, visibles a la
  barra inferior: verda per sobre del 60%, groga fins al 25% i vermella en
  nivell critic. Al seu costat, la barra `MAPA` indica el percentatge recorregut.
  Cada xoc descompta el dany del enemic (dron 10, caca 20, creuer 35),
  l'enemic explota contra el casco i, a zero, game over.
- **Kits de reparacio** — els enemics abatuts de vegades deixen un kit
  vermell que restaura casc en tocar-lo amb la nau. Hi ha tres mides:
  petit (+15), mitja (+30) i gran (+60); com mes vida retorna, mes gran
  es el kit i mes raro cau.
- **Pausa** — la tecla `p` congela la partida en qualsevol moment (els
  enemics, els projectils i el temps del mapa s'aturen); `p` torna a
  engegar-la i `q` surt directament. No repren si la tecla segueix
  fisicament premuda, per evitar una pausa instantania al tornar.
- **Records persistents** — les puntuacions finals es desan al fitxer
  `records.json` (ignorat per Git) i el **top 5** es mostra al menu
  d'introduccio i a les pantalles de fi de partida, amb un `NOU RECORD!`
  destacat quan la puntuacio es la millor de totes. Si el fitxer esta
  trencat o no es pot escriure, el joc continua sense queixar-se.
- **Dron aliat (el mes rar)** — aquest kit desplega un mini-dron (`->`)
  que seguia l'estela de la nau i dispara un projectil addicional cada
  cop que dispres. Maxim 4 drons; si en reps un amb l'esquadra plena,
  es converteix en +50 punts.
- **Missils guiats** — un altre kit rar desplega missils verd-grocs (`=>`)
  que surten sols del morro de la nau cada mig segon i **cacen
  automàticament l'enemic més proper**. Cada kit puja un nivell (fins a
  7 nivells, que son els missils maxims que poden planejar a l'escena
  alhora); amb el nivell ple, el kit es converteix en +50 punts. El HUD
  mostra `MISSL n/7` un cop reculls el primer.
- **Efectes d'impacte** — cada toc genera una espurna groga (`*` `+` `.`)
  on aterra el projectil; en abatre un enemic, aquest explota al centre
  amb una animacio mes gran com mes gran sigui (drons: espurna; cacers
  i creuers: explosio 3x3 de dos frames).
- **Projectils** — la barra espaiadora dispara un `-` des del morro de la
  nau a 5 cel·les per tick; la nau es mou horitzontalment a 3.5 cel·les per
  tick, per sobre del scroll enemic més ràpid (2 cel·les per tick). Hi ha un
  temps de recàrrega de 2 ticks entre dispars.
- **Projectils enemics** — es mostren com `!` amb fons vermell brillant,
  perquè no es confonguin amb els enemics ni amb els trets grocs del jugador.
- **Entrada en temps real** — les tecles es consulten per estat a cada frame:
  mantenir premuda una tecla genera moviment continu, i es poden prémer
  diverses tecles en paral·lel (WASD + fletxes + ESPAI alhora).
- **Col·lisions** — hitbox rectangular real: cada sprite ocupa exactament el
  seu rectangle (amplada x alçada) i dos rectangles que es toquen col·lisionen;
  si un enemic toca la nau, explota i li resta vida al casc. Tocar una paret
  del terreny, en canvi, destrueix la nau a l'instant.
- **Puntuació** — cada tipus d'enemic val punts diferents segons la seva
  mida i les vides que aguantin (10/30/80), visibles al HUD superior.
- **Dificultat progressiva** — no hi ha spawn aleatori: el fitxer de cada
  nivell controla tots els naixements i les parets; la densitat d'enemics i
  l'estretor del corredor creixen dins de cada nivell i entre nivells de la
  campanya.
- **Mida adaptada al terminal** — en arrencar, el joc mesura la finestra del
  terminal i dimensiona el camp UN COP; si redimensiones durant la partida,
  el camp manté la mida inicial.
- **Mapes en fitxers** — cada nivell viu en un fitxer propi numerat
  (`nivell_1.py`, `nivell_2.py`...) al costat de `main.py` i defineix el moment
  exacte, el tipus, la fila i el patró de cada enemic. El nivell 1 dura 1800
  ticks (uns 144 segons); el nivell 2 (*Escull de ferro*) té corredors més
  estrets (mínim de 8 cel·les al pic) i molta més densitat d'enemics. La
  partida acaba amb la pantalla de nivell completat quan la barra de mapa
  arriba al 100% —excepte al nivell 3 (*El cap*), on derrotar el cap final
  es tanca el nivell a l'instant.
- **Campanya** — en superar un nivell s'avança automàticament al següent,
  sense cap pausa, pantalla intermèdia ni tecla de confirmació: acabada
  l'animació de fi de nivell (el banner en mostra el nom), el nivell següent
  comença a l'instant (els fitxers `nivell_<n>.py` es carreguen en ordre
  numèric). En completar l'últim nivell pots reiniciar la campanya des del
  principi. Si la nau és destruïda, qualsevol tecla repeteix el mateix
  nivell i només `q` surt del joc.
- **Parets i terreny** — cada nivell pot definir parets a dalt i a baix del
  camp per **elevacions**: un valor en cel·les per CADA columna, amb caràcter
  i color propis per a la vora i per a l'interior de la paret (i substitucions
  puntuals per columna concreta). Les parets avancen una cel·la per tick,
  estrenyen el pas i fan cada tram del mapa únic; tocar-ne una **destrueix la
  nau**. Si un disseny estreny massa el pas per al terminal actual, les
  elevacions s'escalen deixant sempre un corredor mínim lliure
  (`MIN_CORRIDOR`). Els projectils, dels dos bàndols, moren contra la roca
  amb una espurna.
- **Terreny dibuixat (art) i fons amb profunditat** — a partir del nivell 4
  (*Galeries d'autor*; al 5, *Bastió urbà*, és l'art de tota una ciutat),
  el terreny no es descriu amb elevacions sinó amb
  **ASCII art literal**: 20 files de dibuix on cada columna del nivell és una
  columna del dibuix, pintada cel·la a cel·la amb el seu caràcter i color.
  La col·lisió és directa: **presència de caràcter = roca**; espai = lliure.
  Això permet coves, túnels, illes flotants i missatges gravats a la roca
  (el nivell 4 hi té un grafiti R-TYPE). A més, una capa de **fons**
  decorativa (estels, muntanyes llunyanes) avança 4 cops més lent
  (`FONS_EVERY`) i es repeteix en bucle, donant sensació de profunditat:
  mai col·lisiona i el pilot automàtic l'ignora. En carregar el nivell es
  valida que cada columna deixi un corredor mínim (`MIN_CORRIDOR`) i que
  existeixi un camí lliure de banda a banda (BFS): un dibuix que segelli el
  pas no es carrega. L'eina `eines_art.py` previsualitza i valida el dibuix
  sense haver de jugar.
- **Final de nivell** — en completar el mapa apareix un banner gran de
  `NIVELL COMPLETAT` centrat a la pantalla i la nau surt volant cap a la dreta
  fins desaparèixer. Després s'espera 6 segons abans de tornar al menú.

## Afinament

Tots els paràmetres del joc són a l'inici de [`main.py`](main.py):

| Constant | Per defecte | Significat |
|----------|-------------|------------|
| `MIN_WIDTH` / `MIN_HEIGHT` | 40 x 10 | Mida mínima del camp de joc |
| `PLAYER_ZONE_FRACTION` | 1.0 | Fracció de pantalla navegable (1.0 = tot el camp) |
| `PLAYER_HORIZONTAL_SPEED` | 3.5 | Velocitat horitzontal de la nau, en cel·les/tick |
| `SHOT_SPEED` | 5.0 | Velocitat dels projectils del jugador, en cel·les/tick |
| `SHOT_COOLDOWN_TICKS` | 2 | Ticks entre dispars consecutius |
| `MAPS` / `CURRENT_MAP` | 6 nivells | Nivells de la campanya i nivell actiu |
| `GAME_TICK` | 0.08 s | Segons per frame (menys = més ràpid) |
| `ENEMY_TYPES` | 4 tipus (amb el cap) | Sprites, vides, punts, velocitat, dany i frequencia |
| `SHIP_MAX_HP` / `STATUS_BAR_WIDTH` | 100 / 24 | Vida inicial del casc i celes de la barra |
| `MIN_CORRIDOR` | 6 | Celes lliures mínimes entre parets del terreny |
| `ART_CANON_H` / `FONS_EVERY` | 20 / 4 | Alçada de disseny de l'art dibuixat i ticks per avançar una columna de fons |
| `POWERUPS` / `POWERUP_NO_DROP_WEIGHT` | 5 tipus (3 kits + dron + missils) / 30 | Kits de reparacio (cura, sprite), dron aliat i missils guiats; pes de no-drop |
| `MAX_MISSILES` / `MISSILE_INTERVAL_TICKS` | 7 / 6.25 | Missils guiats: nivells (missils maxims a l'escena) i ticks entre llançaments (500ms) |
| `MISSILE_SPEED` | 6.0 | Velocitat dels missils guiats, en cel·les/tick |
| `BOSS_MAX_HP` / `BOSS_BAR_WIDTH` | 30 / 22 | Vida del cap final i celes de la seva barra a l'HUD |
| `BOSS_DROP_KIND` / `BOSS_DROP_CHANCE` | 2 / 0.65 | Kit gran que deixa el cap en caure i probabilitat |

## Estructura del projecte

```
R-TypeASCII/
├── main.py               # El motor del joc (render, entrada, campanya, CLI)
├── nivell_1.py           # Nivell 1: spawns + parets (terreny)
├── nivell_2.py           # Nivell 2: Escull de ferro
├── nivell_3.py           # Nivell 3: El cap (arena del cap final)
├── nivell_4.py           # Nivell 4: Galeries d'autor (terreny dibuixat + fons)
├── nivell_5.py           # Nivell 5: Bastió urbà (ciutat, grafitis i boss final)
├── nivell_<n>.py         # Més nivells: es carreguen en ordre numèric
├── eines_art.py          # Eina: valida i previsualitza l'art d'un nivell
├── README.md             # Documentació d'usuari (aquest fitxer)
├── PROJECT.md            # Documentació tècnica del projecte
├── PROJECT_SUMMARY.md    # Resum de disseny original (històric)
├── _test_terreny.py      # Suite headless de proves del terreny (22 blocs)
├── test_smoke.py         # Suite headless de proves del motor (106 comprovacions)
├── LICENSE                # Llicència MIT
└── .github/               # CI (GitHub Actions) i plantilles d'issues
```

## Notes de desenvolupament

- Els sprites es creen amb `make_sprite(files, colors)`: les dues graelles
  tenen la mateixa mida i cada entrada de `colors` correspon a una cel·la de
  `files`. Un color `None` és transparent o permet el color general del
  dibuixador per a sprites antics.

- L'estat del teclat es consulta amb `GetAsyncKeyState` (API de Windows via
  `ctypes`); quan aquesta API no està disponible, es fa servir `msvcrt` com a
  fallback. El joc continua sent específic de Windows; per a un port
  multiplataforma caldria fer servir `curses` o `pygame`.
- Renderitzat sense parpalleig: cada frame es composa en memoria i
  s'escriu d'una sola vegada; amb colors actius no s'esborra la consola,
  sino que el cursor torna a l'origen (`\x1b[H`) i el frame es repinta a
  sobre de l'anterior. El cursor s'amaga durant la partida i es restaura
  en sortir; sense suport ANSI es conserva el vell `cls` com a fallback.
- La lògica del joc (`new_state`, `update_world`, `find_collision`, ...) és
  independent del bucle d'entrada/render, fet que facilita provar-la sense
  terminal i ampliar-la.

## Idees futures

Mes tipus d'enemics (inclosos enemics que disparin), patrons de moviment,
vides, efectes de so, nivells de dificultat i enemics
finals — vegeu la secció *Future Enhancements* de
[`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md).

## Registre de canvis

Format basat en [Keep a Changelog](https://keepachangelog.com/ca/1.1.0/);
versionat amb [SemVer](https://semver.org/lang/ca/) i etiquetat a Git
(`vX.Y.Z`, branca `main`).

### [v0.5.0] — 2026-08-30

#### Afegit
- **Terreny dibuixat (format `art`)**: nou format de nivell on el terreny és
  un **dibuix literal** — 20 files (`ART_CANON_H`) de text on cada columna del
  dibuix és una columna del nivell; cada cel·la sòlida es pinta amb el seu
  caràcter i color, i **la col·lisió és la presència/absència de caràcter** a
  la cela avaluada. Això permet coves, túnels, illes flotants i missatges
  gravats a la roca.
- **Capa de fons amb parallax (`fons`)**: segona capa d'art, purament
  estètica (mai col·lisiona i el pilot automàtic l'ignora), que avança una
  columna cada `FONS_EVERY` ticks —més lent que el primer pla— i es repeteix
  en bucle horitzontal. El render la pinta la primera (més lluny) i els
  espais del primer pla la deixen veure: sensació de profunditat.
- **`nivell_4.py` (*GALERIES D'AUTOR*)**: nivell de mostra petit (204
  columnes, 284 ticks) amb cinc escenes — cel obert, cova amb estalactites i
  cristalls, túnel metàl·lic amb llums, cel amb illes flotants i un grafiti
  de roca R-TYPE, i sortida ampla — més un fons d'estels i muntanyes. El seu
  docstring és la referència del format nou.
- **`nivell_5.py` (*BASTIÓ URBÀ*)**: final de campanya amb **art de ciutat**
  (760 columnes): carrers entre blocs amb finestres enceses, tags i cartells
  de neó, canyons que serpentejen, un **mural de grafiti «R-TYPE»** de 40
  columnes i una plaça que s'obre a l'arena, amb un fons de cel, silueta
  llunyana i carretera amb marques. El **cap final** torna al tick 505 per
  defensar la ciutat: abatre'l completa la campanya. La suite de proves
  incorpora els blocs 21-22 (cap en cel net, dibuix sencer creuant el camp).
- **Validació de jugabilitat en carregar**: cada columna del dibuix ha de
  deixar un corredor d'almenys `MIN_CORRIDOR` cel·les i ha d'existir un camí
  lliure de la primera a la darrera columna (BFS): un dibuix que segelli el
  pas rebutja el nivell amb un missatge clar, en lloc d'escanyar la nau.
- **`eines_art.py`**: eina d'autoria que valida un nivell dibuixat i el
  previsualitza amb colors sense jugar (corredor mínim, spawns sobre roca).
- **`_test_terreny.py`**: cinc blocs nous (15-19): normalització i errors de
  dibuix, col·lisió de nau i projectils per cel·les, render de l'art i del
  fons (parallax i bucle), pilot automàtic amb illes flotants i simulació
  completa del nivell 4. Les garanties de disseny (bloc 9) cobreixen també
  els nivells dibuixats, incloent spawns fora de roca.

#### Canviat
- Col·lisions, render i pilot passen per l'adaptador `_column_cells()` i
  `terrain_rects()`, que admeten els DOS formats de columna (elevacions i
  art): els nivells 1-3 (format antic) segueixen funcionant intactes.
- L'art es dissenya a 20 files i es mostreja a l'alçada del terminal amb
  `_art_row()` (nearest-neighbor): render i col·lisions fan servir el mateix
  mostreig, així que el que es pinta és exactament el que col·lisiona.

### [v0.4.1] — 2026-08-29

#### Corregit
- El **cap final ara compleix la seva promesa documentada**: no mor en xocar
  amb la nau. Cada impacte resta 45 punts al casc i **empeny la nau cap a
  l'esquerra, fora del seu casc** (`BOSS_PUSH_COLS`), amb una espurna en
  lloc de la gran explosió que suggeria erròniament la seva mort. Abans el
  boss explotava com qualsevol altre enemic i desapareixia del camp.
- `_test_terreny.py`: 14è bloc que cobreix el xoc amb el cap (dany al casc,
  la nau empesa exactament a `BOSS_PUSH_COLS` i el boss supervivent amb la
  seva vida intacta).

### [v0.4.0] — 2026-08-29

#### Afegit
- **Cap final i `nivell_3.py` (*EL CAP*)**: nou enemic de tipus `cap` (`kind`
  3, `BOSS_KIND`) —sprite 10x4, **30 vides**, 500 pts— que entra per la dreta,
  s'atura a `BOSS_STOP_COLS` celes de la vora i es balanceja disparant trets
  dirigits (projectil pesat). El tercer nivell de la campanya és la seva arena:
  corredor rocós d'aproximació, camp net i el cap al tick 800.
- **Barra de vida del cap a l'HUD**: mentre el cap és viu, la línia d'estat
  mostra `CAP [###...] 30/30` en magenta (`BOSS_BAR_WIDTH`).
- **Derrotar el cap completa el nivell**: en caure, `state["completed"]` passa
  a cert a l'instant —encara que quedin ticks de mapa— i pot deixar un kit
  gran (`BOSS_DROP_KIND`) amb probabilitat `BOSS_DROP_CHANCE`.
- `_test_terreny.py`: 13è bloc amb la derrota del cap (puntuació, neteja del
  camp) i la barra d'HP a l'HUD.

#### Corregit
- **Indentació del patró `cap`**: la branca de `make_enemy`/`_move_enemy`
  havia quedat amb cometes escapades i un sagnat trencat que impedia
  `import main`; l'HUD amb el boss es va afegir sense la definició de
  `render`. Tot s'ha restaurat i verificat amb les dues suites.
- En aparèixer el cap des d'un mapa, `base_y` ja coincideix amb la fila
  d'entrada (abans quedava el valor aleatori de `make_enemy`).

#### Docs
- README: quatre mides d'enemic (amb el cap final), mecànica de la barra i
  de la derrota del cap, i constants `BOSS_*` a la taula.

### [v0.3.0] — 2026-08-28

#### Afegit
- **Pausa en partida** (tecla `p`): congela el bucle amb un rètol PAUSA;
  `p` repren (esperant que la tecla es deixi anar, per no re-pausar a
  l'instant amb `GetAsyncKeyState`) i `q` surt directament. No té efecte
  en el mode demo.
- **Records persistents** (`records.json`, top 5, ignorat per Git): cada
  puntuació final de partida es desa al top (mai a la demo), el menú i les
  pantalles de fi de partida el mostren, i la millor puntuació de totes
  s'anuncia amb `NOU RECORD!`. Lectura i escriptura tolerants: un fitxer
  trencat o sense permisos d'escriptura no impedeix mai jugar.
- `test_smoke.py`: **bloc 15** de pausa i records: taula aïllada en fitxer
  temporal (mai el `records.json` de debó), top ordenat i retallat a 5,
  tolerància a JSON trencat, no-desat de puntuacions no positives i codi
  de tecla `p`.

#### Docs
- README: tecla `p` a la taula de controls, mecàniques de pausa i records,
  estructura de fitxers al dia (`test_smoke.py` ja no és "pendent de
  modernitzar") i "records persistents" tret de les idees futures.

### [v0.2.0] — 2026-08-28

#### Afegit
- **Mode demo** (`python main.py --demo [nivell]`): un **pilot automàtic
  determinista** (llavor fixa `DEMO_SEED`) juga la partida en headless, a
  màxima velocitat (un frame de cada 60, cap espera) — una campanya sencera
  dura ~2 segons. Política: situar-se al corredor que imposen les parets
  properes (intersecció de les franges lliures), esquivar-hi —sense sortir-
  n'en— el tret o enemic més proper i disparar quan té objectiu. Pot morir i
  repetir nivell (així fuma també el game over i el reinici); el codi d'exit
  només falla si el motor s'encalla (fusible `DEMO_MAX_TICKS`).
- `test_smoke.py`: **bloc 14** del pilot automàtic (arguments `--demo`,
  determinisme, inactivitat sense amenaces i esquiva sota una paret).
- **Integració contínua** amb GitHub Actions (`.github/workflows/tests.yml`):
  a cada push i pull request s'executen les dues suites headless sobre
  Python 3.8–3.12 en `windows-latest`, més una fumigació del bucle complet
  amb `python main.py --demo`.
- **Llicència MIT** ([LICENSE](LICENSE)) i plantilles d'issues
  (`.github/ISSUE_TEMPLATE/`).
- `test_smoke.py`: nou **bloc 13 de drons aliats** (wingmans): unió a
  l'esquadra, tir addicional, estela i conversió en punts bonus quan la
  esquadra és plena.
- `test_smoke.py`: **codi d'exit** (0 = tot bé, 1 = fallides), imprescindible
  per a la CI.

#### Corregit
- `test_smoke.py` **aïlla l'estat dels nivells**: `update_world()` ja no
  executa els spawns ni el terreny de `nivell_<n>.py` dins dels tests
  (contaminava les assercions amb enemics i parets del mapa real).
- **Suite modernitzada**: 21 comprovacions obsoletes alineades amb la
  mecànica vigent (velocitats de nau 3,5 i tret 5 cel·les/tick, navegació
  per tot el camp, efectes centrats al punt d'impacte, sprites multicolor,
  centres dels kits). Resultat: **106/106 PASS** (abans 75 PASS / 21 FAIL).

#### Docs
- README: estat real de les suites, taula de constants i estructura de
  fitxers actualitzats; badges d'estat de CI i llicència.

### [v0.1.0] — 2026-08-28

- Primera versió pública: motor complet (campanya, terreny, kits, drons
  aliats, colors ANSI), nivells 1 i 2, suites headless de proves i
  documentació.

## Llicència

Distribuït sota la [llicència MIT](LICENSE).
