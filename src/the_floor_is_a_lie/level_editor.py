#!/usr/bin/env python3
"""
Level Editor module for The Floor Is a Lie
Provides GUI for creating and editing levels
"""

from typing import Optional

import pygame
import pygame_gui

from .config import Config
from .level import Level
from .tile import TileType


class LevelEditor:
    """Level editor for creating and modifying game levels"""

    def __init__(self, config: Config, ui_manager: pygame_gui.UIManager, level: Level):
        self.config = config
        self.ui_manager = ui_manager
        self.level = level
        self.modified = False

        # Editor state
        self.selected_tile_type = TileType.REAL
        self.brush_size = 1

        # UI elements
        self.toolbar_panel = None
        self.tile_buttons = {}
        self.save_button = None
        self.load_button = None
        self.back_button = None

        self.create_ui()

    def create_ui(self):
        """Create editor UI elements"""
        # Toolbar panel
        toolbar_rect = pygame.Rect(
            (self.config.SCREEN_WIDTH - self.config.EDITOR_TOOLBAR_WIDTH, 0),
            (self.config.EDITOR_TOOLBAR_WIDTH, self.config.SCREEN_HEIGHT),
        )

        self.toolbar_panel = pygame_gui.elements.UIPanel(
            relative_rect=toolbar_rect, manager=self.ui_manager
        )

        # Tile type buttons
        tile_types = [
            ("Real", TileType.REAL),
            ("Fake", TileType.FAKE),
            ("Empty", TileType.EMPTY),
            ("Start", TileType.START),
            ("Exit", TileType.EXIT),
        ]

        y_offset = 10
        for name, tile_type in tile_types:
            button_rect = pygame.Rect(
                (10, y_offset),
                (
                    self.config.EDITOR_TOOLBAR_WIDTH - 20,
                    self.config.EDITOR_BUTTON_HEIGHT,
                ),
            )
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=name,
                manager=self.ui_manager,
                container=self.toolbar_panel,
            )
            self.tile_buttons[tile_type] = button
            y_offset += self.config.EDITOR_BUTTON_HEIGHT + 5

        # Action buttons
        y_offset += 20
        self.save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (10, y_offset),
                (
                    self.config.EDITOR_TOOLBAR_WIDTH - 20,
                    self.config.EDITOR_BUTTON_HEIGHT,
                ),
            ),
            text="Save Level",
            manager=self.ui_manager,
            container=self.toolbar_panel,
        )

        y_offset += self.config.EDITOR_BUTTON_HEIGHT + 5
        self.load_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (10, y_offset),
                (
                    self.config.EDITOR_TOOLBAR_WIDTH - 20,
                    self.config.EDITOR_BUTTON_HEIGHT,
                ),
            ),
            text="Load Level",
            manager=self.ui_manager,
            container=self.toolbar_panel,
        )

        y_offset += self.config.EDITOR_BUTTON_HEIGHT + 5
        self.back_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (10, y_offset),
                (
                    self.config.EDITOR_TOOLBAR_WIDTH - 20,
                    self.config.EDITOR_BUTTON_HEIGHT,
                ),
            ),
            text="Back to Game",
            manager=self.ui_manager,
            container=self.toolbar_panel,
        )

    def update(self, delta_time: float):
        """Update editor state"""
        pass

    def handle_events(self, event):
        """Handle editor-specific events"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Left click - place tile
            mouse_pos = pygame.mouse.get_pos()
            grid_pos = self.screen_to_grid(mouse_pos)

            if self.level.is_valid_position(grid_pos):
                self.level.set_tile_type(grid_pos, self.selected_tile_type)
                self.modified = True

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            # Handle button presses
            for tile_type, button in self.tile_buttons.items():
                if event.ui_element == button:
                    self.selected_tile_type = tile_type
                    break

            if event.ui_element == self.save_button:
                self.save_level()
            elif event.ui_element == self.load_button:
                self.load_level()
            elif event.ui_element == self.back_button:
                # Back to game (handled in main loop)
                pygame.event.post(
                    pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
                )

    def screen_to_grid(self, screen_pos):
        """Convert screen coordinates to grid coordinates"""
        x, y = screen_pos
        # Adjust for toolbar
        if x >= self.config.SCREEN_WIDTH - self.config.EDITOR_TOOLBAR_WIDTH:
            return None  # Clicked in toolbar
        grid_x = x // self.config.TILE_SIZE
        grid_y = y // self.config.TILE_SIZE
        return (grid_x, grid_y)

    def save_level(self):
        """Save current level"""
        filename = f"levels/{self.level.name.lower().replace(' ', '_')}.json"
        if self.level.save_level(filename):
            print(f"Level saved to {filename}")
        else:
            print("Failed to save level")

    def load_level(self):
        """Load a level (placeholder for now)"""
        # TODO: Add file dialog for loading levels
        print("Load level functionality not implemented yet")

    def render(self, screen: pygame.Surface):
        """Render the level editor"""
        # Render level with mask always off (show true layout)
        self.level.render(screen, mask_active=True)

        # Highlight selected tile type in toolbar
        # Draw cursor preview
        mouse_pos = pygame.mouse.get_pos()
        grid_pos = self.screen_to_grid(mouse_pos)

        if grid_pos and self.level.is_valid_position(grid_pos):
            # Draw preview of tile to be placed
            preview_color = self.level.get_tile(grid_pos).colors[
                self.selected_tile_type
            ]
            preview_surface = pygame.Surface(
                (self.config.TILE_SIZE, self.config.TILE_SIZE)
            )
            preview_surface.fill(preview_color)
            preview_surface.set_alpha(128)  # Semi-transparent

            screen.blit(preview_surface, self.config.grid_to_screen(grid_pos))

    def cleanup(self):
        """Clean up editor UI elements"""
        if self.toolbar_panel:
            self.toolbar_panel.kill()
