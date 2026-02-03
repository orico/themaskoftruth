"""Asset management module for The Floor Is a Lie.

This module provides a centralized asset manager that preloads all sprites and sounds
once at startup and provides cached access to them throughout the game lifecycle.
"""

import logging
from typing import Dict, Optional

import pygame

logger = logging.getLogger(__name__)


class AssetManager:
    """Singleton asset manager that preloads and caches all game assets."""

    _instance: Optional["AssetManager"] = None
    _initialized: bool = False

    def __new__(cls):
        """Ensure only one instance of AssetManager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the asset manager (only runs once)."""
        if AssetManager._initialized:
            return

        logger.info("Initializing AssetManager - preloading all assets...")

        # Sprite storage
        self.sprites: Dict[str, pygame.Surface] = {}
        self.sounds: Dict[str, pygame.mixer.Sound] = {}

        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # Preload all assets
        self._preload_sprites()
        self._preload_sounds()

        AssetManager._initialized = True
        logger.info("AssetManager initialization complete!")

    def _preload_sprites(self):
        """Preload all sprite images."""
        sprite_files = {
            # Player animations
            "player_idle": "sprites/Direct-overhead-2D-perspective-of-a-young-boy-"
            "with-256px-36 (3).png",
            "player_transition": "sprites/transition-from-idle-to-running.png",
            "player_running": "sprites/Direct-overhead-2D-perspective-of-a-young-boy-"
            "with-256px-36 (1).png",
            "player_mask": "sprites/Direct-overhead-2D-perspective-of-a-young-boy-"
            "with-256px-36 (2).png",
            "player_death": "sprites/falling death.png",
            "player_walk_forward": "sprites/walk forward.png",
            "player_walk_backward": "sprites/walk backward.png",
            # Tile sprites
            "tile_real": "sprites/gen-df79415f-5e74-4ac9-86f6-5ee620955741.png",
            "tile_fake": "sprites/gen-9468de96-df80-4f4d-b92f-4a063b5c86b5.png",
            "tile_start": "sprites/door.png",
            "tile_exit": "sprites/open-door.png",
            # UI sprites
            "mask_image": "sprites/gen-a8f9dc3d-d020-40c2-bb6d-22e58d5d0390.png",
            "game_over_menu": "sprites/game-over-menu.png",
            "level_clear": "sprites/level-clear.png",
            "star": "sprites/star2.png",
            "main_menu": "sprites/main-menu.png",
        }

        for sprite_id, sprite_path in sprite_files.items():
            try:
                sprite = pygame.image.load(sprite_path).convert_alpha()
                self.sprites[sprite_id] = sprite
                logger.debug(f"Loaded sprite '{sprite_id}': {sprite_path}")
            except (pygame.error, FileNotFoundError) as e:
                logger.warning(
                    f"Failed to load sprite '{sprite_id}' from {sprite_path}: {e}"
                )
                self.sprites[sprite_id] = None

    def _preload_sounds(self):
        """Preload all sound effects."""
        sound_files = {
            "fake_tile_fall": "sound/aww.mp3",
            "fake_tile_fall_thump": "sound/aww.mp3",
            "level_complete": "sound/audio-multiple-instruments-in-an-orchestra-doing-"
            "for-lev.mp3",
            "mask_activate": "sound/audio-mortal-kombat-announcer-shouting-.mp3",
            "mask_ready": "sound/mask-ready.mp3",
            "mask_recharging": "sound/mask-recharging.mp3",
            "reach_the_exit": "sound/reach-the-exit-3-press_speed_25pct.mp3",
        }

        for sound_id, sound_path in sound_files.items():
            try:
                sound = pygame.mixer.Sound(sound_path)
                self.sounds[sound_id] = sound
                logger.debug(f"Loaded sound '{sound_id}': {sound_path}")
            except (pygame.error, FileNotFoundError) as e:
                logger.warning(
                    f"Failed to load sound '{sound_id}' from {sound_path}: {e}"
                )
                self.sounds[sound_id] = None

    def get_sprite(self, sprite_id: str) -> Optional[pygame.Surface]:
        """Get a preloaded sprite by ID.

        Args:
            sprite_id: Identifier for the sprite

        Returns:
            The sprite surface, or None if not found
        """
        sprite = self.sprites.get(sprite_id)
        if sprite is None:
            logger.warning(f"Sprite '{sprite_id}' not found in asset cache")
        return sprite

    def get_sound(self, sound_id: str) -> Optional[pygame.mixer.Sound]:
        """Get a preloaded sound by ID.

        Args:
            sound_id: Identifier for the sound

        Returns:
            The sound object, or None if not found
        """
        sound = self.sounds.get(sound_id)
        if sound is None:
            logger.warning(f"Sound '{sound_id}' not found in asset cache")
        return sound

    def is_sprite_loaded(self, sprite_id: str) -> bool:
        """Check if a sprite is loaded.

        Args:
            sprite_id: Identifier for the sprite

        Returns:
            True if sprite is loaded, False otherwise
        """
        return sprite_id in self.sprites and self.sprites[sprite_id] is not None

    def is_sound_loaded(self, sound_id: str) -> bool:
        """Check if a sound is loaded.

        Args:
            sound_id: Identifier for the sound

        Returns:
            True if sound is loaded, False otherwise
        """
        return sound_id in self.sounds and self.sounds[sound_id] is not None


# Global function to get the singleton instance
def get_asset_manager() -> AssetManager:
    """Get the global AssetManager instance.

    Returns:
        The singleton AssetManager instance
    """
    return AssetManager()
