"""Sound effects module for The Floor Is a Lie."""

import logging
from typing import Dict

import pygame

from .assets import get_asset_manager

logger = logging.getLogger(__name__)


class SoundEffects:
    """Handles sound effect playback."""

    def __init__(self):
        """Initialize sound effects manager."""
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.volume = 0.7  # Default volume for sound effects

        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # Load all sounds from asset manager
        self._load_sounds_from_asset_manager()

    def _load_sounds_from_asset_manager(self):
        """Load all sound effects from the asset manager."""
        asset_manager = get_asset_manager()

        # Map of sound IDs used in game to asset manager IDs
        sound_mappings = {
            "fake_tile_fall": "fake_tile_fall",
            "fake_tile_fall_thump": "fake_tile_fall_thump",
            "level_complete": "level_complete",
            "mask_activate": "mask_activate",
            "reach_the_exit": "reach_the_exit",
        }

        for sound_id, asset_id in sound_mappings.items():
            sound = asset_manager.get_sound(asset_id)
            if sound:
                self.sounds[sound_id] = sound
                self.sounds[sound_id].set_volume(self.volume)
                logger.debug(f"Loaded sound effect '{sound_id}' from asset manager")
            else:
                logger.warning(f"Failed to load sound '{sound_id}' from asset manager")

    def load_sound(self, sound_id: str, sound_file: str) -> bool:
        """Load a sound effect (deprecated - now loads from asset manager).

        This method is kept for backwards compatibility but now uses preloaded sounds.

        Args:
            sound_id: Unique identifier for this sound effect
            sound_file: Path to the sound file (ignored, uses asset manager)

        Returns:
            True if sound loaded successfully, False otherwise
        """
        # Sound is already loaded from asset manager in __init__
        return sound_id in self.sounds

    def play_sound(self, sound_id: str) -> bool:
        """Play a sound effect.

        Args:
            sound_id: Identifier of the sound effect to play

        Returns:
            True if sound played successfully, False otherwise
        """
        try:
            if sound_id in self.sounds:
                self.sounds[sound_id].play()
                logger.debug(f"Playing sound effect: {sound_id}")
                return True
            else:
                logger.warning(f"Sound effect '{sound_id}' not found")
                return False
        except pygame.error as e:
            logger.error(f"Failed to play sound '{sound_id}': {e}")
            return False

    def set_volume(self, volume: float) -> None:
        """Set volume for all sound effects.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))  # Clamp to valid range
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
        logger.debug(f"Set sound effects volume to {self.volume}")

    def stop_all_sounds(self) -> None:
        """Stop all currently playing sound effects."""
        for sound in self.sounds.values():
            sound.stop()
        logger.debug("Stopped all sound effects")

    def get_loaded_sounds(self) -> list[str]:
        """Get list of loaded sound effect IDs.

        Returns:
            List of sound effect IDs that have been loaded
        """
        return list(self.sounds.keys())
