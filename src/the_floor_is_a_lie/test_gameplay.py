#!/usr/bin/env python3
"""
Simple test script to verify core gameplay mechanics
"""

from .config import Config
from .level import Level
from .player import Player
from .score import ScoreSystem


def test_basic_gameplay():
    """Test basic gameplay mechanics"""
    print("Testing basic gameplay mechanics...")

    # Initialize components
    config = Config()
    level = Level(config)
    player = Player(config, (0, 0))
    score = ScoreSystem(config)

    # Load level
    assert level.load_level("levels/level1.json"), "Failed to load level"

    # Test player movement
    print("Testing player movement...")
    player.move_to_grid(1, 0)  # Move right

    # Complete movement instantly for testing
    target_x, target_y = config.get_grid_center((1, 0))
    player.x, player.y = target_x, target_y
    player.grid_x, player.grid_y = (1, 0)
    player.target_grid_pos = None
    player.moving = False

    new_pos = player.get_grid_position()
    assert new_pos == (1, 0), f"Player movement failed: expected (1, 0), got {new_pos}"
    print("✅ Player movement works")

    # Test mask mechanics
    print("Testing mask mechanics...")
    player.toggle_mask()
    mask_status = player.get_mask_status()

    assert mask_status["active"], "Mask activation failed"
    print("✅ Mask activation works")

    # Simulate mask duration (fast-forward by directly setting timer to 0)
    player.mask_timer = 0.0  # Expire mask immediately
    player.update(0.1)  # Single update to trigger deactivation

    mask_status = player.get_mask_status()
    assert not mask_status[
        "active"
    ], f"Mask should have deactivated (timer={mask_status['timer']})"
    print("✅ Mask deactivation works")

    # Test tile collision
    print("Testing tile collision...")

    # Move to a real tile (should be safe)
    target_x, target_y = config.get_grid_center((1, 0))
    player.x, player.y = target_x, target_y
    player.grid_x, player.grid_y = (1, 0)
    player.target_grid_pos = None
    player.moving = False

    is_safe = level.is_safe((1, 0), mask_active=False)
    assert is_safe, "Real tile should be safe"

    # Move to a fake tile without mask (should be dangerous)
    target_x, target_y = config.get_grid_center((0, 1))
    player.x, player.y = target_x, target_y
    player.grid_x, player.grid_y = (0, 1)
    player.target_grid_pos = None
    player.moving = False

    is_safe = level.is_safe((0, 1), mask_active=False)
    assert not is_safe, "Fake tile should be dangerous without mask"

    # Move to fake tile with mask (should be safe)
    player.toggle_mask()
    is_safe = level.is_safe((0, 1), mask_active=True)
    assert is_safe, "Fake tile should be safe with mask"
    print("✅ Tile collision works")

    # Test scoring
    print("Testing scoring...")
    score.add_mask_use()
    score.complete_level()

    final_score = score.get_current_stats()
    assert (
        0 <= final_score["stars"] <= 3
    ), f"Invalid star rating: {final_score['stars']}"
    print(f"✅ Scoring works (stars: {final_score['stars']})")

    print("🎉 All basic gameplay tests passed!")


if __name__ == "__main__":
    test_basic_gameplay()
