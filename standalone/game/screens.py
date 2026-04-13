"""
All game screens — menus, configuration forms, and the gameplay canvas.

Each screen exposes four methods:
    on_enter()            – called once when transitioning to this screen
    handle_events(events) – process one frame's worth of pygame events
    update(dt)            – advance game logic (dt = seconds since last frame)
    draw(surface)         – render to the full window surface
"""
from __future__ import annotations

import random
import pygame

from .constants import (
    WINDOW_W, CANVAS_W, CANVAS_H, CANVAS_X, CANVAS_Y,
    PADDLE_W, PADDLE_H, PADDLE_X_OFFSET,
    DIFFICULTIES, SPEEDS, WIN_SCORES,
    STATE_MAIN_MENU, STATE_SETUP_AI, STATE_SETUP_PVP, STATE_THEMES, STATE_PLAYING,
)
from .themes import THEMES, THEME_OPTIONS
from .entities import Ball, Paddle, ParticleSystem
from .ui import (
    get_font,
    draw_glow_rect, draw_border_rect, draw_glow_text, draw_scanlines,
    clear_render_caches,
    Button, TextInput, OptionSelector,
)

__all__ = [
    'MainMenuScreen', 'SetupAIScreen', 'SetupPVPScreen',
    'ThemesScreen', 'GameplayScreen',
]

# Pre-built semi-transparent surfaces reused every frame (avoids allocation)
_FADE_SURF: pygame.Surface | None = None   # canvas motion-blur overlay


def _get_fade_surf() -> pygame.Surface:
    """Return (creating once) the canvas motion-blur overlay surface."""
    global _FADE_SURF
    if _FADE_SURF is None:
        _FADE_SURF = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)
        _FADE_SURF.fill((0, 0, 0, 100))
    return _FADE_SURF


# ─── Base ─────────────────────────────────────────────────────────────────────

class BaseScreen:
    """
    Abstract base for all game screens.

    Subclasses inherit the ``theme`` property and the default ``draw()``
    behaviour (background fill + CRT scanlines).
    """

    def __init__(self, app) -> None:
        self.app = app

    @property
    def theme(self) -> dict:
        """Active colour theme, always read from the App so it stays current."""
        return self.app.theme

    def on_enter(self) -> None:
        """Override to run setup logic each time this screen becomes active."""

    def handle_events(self, events: list) -> None:
        """Override to process pygame events."""

    def update(self, dt: float) -> None:
        """Override to advance frame logic.  *dt* is seconds since last frame."""

    def draw(self, surface: pygame.Surface) -> None:
        """Fill background and draw CRT scanlines — call via ``super()`` first."""
        surface.fill(self.theme['bg'])
        draw_scanlines(surface)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _update_widget_themes(theme: dict, *widgets) -> None:
    """Propagate the current theme dict to a sequence of UI widgets."""
    for w in widgets:
        w.theme = theme


# ─── Main Menu ────────────────────────────────────────────────────────────────

