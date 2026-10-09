#!/usr/bin/env python3.12
"""
Flappy Bird 2D Clone
Built with Python and Pygame.

Core Game Rules & Architecture:
- Kinematic Physics: Pure velocity and gravity integration (no external physics engine).
- Procedural Pipes: Vertical pipe pairs with random gap offsets and programmatic rendering.
- State Management: START -> PLAYING -> GAME_OVER states.
- Exact Collision Detection: Pipes (AABB rects), Ground boundary, and Ceiling boundary.
- Scoring System: Increases by +1 when passing through each pipe pair.
"""

import sys
import math
import random
import pygame
from enum import Enum, auto


# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================
SCREEN_WIDTH = 420
SCREEN_HEIGHT = 650
FPS = 60

# World & Ground Dimensions
GROUND_HEIGHT = 90
GROUND_Y = SCREEN_HEIGHT - GROUND_HEIGHT

# Kinematic Physics Parameters (pixels / frame)
GRAVITY = 0.42
FLAP_VELOCITY = -7.6
MAX_FALL_SPEED = 10.0

# Pipe Obstacle Parameters
PIPE_SPEED = 2.8
PIPE_WIDTH = 68
PIPE_GAP = 145            # Vertical playable gap between upper and lower pipes
PIPE_SPAWN_DISTANCE = 210 # Distance in pixels between consecutive pipe pairs
MIN_PIPE_HEIGHT = 60
MAX_PIPE_HEIGHT = GROUND_Y - PIPE_GAP - MIN_PIPE_HEIGHT

# Color Palette (Crisp geometric visuals)
COLOR_SKY_TOP = (112, 197, 206)
COLOR_SKY_BOTTOM = (180, 230, 238)
COLOR_GROUND_BASE = (222, 216, 149)
COLOR_GROUND_GRASS = (115, 191, 46)
COLOR_GROUND_LINE = (91, 153, 37)
COLOR_PIPE_BODY = (115, 191, 46)
COLOR_PIPE_HIGHLIGHT = (156, 222, 77)
COLOR_PIPE_BORDER = (46, 89, 21)
COLOR_PIPE_LIP = (103, 175, 41)
COLOR_BIRD_BODY = (248, 218, 64)
COLOR_BIRD_BELLY = (235, 180, 36)
COLOR_BIRD_EYE = (255, 255, 255)
COLOR_BIRD_PUPIL = (20, 20, 20)
COLOR_BIRD_BEAK = (244, 91, 56)
COLOR_BIRD_WING = (255, 240, 120)
COLOR_TEXT_MAIN = (255, 255, 255)
COLOR_TEXT_SHADOW = (40, 40, 40)
COLOR_PANEL_BG = (238, 228, 178)
COLOR_PANEL_BORDER = (190, 160, 100)


# =============================================================================
# GAME STATES
# =============================================================================
class GameState(Enum):
    START = auto()
    PLAYING = auto()
    GAME_OVER = auto()


