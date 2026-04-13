<div align="center">

# 🕹️ NEON PONG

**A neon arcade pong game — play in your browser or run as a standalone desktop app.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue?logo=python&logoColor=white)](https://python.org)
[![pygame-ce](https://img.shields.io/badge/pygame--ce-2.5%2B-orange?logo=python)](https://pyga.me)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub Pages](https://img.shields.io/badge/Play%20Online-GitHub%20Pages-blueviolet?logo=github)](https://jojookun.github.io/classic-ping-pong/)

</div>

---

## 📖 Overview

**Neon Pong** is a fully-featured arcade pong game with a cyberpunk neon aesthetic. It ships in two editions:

| Edition | Technology | Audience |
|---|---|---|
| **Web** | HTML5 / CSS3 / Vanilla JS | Play instantly in any browser, no install needed |
| **Desktop** | Python + pygame-ce | Standalone native app, works offline |

Both editions share the same game mechanics, five AI difficulty levels, four colour themes, and configurable match settings.

---

## ✨ Features

- 🤖 **VS AI mode** — 5 difficulties: Easy → Medium → Hard → Insane → Extreme (with predictive bounce AI)
- 👥 **VS Player mode** — local 2-player on one keyboard
- 🎨 **4 colour themes** — Matrix Green, Cyber Magenta, Tron Cyan, Retro White (live preview)
- 🏆 **Configurable match length** — 3 to 10 goals
- ⚡ **Speed multiplier** — Slow 0.5× → Normal → Fast 1.5× → Hyper 2×
- 🎵 **Synthesised audio** — retro beep sounds generated from scratch (no audio files!)
- ✨ **Particle effects** — spark bursts on every paddle hit and wall bounce
- 📺 **CRT scanlines** — classic neon-arcade look
- 📳 **Screen shake** — dynamic impact feedback
- 🖥️ **Web: touch controls** — virtual on-screen buttons for mobile play

---

## 🌐 Play Online (Web Version)

No installation required — just open in a browser:

**[▶ Play on GitHub Pages](https://jojookun.github.io/classic-ping-pong/)**

### Web Controls

| Action | Player 1 | Player 2 |
|---|---|---|
| Move Up    | `W`      | `↑` Up Arrow   |
| Move Down  | `S`      | `↓` Down Arrow |
| Mobile     | On-screen touch buttons | |

---

## 🖥️ Desktop App (Standalone)

A native Python/pygame desktop application with the full feature set and better performance.

### Requirements

- **Python 3.12 or newer**
- **pip** (comes with Python)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/jojookun/classic-ping-pong.git
cd classic-ping-pong/standalone

# 2. Install the only dependency
pip install pygame-ce
```

> **Note:** `pygame-ce` (Community Edition) is used because it provides pre-built wheels for Python 3.12+. It is a drop-in replacement for `pygame` with an identical API.

### Running the Game

```bash
# From inside the standalone/ directory:
python main.py

# If you have multiple Python versions installed on Windows:
py -3.14 main.py
```

### Desktop Controls

| Action | Player 1 | Player 2 |
|---|---|---|
| Move Up       | `W`         | `↑` Up Arrow   |
| Move Down     | `S`         | `↓` Down Arrow |
| Return to menu | `ESC`      | —              |
| Quit          | Close window | —              |

---

## 🗂️ Project Structure

```
classic-ping-pong/
│
├── index.html          ← Web version entry point
├── game.js             ← Web game logic (state machine, physics, rendering)
├── style.css           ← Web styling, CRT effects, touch button layout
├── README.md           ← This file
│
└── standalone/         ← Desktop application
    ├── main.py         ← Entry point (run this)
    ├── requirements.txt
    ├── README.md       ← Standalone-specific quickstart
    │
    └── game/           ← Python package — one responsibility per module
        ├── __init__.py
        ├── constants.py    → All physics values, window sizes, option lists
        ├── themes.py       → 4 colour theme dicts (TypedDict-typed)
        ├── audio.py        → SoundManager — PCM synthesis, volume, mute
        ├── ui.py           → Glow draw helpers + Button/TextInput/OptionSelector
        ├── entities.py     → Ball, Paddle (AI + human), ParticleSystem
        ├── screens.py      → All 5 game screens (state pattern)
        └── app.py          → App + GameSettings + main loop
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `constants.py` | Single source of truth for every numeric constant |
| `themes.py` | Theme colour palettes, `DEFAULT_THEME`, `THEME_OPTIONS` list |
| `audio.py` | Synthesise retro beep sounds from PCM maths — no files required |
| `ui.py` | Cached neon glow renderers + interactive widgets |
| `entities.py` | Ball physics, paddle (human/AI) movement, particle system |
| `screens.py` | Screen state machine — MainMenu, SetupAI, SetupPvP, Themes, Gameplay |
| `app.py` | Creates the window, owns shared state, runs the main loop |

---

## ⚙️ Configuration

All tunable values live in `standalone/game/constants.py`. No other file needs to change for gameplay tweaks.

```python
# Physics
BALL_BASE_SPEED   = 5.0    # starting ball speed at 1× multiplier
MAX_BALL_SPEED    = 25.0   # hard cap — prevents tunnelling at high speeds
PADDLE_ACCEL      = 3.0    # acceleration per frame when key held
PADDLE_FRICTION   = 0.82   # inertia decay (lower = more slippery)

# Window
WINDOW_W, WINDOW_H = 860, 640
CANVAS_W, CANVAS_H = 800, 500    # gameplay area inside the window
FPS                = 60

# AI speeds (canvas px/frame, before speed_multiplier)
BOT_SPEEDS = {
    'easy': 7.0, 'medium': 9.0, 'hard': 12.0,
    'insane': 15.0, 'extreme': 20.0,
}
```

### Optional: Custom Font

For the full retro arcade look, download **Press Start 2P** and place it at:

```
standalone/assets/PressStart2P.ttf
```

Download free from: https://fonts.google.com/specimen/Press+Start+2P

The game works without it (falls back to a bold system monospace font).

---

## 🎮 Adding a New Theme

1. Open `standalone/game/themes.py`
2. Add an entry to `THEMES`:

```python
THEMES: dict[str, Theme] = {
    # ... existing themes ...
    'amber': {'fg': (255, 176, 0), 'bg': (17, 11, 0), 'name': 'Amber Glow'},
}
```

3. Done — the Themes screen picks it up automatically via `THEME_OPTIONS`.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

### Getting Started

```bash
git clone https://github.com/jojookun/classic-ping-pong.git
cd classic-ping-pong
```

### Coding Standards

- **Python (desktop):** Follow [PEP 8](https://peps.python.org/pep-0008/). Type-annotate all function signatures. Use `logging` instead of `print`. Run `py -3.14 -m py_compile game/**/*.py` to check for syntax errors before committing.
- **JavaScript (web):** Keep all logic inside `game.js`. Avoid external libraries — the web version is intentionally dependency-free.
- **CSS:** CSS variables are declared in `:root` inside `style.css`. Add new styles near related existing ones.

### Branching & Pull Requests

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature-name`
3. Make your changes with clear, descriptive commits
4. Open a pull request — describe *what* changed and *why*

### Ideas for Contributions

- [ ] Persistent high-score table (JSON file)
- [ ] Keyboard rebinding screen
- [ ] Additional colour themes
- [ ] Power-ups (speed boost, paddle shrink)
- [ ] Network multiplayer (Python `socket` + `threading`)
- [ ] PyInstaller packaging for one-file executables

---

## 📜 License

This project is released under the **MIT License** — see [`LICENSE`](LICENSE) for details.

---

## 👤 Author

**Jonathan Christian Herutomo** — [GitHub](https://github.com/jojookun)

---

<div align="center">
<i>Built with ❤️ and neon lights.</i>
</div>
