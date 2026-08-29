"""Nivell 4 de R-Type ASCII: GALERIES D'AUTOR - referencia del format nou.

A partir d'aquest nivell el terreny no es descriu amb elevacions (el format
antic, documentat a nivell_1.py) sino amb DIBUIX LITERAL: l'art del nivell
son ART_CANON_H (20) files de text i CADA columna del dibuix es una columna
del nivell. Les columnes avancen cap a l'esquerra UNA cel·la per tick, aixi
que el dibuix sencer es desplaça com una pelicula.

El diccionari LEVEL admet aquestes claus:

  name         Nom del nivell (es mostra a la pantalla d'introduccio).
  duration     Ticks totals del mapa: la partida acaba en arribar-hi. Es
               recomana amplada_de_l'art + 80 (SCREEN_WIDTH per defecte)
               perque el dibuix sencer arribi a creuar la pantalla.
  paleta       Dict del PRIMER PLA: caracter -> (caracter a pintar, color
               ANSI). TOT caracter de la paleta present al dibuix es SOLID:
               la col·lisió es directament la presència/absència de caracter
               a la cela avaluada. L'espai es sempre lliure i no pinta res.
  art          Les 20 files del dibuix del primer pla, totes amb la mateixa
               amplada. Un caracter que no sigui espai ni clau de la paleta
               es una errata de dibuix: el nivell no es carrega.
  paleta_fons  Dict de la capa de FONS, amb la mateixa estructura. Opcional.
  fons         Les 20 files del dibuix de fons: purament estetic (mai
               col·lisiona i el pilot automatic l'ignora); avança una columna
               cada FONS_EVERY ticks (mes lent que el primer pla: parallax)
               i es repeteix en bucle horitzontal, aixi que una franja curta
               de cel cobreix un nivell llarg.
  spawns       Igual que sempre: tuples (tick, tipus d'enemic, fila, patro).

El dibuix es pot escriure a trossos: junta(*paneles) enganxa panells
horitzontalment (tots de 20 files; dins de cada panell, files de la mateixa
amplada). Aquest nivell dura 284 ticks (~23 segons) en cinc escenes:

  A. CEL OBERT      entrada tranquila (els estels son del fons).
  B. LA COVA        estalactites i estalagmites; cristalls magenta incrustats.
  C. EL TUNEL       galeria metal·lica amb llums d'advertencia.
  D. GALERIES       cel obert amb illes flotants i un grafiti de roca: R-TYPE.
  E. CEL OBERT      sortida ampla.

Garanties de jugabilitat, validades en carregar el nivell: cada columna deixa
un corredor lliure d'almenys MIN_CORRIDOR (6) celes i existeix un cami lliure
de la primera a la darrera columna (BFS): un dibuix mal fet no es carrega,
en comptes de segellar la nau. En terminals mes baixos que ART_CANON_H el
dibuix es mostreja per files (nearest-neighbor): render i col·lisions fan
servir el mateix mostreig (_art_row) i mai se'n van de sincronia. Els spawns
d'aquest nivell nomes cauen en columnes amb les seves files lliures.

Eina d'autoria: python eines_art.py [numero de nivell] valida el dibuix i el
previsualitza amb colors sense haver de jugar la partida.
"""

PALETA = {
    "#": ("#", "37"),    # roca: superficie
    "%": ("%", "90"),    # roca: interior
    "@": ("@", "95"),    # cristall magenta
    "=": ("=", "36"),    # panell metallic cian
    "^": ("^", "33"),    # llum d'advertencia groga
}

PALETA_FONS = {
    ".": (".", "90"),    # estel tenu
    "*": ("*", "37"),    # estel brillant
    "^": ("^", "34"),    # muntanya llunyana blava
}


def junta(*paneles):
    """Enganxa panells de 20 files horitzontalment en un sol dibuix."""
    return tuple("".join(fila) for fila in zip(*paneles))


