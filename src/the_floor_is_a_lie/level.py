#!/usr/bin/env python3
"""
Level module for The Floor Is a Lie
Handles level loading, tile grid management, and level state
"""

import json
import pygame
from typing import List, Tuple, Optional, Dict, Any
from config import Config
from tile import Tile, TileType


class Level:
    """Level management class"""

    def __init__(self, config: Config):
        self.config = config
        self.name = "Default Level"
        self.grid: List[List[Tile]] = []
        self.start_pos: Tuple[int, int] = (0, 0)
        self.exit_pos: Tuple[int, int] = (0, 0)

        # Level configuration (can be overridden by level JSON)
        self.mask_duration = config.MASK_DURATION
        self.mask_cooldown = config.MASK_COOLDOWN
        self.time_thresholds = config.TIME_THRESHOLDS.copy()
        self.mask_threshold = config.MASK_USE_THRESHOLD

        # Level metadata
        self.level_config: Dict[str, Any] = {}

    def load_level(self, filename: str) -> bool:
        """Load level from JSON file"""
        try:
            with open(filename, 'r') as f:
                level_data = json.load(f)

            self.name = level_data.get('name', 'Unnamed Level')
            self.level_config = level_data.get('config', {})

            # Load grid
            grid_data = level_data['grid']
            self._create_grid_from_data(grid_data)

            # Load configuration
            self._load_config()

            return True

        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Error loading level {filename}: {e}")
            return False

    def _create_grid_from_data(self, grid_data: List[List[str]]):
        """Create tile grid from level data"""
        self.grid = []

        for y, row in enumerate(grid_data):
            tile_row = []
            for x, tile_str in enumerate(row):
                tile = Tile.from_string(self.config, tile_str, (x, y))

                # Track start and exit positions
                if tile.type == TileType.START:
                    self.start_pos = (x, y)
                elif tile.type == TileType.EXIT:
                    self.exit_pos = (x, y)

                tile_row.append(tile)

            self.grid.append(tile_row)

    def _load_config(self):
        """Load level-specific configuration"""
        self.mask_duration = self.level_config.get('mask_duration', self.config.MASK_DURATION)
        self.mask_cooldown = self.level_config.get('mask_cooldown', self.config.MASK_COOLDOWN)
        self.time_thresholds = self.level_config.get('time_thresholds', self.config.TIME_THRESHOLDS.copy())
        self.mask_threshold = self.level_config.get('mask_threshold', self.config.MASK_USE_THRESHOLD)

    def save_level(self, filename: str) -> bool:
        """Save current level to JSON file"""
        try:
            grid_data = []
            for row in self.grid:
                row_data = []
                for tile in row:
                    # Convert tile type back to string
                    tile_str_map = {
                        TileType.EMPTY: "empty",
                        TileType.REAL: "real",
                        TileType.FAKE: "fake",
                        TileType.START: "start",
                        TileType.EXIT: "exit"
                    }
                    row_data.append(tile_str_map[tile.type])
                grid_data.append(row_data)

            level_data = {
                "name": self.name,
                "grid": grid_data,
                "config": {
                    "mask_duration": self.mask_duration,
                    "mask_cooldown": self.mask_cooldown,
                    "time_thresholds": self.time_thresholds,
                    "mask_threshold": self.mask_threshold
                }
            }

            with open(filename, 'w') as f:
                json.dump(level_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving level {filename}: {e}")
            return False

    def is_valid_position(self, grid_pos: Tuple[int, int]) -> bool:
        """Check if grid position is within bounds"""
        x, y = grid_pos
        return 0 <= x < len(self.grid[0]) and 0 <= y < len(self.grid)

    def get_tile(self, grid_pos: Tuple[int, int]) -> Optional[Tile]:
        """Get tile at grid position"""
        if not self.is_valid_position(grid_pos):
            return None

        x, y = grid_pos
        return self.grid[y][x]

    def is_walkable(self, grid_pos: Tuple[int, int], mask_active: bool = False) -> bool:
        """Check if position is walkable"""
        tile = self.get_tile(grid_pos)
        if tile is None:
            return False
        return tile.is_walkable(mask_active)

    def is_safe(self, grid_pos: Tuple[int, int], mask_active: bool = False) -> bool:
        """Check if position is safe (won't cause death)"""
        tile = self.get_tile(grid_pos)
        if tile is None:
            return False
        return tile.is_safe(mask_active)

    def is_empty_tile(self, grid_pos: Tuple[int, int]) -> bool:
        """Check if tile at position is empty (causes death)"""
        tile = self.get_tile(grid_pos)
        return tile is not None and tile.type == TileType.EMPTY

    def is_fake_tile(self, grid_pos: Tuple[int, int]) -> bool:
        """Check if tile at position is fake"""
        tile = self.get_tile(grid_pos)
        return tile is not None and tile.type == TileType.FAKE

    def is_exit_tile(self, grid_pos: Tuple[int, int]) -> bool:
        """Check if tile at position is the exit"""
        return grid_pos == self.exit_pos

    def is_start_tile(self, grid_pos: Tuple[int, int]) -> bool:
        """Check if tile at position is the start"""
        return grid_pos == self.start_pos

    def set_tile_type(self, grid_pos: Tuple[int, int], tile_type: TileType):
        """Set tile type at grid position"""
        if not self.is_valid_position(grid_pos):
            return

        x, y = grid_pos
        old_tile = self.grid[y][x]

        # Update start/exit positions if necessary
        if tile_type == TileType.START:
            self.start_pos = grid_pos
        elif tile_type == TileType.EXIT:
            self.exit_pos = grid_pos
        elif old_tile.type == TileType.START:
            self.start_pos = (0, 0)  # Reset to default if start tile is changed
        elif old_tile.type == TileType.EXIT:
            self.exit_pos = (0, 0)  # Reset to default if exit tile is changed

        # Create new tile
        self.grid[y][x] = Tile(self.config, tile_type, grid_pos)

    def render(self, screen: pygame.Surface, mask_active: bool = False):
        """Render the entire level"""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Rendering level with mask_active={mask_active}")

        for row in self.grid:
            for tile in row:
                tile.render(screen, mask_active)

    def get_level_info(self) -> Dict[str, Any]:
        """Get level information for display"""
        return {
            "name": self.name,
            "dimensions": (len(self.grid[0]), len(self.grid)),
            "start_pos": self.start_pos,
            "exit_pos": self.exit_pos,
            "mask_duration": self.mask_duration,
            "mask_cooldown": self.mask_cooldown,
            "time_thresholds": self.time_thresholds,
            "mask_threshold": self.mask_threshold
        }

    def reset(self):
        """Reset level state (for restarting)"""
        # Level state doesn't need resetting between plays
        # Player position is handled by Player.reset()
        pass