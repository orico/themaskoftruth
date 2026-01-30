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
from .player import Player
from .score import ScoreSystem
from .ui import RESTART_GAME_EVENT, UI

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

        # Game state
        self.game_state = "playing"  # menu, playing, game_over, level_editor
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

    def initialize_game(self):
        """Initialize or reset game modules."""
        logger.debug("Initializing game modules...")
        self.level = Level(self.config)
        self.player = Player(self.config, self.level.start_pos)
        self.score_system = ScoreSystem(self.config)
        self.ui = UI(self.config, self.ui_manager)

        # Load levels configuration
        if not self.load_levels_config():
            logger.warning(
                "Failed to load levels config, falling back to default level"
            )
            self.create_default_level()
            return

        # Load first level
        self.current_level_index = 0
        if not self.load_level_by_index(self.current_level_index):
            logger.warning("Failed to load first level, creating default level...")
            self.create_default_level()

        logger.debug("Game modules initialized")

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

                # Handle UI-specific events
                self.ui.handle_ui_events(event)

                # Handle game-specific events
                if self.game_state == "playing":
                    self.handle_game_events(event)
                elif self.game_state == "level_editor":
                    self.handle_editor_events(event)
                elif self.game_state == "game_over":
                    # Handle restart events in game over state
                    if (
                        event.type == pygame.KEYDOWN and event.key == pygame.K_r
                    ) or event.type == RESTART_GAME_EVENT:
                        logger.info(
                            "Restart triggered during game over - restarting game"
                        )
                        self.restart_game()

            # Update game state
            if self.game_state == "playing":
                self.update_playing(time_delta)
            elif self.game_state == "level_editor":
                self.level_editor.update(time_delta)

            # Update UI
            self.ui_manager.update(time_delta)

            # Render
            self.render()

        logger.info("Game loop ended")
        pygame.quit()
        sys.exit()

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

                # If mask was just activated (not deactivated), increment score counter
                if not was_active and mask_status["active"]:
                    self.score_system.add_mask_use()
                    logger.info(
                        f"Mask use counted - total uses: {self.score_system.mask_uses}"
                    )
            elif event.key == pygame.K_r:
                logger.info("R key pressed - restarting game")
                self.restart_game()
            elif event.key == pygame.K_e:
                logger.info("E key pressed - entering level editor")
                self.enter_level_editor()

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
            self.game_over()

    def game_win(self):
        """Handle game win condition."""
        self.score_system.complete_level()

        # Check if there's a next level
        next_level_index = self.get_next_level_index()
        if next_level_index is not None:
            logger.info(f"Level completed! Loading next level: {next_level_index + 1}")
            self.load_next_level()
        else:
            logger.info("All levels completed!")
            self.ui.show_win_screen(self.score_system)
            self.game_state = "game_over"

    def game_over(self):
        """Handle game over condition."""
        self.ui.show_game_over_screen(self.score_system)
        self.game_state = "game_over"

    def restart_game(self):
        """Restart the current level."""
        logger.info("Restarting game")
        # Hide result screen before reinitializing
        if self.ui:
            self.ui.hide_result_screen()
            self.ui.cleanup()
        self.initialize_game()
        self.game_state = "playing"

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

    def render(self):
        """Render the current game state."""
        logger.debug(f"Rendering game state: {self.game_state}")
        self.screen.fill(self.config.BACKGROUND_COLOR)

        if self.game_state == "playing":
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
            self.ui.render_game_ui(self.player, self.score_system)

        elif self.game_state == "level_editor":
            self.level_editor.render(self.screen)

        # Render UI manager (buttons, dialogs, etc.)
        self.ui_manager.draw_ui(self.screen)

        pygame.display.flip()
