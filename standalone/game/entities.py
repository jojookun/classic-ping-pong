"""
Game entities — Ball, Paddle, Particle, ParticleSystem.

All coordinates are in canvas-space (0 .. CANVAS_W, 0 .. CANVAS_H).
The renderer applies the canvas window offset before drawing.
"""
from __future__ import annotations

import math
import random

import pygame

from .constants import (
    CANVAS_W, CANVAS_H,
    PADDLE_H, PADDLE_W,
    PADDLE_ACCEL, PADDLE_FRICTION, PADDLE_MAX_SPEED,
    BALL_SIZE, BALL_BASE_SPEED, MAX_BALL_SPEED, MAX_BOUNCE_ANGLE, MIN_BALL_VX,
    PADDLE_X_OFFSET,
    BOT_SPEEDS,
)

__all__ = ['Ball', 'Paddle', 'ParticleSystem']


# ─── Ball ─────────────────────────────────────────────────────────────────────

class Ball:
    """The pong ball — position, velocity, trail history, and collision responses."""

    def __init__(self) -> None:
        self.size: int   = BALL_SIZE
        self.x:   float = CANVAS_W / 2
        self.y:   float = CANVAS_H / 2
        self.vx:  float = 0.0
        self.vy:  float = 0.0
        # Ring-buffer of (x, y) positions used to draw the motion trail
        self.trail: list[tuple[float, float]] = []

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def reset(self, speed_mult: float = 1.0) -> None:
        """
        Recentre the ball and launch it in a random diagonal direction.

        *speed_mult* scales the base speed (1.0 = normal, 2.0 = Hyper mode).
        """
        self.x    = CANVAS_W / 2
        self.y    = CANVAS_H / 2
        self.vx   = BALL_BASE_SPEED * speed_mult * random.choice((-1, 1))
        self.vy   = BALL_BASE_SPEED * speed_mult * random.choice((-1, 1))
        self.trail = []

    def update(self) -> None:
        """Advance position by one frame and append the current position to the trail."""
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy

    # ── Collision responses ───────────────────────────────────────────────────

    def bounce_wall(self) -> None:
        """
        Bounce off a top/bottom wall.

        Reverses the Y component and applies a 5 % uniform speedup.
        Speed is clamped to MAX_BALL_SPEED afterwards.
        """
        self.vy *= -1.05
        self.vx *=  1.05
        self._clamp_speed()

    def bounce_paddle(self, paddle: Paddle, going_right: bool) -> None:
        """
        Deflect off a paddle using normalised hit-position angle maths.

        The hit position on the paddle controls the outgoing angle
        (± MAX_BOUNCE_ANGLE).  Paddle spin is added as a small bias.

        Parameters
        ----------
        paddle:
            The paddle that was struck.
        going_right:
            ``True``  → ball leaves toward the right (P1 just hit it).
            ``False`` → ball leaves toward the left  (P2 just hit it).
        """
        # Apply 8 % speedup by stretching the current velocity magnitude
        self.vx *= -1.08

        # Normalise the hit position on the paddle face (-1 … +1)
        intersect  = (self.y + self.size / 2) - (paddle.y + PADDLE_H / 2)
        normalised = max(-1.0, min(1.0, intersect / (PADDLE_H / 2)))
        angle      = normalised * MAX_BOUNCE_ANGLE
        angle     += paddle.vy * 0.02    # spin transfer from moving paddle

        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        self.vx = ( abs(speed * math.cos(angle)) if going_right
                    else -abs(speed * math.cos(angle)) )
        self.vy = speed * math.sin(angle)

        # Guard: prevent a near-vertical trajectory that loops indefinitely
        if abs(self.vx) < MIN_BALL_VX:
            self.vx = math.copysign(MIN_BALL_VX, self.vx)

        self._clamp_speed()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _clamp_speed(self) -> None:
        """Scale velocity down if its magnitude exceeds MAX_BALL_SPEED."""
        spd = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if spd > MAX_BALL_SPEED:
            f     = MAX_BALL_SPEED / spd
            self.vx *= f
            self.vy *= f


# ─── Paddle ───────────────────────────────────────────────────────────────────

