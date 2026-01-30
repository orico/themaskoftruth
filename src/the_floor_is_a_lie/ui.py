#!/usr/bin/env python3
"""
UI module for The Floor Is a Lie
Handles user interface elements, timers, and result screens
"""

from typing import Any, Dict

import pygame
import pygame_gui

from .config import Config
from .player import Player
from .score import ScoreSystem

# Custom events
RESTART_GAME_EVENT = pygame.USEREVENT + 1


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
        self.editor_button = None

        # Initialize UI elements
        self.create_ui_elements()

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
            text="M: Toggle Mask | Arrow Keys: Move | Reach the yellow exit!",
            manager=self.ui_manager,
        )

    def render_game_ui(self, player: Player, score_system: ScoreSystem):
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

        # Update time display
        time_str = score_system.get_time_formatted()
        self.time_text.set_text(f"Time: {time_str}")

        # Update mask uses
        self.mask_uses_text.set_text(f"Mask Uses: {stats['mask_uses']}")

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
            (400, 250),
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

        # Restart button
        self.restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((140, y_offset), (120, 40)),
            text="Try Again (R)",
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
                    # Trigger restart (handled in main game loop)
                    pygame.event.post(pygame.event.Event(RESTART_GAME_EVENT))
                elif self.editor_button and event.ui_element == self.editor_button:
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
