#!/usr/bin/env python3
"""
Score module for The Floor Is a Lie
Handles time tracking, mask usage counting, and star calculation
"""

from typing import List

from .config import Config


class ScoreSystem:
    """Score and statistics tracking system"""

    def __init__(self, config: Config):
        self.config = config

        # Current level statistics
        self.elapsed_time = 0.0
        self.mask_uses = 0
        self.completed = False
        self.final_time = 0.0
        self.final_mask_uses = 0
        self.stars = 0

        # Configuration (can be updated from level)
        self.time_thresholds: List[float] = (
            config.TIME_THRESHOLDS.copy()
        )  # seconds for 3, 2, 1 stars
        self.mask_threshold: int = config.MASK_USE_THRESHOLD  # max uses before penalty

    def update(self, delta_time: float):
        """Update elapsed time"""
        if not self.completed:
            self.elapsed_time += delta_time

    def add_mask_use(self):
        """Increment mask usage counter"""
        self.mask_uses += 1

    def complete_level(self):
        """Mark level as completed and calculate final score"""
        self.completed = True
        self.final_time = self.elapsed_time
        self.final_mask_uses = self.mask_uses
        self.stars = self.calculate_stars()

    def calculate_stars(self) -> int:
        """Calculate star rating based on time and mask usage"""
        if not self.completed:
            return 0

        # Start with maximum stars
        stars = 3

        # Reduce stars based on completion time
        for threshold in sorted(self.time_thresholds, reverse=True):
            if self.final_time > threshold:
                stars -= 1
                if stars < 1:
                    stars = 1
                    break

        # Apply mask usage penalty
        if self.final_mask_uses > self.mask_threshold:
            stars -= 1
            if stars < 0:
                stars = 0

        return max(0, min(3, stars))  # Clamp between 0 and 3

    def reset(self):
        """Reset score for new level attempt"""
        self.elapsed_time = 0.0
        self.mask_uses = 0
        self.completed = False
        self.final_time = 0.0
        self.final_mask_uses = 0
        self.stars = 0

    def set_config(
        self, time_thresholds: List[float] = None, mask_threshold: int = None
    ):
        """Update scoring configuration"""
        if time_thresholds is not None:
            self.time_thresholds = time_thresholds.copy()
        if mask_threshold is not None:
            self.mask_threshold = mask_threshold

    def get_current_stats(self) -> dict:
        """Get current game statistics"""
        return {
            "elapsed_time": self.elapsed_time,
            "mask_uses": self.mask_uses,
            "completed": self.completed,
            "final_time": self.final_time,
            "final_mask_uses": self.final_mask_uses,
            "stars": self.stars,
        }

    def get_time_formatted(self, time_seconds: float = None) -> str:
        """Format time in MM:SS format"""
        if time_seconds is None:
            time_seconds = self.elapsed_time

        minutes = int(time_seconds // 60)
        seconds = int(time_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def get_star_display(self, stars: int = None) -> str:
        """Get star rating display string"""
        if stars is None:
            stars = self.stars

        star_symbols = "★★★"
        empty_symbols = "☆☆☆"
        return star_symbols[:stars] + empty_symbols[stars:]

    def get_performance_rating(self) -> str:
        """Get performance rating description"""
        if self.stars == 3:
            return "Perfect!"
        elif self.stars == 2:
            return "Good!"
        elif self.stars == 1:
            return "OK"
        else:
            return "Try again!"

    def get_score_summary(self) -> dict:
        """Get complete score summary for display"""
        return {
            "time": self.get_time_formatted(self.final_time),
            "mask_uses": self.final_mask_uses,
            "stars": self.get_star_display(),
            "rating": self.get_performance_rating(),
            "time_thresholds": [
                self.get_time_formatted(t) for t in self.time_thresholds
            ],
            "mask_threshold": self.mask_threshold,
        }