class MainMenuScreen(BaseScreen):
    """Splash screen with VS AI / VS PLAYER / THEMES navigation buttons."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.on_enter()

    def on_enter(self) -> None:
        font     = get_font(13)
        cx       = WINDOW_W // 2
        bw, bh   = 340, 56
        bx       = cx - bw // 2

        self._buttons = [
            Button((bx, 295, bw, bh), 'VS  AI',     font, self.theme),
            Button((bx, 370, bw, bh), 'VS  PLAYER', font, self.theme),
            Button((bx, 445, bw, bh), 'THEMES',     font, self.theme),
        ]
        self._targets = [STATE_SETUP_AI, STATE_SETUP_PVP, STATE_THEMES]

    def handle_events(self, events: list) -> None:
        for event in events:
            for btn, target in zip(self._buttons, self._targets):
                if btn.handle_event(event):
                    self.app.change_state(target)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        cx    = WINDOW_W // 2
        t     = pygame.time.get_ticks() / 1000.0
        color = self.theme['fg']

        # ── Animated title with flicker ──────────────────────────────────────
        # Simulate neon-tube flicker: briefly drop brightness at specific beats
        flicker_on  = (int(t * 10) % 10) not in (2, 3, 5)
        title_font  = get_font(44)
        title_surf  = title_font.render('NEON PONG', True, color)
        title_surf.set_alpha(255 if flicker_on else 185)
        tw, th = title_surf.get_size()

        # Soft glow halos — drawn largest-first (outermost) so they layer correctly
        for g in (10, 6, 3):
            try:
                halo = pygame.transform.smoothscale(title_surf, (tw + g * 8, th + g * 8))
                halo.set_alpha(25)
                surface.blit(halo, (cx - (tw + g * 8) // 2, 135 - g * 4))
            except Exception:
                pass
        surface.blit(title_surf, (cx - tw // 2, 135))

        draw_glow_text(surface, get_font(8), 'ARCADE  EDITION', color, cx, 235, glow=2)

        _update_widget_themes(self.theme, *self._buttons)
        for btn in self._buttons:
            btn.draw(surface)


# ─── Setup AI ─────────────────────────────────────────────────────────────────

class SetupAIScreen(BaseScreen):
    """Configuration form for a single-player vs bot match."""

    # Vertical layout constants
    _FORM_START_Y = 150
    _FORM_GAP     = 85    # pixels between the top of consecutive form rows
    _WIDGET_H     = 50

    def __init__(self, app) -> None:
        super().__init__(app)
        self.on_enter()

    def on_enter(self) -> None:
        cx    = WINDOW_W // 2
        col_x = cx - 190
        col_w = 380
        f10   = get_font(10)
        f8    = get_font(8)
        y     = self._FORM_START_Y
        wh    = self._WIDGET_H

        self._p1_input  = TextInput(
            (col_x, y, col_w, wh), 'P1  NAME', 'PLAYER 1',
            f10, f8, self.theme, max_len=12,
        )
        y += self._FORM_GAP
        self._diff_sel  = OptionSelector(
            (col_x, y, col_w, wh), 'DIFFICULTY', DIFFICULTIES,
            f10, f8, self.theme, default_index=1,
        )
        y += self._FORM_GAP
        self._score_sel = OptionSelector(
            (col_x, y, col_w, wh), 'GOAL  SCORE', WIN_SCORES,
            f10, f8, self.theme, default_index=7,   # default = 10 goals
        )
        y += self._FORM_GAP
        self._speed_sel = OptionSelector(
            (col_x, y, col_w, wh), 'SPEED', SPEEDS,
            f10, f8, self.theme, default_index=1,   # default = Normal
        )
        y += self._FORM_GAP + 10

        half = col_w // 2 - 8
        self._btn_start = Button((col_x,            y, half, 50), 'START', f10, self.theme)
        self._btn_back  = Button((col_x + half + 16, y, half, 50), 'BACK',  f10, self.theme)

    def handle_events(self, events: list) -> None:
        for event in events:
            self._p1_input.handle_event(event)
            self._diff_sel.handle_event(event)
            self._score_sel.handle_event(event)
            self._speed_sel.handle_event(event)

            if self._btn_start.handle_event(event):
                s                  = self.app.settings
                s.mode             = 'bot'
                s.p1_name          = self._p1_input.value.strip() or 'PLAYER 1'
                s.p2_name          = 'BOT ' + self._diff_sel.value.upper()
                s.difficulty       = self._diff_sel.value
                s.win_score        = int(self._score_sel.value)
                s.speed_multiplier = float(self._speed_sel.value)
                self.app.change_state(STATE_PLAYING)

            elif self._btn_back.handle_event(event):
                self.app.change_state(STATE_MAIN_MENU)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        draw_glow_text(surface, get_font(26), 'VS  AI', self.theme['fg'],
                       WINDOW_W // 2, 80, glow=3)
        for widget in (self._p1_input, self._diff_sel,
                       self._score_sel, self._speed_sel,
                       self._btn_start, self._btn_back):
            widget.draw(surface)


# ─── Setup PvP ────────────────────────────────────────────────────────────────

class SetupPVPScreen(BaseScreen):
    """Configuration form for a local two-player match."""

    _FORM_START_Y = 170
    _FORM_GAP     = 85
    _WIDGET_H     = 50

    def __init__(self, app) -> None:
        super().__init__(app)
        self.on_enter()

    def on_enter(self) -> None:
        cx    = WINDOW_W // 2
        col_x = cx - 190
        col_w = 380
        f10   = get_font(10)
        f8    = get_font(8)
        y     = self._FORM_START_Y
        wh    = self._WIDGET_H

        self._p1_input  = TextInput(
            (col_x, y, col_w, wh), 'P1  NAME', 'PLAYER 1',
            f10, f8, self.theme, max_len=12,
        )
        y += self._FORM_GAP
        self._p2_input  = TextInput(
            (col_x, y, col_w, wh), 'P2  NAME', 'PLAYER 2',
            f10, f8, self.theme, max_len=12,
        )
        y += self._FORM_GAP
        self._speed_sel = OptionSelector(
            (col_x, y, col_w, wh), 'SPEED', SPEEDS,
            f10, f8, self.theme, default_index=1,
        )
        y += self._FORM_GAP + 10

        half = col_w // 2 - 8
        self._btn_start = Button((col_x,            y, half, 50), 'START', f10, self.theme)
        self._btn_back  = Button((col_x + half + 16, y, half, 50), 'BACK',  f10, self.theme)

    def handle_events(self, events: list) -> None:
        for event in events:
            self._p1_input.handle_event(event)
            self._p2_input.handle_event(event)
            self._speed_sel.handle_event(event)

            if self._btn_start.handle_event(event):
                s                  = self.app.settings
                s.mode             = 'pvp'
                s.p1_name          = self._p1_input.value.strip() or 'PLAYER 1'
                s.p2_name          = self._p2_input.value.strip() or 'PLAYER 2'
                s.win_score        = 10
                s.speed_multiplier = float(self._speed_sel.value)
                self.app.change_state(STATE_PLAYING)

            elif self._btn_back.handle_event(event):
                self.app.change_state(STATE_MAIN_MENU)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        draw_glow_text(surface, get_font(26), 'VS  PLAYER', self.theme['fg'],
                       WINDOW_W // 2, 80, glow=3)
        for widget in (self._p1_input, self._p2_input,
                       self._speed_sel, self._btn_start, self._btn_back):
            widget.draw(surface)


# ─── Themes ───────────────────────────────────────────────────────────────────

class ThemesScreen(BaseScreen):
    """Live theme-selector screen with a colour-preview swatch."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self.on_enter()

    def on_enter(self) -> None:
        cx  = WINDOW_W // 2
        f10 = get_font(10)
        f8  = get_font(8)
        # Start with the selector pointing at the currently active theme
        try:
            current_idx = [k for k, _ in THEME_OPTIONS].index(
                next(k for k, v in THEMES.items() if v is self.theme)
            )
        except (StopIteration, ValueError):
            current_idx = 0

        self._sel      = OptionSelector(
            (cx - 200, 280, 400, 56), 'THEME', THEME_OPTIONS,
            f10, f8, self.theme, default_index=current_idx,
        )
        self._btn_back = Button((cx - 110, 390, 220, 52), 'BACK', f10, self.theme)

    def handle_events(self, events: list) -> None:
        prev_key = self._sel.value
        for event in events:
            self._sel.handle_event(event)
            if self._btn_back.handle_event(event):
                self.app.change_state(STATE_MAIN_MENU)

        # Apply theme only when selection actually changed
        new_key = self._sel.value
        if new_key != prev_key:
            self.app.theme = THEMES[new_key]
            clear_render_caches()    # flush old-colour glow surfaces
            # Sync widgets to new theme
            _update_widget_themes(self.theme, self._sel, self._btn_back)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        color = self.theme['fg']
        draw_glow_text(surface, get_font(28), 'THEMES', color, WINDOW_W // 2, 120, glow=3)

        # Live colour-preview swatch
        preview = THEMES[self._sel.value]['fg']
        sw_rect = pygame.Rect(WINDOW_W // 2 - 100, 360, 200, 28)
        swatch  = pygame.Surface(sw_rect.size, pygame.SRCALPHA)
        swatch.fill((*preview, 40))
        surface.blit(swatch, sw_rect.topleft)
        draw_border_rect(surface, preview, sw_rect, glow=4)

        self._sel.draw(surface)
        self._btn_back.draw(surface)


# ─── Gameplay ─────────────────────────────────────────────────────────────────

class GameplayScreen(BaseScreen):
    """
    Main gameplay screen.

    Internal coordinates are all in canvas-space (0 … CANVAS_W, 0 … CANVAS_H).
    The ``_cx`` / ``_cy`` offsets (with optional screen-shake jitter) are
    applied at draw time to translate to window-space.
    """

    # Quit button rect — positioned in the header area, fixed regardless of shake
    _QUIT_RECT = pygame.Rect(CANVAS_X + CANVAS_W - 110, CANVAS_Y - 68, 100, 40)

    def __init__(self, app) -> None:
        super().__init__(app)

        # Game entities (persist across matches; reset in on_enter)
        self.p1        = Paddle(float(PADDLE_X_OFFSET))
        self.p2        = Paddle(float(CANVAS_W - PADDLE_X_OFFSET - PADDLE_W))
        self.ball      = Ball()
        self.particles = ParticleSystem()

        # Keyboard state — four named booleans instead of a nested dict
        self._p1_up   = False
        self._p1_down = False
        self._p2_up   = False
        self._p2_down = False

        # Match state
        self._game_over       = False
        self._winner_text     = ''
        self._game_over_timer = 0.0
        self._screen_shake    = 0.0

        # Quit button (created once, theme updated before each draw)
        self._quit_btn = Button(self._QUIT_RECT, 'QUIT', get_font(8), self.theme)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self) -> None:
        """Reset all match state and initialise entities from GameSettings."""
        s = self.app.settings

        for pad, name in ((self.p1, s.p1_name), (self.p2, s.p2_name)):
            pad.name  = name
            pad.score = 0
            pad.reset_pos()

        self.particles.clear()
        self.ball.reset(s.speed_multiplier)

        self._game_over       = False
        self._winner_text     = ''
        self._game_over_timer = 0.0
        self._screen_shake    = 0.0

        # Clear all key flags to prevent "sticky" keys across screen transitions
        self._p1_up = self._p1_down = self._p2_up = self._p2_down = False

        # Reset quit-button hover so the button does not appear pre-hovered
        self._quit_btn.reset_hover()

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_events(self, events: list) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:     self._p1_up   = True
                if event.key == pygame.K_s:     self._p1_down = True
                if event.key == pygame.K_UP:    self._p2_up   = True
                if event.key == pygame.K_DOWN:  self._p2_down = True

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_w:     self._p1_up   = False
                if event.key == pygame.K_s:     self._p1_down = False
                if event.key == pygame.K_UP:    self._p2_up   = False
                if event.key == pygame.K_DOWN:  self._p2_down = False

            # Quit button — handle_event returns True on left-click inside rect
            if self._quit_btn.handle_event(event):
                self.app.change_state(STATE_MAIN_MENU)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._game_over:
            self._game_over_timer -= dt
            if self._game_over_timer <= 0.0:
                self.app.change_state(STATE_MAIN_MENU)
            return

        s = self.app.settings
        b, p1, p2 = self.ball, self.p1, self.p2

        # ── Paddle movement ───────────────────────────────────────────────────
        p1.apply_input(self._p1_up, self._p1_down, s.speed_multiplier)
        if s.mode == 'pvp':
            p2.apply_input(self._p2_up, self._p2_down, s.speed_multiplier)
        else:
            p2.ai_move(b, s.difficulty, s.speed_multiplier)

        # ── Ball movement ─────────────────────────────────────────────────────
        b.update()

        # ── Wall collisions (top / bottom) ────────────────────────────────────
        if b.y <= 0 or b.y + b.size >= CANVAS_H:
            b.bounce_wall()
            b.y = max(0.0, min(float(CANVAS_H - b.size), b.y))
            self.particles.emit(b.x, b.y, wall_hit=True)
            self.app.audio.play('wall')
            self._screen_shake = 3.0

        # ── Paddle collisions ─────────────────────────────────────────────────
        # P1 (left paddle): ball approaches from right (vx < 0)
        if (b.x <= p1.x + PADDLE_W
                and b.y + b.size >= p1.y
                and b.y <= p1.y + PADDLE_H
                and b.vx < 0):
            b.x = p1.x + PADDLE_W          # push ball outside paddle face
            b.bounce_paddle(p1, going_right=True)
            self.particles.emit(b.x, b.y)
            self.app.audio.play('hit')
            self._screen_shake = 5.0

        # P2 (right paddle): ball approaches from left (vx > 0)
        elif (b.x + b.size >= p2.x
                and b.y + b.size >= p2.y
                and b.y <= p2.y + PADDLE_H
                and b.vx > 0):
            b.x = p2.x - b.size            # push ball outside paddle face
            b.bounce_paddle(p2, going_right=False)
            self.particles.emit(b.x, b.y)
            self.app.audio.play('hit')
            self._screen_shake = 5.0

        # ── Scoring ───────────────────────────────────────────────────────────
        # Use elif so the same ball can't trigger both scoring events in one frame.
        if b.x < -20:
            p2.score += 1
            self._screen_shake = 15.0
            self._check_win()
            if not self._game_over:
                b.reset(s.speed_multiplier)
                self.app.audio.play('score')

        elif b.x > CANVAS_W + 20:
            p1.score += 1
            self._screen_shake = 15.0
            self._check_win()
            if not self._game_over:
                b.reset(s.speed_multiplier)
                self.app.audio.play('score')

        # ── Particles & screen-shake decay ────────────────────────────────────
        self.particles.update()
        self._screen_shake *= 0.85
        if self._screen_shake < 0.5:
            self._screen_shake = 0.0

    def _check_win(self) -> None:
        """End the match if either player has reached the win score."""
        ws = self.app.settings.win_score
        if self.p1.score >= ws:
            self._end_game(f'{self.p1.name}  WINS!')
        elif self.p2.score >= ws:
            self._end_game(f'{self.p2.name}  WINS!')

    def _end_game(self, text: str) -> None:
        self._game_over       = True
        self._winner_text     = text
        self._game_over_timer = 3.0

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        color = self.theme['fg']

        # Window background + CRT overlay
        surface.fill(self.theme['bg'])
        draw_scanlines(surface)

        self._draw_header(surface, color)

        # Apply screen-shake jitter to the canvas offset
        shake  = int(self._screen_shake)
        cx_off = CANVAS_X + (random.randint(-shake, shake) if shake else 0)
        cy_off = CANVAS_Y + (random.randint(-shake, shake) if shake else 0)

        self._draw_canvas(surface, color, cx_off, cy_off)

        if self._game_over:
            self._draw_game_over(surface, color, cx_off, cy_off)

    # ── Private draw helpers ──────────────────────────────────────────────────

    def _draw_header(self, surface: pygame.Surface, color: tuple) -> None:
        """Render the glassmorphism header panel above the canvas."""
        hx, hy, hw, hh = CANVAS_X, CANVAS_Y - 80, CANVAS_W, 70

        # Translucent tinted background
        fill = pygame.Surface((hw, hh), pygame.SRCALPHA)
        fill.fill((*color[:3], 12))
        surface.blit(fill, (hx, hy))
        draw_border_rect(surface, color, (hx, hy, hw, hh), width=1, glow=2)

        draw_glow_text(surface, get_font(13), 'NEON PONG', color,
                       CANVAS_X + CANVAS_W // 2, hy + hh // 2, glow=2)

        # Controls hint — dimmed
        hint = get_font(7).render('W/S  ←  P1       P2  →  UP/DOWN', True, color[:3])
        hint.set_alpha(100)
        surface.blit(hint, (hx + 10, hy + hh - 20))

        # Quit button — always uses the current theme
        self._quit_btn.theme = self.theme
        self._quit_btn.draw(surface)

    def _draw_canvas(
        self,
        surface: pygame.Surface,
        color: tuple,
        cx_off: int,
        cy_off: int,
    ) -> None:
        """Render the full gameplay canvas at the (possibly shaken) offset."""
        b  = self.ball
        s  = self.app.settings

        # Black canvas fill + neon border
        surface.fill((0, 0, 0), (cx_off, cy_off, CANVAS_W, CANVAS_H))
        draw_border_rect(surface, color, (cx_off, cy_off, CANVAS_W, CANVAS_H),
                         width=2, glow=3)

        # Motion-blur overlay (pre-built surface — no allocation per frame)
        surface.blit(_get_fade_surf(), (cx_off, cy_off))

        # Centre dashed divider
        dash  = pygame.Surface((2, 15), pygame.SRCALPHA)
        dash.fill((*color[:3], 50))
        for i in range(0, CANVAS_H, 30):
            surface.blit(dash, (cx_off + CANVAS_W // 2 - 1, cy_off + i))

        # Ball motion trail — draw from oldest (dimmest) to newest (brightest)
        trail_len = max(len(b.trail), 1)
        for idx, (tx, ty) in enumerate(b.trail):
            brightness = idx / trail_len         # 0.0 = oldest, ~1.0 = newest
            col        = tuple(int(c * brightness) for c in color[:3])
            pygame.draw.rect(surface, col,
                             (cx_off + int(tx), cy_off + int(ty), b.size, b.size))

        # Particles
        self.particles.draw(surface, color, cx_off, cy_off)

        # Paddles
        draw_glow_rect(surface, color,
                       (cx_off + int(self.p1.x), cy_off + int(self.p1.y), PADDLE_W, PADDLE_H),
                       glow=5)
        draw_glow_rect(surface, color,
                       (cx_off + int(self.p2.x), cy_off + int(self.p2.y), PADDLE_W, PADDLE_H),
                       glow=5)

        # Ball
        draw_glow_rect(surface, color,
                       (cx_off + int(b.x), cy_off + int(b.y), b.size, b.size),
                       glow=8)

        # Score digits
        sf = get_font(36)
        draw_glow_text(surface, sf, str(self.p1.score), color,
                       cx_off + CANVAS_W // 4,     cy_off + 65, glow=3)
        draw_glow_text(surface, sf, str(self.p2.score), color,
                       cx_off + 3 * CANVAS_W // 4, cy_off + 65, glow=3)

        # Player names
        nf = get_font(9)
        draw_glow_text(surface, nf, self.p1.name, color,
                       cx_off + CANVAS_W // 4,     cy_off + 22, glow=1)
        draw_glow_text(surface, nf, self.p2.name, color,
                       cx_off + 3 * CANVAS_W // 4, cy_off + 22, glow=1)

        # Target score
        draw_glow_text(surface, get_font(8), f'TARGET: {s.win_score}', color,
                       cx_off + CANVAS_W // 2, cy_off + 22, glow=1)

    def _draw_game_over(
        self,
        surface: pygame.Surface,
        color: tuple,
        cx_off: int,
        cy_off: int,
    ) -> None:
        """Render the translucent victory overlay on top of the canvas."""
        ov = pygame.Surface((CANVAS_W, CANVAS_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        surface.blit(ov, (cx_off, cy_off))

        mid_x = cx_off + CANVAS_W // 2
        mid_y = cy_off + CANVAS_H // 2

        draw_glow_text(surface, get_font(34), self._winner_text, color,
                       mid_x, mid_y - 30, glow=5)
        draw_glow_text(surface, get_font(9), 'RETURNING TO MENU...', color,
                       mid_x, mid_y + 42, glow=2)
