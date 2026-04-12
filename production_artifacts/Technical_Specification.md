Technical Specification: Retro Ping Pong
1. Executive Summary
A web-based, classic arcade-style Ping Pong game. It features a nostalgic CRT-inspired monochrome aesthetic but is powered by modern JavaScript. The game supports both local 2-Player (PvP) and 1-Player vs Bot (PvE) modes, featuring dynamic game speeds and a highly scalable bot AI ranging from "Easy" to "Extreme".

2. Requirements
Game Modes: Player vs Player (Local Keyboard) and Player vs Bot.

Bot Difficulties:

Easy: Sluggish reaction, caps out at a low speed.

Medium: Fair reaction time, decent speed.

Hard: Fast tracking, rarely misses basic shots.

Insane: Predicts ball trajectory, moves faster than the base ball speed.

Extreme: Instantaneous tracking, mathematically perfect deflections.

Speed Settings: Adjustable overall game speed (0.5x, 1.0x, 1.5x, 2.0x) affecting both ball and paddle velocities.

Controls:

Player 1: W (Up), S (Down)

Player 2: Arrow Up (Up), Arrow Down (Down)

3. Architecture & Tech Stack
Frontend: HTML5 Canvas API (for high-performance 2D rendering).

Logic: Vanilla JavaScript (ES6+). No external libraries required to keep the bundle lightweight and strictly classic.

Styling: Vanilla CSS3 with retro-arcade UI elements (monospace fonts, high contrast black-and-white theme).

4. State Management
The game loop will run via requestAnimationFrame. State variables (Ball X/Y, Paddle Y coordinates, Scores, and Settings) will be mutated globally within the game.js closure to ensure real-time rendering and collision detection accuracy.