"""
UI drawing helpers and interactive widget classes.

Public API
----------
get_font(size)          – Cached font loader (Press Start 2P → system fallback)
draw_glow_rect(...)     – Solid neon rectangle with halo (surface-cached)
draw_border_rect(...)   – Hollow neon border rectangle
draw_glow_text(...)     – Centred text with neon glow layers (surface-cached)
draw_scanlines(...)     – CRT scanline overlay (surface-cached per window size)
Button                  – Clickable neon button with hover state
TextInput               – Single-line editable field
OptionSelector          – Left/right arrow option picker
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    pass


# ─── Font ─────────────────────────────────────────────────────────────────────

_font_cache: dict[int, pygame.font.Font] = {}
_FONT_PATH: Path | None = None


def _find_font() -> Path | None:
    """
    Locate the Press Start 2P TTF file bundled next to the package.
    Returns None when not present so the caller can fall back to a system font.
    """
    candidate = Path(__file__).parent.parent / 'assets' / 'PressStart2P.ttf'
    return candidate if candidate.is_file() else None


def get_font(size: int) -> pygame.font.Font:
    """Return a :class:`pygame.font.Font` at *size* pixels, result is cached."""
    if size not in _font_cache:
        global _FONT_PATH
        if _FONT_PATH is None:
            _FONT_PATH = _find_font() or Path()   # empty Path means 'not found'
        path = _FONT_PATH if _FONT_PATH.suffix else None
        _font_cache[size] = (
            pygame.font.Font(str(path), size)
            if path
            else pygame.font.SysFont('courier', size, bold=True)
        )
    return _font_cache[size]


# ─── Render caches ────────────────────────────────────────────────────────────
# Each cache is keyed so that the same visual element is only composed once.
# Keys include all parameters that affect the rendered output (size, color, glow).

_scanline_cache:   dict[tuple, pygame.Surface] = {}
_glow_rect_cache:  dict[tuple, pygame.Surface] = {}
_glow_text_cache:  dict[tuple, pygame.Surface] = {}

# Evict all render caches — call this after a theme change so stale
# per-color surfaces don't accumulate indefinitely.
def clear_render_caches() -> None:
    """Flush all surface caches (call when the active theme changes)."""
    _glow_rect_cache.clear()
    _glow_text_cache.clear()
    # _scanline_cache is theme-independent so we leave it intact.


# ─── Glow helpers ─────────────────────────────────────────────────────────────

def draw_glow_rect(
    surface: pygame.Surface,
    color: tuple,
    rect,
    glow: int = 6,
) -> None:
    """
    Draw a solid neon rectangle with a layered halo.

    Raises no exceptions.  The composed surface is cached by
    ``(width, height, color_rgb, glow)`` so the first call per unique
    combination pays the allocation cost; subsequent calls are a fast blit.
    """
    r   = pygame.Rect(rect)
    key = (r.width, r.height, color[:3], glow)

    if key not in _glow_rect_cache:
        total = glow * 2
        comp  = pygame.Surface((r.width + total, r.height + total), pygame.SRCALPHA)
        # Draw halo rings from outermost (dimmest) to innermost (brightest)
        for i in range(glow, 0, -1):
            alpha = min(180, int(90 / i))
            halo  = pygame.Rect(glow - i, glow - i, r.width + i * 2, r.height + i * 2)
            pygame.draw.rect(comp, (*color[:3], alpha), halo)
        # Solid core
        pygame.draw.rect(comp, (*color[:3], 255), (glow, glow, r.width, r.height))
        _glow_rect_cache[key] = comp

    cached = _glow_rect_cache[key]
    surface.blit(cached, (r.x - glow, r.y - glow))


def draw_border_rect(
    surface: pygame.Surface,
    color: tuple,
    rect,
    width: int = 2,
    glow: int = 4,
) -> None:
    """Draw a hollow neon border rectangle with a soft glow halo."""
    r = pygame.Rect(rect)
    for i in range(glow, 0, -1):
        alpha    = max(6, int(70 / i))
        expanded = r.inflate(i * 2, i * 2)
        s        = pygame.Surface(expanded.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (*color[:3], alpha), s.get_rect(), width)
        surface.blit(s, expanded.topleft)
    pygame.draw.rect(surface, color[:3], r, width)


def draw_glow_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: tuple,
    cx: int,
    cy: int,
    glow: int = 3,
) -> None:
    """
    Render *text* centred at *(cx, cy)* with layered neon glow.

    The composed surface (glow halos + sharp text) is cached by
    ``(font_id, text, color_rgb, glow)``.
    """
    key = (id(font), text, color[:3], glow)

    if key not in _glow_text_cache:
        # Limit cache growth — rare theme-change artefacts are acceptable
        if len(_glow_text_cache) > 256:
            _glow_text_cache.clear()

        base = font.render(text, True, color[:3])
        bw, bh = base.get_size()
        pad    = glow * 6      # extra pixels for the outermost glow ring
        comp   = pygame.Surface((bw + pad, bh + pad), pygame.SRCALPHA)

        for i in range(glow, 0, -1):
            alpha = max(10, int(65 / i))
            try:
                scaled = pygame.transform.smoothscale(base, (bw + i * 6, bh + i * 6))
                scaled.set_alpha(alpha)
                # Centre each ring inside the composite surface
                ox = (pad - i * 6) // 2
                oy = (pad - i * 6) // 2
                comp.blit(scaled, (ox, oy))
            except Exception:
                pass
        # Blit the sharp base text centred in the composite
        comp.blit(base, (pad // 2, pad // 2))
        _glow_text_cache[key] = comp

    cached     = _glow_text_cache[key]
    cw, ch     = cached.get_size()
    surface.blit(cached, (cx - cw // 2, cy - ch // 2))


def draw_scanlines(surface: pygame.Surface, alpha: int = 14) -> None:
    """
    Overlay CRT-style horizontal scanlines across the full surface.

    The overlay is cached per ``(width, height, alpha)`` — typically one entry
    for the full window and never rebuilt unless the window is resized.
    """
    w, h = surface.get_size()
    key  = (w, h, alpha)

    if key not in _scanline_cache:
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        line    = pygame.Surface((w, 1), pygame.SRCALPHA)
        line.fill((0, 0, 0, alpha))
        for y in range(0, h, 2):
            overlay.blit(line, (0, y))
        _scanline_cache[key] = overlay

    surface.blit(_scanline_cache[key], (0, 0))


# ─── Widgets ──────────────────────────────────────────────────────────────────

class Button:
    """
    A neon-styled clickable button.

    Hover state is tracked via MOUSEMOTION events.  Call ``reset_hover()``
    when leaving a screen to avoid ghost-hover on the next visit.
    """

    def __init__(
        self,
        rect,
        text: str,
        font: pygame.font.Font,
        theme: dict,
    ) -> None:
        self.rect    = pygame.Rect(rect)
        self.text    = text
        self.font    = font
        self.theme   = theme
        self.hovered = False

    def reset_hover(self) -> None:
        """Clear hover state — call each time the parent screen is entered."""
        self.hovered = False

    def handle_event(self, event) -> bool:
        """
        Process a single pygame event.

        Returns ``True`` on a left-mouse-click inside the button rect.
        Does not consume the event.
        """
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        color = self.theme['fg']
        if self.hovered:
            # Filled with neon colour; text in black for contrast
            draw_glow_rect(surface, color, self.rect, glow=8)
            label = self.font.render(self.text, True, (0, 0, 0))
        else:
            # Transparent fill + neon border
            fill = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            fill.fill((*color[:3], 18))
            surface.blit(fill, self.rect.topleft)
            draw_border_rect(surface, color, self.rect, width=2, glow=3)
            label = self.font.render(self.text, True, color[:3])

        lw, lh = label.get_size()
        surface.blit(label, (
            self.rect.centerx - lw // 2,
            self.rect.centery - lh // 2,
        ))


class TextInput:
    """
    Single-line editable text field with a neon aesthetic.

    Activation: click inside the rect.
    Deactivation: click outside, press Enter, or press Tab.
    Characters are forced upper-case.
    """

    def __init__(
        self,
        rect,
        label: str,
        default: str,
        font: pygame.font.Font,
        label_font: pygame.font.Font,
        theme: dict,
        max_len: int = 12,
    ) -> None:
        self.rect       = pygame.Rect(rect)
        self.label      = label
        self.value      = default
        self.font       = font
        self.label_font = label_font
        self.theme      = theme
        self.max_len    = max_len
        self.active     = False

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE):
                self.active = False
            elif len(self.value) < self.max_len and event.unicode.isprintable():
                self.value += event.unicode.upper()

    def draw(self, surface: pygame.Surface) -> None:
        color = self.theme['fg']

        # Label above the box
        lbl = self.label_font.render(self.label, True, color[:3])
        surface.blit(lbl, (self.rect.x, self.rect.y - lbl.get_height() - 5))

        # Box background tint
        fill = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        fill.fill((*color[:3], 22 if self.active else 12))
        surface.blit(fill, self.rect.topleft)

        # Border — glowing when active
        if self.active:
            draw_border_rect(surface, color, self.rect, width=2, glow=4)
        else:
            pygame.draw.rect(surface, color[:3], self.rect, 1)

        # Value text
        val_surf = self.font.render(self.value, True, color[:3])
        vh       = val_surf.get_height()
        surface.blit(val_surf, (self.rect.x + 8, self.rect.centery - vh // 2))

        # Blinking cursor when active (toggles every 500 ms)
        if self.active and (pygame.time.get_ticks() // 500) % 2 == 0:
            cur_x   = self.rect.x + 8 + val_surf.get_width() + 3
            cur_top = self.rect.centery - vh // 2
            pygame.draw.line(surface, color[:3],
                             (cur_x, cur_top), (cur_x, cur_top + vh), 2)


class OptionSelector:
    """
    A left / right arrow option picker — arcade-friendly alternative to a dropdown.

    *options* is a list of ``(value, display_label)`` tuples.
    Read the currently selected value via the ``.value`` property.
    """

    def __init__(
        self,
        rect,
        label: str,
        options: list[tuple],
        font: pygame.font.Font,
        label_font: pygame.font.Font,
        theme: dict,
        default_index: int = 0,
    ) -> None:
        self.rect       = pygame.Rect(rect)
        self.label      = label
        self.options    = options
        self.index      = default_index
        self.font       = font
        self.label_font = label_font
        self.theme      = theme

        aw             = 36     # arrow button width
        self.left_btn  = pygame.Rect(rect[0],                rect[1], aw, rect[3])
        self.right_btn = pygame.Rect(rect[0] + rect[2] - aw, rect[1], aw, rect[3])

    @property
    def value(self):
        """Currently selected option value."""
        return self.options[self.index][0]

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.left_btn.collidepoint(event.pos):
                self.index = (self.index - 1) % len(self.options)
            elif self.right_btn.collidepoint(event.pos):
                self.index = (self.index + 1) % len(self.options)

    def draw(self, surface: pygame.Surface) -> None:
        color = self.theme['fg']

        # Label above
        lbl = self.label_font.render(self.label, True, color[:3])
        surface.blit(lbl, (self.rect.x, self.rect.y - lbl.get_height() - 5))

        # Box tint
        fill = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        fill.fill((*color[:3], 12))
        surface.blit(fill, self.rect.topleft)
        pygame.draw.rect(surface, color[:3], self.rect, 1)

        # Arrow glyphs
        for btn, glyph in ((self.left_btn, '<'), (self.right_btn, '>')):
            arr = self.font.render(glyph, True, color[:3])
            surface.blit(arr, (
                btn.centerx - arr.get_width()  // 2,
                btn.centery - arr.get_height() // 2,
            ))

        # Divider lines between arrows and label area
        pygame.draw.line(surface, color[:3],
                         (self.left_btn.right,  self.rect.top),
                         (self.left_btn.right,  self.rect.bottom), 1)
        pygame.draw.line(surface, color[:3],
                         (self.right_btn.left,  self.rect.top),
                         (self.right_btn.left,  self.rect.bottom), 1)

        # Selected value label
        val_surf = self.font.render(self.options[self.index][1], True, color[:3])
        vw, vh   = val_surf.get_size()
        surface.blit(val_surf, (
            self.rect.centerx - vw // 2,
            self.rect.centery - vh // 2,
        ))
