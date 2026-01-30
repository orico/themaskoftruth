#!/usr/bin/env python3
"""
UI module for The Floor Is a Lie
Handles user interface elements, timers, and result screens
"""

import logging
from typing import Any, Dict

import pygame
import pygame_gui

from .config import Config
from .player import Player
from .score import ScoreSystem

logger = logging.getLogger(__name__)

# Custom events
# NOTE: pygame_gui uses USEREVENT + 1 through USEREVENT + 20 for its own events
# So we need to start our custom events after that range
RESTART_GAME_EVENT = pygame.USEREVENT + 100
RESTART_FROM_LEVEL_1_EVENT = pygame.USEREVENT + 101


class UI:
    """User Interface management class"""

    def __init__(self, config: Config, ui_manager: pygame_gui.UIManager):
        self.config = config
        self.ui_manager = ui_manager

        # UI elements
        self.mask_timer_text = None
        self.mask_recharge_text = None
        self.time_text = None
        self.mask_uses_text = None

        # Result screen elements
        self.result_panel = None
        self.win_text = None
        self.game_over_text = None
        self.restart_button = None
        self.restart_level_1_button = None
        self.editor_button = None

        # Mask image for display
        self.mask_image = None
        self.mask_image_loaded = False
        self.small_mask_icon = None
        self.mask_icon_loaded = False

        # Initialize UI elements
        self.create_ui_elements()
        self.load_mask_image()

    def load_mask_image(self):
        """Load the mask display image and create small icon"""
        try:
            self.mask_image = pygame.image.load(
                "sprites/gen-a8f9dc3d-d020-40c2-bb6d-22e58d5d0390.png"
            ).convert_alpha()
            self.mask_image_loaded = True

            # Create small icon version (64x64 pixels)
            icon_size = 64
            img_width = self.mask_image.get_width()
            img_height = self.mask_image.get_height()

            # Scale maintaining aspect ratio
            scale_factor = min(icon_size / img_width, icon_size / img_height)
            scaled_width = int(img_width * scale_factor)
            scaled_height = int(img_height * scale_factor)

            self.small_mask_icon = pygame.transform.scale(
                self.mask_image, (scaled_width, scaled_height)
            )
            self.mask_icon_loaded = True

            logger.info("Mask image and icon loaded successfully")
        except (pygame.error, FileNotFoundError) as e:
            logger.warning(f"Failed to load mask image: {e}")
            self.mask_image_loaded = False
            self.mask_icon_loaded = False

    def create_ui_elements(self):
        """Create initial UI elements"""
        # Time display (top-right)
        self.time_text = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.config.SCREEN_WIDTH - 210, 10), (200, 30)),
            text="Time: 00:00",
            manager=self.ui_manager,
        )

        # Mask timer display (below time on right side)
        self.mask_timer_text = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.config.SCREEN_WIDTH - 210, 40), (200, 30)),
            text="Mask: Ready",
            manager=self.ui_manager,
        )

        # Mask uses display (below mask timer on right side)
        self.mask_uses_text = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((self.config.SCREEN_WIDTH - 210, 70), (200, 30)),
            text="Uses: 0",
            manager=self.ui_manager,
        )

        # Instructions (bottom)
        # Note: not stored as we don't need to update it
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (10, self.config.SCREEN_HEIGHT - 60),
                (self.config.SCREEN_WIDTH - 20, 50),
            ),
            text="M: Mask | B: Music | U: Mute Music | S: Mute SFX | Arrows: Move",
            manager=self.ui_manager,
        )

    def render_game_ui(
        self, screen: pygame.Surface, player: Player, score_system: ScoreSystem
    ):
        """Render game UI elements"""
        mask_status = player.get_mask_status()
        stats = score_system.get_current_stats()

        # Update mask timer display
        if mask_status["active"]:
            timer_text = f"Mask: Active ({mask_status['timer']:.1f}s)"
        elif not mask_status["available"]:
            timer_text = f"Mask: Loading ({mask_status['recharge_timer']:.1f}s)"
        else:
            timer_text = "Mask: Ready"

        self.mask_timer_text.set_text(timer_text)

        # Render mask icon if available and loaded
        if mask_status["available"] and self.mask_icon_loaded:
            # Position icon to the left of the mask timer text
            text_x = (
                self.config.SCREEN_WIDTH - 210
            )  # Same x position as mask_timer_text
            text_y = 40  # Same y position as mask_timer_text

            # Position icon 20 pixels to the left of the text, centered vertically
            icon_x = text_x - 20
            icon_y = (
                text_y + (30 - self.small_mask_icon.get_height()) // 2
            )  # 30 is approximate text height

            screen.blit(self.small_mask_icon, (icon_x, icon_y))

        # Update time display
        time_str = score_system.get_time_formatted()
        self.time_text.set_text(f"Time: {time_str}")

        # Update mask uses
        self.mask_uses_text.set_text(f"Mask Uses: {stats['mask_uses']}")

    def render_mask_image(self, screen: pygame.Surface, mask_status: dict):
        """Render the mask image for the first half of mask duration"""
        if not self.mask_image_loaded or not mask_status["active"]:
            return

        # Only show mask image for first half of mask duration
        remaining_time = mask_status["timer"]
        total_duration = mask_status["duration"]
        half_duration = total_duration / 2

        if remaining_time <= half_duration:
            return

        # Calculate fade opacity for the remaining half-duration
        time_in_display_period = remaining_time - half_duration
        fade_ratio = (
            time_in_display_period / half_duration
        )  # 1.0 at start of display, 0.0 at end
        alpha = int(255 * fade_ratio)

        # Create a copy of the image with alpha
        mask_image_with_alpha = self.mask_image.copy()
        mask_image_with_alpha.set_alpha(alpha)

        # Calculate scaled size maintaining aspect ratio
        img_width = self.mask_image.get_width()
        img_height = self.mask_image.get_height()
        screen_width = self.config.SCREEN_WIDTH
        screen_height = self.config.SCREEN_HEIGHT

        # Scale to fit screen while maintaining aspect ratio
        scale_factor = min(screen_width / img_width, screen_height / img_height)
        scaled_width = int(img_width * scale_factor)
        scaled_height = int(img_height * scale_factor)

        # Scale the image
        if scale_factor != 1.0:
            scaled_image = pygame.transform.scale(
                mask_image_with_alpha, (scaled_width, scaled_height)
            )
        else:
            scaled_image = mask_image_with_alpha

        # Center the image on screen
        x = (screen_width - scaled_width) // 2
        y = (screen_height - scaled_height) // 2

        # Render the image
        screen.blit(scaled_image, (x, y))

    def show_win_screen(self, score_system: ScoreSystem):
        """Show victory screen"""
        score_summary = score_system.get_score_summary()

        # Create result panel
        panel_rect = pygame.Rect(
            (self.config.SCREEN_WIDTH // 2 - 200, self.config.SCREEN_HEIGHT // 2 - 150),
            (400, 300),
        )

        self.result_panel = pygame_gui.elements.UIPanel(
            relative_rect=panel_rect, manager=self.ui_manager
        )

        # Title
        title_rect = pygame.Rect((0, 10), (400, 40))
        self.win_text = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="LEVEL COMPLETE!",
            manager=self.ui_manager,
            container=self.result_panel,
        )

        # Score details
        y_offset = 60
        details = [
            f"Time: {score_summary['time']}",
            f"Mask Uses: {score_summary['mask_uses']}",
            f"Stars: {score_summary['stars']}",
            f"Rating: {score_summary['rating']}",
        ]

        for detail in details:
            detail_rect = pygame.Rect((20, y_offset), (360, 30))
            pygame_gui.elements.UILabel(
                relative_rect=detail_rect,
                text=detail,
                manager=self.ui_manager,
                container=self.result_panel,
            )
            y_offset += 35

        # Buttons
        button_y = y_offset + 20
        self.restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, button_y), (120, 40)),
            text="Restart (R)",
            manager=self.ui_manager,
            container=self.result_panel,
        )

        self.editor_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((200, button_y), (150, 40)),
            text="Level Editor (E)",
            manager=self.ui_manager,
            container=self.result_panel,
        )

    def show_game_over_screen(self, score_system: ScoreSystem):
        """Show game over screen"""
        score_summary = score_system.get_score_summary()

        # Create result panel
        panel_rect = pygame.Rect(
            (self.config.SCREEN_WIDTH // 2 - 200, self.config.SCREEN_HEIGHT // 2 - 150),
            (400, 280),
        )

        self.result_panel = pygame_gui.elements.UIPanel(
            relative_rect=panel_rect, manager=self.ui_manager
        )

        # Title
        title_rect = pygame.Rect((0, 10), (400, 40))
        self.game_over_text = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text="GAME OVER",
            manager=self.ui_manager,
            container=self.result_panel,
        )

        # Reason
        reason_rect = pygame.Rect((20, 60), (360, 30))
        pygame_gui.elements.UILabel(
            relative_rect=reason_rect,
            text="You fell into the void!",
            manager=self.ui_manager,
            container=self.result_panel,
        )

        # Score details
        y_offset = 100
        details = [
            f"Time: {score_summary['time']}",
            f"Mask Uses: {score_summary['mask_uses']}",
        ]

        for detail in details:
            detail_rect = pygame.Rect((20, y_offset), (360, 30))
            pygame_gui.elements.UILabel(
                relative_rect=detail_rect,
                text=detail,
                manager=self.ui_manager,
                container=self.result_panel,
            )
            y_offset += 35

        # Buttons
        button_y = y_offset + 10
        self.restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, button_y), (130, 40)),
            text="Try Again",
            manager=self.ui_manager,
            container=self.result_panel,
        )

        self.restart_level_1_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((200, button_y), (150, 40)),
            text="Restart",
            manager=self.ui_manager,
            container=self.result_panel,
        )

    def hide_result_screen(self):
        """Hide result screen elements"""
        if self.result_panel:
            self.result_panel.kill()
            self.result_panel = None
            self.win_text = None
            self.game_over_text = None
            self.restart_button = None
            self.restart_level_1_button = None
            self.editor_button = None

    def cleanup(self):
        """Clean up all UI elements"""
        # Kill main UI elements
        if self.mask_timer_text:
            self.mask_timer_text.kill()
            self.mask_timer_text = None
        if self.mask_recharge_text:
            self.mask_recharge_text.kill()
            self.mask_recharge_text = None
        if self.time_text:
            self.time_text.kill()
            self.time_text = None
        if self.mask_uses_text:
            self.mask_uses_text.kill()
            self.mask_uses_text = None

        # Kill result screen elements
        self.hide_result_screen()

    def handle_ui_events(self, event):
        """Handle UI-specific events"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if hasattr(event, "ui_element"):
                if self.restart_button and event.ui_element == self.restart_button:
                    logger.info("Try Again button clicked - restarting current level")
                    # Trigger restart current level (handled in main game loop)
                    pygame.event.post(pygame.event.Event(RESTART_GAME_EVENT))
                elif (
                    self.restart_level_1_button
                    and event.ui_element == self.restart_level_1_button
                ):
                    logger.info("Restart from Level 1 button clicked")
                    # Trigger restart from level 1 (handled in main game loop)
                    pygame.event.post(pygame.event.Event(RESTART_FROM_LEVEL_1_EVENT))
                elif self.editor_button and event.ui_element == self.editor_button:
                    logger.info("Level Editor button clicked")
                    # Trigger level editor (handled in main game loop)
                    pygame.event.post(
                        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
                    )

    def update_from_level_config(self, level_config: Dict[str, Any]):
        """Update UI elements based on level configuration"""
        # Could update thresholds display or other level-specific UI
        pass

    def render_debug_info(self, screen: pygame.Surface, debug_info: Dict[str, Any]):
        """Render debug information (for development)"""
        font = self.config.get_font("small")
        y_offset = 80

        for key, value in debug_info.items():
            text = f"{key}: {value}"
            text_surface = font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (10, y_offset))
            y_offset += 20
