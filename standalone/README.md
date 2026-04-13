# 🕹️ Neon Pong — Desktop App Quickstart

> For the full documentation, feature list, and contribution guide see the [root README](../README.md).

---

## Requirements

- Python **3.12** or newer
- `pip`

## Install & Run

```bash
# Install the single dependency
pip install pygame-ce

# Launch the game (from this directory)
python main.py

# Windows with multiple Python versions
py -3.14 main.py
```

## Controls

| | Player 1 | Player 2 |
|---|---|---|
| Up   | `W`   | `↑` Up Arrow   |
| Down | `S`   | `↓` Down Arrow |
| Menu | `ESC` | —              |

## Optional Font

Place `PressStart2P.ttf` ([download](https://fonts.google.com/specimen/Press+Start+2P))
inside `standalone/assets/` for the authentic arcade typeface.
The game runs without it using a bold system font fallback.

## Package Layout

```
game/
├── constants.py   ← All physics / window / option constants
├── themes.py      ← Colour palettes (TypedDict-typed)
├── audio.py       ← PCM-synthesised retro sounds (no audio files)
├── ui.py          ← Cached neon glow renderers + widgets
├── entities.py    ← Ball, Paddle (human + AI), ParticleSystem
├── screens.py     ← 5 game screens (BaseScreen state pattern)
└── app.py         ← App + GameSettings + main loop
```
