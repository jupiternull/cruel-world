# Cruel World

A 2D dungeon survival platformer built with Python and Pygame. Work in progress.

Fight off endless waves of skeletons in a dungeon arena, chaining combos and using movement abilities to stay alive as the difficulty ramps up each wave.

## Gameplay

- Survive increasingly difficult waves of enemies
- Score points by killing enemies — multiplied by the current wave number
- Collect health and score powerups dropped by enemies
- Wave difficulty increases every 30 seconds: faster spawns, more enemies per wave

### Controls

| Key | Action |
|-----|--------|
| A / D or Arrow Keys | Move left / right |
| Space / W | Jump |
| S / Down | Crouch |
| F | Attack (3-hit combo) |
| Shift | Dash |
| Q | Roll (invincibility frames) |
| E | Slide (while running) |
| R | Restart (after game over) |
| Escape | Quit |

### Combat

Attacks can be chained into a 3-hit combo by pressing F within the combo window after each hit. Damage scales per hit: 10 → 15 → 25. Rolling grants brief invincibility frames to dodge through enemies.

### Enemies

| Enemy | HP | Speed | Damage | Notes |
|-------|----|-------|--------|-------|
| White Skeleton | 2 | Fast | 8 | Common |
| Yellow Skeleton | 4 | Slow | 15 | Tankier, hits harder |

## Requirements

- Python 3.x
- Pygame

```
pip install pygame
```

## Running

```
python main.py
```

## Project Structure

```
cruelworld_game/
├── main.py          # Game loop
├── config.py        # All tunable constants
├── assets.py        # Asset loading
├── level.py         # Tilemap and layout
├── game_state.py    # Wave and score logic
├── ui.py            # HUD and game over screen
├── entities/
│   ├── player.py    # Knight with full ability set
│   ├── enemy.py     # Skeleton AI and variants
│   ├── effects.py   # Particles and powerups
│   └── base.py      # Shared entity base class
└── assets/          # Sprites, tilesets, backgrounds
```

---

*Early development. More content coming.*
