# 2D-Flappy-Birds
Flappy Bird 2D (Python / Pygame)

A 2D Flappy Bird clone implemented in Python using Pygame, adhering to all foundational game development constraints.

Features & Core Mechanics

Player Physics (Pure Kinematics)

No external physics engines used.
Gravity updates velocity each frame: velocity += GRAVITY.
Velocity updates vertical position: y += velocity.
Terminal falling velocity cap prevents runaway acceleration.
Flap/Jump impulse via SPACE, UP ARROW, or LEFT MOUSE CLICK applies an instantaneous negative vertical velocity.

Procedural Obstacles & Movement

Vertical pipe pairs generated programmatically with a randomized playable gap.
Smooth horizontal movement from right to left (PIPE_SPEED).
Automatically pruned once completely off-screen.

Collision Detection

Precise bounding-box (AABB) intersection check against top and bottom pipes.
Instant boundary collision triggers for:
Touching ground boundary (y + radius >= GROUND_Y).
Exceeding top ceiling boundary (y <= 0).

Scoring System

Detects when the player's horizontal position crosses the right edge of a pipe pair.
Increments score by +1 once per pair.
Tracks session high score.

State Management

START: Displays title, controls, game tips, and an idle floating bird.
PLAYING: Active gameplay with moving pipes, physics, and real-time score counter.
GAME_OVER: Displays "Game Over", scorecard with current and best score, and prompt to restart.
Requirements
Python 3.10+
Pygame (pip install pygame)

How to Run

From this directory:

bash
python3.12 main.py

or if using default Python with Pygame installed:

bash
python3 main.py

or directly:

bash
./main.py
