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
    if not level.load_level("levels/level1.json"):
        print("❌ Failed to load level")
        return False

    # Test player movement
    print("Testing player movement...")
    start_pos = player.get_grid_position()
    player.move_to_grid(1, 0)  # Move right

    # Simulate movement completion
    for _ in range(10):  # Simulate 10 frames
        player.update(1.0 / 60)  # 60 FPS

    new_pos = player.get_grid_position()
    if new_pos != (1, 0):
        print(f"❌ Player movement failed: expected (1, 0), got {new_pos}")
        return False
    print("✅ Player movement works")

    # Test mask mechanics
    print("Testing mask mechanics...")
    player.toggle_mask()
    mask_status = player.get_mask_status()

    if not mask_status["active"]:
        print("❌ Mask activation failed")
        return False
    print("✅ Mask activation works")

    # Simulate mask duration
    frames_needed = int(config.MASK_DURATION * 60) + 1  # Add 1 for safety
    for i in range(frames_needed):
        player.update(1.0 / 60)
        if i % 60 == 0:  # Print every second
            print(
                f"  Frame {i}: mask_timer={player.mask_timer:.2f}, active={player.mask_active}"
            )

    mask_status = player.get_mask_status()
    if mask_status["active"]:
        print(f"❌ Mask should have deactivated (timer={mask_status['timer']})")
        return False
    print("✅ Mask deactivation works")

    # Test tile collision
    print("Testing tile collision...")

    # Move to a real tile (should be safe)
    player.move_to_grid(1, 0)
    for _ in range(10):
        player.update(1.0 / 60)

    is_safe = level.is_safe((1, 0), mask_active=False)
    if not is_safe:
        print("❌ Real tile should be safe")
        return False

    # Move to a fake tile without mask (should be dangerous)
    player.move_to_grid(0, 1)  # fake tile position
    for _ in range(10):
        player.update(1.0 / 60)

    is_safe = level.is_safe((0, 1), mask_active=False)
    if is_safe:
        print("❌ Fake tile should be dangerous without mask")
        return False

    # Move to fake tile with mask (should be safe)
    player.toggle_mask()
    is_safe = level.is_safe((0, 1), mask_active=True)
    if not is_safe:
        print("❌ Fake tile should be safe with mask")
        return False
    print("✅ Tile collision works")

    # Test scoring
    print("Testing scoring...")
    score.add_mask_use()
    score.complete_level()

    final_score = score.get_current_stats()
    if final_score["stars"] < 0 or final_score["stars"] > 3:
        print(f"❌ Invalid star rating: {final_score['stars']}")
        return False
    print(f"✅ Scoring works (stars: {final_score['stars']})")

    print("🎉 All basic gameplay tests passed!")
    return True


if __name__ == "__main__":
    test_basic_gameplay()