# =============================================================================
# BIRD CLASS
# =============================================================================
class Bird:
    def __init__(self, x: float, y: float):
        self.initial_x = x
        self.initial_y = y
        self.x = x
        self.y = y
        self.radius = 15
        self.velocity = 0.0
        self.hover_angle = 0.0
        self.flap_anim_timer = 0

    def reset(self):
        """Reset bird to initial start position."""
        self.x = self.initial_x
        self.y = self.initial_y
        self.velocity = 0.0
        self.hover_angle = 0.0
        self.flap_anim_timer = 0

    def flap(self):
        """Apply upward kinematic impulse when user triggers flap action."""
        self.velocity = FLAP_VELOCITY
        self.flap_anim_timer = 12

    def update_idle(self):
        """Gentle floating bob animation for the Start Screen state."""
        self.hover_angle += 0.07
        self.y = self.initial_y + math.sin(self.hover_angle) * 7.0
        self.velocity = 0.0

    def update_physics(self):
        """Kinematic integration: velocity += gravity, position += velocity."""
        self.velocity += GRAVITY
        if self.velocity > MAX_FALL_SPEED:
            self.velocity = MAX_FALL_SPEED
        self.y += self.velocity

        if self.flap_anim_timer > 0:
            self.flap_anim_timer -= 1

    def get_rect(self) -> pygame.Rect:
        """Returns the bounding box rectangle for collision detection."""
        # A slightly snug rectangular hitbox around the circular body
        return pygame.Rect(
            int(self.x - self.radius + 2),
            int(self.y - self.radius + 2),
            (self.radius - 2) * 2,
            (self.radius - 2) * 2
        )

    def draw(self, surface: pygame.Surface):
        """Draw the bird programmatically using 2D geometric primitives."""
        bx = int(self.x)
        by = int(self.y)
        r = self.radius

        # Calculate rotation angle based on vertical velocity
        tilt_angle = max(-30, min(70, self.velocity * 4.5))

        # Create a transparent surface for tilted rendering
        size = r * 3
        bird_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)

        # 1. Main body (yellow circle)
        pygame.draw.circle(bird_surf, COLOR_BIRD_BODY, center, r)
        pygame.draw.circle(bird_surf, (180, 150, 20), center, r, width=2)

        # 2. Belly shading (lower arc / crescent)
        pygame.draw.circle(bird_surf, COLOR_BIRD_BELLY, (center[0] - 2, center[1] + 4), r - 4)

        # 3. Wing (geometric oval)
        wing_y_offset = -2 if self.flap_anim_timer > 0 else 1
        pygame.draw.ellipse(bird_surf, COLOR_BIRD_WING, (center[0] - 11, center[1] - 4 + wing_y_offset, 12, 8))
        pygame.draw.ellipse(bird_surf, (180, 150, 20), (center[0] - 11, center[1] - 4 + wing_y_offset, 12, 8), width=1)

        # 4. Eye (white circle + dark pupil)
        eye_center = (center[0] + 6, center[1] - 6)
        pygame.draw.circle(bird_surf, COLOR_BIRD_EYE, eye_center, 5)
        pygame.draw.circle(bird_surf, (30, 30, 30), eye_center, 5, width=1)
        pygame.draw.circle(bird_surf, COLOR_BIRD_PUPIL, (eye_center[0] + 1, eye_center[1] - 1), 2)

        # 5. Beak (orange triangle)
        beak_points = [
            (center[0] + 9, center[1] - 1),
            (center[0] + 17, center[1] + 3),
            (center[0] + 9, center[1] + 7)
        ]
        pygame.draw.polygon(bird_surf, COLOR_BIRD_BEAK, beak_points)
        pygame.draw.polygon(bird_surf, (170, 40, 10), beak_points, width=1)

        # Rotate bird based on trajectory tilt
        rotated_surf = pygame.transform.rotate(bird_surf, -tilt_angle)
        rect = rotated_surf.get_rect(center=(bx, by))
        surface.blit(rotated_surf, rect)


