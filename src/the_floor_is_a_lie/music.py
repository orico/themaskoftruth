"""Music module for The Floor Is a Lie."""

import logging
import os
from typing import Optional

import pygame

logger = logging.getLogger(__name__)


class Music:
    """Handles background music playback."""

    def __init__(self, music_file: str, volume: float = 0.5):
        """Initialize music player.

        Args:
            music_file: Path to the music file
            volume: Music volume (0.0 to 1.0)
        """
        self.music_file = music_file
        self.volume = volume
        self.saved_volume = volume  # Remember volume before muting
        self.is_playing = False
        self.is_paused = False
        self.muted = False

        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.load_music()

    def load_music(self) -> bool:
        """Load the music file.

        Returns:
            True if music loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.music_file):
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.set_volume(self.volume)
                logger.info(f"Loaded music: {self.music_file}")
                return True
            else:
                logger.warning(f"Music file not found: {self.music_file}")
                return False
        except pygame.error as e:
            logger.error(f"Failed to load music {self.music_file}: {e}")
            return False

    def play(self, loops: int = -1) -> None:
        """Start playing music.

        Args:
            loops: Number of times to loop (-1 for infinite)
        """
        try:
            if not self.is_playing:
                pygame.mixer.music.play(loops)
                self.is_playing = True
                self.is_paused = False
                logger.info("Started playing background music")
        except pygame.error as e:
            logger.error(f"Failed to play music: {e}")

    def pause(self) -> None:
        """Pause music playback."""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            logger.info("Paused background music")

    def unpause(self) -> None:
        """Resume music playback."""
        if self.is_playing and self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            logger.info("Resumed background music")

    def stop(self) -> None:
        """Stop music playback."""
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            logger.info("Stopped background music")

    def set_volume(self, volume: float) -> None:
        """Set music volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))  # Clamp to valid range
        if not self.muted:
            pygame.mixer.music.set_volume(self.volume)
        else:
            self.saved_volume = self.volume  # Update saved volume while muted
        logger.debug(f"Set music volume to {self.volume}")

    def toggle_pause(self) -> None:
        """Toggle between paused and playing states."""
        if self.is_paused:
            self.unpause()
        else:
            self.pause()

    def toggle_mute(self) -> None:
        """Toggle mute on/off."""
        if self.muted:
            self.unmute()
        else:
            self.mute()

    def mute(self) -> None:
        """Mute the music."""
        if not self.muted:
            self.saved_volume = self.volume
            pygame.mixer.music.set_volume(0.0)
            self.muted = True
            logger.info("Muted background music")

    def unmute(self) -> None:
        """Unmute the music."""
        if self.muted:
            pygame.mixer.music.set_volume(self.saved_volume)
            self.volume = self.saved_volume
            self.muted = False
            logger.info("Unmuted background music")

    def get_status(self) -> dict:
        """Get current music status.

        Returns:
            Dictionary with music status information
        """
        return {
            "is_playing": self.is_playing,
            "is_paused": self.is_paused,
            "volume": self.volume,
            "muted": self.muted,
            "music_file": self.music_file
        }