# A. cel obert d'entrada
PANELL_A = (
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
)

# B. la cova, amb estalactites i cristalls
PANELL_B = (
    "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%",
    "##@#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%",
    "  # ##%#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%",
    "      # #@%#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%",
    "          # ##%#%%%%%%%@%%%%%%%%%%%%%%%%%%%%%%%%",
    "              # @#%##%%%%#%%#%%@%%%#%%@%%%%%@%%%",
    "                  #  #### ## ###### ############",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                      ##########",
    "                          # ##########%%%%%%%%%%",
    "                ##########%#%%%%%@%%%%%%%%%%%%%%",
    "          ####@#%%%%%%%%%@%%%%%%%%%%%%%%%@%%%%%%",
    "    ##@###%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%",
    "####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%",
)

# C. el tunel metallic
PANELL_C = (
    "================================================",
    "================================================",
    "================================================",
    "================================================",
    "================================================",
    "================================================",
    "####^#######^#######^#######^#######^#######^###",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                ",
    "                                                ",
    "####^#######^#######^#######^#######^#######^###",
    "================================================",
    "================================================",
    "================================================",
    "================================================",
    "================================================",
)

# D. cel obert, illes flotants i grafiti de roca
PANELL_D = (
    "                                                            ",
    "  #######                                                   ",
    "  #######                                        #########  ",
    "              ###       #### #  # ###  ####      #%%%%%%%#  ",
    "              #  #        #  #  # #  # #         #########  ",
    "              ###  ####   #   ##  ###  ###                  ",
    "              # #         #    #  #    #                    ",
    "              #  #        #    #  #    ####                 ",
    "                                                            ",
    "                                                            ",
    "                                                            ",
    "                                                            ",
    "                                                            ",
    "                                                            ",
    "                                                            ",
    "                                                            ",
    "                    #####                                   ",
    "                    #####                                   ",
    "                                                            ",
    "                                                            ",
)

# E. cel obert de sortida
PANELL_E = (
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
    "                        ",
)


# Fons: es repeteix en bucle horitzontal (96 columnes)
FONS = (
    "                           ..                     .  *                  . .                     ",
    "      . *.                    .                      .              .                *   * .    ",
    "                               .         .                             .               .        ",
    "               .                                                               .         .      ",
    "       *                                      .                                                 ",
    "                     .  .                  *                   .       *             *          ",
    "           .                        *.                           .  . .                         ",
    "                   *              *     .                                 . *     *          .  ",
    "       .    .     .                   ..                                                        ",
    "       .  .  . .                    .         .                          .                      ",
    "                                                  .            .         .      .               ",
    "                                                                                                ",
    "                                                                                                ",
    "    ^^^^^^^      ^^               ^^^^       ^^^^^^^      ^^^^^               ^       ^^^^^^^   ",
    "  ^^^^^^^^^^^   ^^^^^^^^^      ^^^^^^^^^   ^^^^^^^^^^^   ^^^^^^^^^      ^^^^^^^^^   ^^^^^^^^^^^ ",
    "^^^^^^^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^",
    "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
    "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
    "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
    "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
)


LEVEL = {
    "name": "NIVELL 4 - GALERIES D'AUTOR",
    "duration": 284,             # 204 columnes d'art + 80 de pantalla
    "paleta": PALETA,
    "art": junta(PANELL_A, PANELL_B, PANELL_C, PANELL_D, PANELL_E),
    "paleta_fons": PALETA_FONS,
    "fons": FONS,
    "spawns": (
        (5, 0, 0.40, "recta"),       # cel obert (panell A)
        (14, 0, 0.70, "ona"),
        (128, 0, 0.80, "recta"),     # galeries, sota el grafiti (D)
        (150, 1, 0.80, "ona"),
        (185, 0, 0.30, "ona"),       # cel obert de sortida (E)
        (196, 0, 0.60, "recta"),
    ),
}