# =============================================================================
# PIPE OBSTACLE CLASS
# =============================================================================
class PipePair:
    def __init__(self, x: float):
        self.x = x
        self.width = PIPE_WIDTH
        self.gap = PIPE_GAP
        # Randomize upper pipe height within bounded playable range
        self.top_height = random.randint(MIN_PIPE_HEIGHT, MAX_PIPE_HEIGHT)
        self.bottom_y = self.top_height + self.gap
        self.bottom_height = GROUND_Y - self.bottom_y
        self.passed = False  # Set to True when score has been awarded

    def update(self):
        """Move pipe continuously to the left."""
        self.x -= PIPE_SPEED

    def is_offscreen(self) -> bool:
        """Returns True when pipe pair completely exits left screen edge."""
        return self.x + self.width < 0

    def get_top_rect(self) -> pygame.Rect:
        """Returns bounding rectangle for top obstacle."""
        return pygame.Rect(int(self.x), 0, self.width, int(self.top_height))

    def get_bottom_rect(self) -> pygame.Rect:
        """Returns bounding rectangle for bottom obstacle."""
        return pygame.Rect(int(self.x), int(self.bottom_y), self.width, int(self.bottom_height))

    def collides_with(self, bird_rect: pygame.Rect) -> bool:
        """AABB collision detection against both top and bottom pipes."""
        return bird_rect.colliderect(self.get_top_rect()) or bird_rect.colliderect(self.get_bottom_rect())

    def draw(self, surface: pygame.Surface):
        """Render upper and lower pipes with decorative lips/caps programmatically."""
        px = int(self.x)
        pw = self.width
        lip_height = 24
        lip_extend = 4  # Cap is slightly wider than pipe body

        # --- Top Pipe ---
        top_body_rect = pygame.Rect(px, 0, pw, int(self.top_height) - lip_height)
        top_lip_rect = pygame.Rect(px - lip_extend, int(self.top_height) - lip_height, pw + lip_extend * 2, lip_height)

        # Body
        pygame.draw.rect(surface, COLOR_PIPE_BODY, top_body_rect)
        pygame.draw.rect(surface, COLOR_PIPE_HIGHLIGHT, (px + 6, 0, 10, int(self.top_height) - lip_height))
        pygame.draw.rect(surface, COLOR_PIPE_BORDER, top_body_rect, width=3)

        # Lip / Collar
        pygame.draw.rect(surface, COLOR_PIPE_LIP, top_lip_rect)
        pygame.draw.rect(surface, COLOR_PIPE_HIGHLIGHT, (px - lip_extend + 6, int(self.top_height) - lip_height, 10, lip_height))
        pygame.draw.rect(surface, COLOR_PIPE_BORDER, top_lip_rect, width=3)

        # --- Bottom Pipe ---
        bot_lip_rect = pygame.Rect(px - lip_extend, int(self.bottom_y), pw + lip_extend * 2, lip_height)
        bot_body_rect = pygame.Rect(px, int(self.bottom_y) + lip_height, pw, int(self.bottom_height) - lip_height)

        # Lip / Collar
        pygame.draw.rect(surface, COLOR_PIPE_LIP, bot_lip_rect)
        pygame.draw.rect(surface, COLOR_PIPE_HIGHLIGHT, (px - lip_extend + 6, int(self.bottom_y), 10, lip_height))
        pygame.draw.rect(surface, COLOR_PIPE_BORDER, bot_lip_rect, width=3)

        # Body
        pygame.draw.rect(surface, COLOR_PIPE_BODY, bot_body_rect)
        pygame.draw.rect(surface, COLOR_PIPE_HIGHLIGHT, (px + 6, int(self.bottom_y) + lip_height, 10, int(self.bottom_height) - lip_height))
        pygame.draw.rect(surface, COLOR_PIPE_BORDER, bot_body_rect, width=3)