class Paddle:
    """A player-controlled or AI-controlled paddle."""

    def __init__(self, x: float) -> None:
        self.x:     float = x
        self.y:     float = CANVAS_H / 2 - PADDLE_H / 2
        self.vy:    float = 0.0
        self.score: int   = 0
        self.name:  str   = 'PLAYER'

    def reset_pos(self) -> None:
        """Return paddle to the vertical centre of the canvas."""
        self.y  = CANVAS_H / 2 - PADDLE_H / 2
        self.vy = 0.0

    # ── Human input ──────────────────────────────────────────────────────────

    def apply_input(self, up: bool, down: bool, speed_mult: float) -> None:
        """
        Accelerate the paddle based on keyboard state.

        Uses an acceleration/deceleration (inertia) model for a smoother feel
        than simple position-step movement.
        """
        accel = PADDLE_ACCEL     * speed_mult
        max_v = PADDLE_MAX_SPEED * speed_mult

        if up:
            self.vy -= accel
        if down:
            self.vy += accel

        self.vy  = self.vy * PADDLE_FRICTION           # friction / deceleration
        self.vy  = max(-max_v, min(max_v, self.vy))    # hard velocity cap
        self.y  += self.vy
        self._clamp()

    # ── AI ───────────────────────────────────────────────────────────────────

    def ai_move(self, ball: Ball, difficulty: str, speed_mult: float) -> None:
        """
        Move the AI paddle toward a difficulty-appropriate target position.

        Difficulty behaviours
        ---------------------
        easy / medium / hard
            Only begin tracking once the ball crosses a threshold fraction of
            the canvas; drifts back to centre when the ball moves away.
        insane
            Uses linear trajectory prediction when the ball approaches;
            drifts to centre when the ball moves away.
        extreme
            Perfectly predicts trajectory in both directions — always tracks.
        """
        bot_max  = BOT_SPEEDS[difficulty] * speed_mult
        # Default target: centre the paddle on the ball
        target_y = ball.y - PADDLE_H / 2

        if difficulty in ('insane', 'extreme') and ball.vx > 0:
            # Predictive targeting: extrapolate where the ball will arrive
            time_to = (self.x - ball.x) / ball.vx
            pred    = ball.y + ball.vy * time_to
            # Reflect prediction for wall bounces (up to 5 bounces)
            for _ in range(5):
                if 0 <= pred <= CANVAS_H - PADDLE_H:
                    break
                if pred < 0:
                    pred = -pred
                elif pred > CANVAS_H - PADDLE_H:
                    pred = 2 * (CANVAS_H - PADDLE_H) - pred
            target_y = pred

        elif ball.vx < 0 and difficulty != 'extreme':
            # Ball is moving away — drift to centre (except extreme always tracks)
            target_y = CANVAS_H / 2 - PADDLE_H / 2

        elif difficulty not in ('insane', 'extreme'):
            # Delayed reaction: only start tracking after a threshold distance
            thresholds = {'easy': 0.70, 'medium': 0.55, 'hard': 0.35}
            thresh     = thresholds.get(difficulty, 0.5)
            if ball.x / CANVAS_W <= thresh:
                target_y = CANVAS_H / 2 - PADDLE_H / 2   # still lazy

        # Step toward target at bot_max speed
        diff = target_y - self.y
        if abs(diff) <= bot_max:
            self.y  = target_y
            self.vy = 0.0
        else:
            step    = math.copysign(bot_max, diff)
            self.y += step
            self.vy = step
        self._clamp()

    # ── Internal ─────────────────────────────────────────────────────────────

    def _clamp(self) -> None:
        """Keep the paddle within the canvas bounds and zero velocity at walls."""
        if self.y < 0:
            self.y  = 0.0
            self.vy = 0.0
        elif self.y > CANVAS_H - PADDLE_H:
            self.y  = float(CANVAS_H - PADDLE_H)
            self.vy = 0.0


# ─── Particles ────────────────────────────────────────────────────────────────

class Particle:
    """A single short-lived spark emitted on ball collisions."""

    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'size')

    def __init__(self, x: float, y: float, wall_hit: bool = False) -> None:
        scale      = 0.5 if wall_hit else 1.0
        self.x     = x
        self.y     = y
        self.vx    = (random.random() - 0.5) * 10 * scale
        self.vy    = (random.random() - 0.5) * 10 * scale
        self.life  = 1.0
        self.size  = random.uniform(2.0, 6.0)

    def update(self) -> bool:
        """
        Advance the particle by one frame.

        Returns ``False`` when the particle has faded out and should be removed.
        """
        self.x    += self.vx
        self.y    += self.vy
        self.life -= 0.03
        return self.life > 0.0


class ParticleSystem:
    """
    Pool manager for :class:`Particle` objects.

    Drawing uses brightness-fade rather than per-particle alpha surfaces,
    which avoids Surface allocation in the hot render path.
    """

    def __init__(self) -> None:
        self._pool: list[Particle] = []

    def emit(self, x: float, y: float, wall_hit: bool = False) -> None:
        """Spawn a burst of particles at canvas position *(x, y)*."""
        count = 5 if wall_hit else 15
        for _ in range(count):
            self._pool.append(Particle(x, y, wall_hit))

    def update(self) -> None:
        """Advance all particles and remove expired ones."""
        self._pool = [p for p in self._pool if p.update()]

    def draw(
        self,
        surface: pygame.Surface,
        color: tuple,
        offset_x: int,
        offset_y: int,
    ) -> None:
        """
        Render all live particles.

        Particles fade by *brightness* (not alpha) so no Surface allocation
        is needed per particle per frame — just direct ``draw.rect`` calls.
        """
        r, g, b = color[0], color[1], color[2]
        for p in self._pool:
            if p.life <= 0.0:
                continue
            f   = p.life              # 1.0 → bright, 0.0 → black (invisible)
            col = (int(r * f), int(g * f), int(b * f))
            sz  = max(1, int(p.size))
            pygame.draw.rect(
                surface, col,
                (offset_x + int(p.x), offset_y + int(p.y), sz, sz),
            )

    def clear(self) -> None:
        """Remove all particles instantly."""
        self._pool.clear()
