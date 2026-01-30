#!/usr/bin/env python3
"""
Player module for The Floor Is a Lie
Handles player movement, mask mechanics, and collision detection
"""

import pygame
from typing import Tuple
from config import Config


class Player:
    def __init__(self, config: Config, start_pos: Tuple[int, int]):
        self.config = config

        # Position (screen coordinates)
        self.x, self.y = config.get_grid_center(start_pos)
        self.grid_x, self.grid_y = start_pos

        # Movement
        self.speed = config.PLAYER_SPEED
        self.velocity_x = 0
        self.velocity_y = 0

        # Mask mechanics
        self.mask_active = False
        self.mask_timer = 0.0
        self.mask_duration = config.MASK_DURATION
        self.mask_cooldown = config.MASK_COOLDOWN
        self.mask_recharge_timer = 0.0
        self.mask_available = True
        self.mask_uses = 0

        # Player appearance
        self.size = config.PLAYER_SIZE
        self.color = config.PLAYER_COLOR

        # Movement state
        self.moving = False
        self.target_grid_pos = None

    def update(self, delta_time: float):
        """Update player state"""
        self.update_movement(delta_time)
        self.update_mask(delta_time)

    def update_movement(self, delta_time: float):
        """Update player movement"""
        # If we have a target grid position, move towards it
        if self.target_grid_pos:
            target_x, target_y = self.config.get_grid_center(self.target_grid_pos)
            dx = target_x - self.x
            dy = target_y - self.y

            distance = (dx**2 + dy**2)**0.5

            if distance < 5:  # Close enough to target
                self.x, self.y = target_x, target_y
                self.grid_x, self.grid_y = self.target_grid_pos
                self.target_grid_pos = None
                self.velocity_x = 0
                self.velocity_y = 0
                self.moving = False
            else:
                # Move towards target
                self.velocity_x = (dx / distance) * self.speed
                self.velocity_y = (dy / distance) * self.speed
                self.moving = True

                # Update position
                self.x += self.velocity_x * delta_time
                self.y += self.velocity_y * delta_time

                # Update grid position (for collision detection)
                self.grid_x = int(self.x // self.config.TILE_SIZE)
                self.grid_y = int(self.y // self.config.TILE_SIZE)

    def update_mask(self, delta_time: float):
        """Update mask timer and recharge"""
        if self.mask_active:
            self.mask_timer -= delta_time
            if self.mask_timer <= 0:
                self.deactivate_mask()
        elif not self.mask_available:
            self.mask_recharge_timer -= delta_time
            if self.mask_recharge_timer <= 0:
                self.mask_available = True
                self.mask_recharge_timer = 0

    def handle_input(self, keys):
        """Handle keyboard input for movement"""
        # Only allow movement if not currently moving to another tile
        if self.moving:
            return

        new_grid_x, new_grid_y = self.grid_x, self.grid_y

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_grid_x -= 1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_grid_x += 1
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            new_grid_y -= 1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_grid_y += 1

        # Only move if position changed
        if (new_grid_x, new_grid_y) != (self.grid_x, self.grid_y):
            self.move_to_grid(new_grid_x, new_grid_y)

    def move_to_grid(self, grid_x: int, grid_y: int):
        """Move player to specific grid position"""
        # Validate bounds
        if 0 <= grid_x < self.config.GRID_WIDTH and 0 <= grid_y < self.config.GRID_HEIGHT:
            self.target_grid_pos = (grid_x, grid_y)
            self.moving = True

    def toggle_mask(self):
        """Toggle mask on/off"""
        if self.mask_available and not self.mask_active:
            self.activate_mask()
        elif self.mask_active:
            self.deactivate_mask()

    def activate_mask(self):
        """Activate the mask"""
        self.mask_active = True
        self.mask_timer = self.mask_duration
        self.mask_uses += 1

    def deactivate_mask(self):
        """Deactivate the mask and start recharge"""
        self.mask_active = False
        self.mask_timer = 0
        self.mask_available = False
        self.mask_recharge_timer = self.mask_cooldown

    def get_grid_position(self) -> Tuple[int, int]:
        """Get current grid position"""
        return (self.grid_x, self.grid_y)

    def get_screen_position(self) -> Tuple[float, float]:
        """Get current screen position"""
        return (self.x, self.y)

    def set_config(self, mask_duration: float = None, mask_cooldown: float = None):
        """Update mask configuration"""
        if mask_duration is not None:
            self.mask_duration = mask_duration
        if mask_cooldown is not None:
            self.mask_cooldown = mask_cooldown

    def reset(self, start_pos: Tuple[int, int]):
        """Reset player to starting position and state"""
        self.x, self.y = self.config.get_grid_center(start_pos)
        self.grid_x, self.grid_y = start_pos
        self.velocity_x = 0
        self.velocity_y = 0
        self.moving = False
        self.target_grid_pos = None

        # Reset mask
        self.mask_active = False
        self.mask_timer = 0
        self.mask_recharge_timer = 0
        self.mask_available = True
        self.mask_uses = 0

    def render(self, screen: pygame.Surface):
        """Render the player"""
        # Draw player as a circle
        pygame.draw.circle(screen, self.color,
                          (int(self.x), int(self.y)),
                          self.size // 2)

        # Draw mask indicator if active
        if self.mask_active:
            # Draw mask overlay effect
            mask_surface = pygame.Surface((self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.SRCALPHA)
            mask_surface.fill(self.config.MASK_OVERLAY_COLOR)
            screen.blit(mask_surface, (0, 0))

    def get_mask_status(self) -> dict:
        """Get current mask status for UI display"""
        return {
            "active": self.mask_active,
            "timer": self.mask_timer,
            "duration": self.mask_duration,
            "recharge_timer": self.mask_recharge_timer,
            "cooldown": self.mask_cooldown,
            "available": self.mask_available,
            "uses": self.mask_uses
        }