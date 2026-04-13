"""
Application core — window, clock, theme, audio, and the screen state machine.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import pygame

from .constants import (
    WINDOW_W, WINDOW_H, FPS,
    STATE_MAIN_MENU, STATE_SETUP_AI, STATE_SETUP_PVP, STATE_THEMES, STATE_PLAYING,
    DIFFICULTIES, SPEEDS, WIN_SCORES,
)
from .themes import THEMES, DEFAULT_THEME
from .audio import SoundManager
from .screens import (
    MainMenuScreen, SetupAIScreen, SetupPVPScreen, ThemesScreen, GameplayScreen,
)

log = logging.getLogger(__name__)


# ─── Settings ─────────────────────────────────────────────────────────────────

@dataclass
class GameSettings:
    """
    Parameters chosen on the setup screens.

    ``GameplayScreen.on_enter()`` reads these at the start of each match, so
    changing them after that point has no effect on the ongoing game.
    """
    mode:             str   = 'bot'      # 'bot' | 'pvp'
    difficulty:       str   = 'medium'   # key into BOT_SPEEDS
    speed_multiplier: float = 1.0        # applied to ball and paddle speeds
    win_score:        int   = 10         # first to this score wins
    p1_name:          str   = 'PLAYER 1'
    p2_name:          str   = 'PLAYER 2'

    def __post_init__(self) -> None:
        valid_modes  = ('bot', 'pvp')
        valid_diffs  = tuple(k for k, _ in DIFFICULTIES)
        valid_speeds = tuple(v for v, _ in SPEEDS)
        valid_scores = tuple(v for v, _ in WIN_SCORES)

        if self.mode not in valid_modes:
            log.warning('Invalid mode %r — resetting to "bot".', self.mode)
            self.mode = 'bot'

        if self.difficulty not in valid_diffs:
            log.warning('Invalid difficulty %r — resetting to "medium".', self.difficulty)
            self.difficulty = 'medium'

        if self.speed_multiplier not in valid_speeds:
            log.warning('Invalid speed %s — resetting to 1.0.', self.speed_multiplier)
            self.speed_multiplier = 1.0

        if self.win_score not in valid_scores:
            log.warning('Invalid win_score %d — clamping.', self.win_score)
            self.win_score = max(min(self.win_score, valid_scores[-1]),
                                 valid_scores[0])


# ─── App ──────────────────────────────────────────────────────────────────────

class App:
    """
    Top-level application object.

    Owns the pygame display, clock, global audio engine, active theme, and the
    screen state machine.  Screens communicate up via ``self.app.change_state()``.
    """

    def __init__(self) -> None:
        self.screen   = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock    = pygame.time.Clock()
        self.theme    = THEMES[DEFAULT_THEME]     # active colour theme
        self.audio    = SoundManager()
        self.settings = GameSettings()
        self._state   = STATE_MAIN_MENU

        # All screens are instantiated once; on_enter() is called on every visit
        # Keys are STATE_* string constants; values satisfy the BaseScreen interface.
        self._screens: dict[str, object] = {
            STATE_MAIN_MENU: MainMenuScreen(self),
            STATE_SETUP_AI:  SetupAIScreen(self),
            STATE_SETUP_PVP: SetupPVPScreen(self),
            STATE_THEMES:    ThemesScreen(self),
            STATE_PLAYING:   GameplayScreen(self),
        }

    def change_state(self, state: str) -> None:
        """
        Transition to *state*.

        Calls ``on_enter()`` on the target screen so it can reset its own state.
        """
        if state not in self._screens:
            log.error('Unknown state %r — ignoring transition.', state)
            return
        log.debug('State: %s → %s', self._state, state)
        self._state = state
        self._screens[state].on_enter()

    def run(self) -> None:
        """
        Main game loop.

        Runs at *FPS* frames per second until the window is closed or ESC is
        pressed on the main menu.
        """
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0   # seconds since last frame

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

                # ESC: quit the game → go back to main menu; on main menu → exit
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self._state == STATE_PLAYING:
                        self.change_state(STATE_MAIN_MENU)
                    else:
                        running = False

            current = self._screens.get(self._state)
            if current:
                current.handle_events(events)
                current.update(dt)
                current.draw(self.screen)

            pygame.display.flip()

