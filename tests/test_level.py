"""Tests for the Level module."""

import pytest
import json
import tempfile
import os
from src.the_floor_is_a_lie.config import Config
from src.the_floor_is_a_lie.level import Level
from src.the_floor_is_a_lie.tile import TileType


class TestLevel:
    """Test cases for Level class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.level = Level(self.config)

    def test_initialization(self):
        """Test level initialization."""
        assert self.level.name == "Default Level"
        assert len(self.level.grid) == 0  # Empty until loaded

    def test_load_level_success(self):
        """Test successful level loading."""
        # Create a temporary level file
        level_data = {
            "name": "Test Level",
            "grid": [
                ["start", "real", "fake"],
                ["real", "empty", "exit"]
            ],
            "config": {
                "mask_duration": 3.0,
                "mask_cooldown": 4.0,
                "time_thresholds": [20, 40, 80],
                "mask_threshold": 3
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(level_data, f)
            temp_path = f.name

        try:
            # Load the level
            success = self.level.load_level(temp_path)
            assert success

            # Check level properties
            assert self.level.name == "Test Level"
            assert len(self.level.grid) == 2
            assert len(self.level.grid[0]) == 3
            assert self.level.start_pos == (0, 0)
            assert self.level.exit_pos == (2, 1)

            # Check configuration
            assert self.level.mask_duration == 3.0
            assert self.level.mask_cooldown == 4.0
            assert self.level.time_thresholds == [20, 40, 80]
            assert self.level.mask_threshold == 3

        finally:
            os.unlink(temp_path)

    def test_load_level_invalid_file(self):
        """Test loading invalid level file."""
        success = self.level.load_level("nonexistent.json")
        assert not success

    def test_save_level(self):
        """Test level saving."""
        # Set up a level
        self.level.name = "Save Test"
        self.level.start_pos = (0, 0)
        self.level.exit_pos = (2, 2)

        # Create a simple grid
        from src.the_floor_is_a_lie.tile import Tile
        self.level.grid = [
            [Tile(self.config, TileType.START, (0, 0)), Tile(self.config, TileType.REAL, (1, 0)), Tile(self.config, TileType.FAKE, (2, 0))],
            [Tile(self.config, TileType.REAL, (0, 1)), Tile(self.config, TileType.EMPTY, (1, 1)), Tile(self.config, TileType.REAL, (2, 1))],
            [Tile(self.config, TileType.FAKE, (0, 2)), Tile(self.config, TileType.REAL, (1, 2)), Tile(self.config, TileType.EXIT, (2, 2))]
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            # Save the level
            success = self.level.save_level(temp_path)
            assert success

            # Load it back and verify
            new_level = Level(self.config)
            success = new_level.load_level(temp_path)
            assert success
            assert new_level.name == "Save Test"
            assert new_level.start_pos == (0, 0)
            assert new_level.exit_pos == (2, 2)

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_valid_position(self):
        """Test position validation."""
        # Create a small grid
        self.level.grid = [
            [None, None],
            [None, None]
        ]

        assert self.level.is_valid_position((0, 0))
        assert self.level.is_valid_position((1, 1))
        assert not self.level.is_valid_position((-1, 0))
        assert not self.level.is_valid_position((2, 0))
        assert not self.level.is_valid_position((0, 2))

    def test_walkable_tiles(self):
        """Test tile walkability logic."""
        from src.the_floor_is_a_lie.tile import Tile

        # Create tiles
        real_tile = Tile(self.config, TileType.REAL, (0, 0))
        fake_tile = Tile(self.config, TileType.FAKE, (1, 0))
        empty_tile = Tile(self.config, TileType.EMPTY, (2, 0))
        start_tile = Tile(self.config, TileType.START, (0, 1))

        # Set up level grid
        self.level.grid = [
            [real_tile, fake_tile, empty_tile],
            [start_tile, None, None]
        ]

        # Test walkability without mask
        assert self.level.is_walkable((0, 0), False)  # Real tile
        assert not self.level.is_walkable((1, 0), False)  # Fake tile without mask
        assert not self.level.is_walkable((2, 0), False)  # Empty tile
        assert self.level.is_walkable((0, 1), False)  # Start tile

        # Test walkability with mask
        assert self.level.is_walkable((0, 0), True)  # Real tile
        assert self.level.is_walkable((1, 0), True)  # Fake tile with mask
        assert not self.level.is_walkable((2, 0), True)  # Empty tile still dangerous

    def test_safe_tiles(self):
        """Test tile safety logic."""
        from src.the_floor_is_a_lie.tile import Tile

        # Create tiles
        real_tile = Tile(self.config, TileType.REAL, (0, 0))
        fake_tile = Tile(self.config, TileType.FAKE, (1, 0))
        empty_tile = Tile(self.config, TileType.EMPTY, (2, 0))

        # Set up level grid
        self.level.grid = [
            [real_tile, fake_tile, empty_tile]
        ]

        # Test safety without mask
        assert self.level.is_safe((0, 0), False)  # Real tile is safe
        assert not self.level.is_safe((1, 0), False)  # Fake tile dangerous without mask
        assert not self.level.is_safe((2, 0), False)  # Empty tile dangerous

        # Test safety with mask
        assert self.level.is_safe((0, 0), True)  # Real tile still safe
        assert self.level.is_safe((1, 0), True)  # Fake tile safe with mask
        assert not self.level.is_safe((2, 0), True)  # Empty tile still dangerous

    def test_exit_detection(self):
        """Test exit tile detection."""
        self.level.exit_pos = (2, 1)

        assert self.level.is_exit_tile((2, 1))
        assert not self.level.is_exit_tile((0, 0))
        assert not self.level.is_exit_tile((1, 1))

    def test_set_tile_type(self):
        """Test changing tile types."""
        from src.the_floor_is_a_lie.tile import Tile

        # Create initial tile
        initial_tile = Tile(self.config, TileType.REAL, (0, 0))
        self.level.grid = [[initial_tile]]

        # Change to fake
        self.level.set_tile_type((0, 0), TileType.FAKE)
        assert self.level.grid[0][0].type == TileType.FAKE

        # Change to start (should update start_pos)
        self.level.set_tile_type((0, 0), TileType.START)
        assert self.level.grid[0][0].type == TileType.START
        assert self.level.start_pos == (0, 0)

        # Change start to exit (should update exit_pos)
        self.level.set_tile_type((0, 0), TileType.EXIT)
        assert self.level.grid[0][0].type == TileType.EXIT
        assert self.level.exit_pos == (0, 0)

    def test_level_info(self):
        """Test getting level information."""
        self.level.name = "Test Level"
        self.level.start_pos = (1, 2)
        self.level.exit_pos = (3, 4)
        self.level.mask_duration = 2.5

        info = self.level.get_level_info()
        assert info['name'] == "Test Level"
        assert info['start_pos'] == (1, 2)
        assert info['exit_pos'] == (3, 4)
        assert info['mask_duration'] == 2.5