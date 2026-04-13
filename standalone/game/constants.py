"""
Game constants — all magic numbers live here.

Every physics value, screen dimension, and option list is defined once.
Import with: ``from game.constants import *``
"""
from __future__ import annotations
from typing import Final

# ── Window & Canvas ────────────────────────────────────────────────────────────
WINDOW_W: Final = 860          # total window width  (px)
WINDOW_H: Final = 640          # total window height (px)
CANVAS_W: Final = 800          # gameplay area width  (px)
CANVAS_H: Final = 500          # gameplay area height (px)
CANVAS_X: Final = (WINDOW_W - CANVAS_W) // 2   # left margin = 30
CANVAS_Y: Final = 90           # top of canvas, below the header panel
FPS:      Final = 60

# ── Paddle physics ─────────────────────────────────────────────────────────────
PADDLE_W:         Final = 12     # paddle width  (px)
PADDLE_H:         Final = 80     # paddle height (px)
PADDLE_X_OFFSET:  Final = 20     # distance from canvas left/right edge
PADDLE_ACCEL:     Final = 3.0    # velocity added per frame when key held
PADDLE_FRICTION:  Final = 0.82   # velocity multiplier applied every frame
PADDLE_MAX_SPEED: Final = 18.0   # capped absolute velocity (canvas px/frame)

# ── Ball physics ───────────────────────────────────────────────────────────────
BALL_SIZE:        Final = 12     # ball square side length (px)
BALL_BASE_SPEED:  Final = 5.0    # starting speed at 1× multiplier
MAX_BALL_SPEED:   Final = 25.0   # hard cap to prevent tunnelling
MAX_BOUNCE_ANGLE: Final = 1.047  # 60° in radians — max angle off a paddle
MIN_BALL_VX:      Final = 2.5    # floor on horizontal speed; prevents infinite vertical rally

# ── AI difficulty speeds ───────────────────────────────────────────────────────
# Max canvas-px the bot can move per frame (before speed_multiplier is applied).
BOT_SPEEDS: Final[dict[str, float]] = {
    'easy':    7.0,
    'medium':  9.0,
    'hard':   12.0,
    'insane': 15.0,
    'extreme':20.0,
}

# ── Option lists (value, display label) ───────────────────────────────────────
DIFFICULTIES: Final[list[tuple[str, str]]] = [
    ('easy',    'Easy'),
    ('medium',  'Medium'),
    ('hard',    'Hard'),
    ('insane',  'Insane'),
    ('extreme', 'Extreme'),
]

SPEEDS: Final[list[tuple[float, str]]] = [
    (0.5, 'Slow  0.5x'),
    (1.0, 'Normal 1x'),
    (1.5, 'Fast  1.5x'),
    (2.0, 'Hyper  2x'),
]

# Selectable win scores: 3 – 10 goals (value, display)
WIN_SCORES: Final[list[tuple[int, str]]] = [(i, str(i)) for i in range(3, 11)]

# ── Game-state identifiers ─────────────────────────────────────────────────────
STATE_MAIN_MENU: Final = 'main_menu'
STATE_SETUP_AI:  Final = 'setup_ai'
STATE_SETUP_PVP: Final = 'setup_pvp'
STATE_THEMES:    Final = 'themes'
STATE_PLAYING:   Final = 'playing'
