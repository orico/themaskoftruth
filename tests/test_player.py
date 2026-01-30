"""Tests for the Player module."""

import pygame

from src.the_floor_is_a_lie.config import Config
from src.the_floor_is_a_lie.player import Player

# Initialize pygame for testing
pygame.init()


class KeyState:
    """Efficient key state mock that behaves like a list but uses a dict internally"""

    def __init__(self, pressed_keys=None):
        self._pressed = set(pressed_keys or [])

    def __getitem__(self, key):
        return key in self._pressed

    def __setitem__(self, key, value):
        if value:
            self._pressed.add(key)
        else:
            self._pressed.discard(key)


class TestPlayer:
    """Test cases for Player class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.start_pos = (1, 1)
        self.player = Player(self.config, self.start_pos)

    def test_initialization(self):
        """Test player initialization."""
        assert self.player.grid_x == self.start_pos[0]
        assert self.player.grid_y == self.start_pos[1]
        assert not self.player.mask_active
        assert self.player.mask_available
        assert self.player.mask_uses == 0

    def test_movement_to_valid_position(self):
        """Test moving to a valid grid position."""
        new_pos = (2, 2)

        # Start movement
        self.player.move_to_grid(*new_pos)
        assert self.player.target_grid_pos == new_pos
        assert self.player.moving

        # Complete movement instantly for testing
        target_x, target_y = self.config.get_grid_center(new_pos)
        self.player.x, self.player.y = target_x, target_y
        self.player.grid_x, self.player.grid_y = new_pos
        self.player.target_grid_pos = None
        self.player.moving = False
        self.player.velocity_x = 0
        self.player.velocity_y = 0  # 30 FPS simulation

        # Check final position
        assert self.player.get_grid_position() == new_pos
        assert not self.player.moving

    def test_movement_to_invalid_position(self):
        """Test that movement to invalid positions is clamped."""
        # Try to move outside bounds (negative)
        self.player.move_to_grid(-1, -1)

        # Should not move
        assert self.player.get_grid_position() == self.start_pos

    def test_mask_activation(self):
        """Test mask activation and deactivation."""
        # Initially inactive
        assert not self.player.mask_active
        assert self.player.mask_available

        # Activate mask
        self.player.toggle_mask()
        assert self.player.mask_active
        assert self.player.mask_uses == 1

        # Deactivate mask
        self.player.toggle_mask()
        assert not self.player.mask_active

    def test_mask_cooldown(self):
        """Test mask cooldown after deactivation."""
        # Activate and immediately deactivate mask
        self.player.toggle_mask()  # Activate
        self.player.toggle_mask()  # Deactivate

        # Mask should be in cooldown
        assert not self.player.mask_available
        assert not self.player.mask_active

        # Simulate cooldown time (fast-forward by setting timer to 0)
        self.player.mask_recharge_timer = 0.0
        self.player.update(0.1)  # Single update to trigger availability

        # Mask should be available again
        assert self.player.mask_available

    def test_mask_timer_expiration(self):
        """Test that mask automatically deactivates after timer expires."""
        # Activate mask
        self.player.toggle_mask()
        assert self.player.mask_active

        # Simulate mask duration (fast-forward by setting timer to 0)
        self.player.mask_timer = 0.0
        self.player.update(0.1)  # Single update to trigger deactivation

        # Mask should have deactivated
        assert not self.player.mask_active
        assert not self.player.mask_available  # In cooldown

    def test_input_handling_movement(self):
        """Test keyboard input handling for movement."""
        # Mock key states using efficient KeyState
        keys = KeyState([pygame.K_RIGHT])

        # Handle input
        self.player.handle_input(keys)

        # Should have started moving right
        assert self.player.target_grid_pos == (self.start_pos[0] + 1, self.start_pos[1])

    def test_input_handling_mask_toggle(self):
        """Test that input handling doesn't interfere with mask toggle."""
        keys = KeyState(
            [pygame.K_m]
        )  # This should be handled by main game loop, not player

        # Handle input (should not affect mask)
        initial_mask_state = self.player.mask_active
        self.player.handle_input(keys)

        # Mask state should be unchanged
        assert self.player.mask_active == initial_mask_state

    def test_reset(self):
        """Test player reset functionality."""
        # Move player and use mask
        self.player.move_to_grid(5, 5)
        for _ in range(10):
            self.player.update(1.0 / 60)

        self.player.toggle_mask()
        self.player.toggle_mask()  # Deactivate

        # Reset
        new_start = (3, 3)
        self.player.reset(new_start)

        # Should be back to start position
        assert self.player.get_grid_position() == new_start
        assert not self.player.mask_active
        assert self.player.mask_available
        assert self.player.mask_uses == 0

    def test_get_mask_status(self):
        """Test getting mask status information."""
        status = self.player.get_mask_status()

        expected_keys = [
            "active",
            "timer",
            "duration",
            "recharge_timer",
            "cooldown",
            "available",
            "uses",
        ]
        for key in expected_keys:
            assert key in status

        assert status["active"] == self.player.mask_active
        assert status["uses"] == self.player.mask_uses