# =============================================================================
# SCENERY & BACKGROUND RENDERING
# =============================================================================
class Background:
    def __init__(self):
        self.ground_offset = 0.0
        # Generate some static distant clouds
        self.clouds = [
            (40, 80, 50),
            (180, 130, 65),
            (320, 60, 45)
        ]

    def update(self, is_moving: bool):
        """Scroll ground stripes to produce illusion of continuous motion."""
        if is_moving:
            self.ground_offset = (self.ground_offset + PIPE_SPEED) % 24

    def draw(self, surface: pygame.Surface):
        """Draw sky gradient, geometric clouds, and textured ground."""
        # 1. Sky background
        surface.fill(COLOR_SKY_TOP)
        # Subtle gradient band near bottom sky
        gradient_rect = pygame.Rect(0, GROUND_Y - 120, SCREEN_WIDTH, 120)
        pygame.draw.rect(surface, COLOR_SKY_BOTTOM, gradient_rect)

        # 2. Geometric clouds
        for cx, cy, cr in self.clouds:
            pygame.draw.circle(surface, (255, 255, 255, 200), (cx, cy), cr)
            pygame.draw.circle(surface, (255, 255, 255, 200), (cx + int(cr * 0.7), cy - 6), int(cr * 0.75))
            pygame.draw.circle(surface, (255, 255, 255, 200), (cx - int(cr * 0.7), cy + 4), int(cr * 0.65))

        # 3. Ground base
        ground_rect = pygame.Rect(0, GROUND_Y, SCREEN_WIDTH, GROUND_HEIGHT)
        pygame.draw.rect(surface, COLOR_GROUND_BASE, ground_rect)

        # 4. Grass top strip
        grass_rect = pygame.Rect(0, GROUND_Y, SCREEN_WIDTH, 14)
        pygame.draw.rect(surface, COLOR_GROUND_GRASS, grass_rect)
        pygame.draw.line(surface, COLOR_GROUND_LINE, (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 3)

        # 5. Animated moving stripe details on the ground
        stripe_spacing = 24
        start_x = -int(self.ground_offset)
        for sx in range(start_x, SCREEN_WIDTH + stripe_spacing, stripe_spacing):
            p1 = (sx, GROUND_Y + 14)
            p2 = (sx - 8, GROUND_Y + 28)
            pygame.draw.line(surface, (190, 180, 110), p1, p2, 3)


# =============================================================================
# MAIN GAME CONTROLLER & STATE MANAGER
# =============================================================================
class FlappyBirdGame:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird 2D")
        self.clock = pygame.time.Clock()

        # Built-in fonts (guaranteed to work across all platforms without OS font permission requirements)
        self.font_title = pygame.font.Font(None, 46)
        self.font_score = pygame.font.Font(None, 40)
        self.font_med = pygame.font.Font(None, 26)
        self.font_small = pygame.font.Font(None, 20)

        self.background = Background()
        self.bird = Bird(SCREEN_WIDTH // 3, SCREEN_HEIGHT // 2 - 40)
        self.pipes: list[PipePair] = []

        self.state = GameState.START
        self.score = 0
        self.high_score = 0
        self.running = True

    def reset_game(self):
        """Reset variables to initialize a fresh gameplay session."""
        self.bird.reset()
        self.pipes.clear()
        self.score = 0
        # Seed initial pipe with ample initial clearance
        self.pipes.append(PipePair(SCREEN_WIDTH + 100))

    def handle_flap_input(self):
        """Unified input handler for Spacebar, Up Arrow, or Mouse Click."""
        if self.state == GameState.START:
            self.reset_game()
            self.bird.flap()
            self.state = GameState.PLAYING
        elif self.state == GameState.PLAYING:
            self.bird.flap()
        elif self.state == GameState.GAME_OVER:
            self.reset_game()
            self.state = GameState.START

    def process_events(self):
        """Handle user input events and window close signals."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    self.handle_flap_input()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.handle_flap_input()

    def update(self):
        """Execute state-specific game loop logic."""
        if self.state == GameState.START:
            self.bird.update_idle()
            self.background.update(is_moving=True)

        elif self.state == GameState.PLAYING:
            # 1. Update player physics
            self.bird.update_physics()
            self.background.update(is_moving=True)

            # 2. Check boundary collisions (Ceiling & Ground)
            # Ceiling boundary: bird moves above top edge (y <= 0)
            if self.bird.y - self.bird.radius <= 0:
                self.trigger_game_over()
                return

            # Ground boundary: bird touches the ground (y + radius >= GROUND_Y)
            if self.bird.y + self.bird.radius >= GROUND_Y:
                self.bird.y = GROUND_Y - self.bird.radius
                self.trigger_game_over()
                return

            # 3. Update & spawn pipes
            # Spawn next pipe pair when rightmost pipe has traveled enough distance
            if len(self.pipes) == 0 or (SCREEN_WIDTH - self.pipes[-1].x >= PIPE_SPAWN_DISTANCE):
                self.pipes.append(PipePair(SCREEN_WIDTH))

            bird_rect = self.bird.get_rect()

            for pipe in self.pipes:
                pipe.update()

                # Check pipe obstacle collision
                if pipe.collides_with(bird_rect):
                    self.trigger_game_over()
                    return

                # Scoring: award +1 once when bird successfully passes pipe pair
                if not pipe.passed and self.bird.x > pipe.x + pipe.width:
                    pipe.passed = True
                    self.score += 1
                    if self.score > self.high_score:
                        self.high_score = self.score

            # Remove off-screen pipes
            self.pipes = [p for p in self.pipes if not p.is_offscreen()]

        elif self.state == GameState.GAME_OVER:
            # In Game Over state, allow bird to fall to ground if not already there
            if self.bird.y + self.bird.radius < GROUND_Y:
                self.bird.update_physics()
                if self.bird.y + self.bird.radius >= GROUND_Y:
                    self.bird.y = GROUND_Y - self.bird.radius

    def trigger_game_over(self):
        """Switch to Game Over state immediately upon any collision."""
        self.state = GameState.GAME_OVER
        if self.score > self.high_score:
            self.high_score = self.score

    def render_text_with_shadow(self, text: str, font: pygame.font.Font,
                                color: tuple, pos: tuple, center: bool = True):
        """Helper to render text with a crisp contrasting drop shadow."""
        shadow_surf = font.render(text, True, COLOR_TEXT_SHADOW)
        text_surf = font.render(text, True, color)

        if center:
            rect = text_surf.get_rect(center=pos)
            shadow_rect = shadow_surf.get_rect(center=(pos[0] + 2, pos[1] + 2))
        else:
            rect = text_surf.get_rect(topleft=pos)
            shadow_rect = shadow_surf.get_rect(topleft=(pos[0] + 2, pos[1] + 2))

        self.screen.blit(shadow_surf, shadow_rect)
        self.screen.blit(text_surf, rect)

    def draw_hud_and_overlays(self):
        """Render HUD, instructions, and scoreboards based on current game state."""
        # 1. State: START SCREEN
        if self.state == GameState.START:
            self.render_text_with_shadow("FLAPPY BIRD", self.font_title, (255, 230, 70), (SCREEN_WIDTH // 2, 130))

            # Instructions Box
            box_rect = pygame.Rect(40, 240, SCREEN_WIDTH - 80, 150)
            pygame.draw.rect(self.screen, (0, 0, 0, 70), box_rect, border_radius=12)
            pygame.draw.rect(self.screen, COLOR_TEXT_MAIN, box_rect, width=2, border_radius=12)

            self.render_text_with_shadow("HOW TO PLAY", self.font_med, (255, 255, 255), (SCREEN_WIDTH // 2, 265))
            self.render_text_with_shadow("Press SPACE / UP / CLICK", self.font_small, (240, 240, 240), (SCREEN_WIDTH // 2, 305))
            self.render_text_with_shadow("to Flap your wings", self.font_small, (240, 240, 240), (SCREEN_WIDTH // 2, 325))
            self.render_text_with_shadow("Avoid pipes, ceiling & ground!", self.font_small, (255, 210, 80), (SCREEN_WIDTH // 2, 355))

            # Prompt to start
            pulse_color = (255, 255, 255)
            self.render_text_with_shadow("Press SPACE to Start", self.font_med, pulse_color, (SCREEN_WIDTH // 2, 450))

        # 2. State: ACTIVE GAMEPLAY
        elif self.state == GameState.PLAYING:
            # Active Score display in top center
            self.render_text_with_shadow(str(self.score), self.font_title, COLOR_TEXT_MAIN, (SCREEN_WIDTH // 2, 60))

        # 3. State: GAME OVER SCREEN
        elif self.state == GameState.GAME_OVER:
            self.render_text_with_shadow("GAME OVER", self.font_title, (240, 70, 70), (SCREEN_WIDTH // 2, 140))

            # Scorecard panel
            panel_w, panel_h = 280, 180
            panel_x = (SCREEN_WIDTH - panel_w) // 2
            panel_y = 200
            panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

            pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect, border_radius=14)
            pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, panel_rect, width=4, border_radius=14)

            # Scorecard contents
            self.render_text_with_shadow("SCORE", self.font_small, (120, 100, 70), (SCREEN_WIDTH // 2, panel_y + 35))
            self.render_text_with_shadow(f"{self.score}", self.font_score, (60, 60, 60), (SCREEN_WIDTH // 2, panel_y + 68))

            pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (panel_x + 30, panel_y + 98), (panel_x + panel_w - 30, panel_y + 98), 2)

            self.render_text_with_shadow(f"BEST: {self.high_score}", self.font_med, (210, 130, 20), (SCREEN_WIDTH // 2, panel_y + 130))

            # Restart prompt
            self.render_text_with_shadow("Press SPACE or Click to Restart", self.font_med, COLOR_TEXT_MAIN, (SCREEN_WIDTH // 2, 430))

    def render(self):
        """Draw complete frame: Background -> Obstacles -> Bird -> HUD."""
        # 1. Background (sky, clouds, ground)
        self.background.draw(self.screen)

        # 2. Pipes
        for pipe in self.pipes:
            pipe.draw(self.screen)

        # 3. Player Bird
        self.bird.draw(self.screen)

        # 4. HUD / State-specific overlays
        self.draw_hud_and_overlays()

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.running:
            self.process_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    game = FlappyBirdGame()
    game.run()
