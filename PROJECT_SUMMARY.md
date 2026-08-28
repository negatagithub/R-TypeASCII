# R-Type ASCII - Project Summary

> **Nota (2026-08-27):** aquest document és el resum de disseny ORIGINAL del
> projecte i es conserva com a referència històrica: descriu el prototip
> inicial i no reflecteix l'estat actual del joc. La documentació tècnica
> al dia és a [PROJECT.md](PROJECT.md) i la d'usuari a [README.md](README.md).

## Overview
This project is a prototype of the classic arcade game R-Type, implemented in ASCII art for the console. The goal is to create a simple, text-based version of the game that captures the essence of the original while being accessible and fun to play in a terminal environment.

## Game Concept
R-Type is a vertically scrolling shooter game where the player controls a spacecraft and battles through waves of enemies. This ASCII version simplifies the graphics to text characters while maintaining the core gameplay mechanics:
- Player movement (left/right)
- Enemy spawning and movement
- Basic collision detection
- Simple scoring system

## Technical Stack
- **Language**: Python 3.x
- **Platform**: Windows (console-based)
- **Libraries**: 
  - `os` (for screen clearing)
  - `msvcrt` (for keyboard input)
  - `random` (for enemy spawning)
  - `time` (for game timing)

## Project Structure
```
R-TypeASCII/
├── main.py          # Main game file
├── README.md        # Project documentation
└── PROJECT_SUMMARY.md # This file
```

## Game Mechanics

### Player
- Represented by the `^` character
- Moves left (`a` key) and right (`d` key)
- Position tracked by `(player_x, player_y)` coordinates

### Enemies
- Represented by the `E` character
- Spawn randomly at the top of the screen
- Move downward automatically
- Basic AI: simple vertical movement

### Collision System
- Detects when player and enemy positions overlap
- Game ends when collision occurs
- Simple hitbox: 2x2 character area around player/enemy

### Game Loop
1. Clear screen
2. Draw player and enemies
3. Handle keyboard input
4. Update enemy positions
5. Check for collisions
6. Sleep to control game speed
7. Repeat

## Implementation Details

### Key Functions
1. `clear_screen()`: Clears the console screen
2. `draw_player(x, y)`: Draws the player spacecraft at given coordinates
3. `draw_enemy(x, y)`: Draws an enemy at given coordinates
4. `main()`: Main game loop

### Game Flow
1. Initialize player position
2. Spawn initial enemies
3. Enter main game loop
4. Process input and update game state
5. Render game state
6. Check for game-over conditions
7. Exit on player quit (`q` key)

## Future Enhancements
Potential features to add in future iterations:
- Player shooting mechanics
- Multiple enemy types
- Power-ups and upgrades
- Score tracking
- Lives system
- Sound effects (if terminal supports it)
- High score system
- Difficulty levels
- Boss battles

## How to Play
1. Run `python main.py` in the terminal
2. Use `a` to move left
3. Use `d` to move right
4. Avoid enemies (E)
5. Press `q` to quit

## Known Limitations
- No sound effects
- Basic graphics (ASCII characters only)
- Simple collision detection
- No save/load functionality
- Limited to console/terminal environment

## Development Notes
- The game uses `msvcrt` for keyboard input, which is Windows-specific
- For cross-platform compatibility, consider using libraries like `curses` or `pygame`
- Game speed can be adjusted by changing the `time.sleep()` value
- Enemy spawn rate and movement speed can be modified for difficulty balancing

## Testing
The game can be tested by running `main.py` and verifying:
- Player movement responds to keyboard input
- Enemies spawn and move downward
- Collision detection works correctly
- Game exits cleanly when `q` is pressed

## Conclusion
This ASCII version of R-Type provides a fun, lightweight way to experience the classic shooter gameplay. While simplified, it maintains the core mechanics and offers a foundation for further expansion and customization.