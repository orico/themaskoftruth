"""Main game class for The Floor Is a Lie."""

import json
import logging
import sys
from typing import Dict, List, Optional

import pygame
import pygame_gui

from .config import Config
from .level import Level
from .level_editor import LevelEditor
from .music import Music
from .player import Player
from .score import ScoreSystem
from .sound_effects import SoundEffects
from .ui import (
    CONTINUE_TO_NEXT_LEVEL_EVENT,
    RESTART_FROM_LEVEL_1_EVENT,
    RESTART_GAME_EVENT,
    START_MUSIC_EVENT,
    UI,
)

logger = logging.getLogger(__name__)


class Game:
    """Main game class that orchestrates all modules."""

    def __init__(self):
        logger.info("Initializing game...")
        pygame.init()

        # Load configuration
        self.config = Config()

        # Set up display
        self.screen = pygame.display.set_mode(
            (self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption("The Floor Is a Lie")

        # Initialize GUI manager
        self.ui_manager = pygame_gui.UIManager(
            (self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT)
        )
        # Load transparent button theme
        try:
            self.ui_manager.get_theme().load_theme_file(
                "themes/transparent_buttons.json"
            )
        except Exception as e:
            logger.warning(f"Failed to load transparent button theme: {e}")

        # Game state
        self.game_state = "menu"  # menu, playing, game_over, level_editor
        self.clock = pygame.time.Clock()

        # Level management
        self.levels_config: List[Dict] = []
        self.current_level_index = 0

        # Initialize game modules
        self.player: Optional[Player] = None
        self.level: Optional[Level] = None
        self.score_system: Optional[ScoreSystem] = None
        self.ui: Optional[UI] = None
        self.level_editor: Optional[LevelEditor] = None
        self.music: Optional[Music] = None
        self.sound_effects: Optional[SoundEffects] = None

        # Initialize game
        self.initialize_game()
        logger.info("Game initialized successfully")

    def load_levels_config(self) -> bool:
        """Load levels configuration from file."""
        try:
            config_path = "levels/levels_config.json"
            with open(config_path, "r") as f:
                config_data = json.load(f)
                self.levels_config = config_data.get("levels", [])
                logger.info(f"Loaded {len(self.levels_config)} levels from config")
                return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load levels config: {e}")
            return False

    def load_level_by_index(self, level_index: int) -> bool:
        """Load a specific level by index from the levels config."""
        if not self.levels_config:
            logger.warning("No levels config loaded")
            return False

        if level_index < 0 or level_index >= len(self.levels_config):
            logger.warning(f"Invalid level index: {level_index}")
            return False

        level_data = self.levels_config[level_index]
        level_file = f"levels/{level_data['file']}"

        logger.info(
            f"Loading level {level_index + 1}: {level_data['name']} ({level_file})"
        )

        # Update window title with level name
        pygame.display.set_caption(f"{level_data['name']} - Level {level_index + 1}")

        return self.level.load_level(level_file)

    def get_next_level_index(self) -> Optional[int]:
        """Get the index of the next level, or None if no more levels."""
        next_index = self.current_level_index + 1
        if next_index < len(self.levels_config):
            return next_index
        return None

    def load_next_level(self):
        """Load the next level in sequence."""
        next_level_index = self.get_next_level_index()
        if next_level_index is not None:
            # Load the next level first
            self.current_level_index = next_level_index
            if not self.load_level_by_index(self.current_level_index):
                logger.error(f"Failed to load next level {self.current_level_index}")
                self.game_over()
                return

            # Reset game modules for new level
            self.player.reset(self.level.start_pos)
            self.score_system.reset()

            logger.info(f"Successfully loaded level {self.current_level_index + 1}")
        else:
            logger.info("No more levels to load")

    def initialize_game(self, level_index: Optional[int] = None):
        """Initialize or reset game modules.

        Args:
            level_index: If provided, load this specific level.
                If None, use current_level_index.
        """
        logger.debug("Initializing game modules...")

        # Clean up old UI if it exists
        if self.ui:
            self.ui.cleanup()

        self.level = Level(self.config)
        self.score_system = ScoreSystem(self.config)
        self.ui = UI(self.config, self.ui_manager)
        self.music = Music(self.config.MUSIC_FILE, self.config.MUSIC_VOLUME)
        self.sound_effects = SoundEffects()

        # Load sound effects
        self.sound_effects.load_sound(
            "fake_tile_fall", "sound/audio-Shattered-glass.mp3"
        )
        self.sound_effects.load_sound(
            "fake_tile_fall_thump", "sound/audio-falling-sound-ending-with-a-thump.mp3"
        )
        self.sound_effects.load_sound(
            "level_complete",
            "sound/audio-multiple-instruments-in-an-orchestra-doing-for-lev.mp3",
        )
        self.sound_effects.load_sound(
            "mask_activate", "sound/audio-mortal-kombat-announcer-shouting-.mp3"
        )
        self.sound_effects.load_sound(
            "reach_the_exit", "sound/reach-the-exit_speed_25pct.mp3"
        )

        # Load levels configuration
        if not self.load_levels_config():
            logger.warning(
                "Failed to load levels config, falling back to default level"
            )
            self.create_default_level()
            # Create player AFTER level is loaded
            self.player = Player(self.config, self.level.start_pos)
            return

        # Load specified level or current level
        if level_index is not None:
            self.current_level_index = level_index

        if not self.load_level_by_index(self.current_level_index):
            logger.warning(
                f"Failed to load level {self.current_level_index}, "
                "creating default level..."
            )
            self.create_default_level()

        # Create player AFTER level is loaded so it gets the correct start position
        self.player = Player(self.config, self.level.start_pos)

        logger.debug(
            f"Game modules initialized with level {self.current_level_index + 1}"
        )

    def create_default_level(self):
        """Create a basic default level if none exists."""
        import json
        import os

        os.makedirs("levels", exist_ok=True)

        # Load default level template
        default_level_path = "levels/default_level.json"
        with open(default_level_path, "r") as f:
            default_level = json.load(f)

        # Write to level1.json as the actual level file
        with open("levels/level1.json", "w") as f:
            json.dump(default_level, f, indent=2)

        self.level.load_level("levels/level1.json")

        # Update window title for default level
        pygame.display.set_caption("The Floor Is a Lie - Level 1 (Default)")

    def run(self):
        """Main game loop."""
        logger.info("Starting main game loop")
        running = True

        while running:
            time_delta = self.clock.tick(self.config.FPS) / 1000.0

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    logger.info("Quit event received")
                    running = False

                # Handle UI events
                self.ui_manager.process_events(event)

                # Handle UI-specific events (check all events)
                self.ui.handle_ui_events(event)

                # Handle start music event (timer after intro sound)
                if event.type == START_MUSIC_EVENT:
                    logger.info("Intro sound finished - starting background music")
                    if self.music:
                        self.music.play()

                # Handle game-specific events
                if self.game_state == "menu":
                    self.handle_menu_events(event)
                elif self.game_state == "playing":
                    self.handle_game_events(event)
                elif self.game_state == "level_editor":
                    self.handle_editor_events(event)
                elif self.game_state == "game_over":
                    # Handle restart events in game over state
                    if (
                        event.type == pygame.KEYDOWN and event.key == pygame.K_r
                    ) or event.type == RESTART_GAME_EVENT:
                        logger.info(
                            f"Restarting current level {self.current_level_index + 1}"
                        )
                        self.restart_game()
                    elif event.type == RESTART_FROM_LEVEL_1_EVENT:
                        logger.info("Restarting from level 1")
                        self.restart_from_level_1()
                    elif event.type == CONTINUE_TO_NEXT_LEVEL_EVENT:
                        logger.info("Continuing to next level")
                        self.continue_to_next_level()
                elif self.game_state == "level_clear":
                    # Handle any key press to continue to next level
                    if event.type == pygame.KEYDOWN:
                        logger.info("Any key pressed - continuing to next level")
                        self.continue_to_next_level()
                    elif event.type == CONTINUE_TO_NEXT_LEVEL_EVENT:
                        logger.info("Continuing to next level")
                        self.continue_to_next_level()

            # Update game state
            if self.game_state == "playing":
                self.update_playing(time_delta)
            elif self.game_state == "level_editor":
                self.level_editor.update(time_delta)

            # Update UI
            self.ui_manager.update(time_delta)
            # Update color cycle for menu and other states that use it
            self.ui.update_color_cycle(time_delta)

            # Render
            self.render()

        logger.info("Game loop ended")
        pygame.quit()
        sys.exit()

    def _start_music_sequence(self):
        """Start the music sequence: play intro sound first, then music."""
        if self.sound_effects:
            self.sound_effects.play_sound("reach_the_exit")
        # Start music after 2.85s delay (2850ms) - 25% reduction from 3.8s
        pygame.time.set_timer(START_MUSIC_EVENT, 2850, loops=1)

    def handle_menu_events(self, event):
        """Handle events in the main menu."""
        if event.type == pygame.KEYDOWN:
            logger.info("Any key pressed in menu - starting game")
            # Start the game by loading the first level
            self.initialize_game(level_index=0)
            self.game_state = "playing"
            # Start the music sequence: intro sound first, then music
            self._start_music_sequence()

    def handle_game_events(self, event):
        """Handle events during gameplay."""
        if event.type == pygame.KEYDOWN:
            logger.debug(f"Key pressed: {pygame.key.name(event.key)}")
            if event.key == pygame.K_m:
                logger.info("M key pressed - toggling mask")
                was_active = self.player.mask_active
                self.player.toggle_mask()
                mask_status = self.player.get_mask_status()
                logger.info(f"Mask status after toggle: active={mask_status['active']}")

                # If mask was just activated (not deactivated),
                # increment score counter and play sound
                if not was_active and mask_status["active"]:
                    self.score_system.add_mask_use()
                    logger.info(
                        f"Mask use counted - total uses: {self.score_system.mask_uses}"
                    )
                    # Play mask activation sound
                    self.sound_effects.play_sound("mask_activate")
            elif event.key == pygame.K_r:
                logger.info("R key pressed - restarting game")
                self.restart_game()
            elif event.key == pygame.K_e:
                logger.info("E key pressed - entering level editor")
                self.enter_level_editor()
            elif event.key == pygame.K_b:
                logger.info("B key pressed - toggling background music")
                if self.music:
                    self.music.toggle_pause()
            elif event.key == pygame.K_u:
                logger.info("U key pressed - toggling music mute")
                if self.music:
                    self.music.toggle_mute()
            elif event.key == pygame.K_s:
                logger.info("S key pressed - toggling sound effects mute")
                if self.sound_effects:
                    self.sound_effects.toggle_mute()
            elif event.key == pygame.K_c:
                logger.info("C key pressed - cheat: teleporting to yellow block (exit)")
                # Teleport player instantly to exit position
                self.player.grid_x, self.player.grid_y = self.level.exit_pos
                self.player.x, self.player.y = self.config.get_grid_center(
                    self.level.exit_pos
                )
                self.player.target_grid_pos = None
                self.player.velocity_x = 0
                self.player.velocity_y = 0
                self.player.moving = False

        # Handle movement input
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys, self.level)

    def handle_editor_events(self, event):
        """Handle events in level editor."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                logger.info("ESC key pressed - exiting level editor")
                self.exit_level_editor()

        self.level_editor.handle_events(event)

    def update_playing(self, delta_time):
        """Update game logic during play."""
        # Update player
        self.player.update(delta_time)

        # Update score system
        self.score_system.update(delta_time)

        # Check collisions and game state
        player_pos = self.player.get_grid_position()

        # Check if player reached exit
        if self.level.is_exit_tile(player_pos):
            logger.info("Player reached exit - game won!")
            self.game_win()

        # Check if player fell (on empty tile)
        elif self.level.is_empty_tile(player_pos):
            logger.warning("Player fell on empty tile - game over!")
            self.game_over()

        # Check if player stepped on fake tile (always dangerous)
        elif self.level.is_fake_tile(player_pos):
            logger.warning("Player stepped on fake tile - game over!")
            # Play fake tile falling sound effects
            self.sound_effects.play_sound("fake_tile_fall")
            self.sound_effects.play_sound("fake_tile_fall_thump")
            self.game_over()

    def game_win(self):
        """Handle game win condition."""
        # Play level completion sound
        self.sound_effects.play_sound("level_complete")

        self.score_system.complete_level()

        # Show level clear screen for every level completion
        logger.info(f"Level {self.current_level_index + 1} completed!")
        self.ui.show_win_screen(self.score_system)
        self.game_state = "level_clear"

    def game_over(self):
        """Handle game over condition."""
        logger.info(f"Game over on level {self.current_level_index + 1}")
        self.ui.show_game_over_screen(self.score_system)
        self.game_state = "game_over"

    def restart_game(self):
        """Restart the current level."""
        logger.debug(f"Restarting level {self.current_level_index + 1}")
        # Store current level index before reinitializing
        current_idx = self.current_level_index
        # Hide result screen before reinitializing
        if self.ui:
            self.ui.hide_result_screen()
            self.ui.cleanup()
        self.initialize_game(level_index=current_idx)  # Explicitly pass current level
        self.game_state = "playing"
        # Start the music sequence: intro sound first, then music
        self._start_music_sequence()

    def continue_to_next_level(self):
        """Continue to the next level or restart from level 1 if final level."""
        # Hide result screen before continuing
        if self.ui:
            self.ui.hide_result_screen()

        next_level_index = self.get_next_level_index()
        if next_level_index is not None:
            logger.info(f"Continuing to level {next_level_index + 1}")
            self.initialize_game(level_index=next_level_index)
        else:
            # Final level completed - restart from level 1
            logger.info("All levels completed! Restarting from level 1")
            self.initialize_game(level_index=0)

        self.game_state = "playing"
        # Start the music sequence: intro sound first, then music
        self._start_music_sequence()

    def restart_from_level_1(self):
        """Restart from level 1."""
        logger.debug("Restarting from level 1")
        # Hide result screen before reinitializing
        if self.ui:
            self.ui.hide_result_screen()
            self.ui.cleanup()
        self.initialize_game(level_index=0)  # Start from level 1
        self.game_state = "playing"
        # Start the music sequence: intro sound first, then music
        self._start_music_sequence()

    def enter_level_editor(self):
        """Switch to level editor mode."""
        # Always create a fresh level editor instance to avoid UI cleanup issues
        if self.level_editor is not None:
            self.level_editor.cleanup()
        self.level_editor = LevelEditor(self.config, self.ui_manager, self.level)

        self.game_state = "level_editor"

    def exit_level_editor(self):
        """Exit level editor and return to game."""
        # Clean up level editor
        if self.level_editor:
            self.level_editor.cleanup()

        self.game_state = "playing"
        # Reload level if it was modified
        if self.level_editor and self.level_editor.modified:
            logger.info("Level was modified, reloading...")
            self.initialize_game()
            # Start the music sequence: intro sound first, then music
            self._start_music_sequence()

    def render(self):
        """Render the current game state."""
        logger.debug(f"Rendering game state: {self.game_state}")
        self.screen.fill(self.config.BACKGROUND_COLOR)

        if self.game_state == "menu":
            # Render main menu
            self.ui.render_main_menu(self.screen)

        elif self.game_state == "playing":
            # Render level
            mask_active = self.player.mask_active if self.player else False
            logger.debug(f"Rendering level with mask_active={mask_active}")
            self.level.render(self.screen, mask_active)

            # Render player
            if self.player:
                player_pos = self.player.get_screen_position()
                logger.debug(f"Rendering player at screen position: {player_pos}")
                self.player.render(self.screen)
            else:
                logger.warning("No player object to render!")

            # Render UI overlays
            self.ui.render_game_ui(self.screen, self.player, self.score_system)

            # Render mask image overlay (if active)
            if self.player:
                mask_status = self.player.get_mask_status()
                self.ui.render_mask_image(self.screen, mask_status)

        elif self.game_state == "level_editor":
            self.level_editor.render(self.screen)

        elif self.game_state == "game_over":
            # Render game over sprite
            self.ui.render_game_over_sprite(self.screen)

        elif self.game_state == "level_clear":
            # Render level clear sprite
            self.ui.render_level_clear_sprite(self.screen)

        # Render UI manager (buttons, dialogs, etc.)
        self.ui_manager.draw_ui(self.screen)

        pygame.display.flip()
