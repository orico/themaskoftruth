"""Tests for the Score module."""

from src.the_floor_is_a_lie.config import Config
from src.the_floor_is_a_lie.score import ScoreSystem


class TestScoreSystem:
    """Test cases for ScoreSystem class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.score = ScoreSystem(self.config)

    def test_initialization(self):
        """Test score system initialization."""
        assert self.score.elapsed_time == 0.0
        assert self.score.mask_uses == 0
        assert not self.score.completed
        assert self.score.stars == 0
        assert self.score.time_thresholds == self.config.TIME_THRESHOLDS
        assert self.score.mask_threshold == self.config.MASK_USE_THRESHOLD

    def test_time_tracking(self):
        """Test elapsed time tracking."""
        # Update for 5 seconds
        for _ in range(300):  # 5 seconds at 60 FPS
            self.score.update(1.0 / 60)

        assert (
            abs(self.score.elapsed_time - 5.0) < 0.1
        )  # Allow small floating point error

    def test_mask_usage_tracking(self):
        """Test mask usage counting."""
        assert self.score.mask_uses == 0

        self.score.add_mask_use()
        assert self.score.mask_uses == 1

        self.score.add_mask_use()
        self.score.add_mask_use()
        assert self.score.mask_uses == 3

    def test_star_calculation_perfect(self):
        """Test star calculation for perfect performance."""
        # Fast completion, no mask uses
        self.score.elapsed_time = 10.0  # Well under first threshold
        self.score.mask_uses = 0

        self.score.complete_level()

        assert self.score.stars == 3
        assert self.score.final_time == 10.0
        assert self.score.final_mask_uses == 0
        assert self.score.completed

    def test_star_calculation_good(self):
        """Test star calculation for good performance."""
        # Medium completion time, no mask uses
        self.score.elapsed_time = 40.0  # Between first and second threshold
        self.score.mask_uses = 0

        self.score.complete_level()

        assert self.score.stars == 2

    def test_star_calculation_ok(self):
        """Test star calculation for okay performance."""
        # Slow completion time, no mask uses
        self.score.elapsed_time = 70.0  # Between second and third threshold
        self.score.mask_uses = 0

        self.score.complete_level()

        assert self.score.stars == 1

    def test_star_calculation_poor(self):
        """Test star calculation for poor performance."""
        # Very slow completion time, no mask uses
        self.score.elapsed_time = 150.0  # Over all thresholds
        self.score.mask_uses = 0

        self.score.complete_level()

        assert self.score.stars == 0

    def test_mask_penalty(self):
        """Test star reduction due to excessive mask usage."""
        # Fast completion but too many mask uses
        self.score.elapsed_time = 10.0
        self.score.mask_uses = 10  # Over threshold

        self.score.complete_level()

        assert self.score.stars == 2  # Should be reduced from 3 to 2

    def test_combined_penalties(self):
        """Test star calculation with both time and mask penalties."""
        # Slow completion and excessive mask usage
        self.score.elapsed_time = 70.0  # Would give 1 star
        self.score.mask_uses = 10  # Would reduce by 1

        self.score.complete_level()

        assert self.score.stars == 0  # 1 - 1 = 0, clamped to 0

    def test_time_formatting(self):
        """Test time formatting for display."""
        # Test various times
        assert self.score.get_time_formatted(0) == "00:00"
        assert self.score.get_time_formatted(59) == "00:59"
        assert self.score.get_time_formatted(60) == "01:00"
        assert self.score.get_time_formatted(125) == "02:05"
        assert self.score.get_time_formatted(3661) == "61:01"

        # Test with current elapsed time
        self.score.elapsed_time = 90.5
        assert self.score.get_time_formatted() == "01:30"

    def test_star_display(self):
        """Test star display formatting."""
        assert self.score.get_star_display(0) == "☆☆☆"
        assert self.score.get_star_display(1) == "★☆☆"
        assert self.score.get_star_display(2) == "★★☆"
        assert self.score.get_star_display(3) == "★★★"

        # Test with current stars
        self.score.stars = 2
        assert self.score.get_star_display() == "★★☆"

    def test_performance_rating(self):
        """Test performance rating descriptions."""
        self.score.stars = 3
        assert self.score.get_performance_rating() == "Perfect!"

        self.score.stars = 2
        assert self.score.get_performance_rating() == "Good!"

        self.score.stars = 1
        assert self.score.get_performance_rating() == "OK"

        self.score.stars = 0
        assert self.score.get_performance_rating() == "Try again!"

    def test_score_summary(self):
        """Test complete score summary."""
        self.score.elapsed_time = 45.0
        self.score.mask_uses = 2
        self.score.stars = 2
        self.score.complete_level()

        summary = self.score.get_score_summary()

        assert summary["time"] == "00:45"
        assert summary["mask_uses"] == 2
        assert summary["stars"] == "★★☆"
        assert summary["rating"] == "Good!"
        assert summary["time_thresholds"] == ["00:30", "01:00", "02:00"]
        assert summary["mask_threshold"] == 5

    def test_reset(self):
        """Test score system reset."""
        # Set up some scores
        self.score.elapsed_time = 100.0
        self.score.mask_uses = 5
        self.score.complete_level()

        # Reset
        self.score.reset()

        # Should be back to initial state
        assert self.score.elapsed_time == 0.0
        assert self.score.mask_uses == 0
        assert not self.score.completed
        assert self.score.stars == 0
        assert self.score.final_time == 0.0
        assert self.score.final_mask_uses == 0

    def test_config_updates(self):
        """Test updating scoring configuration."""
        # Update time thresholds
        new_thresholds = [15, 30, 60]
        self.score.set_config(time_thresholds=new_thresholds)
        assert self.score.time_thresholds == new_thresholds

        # Update mask threshold
        self.score.set_config(mask_threshold=8)
        assert self.score.mask_threshold == 8

        # Update both
        self.score.set_config(time_thresholds=[20, 40, 80], mask_threshold=3)
        assert self.score.time_thresholds == [20, 40, 80]
        assert self.score.mask_threshold == 3

    def test_get_current_stats(self):
        """Test getting current game statistics."""
        self.score.elapsed_time = 25.0
        self.score.mask_uses = 2

        stats = self.score.get_current_stats()

        assert stats["elapsed_time"] == 25.0
        assert stats["mask_uses"] == 2
        assert not stats["completed"]
        assert stats["final_time"] == 0.0
        assert stats["final_mask_uses"] == 0
        assert stats["stars"] == 0
