#!/usr/bin/env python3
"""
NEON PONG — Standalone Desktop Application
==========================================

Run:
    py -3.14 main.py          (Windows with multiple Python versions)
    python  main.py           (single-Python environments)

Requirements:
    pip install pygame-ce      # community-edition pygame; Python ≥ 3.12 wheels
"""
import logging
import sys
import pygame


def _configure_logging() -> None:
    """Set up basic console logging (INFO level by default)."""
    logging.basicConfig(
        format='%(levelname)s [%(name)s] %(message)s',
        level=logging.INFO,
    )


def main() -> None:
    _configure_logging()
    log = logging.getLogger('neon_pong')

    # ── Initialise pygame ────────────────────────────────────────────────────
    try:
        pygame.init()
    except Exception as exc:
        log.critical('pygame.init() failed: %s', exc)
        sys.exit(1)

    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    except pygame.error as exc:
        # Audio failure is non-fatal — the SoundManager will disable itself
        log.warning('Audio initialisation failed (%s).  Running without sound.', exc)

    pygame.display.set_caption('NEON PONG')

    # ── Run the game ─────────────────────────────────────────────────────────
    # Deferred import so pygame is fully initialised before we import modules
    # that reference pygame constants at class-definition time (e.g. K_w).
    try:
        from game.app import App
        App().run()
    except Exception as exc:
        log.critical('Fatal error: %s', exc, exc_info=True)
        sys.exit(1)
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
