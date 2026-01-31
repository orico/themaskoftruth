#!/usr/bin/env python3
"""
Tile module for The Floor Is a Lie
Handles different tile types and their visual representation
"""

from enum import Enum
from typing import Tuple

import pygame

from .config import Config


class TileType(Enum):
    """Enumeration of tile types"""

    EMPTY = "empty"
    REAL = "real"
    FAKE = "fake"
    START = "start"
    EXIT = "exit"


class Tile:
    """Individual tile in the game grid"""

    def __init__(self, config: Config, tile_type: TileType, grid_pos: Tuple[int, int]):
        self.config = config
        self.type = tile_type
        self.grid_x, self.grid_y = grid_pos
        self.screen_x = grid_pos[0] * config.TILE_SIZE
        self.screen_y = grid_pos[1] * config.TILE_SIZE

        # Colors for different tile types
        self.colors = {
            TileType.EMPTY: config.TILE_EMPTY_COLOR,
            TileType.REAL: config.TILE_REAL_COLOR,
            TileType.FAKE: config.TILE_FAKE_COLOR,
            TileType.START: config.TILE_START_COLOR,
            TileType.EXIT: config.TILE_EXIT_COLOR,
        }

        # Load tile sprites (preload both for efficiency)
        self.real_sprite = None
        self.fake_sprite = None
        self._load_sprites()

    def _load_sprites(self):
        """Load and scale tile sprites"""
        tile_size = self.config.TILE_SIZE

        # Load real tile sprite
        try:
            real_sprite = pygame.image.load(
                "sprites/gen-df79415f-5e74-4ac9-86f6-5ee620955741.png"
            ).convert_alpha()
            sprite_width = real_sprite.get_width()
            sprite_height = real_sprite.get_height()
            scale_x = tile_size / sprite_width
            scale_y = tile_size / sprite_height
            scale = min(scale_x, scale_y)
            new_width = int(sprite_width * scale)
            new_height = int(sprite_height * scale)
            self.real_sprite = pygame.transform.scale(
                real_sprite, (new_width, new_height)
            )
        except pygame.error as e:
            print(f"Failed to load real tile sprite: {e}")
            self.real_sprite = None

        # Load fake tile sprite
        try:
            fake_sprite = pygame.image.load(
                "sprites/gen-9468de96-df80-4f4d-b92f-4a063b5c86b5.png"
            ).convert_alpha()
            sprite_width = fake_sprite.get_width()
            sprite_height = fake_sprite.get_height()
            scale_x = tile_size / sprite_width
            scale_y = tile_size / sprite_height
            scale = min(scale_x, scale_y)
            new_width = int(sprite_width * scale)
            new_height = int(sprite_height * scale)
            self.fake_sprite = pygame.transform.scale(
                fake_sprite, (new_width, new_height)
            )
        except pygame.error as e:
            print(f"Failed to load fake tile sprite: {e}")
            self.fake_sprite = None

    def is_walkable(self, mask_active: bool = False) -> bool:
        """Check if tile is walkable given mask state"""
        if self.type == TileType.EMPTY:
            return False
        elif self.type == TileType.REAL:
            return True
        elif self.type == TileType.FAKE:
            # Fake tiles are always walkable, but they're deadly
            return True
        elif self.type in [TileType.START, TileType.EXIT]:
            return True
        return False

    def is_safe(self, mask_active: bool = False) -> bool:
        """Check if tile is safe to walk on (won't cause death)"""
        if self.type == TileType.FAKE:
            return False  # Fake tiles are always dangerous
        return self.is_walkable(mask_active)

    def get_display_color(self, mask_active: bool = False) -> Tuple[int, int, int]:
        """Get the color to display for this tile"""
        if mask_active:
            # When mask is active, show true tile colors
            return self.colors[self.type]
        else:
            # When mask is inactive, fake tiles appear as real tiles
            if self.type == TileType.FAKE:
                return self.colors[TileType.REAL]
            elif self.type == TileType.REAL:
                return self.colors[TileType.REAL]
            else:
                return self.colors[self.type]

    def render(self, screen: pygame.Surface, mask_active: bool = False):
        """Render the tile"""
        color = self.get_display_color(mask_active)

        # Draw tile rectangle (background)
        rect = pygame.Rect(
            self.screen_x, self.screen_y, self.config.TILE_SIZE, self.config.TILE_SIZE
        )
        pygame.draw.rect(screen, color, rect)

        # Draw sprite if available
        # When mask is inactive, fake tiles appear as real tiles (show real sprite)
        # When mask is active, fake tiles show their true appearance (show fake sprite)
        display_sprite = None
        if self.type == TileType.REAL:
            display_sprite = self.real_sprite
        elif self.type == TileType.FAKE:
            if mask_active:
                display_sprite = (
                    self.fake_sprite
                )  # Show fake sprite when mask is active
            else:
                display_sprite = (
                    self.real_sprite
                )  # Show real sprite when mask is inactive

        if display_sprite:
            # Center the sprite in the tile
            sprite_x = (
                self.screen_x
                + (self.config.TILE_SIZE - display_sprite.get_width()) // 2
            )
            sprite_y = (
                self.screen_y
                + (self.config.TILE_SIZE - display_sprite.get_height()) // 2
            )
            screen.blit(display_sprite, (sprite_x, sprite_y))

        # Draw grid lines
        pygame.draw.rect(screen, (60, 60, 80), rect, 1)

    def _draw_start_indicator(self, screen: pygame.Surface, rect: pygame.Rect):
        """Draw start tile indicator"""
        center_x = rect.centerx
        center_y = rect.centery
        size = self.config.TILE_SIZE // 4

        # Draw an "S" or simple arrow
        points = [
            (center_x - size, center_y - size),
            (center_x + size, center_y - size),
            (center_x + size, center_y),
            (center_x - size, center_y),
            (center_x - size, center_y + size),
            (center_x + size, center_y + size),
        ]
        pygame.draw.lines(screen, (255, 255, 255), False, points, 2)

    def _draw_exit_indicator(self, screen: pygame.Surface, rect: pygame.Rect):
        """Draw exit tile indicator"""
        center_x = rect.centerx
        center_y = rect.centery
        size = self.config.TILE_SIZE // 3

        # Draw an "E" or diamond shape
        points = [
            (center_x, center_y - size),
            (center_x + size, center_y),
            (center_x, center_y + size),
            (center_x - size, center_y),
        ]
        pygame.draw.polygon(screen, (255, 255, 255), points, 2)

    @classmethod
    def from_string(cls, config: Config, tile_string: str, grid_pos: Tuple[int, int]):
        """Create tile from string representation"""
        tile_type_map = {
            "empty": TileType.EMPTY,
            "real": TileType.REAL,
            "fake": TileType.FAKE,
            "start": TileType.START,
            "exit": TileType.EXIT,
            ".": TileType.EMPTY,  # Alternative representation
            "#": TileType.REAL,  # Alternative representation
            "■": TileType.REAL,  # Unicode representation
            "▫": TileType.FAKE,  # Unicode representation
        }

        tile_type = tile_type_map.get(tile_string.lower(), TileType.EMPTY)
        return cls(config, tile_type, grid_pos)
