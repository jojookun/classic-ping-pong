"""
Colour theme definitions for Neon Pong.

Each theme is a :class:`Theme` dict with three keys:

* ``fg``   — foreground (neon glow) colour as an ``(R, G, B)`` tuple
* ``bg``   — background colour as an ``(R, G, B)`` tuple
* ``name`` — display label shown in the Themes screen

``THEMES`` maps a short identifier string to its ``Theme``.
``THEME_OPTIONS`` is a list of ``(key, label)`` tuples in display order,
suitable for feeding directly into an :class:`~game.ui.OptionSelector`.
"""
from __future__ import annotations

from typing import TypedDict


class Theme(TypedDict):
    """Type-safe structure for a colour theme."""
    fg:   tuple[int, int, int]   # neon / foreground colour
    bg:   tuple[int, int, int]   # background fill colour
    name: str                    # human-readable label


THEMES: dict[str, Theme] = {
    'green':   {'fg': (0,   255, 170), 'bg': (2,  17,  12), 'name': 'Matrix Green'},
    'magenta': {'fg': (255,   0, 255), 'bg': (16,   1,  16), 'name': 'Cyber Magenta'},
    'cyan':    {'fg': (0,   255, 255), 'bg': (0,  17,  17), 'name': 'Tron Cyan'},
    'white':   {'fg': (255, 255, 255), 'bg': (17,  17,  17), 'name': 'Retro White'},
}

# Ordered list consumed by OptionSelector: [(key, display_label), ...]
THEME_OPTIONS: list[tuple[str, str]] = [(k, v['name']) for k, v in THEMES.items()]

# The default theme key applied at startup
DEFAULT_THEME: str = 'green'
