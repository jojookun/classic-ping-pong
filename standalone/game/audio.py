"""
Audio synthesis engine — zero external files, zero external dependencies.

Sounds are generated entirely at startup using Python's built-in ``array``
module and signed-16-bit PCM maths, then stored as :class:`pygame.mixer.Sound`
objects.  The game works offline and in environments where audio files are
not bundled.

Sound catalogue
---------------
``hit``   — high-pitched chirp on paddle contact (square wave, swept up)
``wall``  — soft thud on wall bounce (sine, steady)
``score`` — descending blip on a point scored (sawtooth, swept down)
"""
from __future__ import annotations

import array
import logging
import math

import pygame

log = logging.getLogger(__name__)

__all__ = ['SoundManager']


class SoundManager:
    """
    Synthesise and cache retro beep sound effects.

    Usage::

        audio = SoundManager()
        audio.play('hit')
        audio.set_volume(0.5)   # 50 % — affects all future play() calls
        audio.toggle_mute()     # silence / un-silence without losing volume

    When ``enabled`` is ``False`` (set automatically on initialisation failure),
    all public methods become no-ops so callers need no guard logic.
    """

    _SAMPLE_RATE: int = 44100   # Hz — must match pygame.mixer.init frequency

    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._volume: float = 0.08    # master volume (0.0 – 1.0 range)
        self._muted:  bool  = False
        self.enabled: bool  = True
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def play(self, name: str) -> None:
        """Play a sound by name.  Silently ignored when muted or disabled."""
        if self.enabled and not self._muted and name in self._sounds:
            self._sounds[name].play()

    def set_volume(self, volume: float) -> None:
        """
        Set master volume for all sounds.

        Parameters
        ----------
        volume:
            Float in the range 0.0 (silent) … 1.0 (maximum).
            Values outside this range are clamped.
        """
        self._volume = max(0.0, min(1.0, volume))
        for snd in self._sounds.values():
            snd.set_volume(self._volume)

    def toggle_mute(self) -> bool:
        """
        Toggle mute state.

        Returns the new muted state (``True`` = muted, ``False`` = unmuted).
        """
        self._muted = not self._muted
        log.debug('Audio %s.', 'muted' if self._muted else 'unmuted')
        return self._muted

    @property
    def volume(self) -> float:
        """Current master volume (0.0 – 1.0)."""
        return self._volume

    @property
    def muted(self) -> bool:
        """``True`` when audio is muted without losing the volume value."""
        return self._muted

    # ── Sound synthesis ───────────────────────────────────────────────────────

    def _make(
        self,
        freq1: float,
        freq2: float,
        duration: float,
        wave: str = 'square',
    ) -> pygame.mixer.Sound:
        """
        Synthesise a single sound swept from *freq1* Hz to *freq2* Hz.

        Parameters
        ----------
        freq1, freq2:
            Start and end frequencies in Hz.  Set equal for a fixed pitch.
        duration:
            Length of the sound in seconds.
        wave:
            Waveform shape — ``'square'``, ``'saw'``, or ``'sine'``.

        Returns
        -------
        pygame.mixer.Sound
            A ready-to-play Sound object encoded as signed 16-bit stereo PCM
            at :attr:`_SAMPLE_RATE` Hz, matching ``pygame.mixer.init`` defaults.
        """
        rate = self._SAMPLE_RATE
        n    = int(rate * duration)
        buf  = array.array('h', [0] * n * 2)   # stereo: 2 int16 per frame

        for i in range(n):
            t    = i / rate
            freq = freq1 + (freq2 - freq1) * (i / n)   # linear frequency sweep

            if wave == 'square':
                v = 1.0 if math.sin(2.0 * math.pi * freq * t) >= 0 else -1.0
            elif wave == 'saw':
                v = 2.0 * ((freq * t) % 1.0) - 1.0
            else:   # sine (default fallback)
                v = math.sin(2.0 * math.pi * freq * t)

            env = 1.0 - (i / n)               # linear decay envelope (pop-free)
            val = int(v * env * self._volume * 32767)
            val = max(-32768, min(32767, val))
            buf[i * 2]     = val              # left channel
            buf[i * 2 + 1] = val              # right channel (identical → mono)

        return pygame.mixer.Sound(buffer=buf)

    def _load(self) -> None:
        """
        Build and cache all game sounds.

        On failure (e.g. mixer not initialised) sets ``self.enabled = False``
        so the rest of the game continues without audio.
        """
        try:
            self._sounds['hit']   = self._make(440, 880, 0.10, wave='square')
            self._sounds['wall']  = self._make(200, 200, 0.10, wave='sine')
            self._sounds['score'] = self._make(220, 110, 0.30, wave='saw')
            log.debug('Audio: %d sounds synthesised at %d Hz.',
                      len(self._sounds), self._SAMPLE_RATE)
        except Exception as exc:
            log.warning('Audio initialisation failed (%s).  Running muted.', exc)
            self.enabled = False
