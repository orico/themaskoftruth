#!/usr/bin/env python3
"""
Configuration module for The Floor Is a Lie
Contains all game constants and settings
"""

import pygame


class Config:
    """Game configuration class"""

    # Display settings
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60

    # Colors
    BACKGROUND_COLOR = (20, 20, 30)
    TILE_REAL_COLOR = (100, 150, 100)  # Green for real tiles
    TILE_FAKE_COLOR = (150, 100, 100)  # Red for fake tiles (when visible)
    TILE_EMPTY_COLOR = (50, 50, 70)  # Dark for empty tiles
    TILE_START_COLOR = (100, 100, 200)  # Blue for start
    TILE_EXIT_COLOR = (200, 200, 100)  # Yellow for exit
    PLAYER_COLOR = (255, 255, 255)  # White player
    MASK_OVERLAY_COLOR = (0, 0, 0, 128)  # Semi-transparent black

    # Tile settings
    TILE_SIZE = 40
    GRID_WIDTH = 11
    GRID_HEIGHT = 10

    # Player settings
    PLAYER_SPEED = 200  # pixels per second
    PLAYER_SIZE = 32

    # Mask settings (default values, can be overridden by level)
    MASK_DURATION = 2.0  # seconds mask stays active
    MASK_COOLDOWN = 5.0  # seconds to recharge after use

    # Scoring settings (default values, can be overridden by level)
    TIME_THRESHOLDS = [30, 60, 120]  # seconds for 3, 2, 1 stars
    MASK_USE_THRESHOLD = 5  # maximum mask uses before star penalty

    # UI settings
    FONT_SIZE_SMALL = 16
    FONT_SIZE_MEDIUM = 24
    FONT_SIZE_LARGE = 32
    UI_PADDING = 10

    # Level editor settings
    EDITOR_BUTTON_HEIGHT = 30
    EDITOR_TOOLBAR_WIDTH = 200

    @classmethod
    def get_font(cls, size="medium"):
        """Get pygame font with specified size"""
        size_map = {
            "small": cls.FONT_SIZE_SMALL,
            "medium": cls.FONT_SIZE_MEDIUM,
            "large": cls.FONT_SIZE_LARGE,
        }
        return pygame.font.Font(None, size_map.get(size, cls.FONT_SIZE_MEDIUM))

    @classmethod
    def screen_to_grid(cls, screen_pos):
        """Convert screen coordinates to grid coordinates"""
        x, y = screen_pos
        grid_x = x // cls.TILE_SIZE
        grid_y = y // cls.TILE_SIZE
        return (grid_x, grid_y)

    @classmethod
    def grid_to_screen(cls, grid_pos):
        """Convert grid coordinates to screen coordinates"""
        grid_x, grid_y = grid_pos
        screen_x = grid_x * cls.TILE_SIZE
        screen_y = grid_y * cls.TILE_SIZE
        return (screen_x, screen_y)

    @classmethod
    def get_grid_center(cls, grid_pos):
        """Get screen coordinates for center of grid tile"""
        screen_x, screen_y = cls.grid_to_screen(grid_pos)
        return (screen_x + cls.TILE_SIZE // 2, screen_y + cls.TILE_SIZE // 2)
