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
CONTINUE_TO_NEXT_LEVEL_EVENT = pygame.USEREVENT + 102


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
        self.continue_button = None

        # Sprites for result screens
        self.game_over_sprite = None
        self.game_over_sprite_loaded = False
        self.level_clear_sprite = None
        self.level_clear_sprite_loaded = False
        self.star_sprite = None
        self.star_sprite_loaded = False
        self.main_menu_sprite = None
        self.main_menu_sprite_loaded = False

        # Level clear text elements
        self.level_clear_texts = []

        # Color cycling for "Push The Any Key" text
        self.color_cycle_time = 0.0
        self.color_cycle_speed = 2.0  # Speed of color transition
        self.current_color = (0, 255, 255)  # Start with cyan

        # Mask image for display
        self.mask_image = None
        self.mask_image_loaded = False
        self.small_mask_icon = None
        self.mask_icon_loaded = False

        # Initialize UI elements
        self.create_ui_elements()
        self.load_mask_image()
        self.load_game_over_sprite()
        self.load_level_clear_sprite()
        self.load_star_sprite()
        self.load_main_menu_sprite()

    def update_color_cycle(self, delta_time: float):
        """Update the color cycling for the 'Push The Any Key' text"""
        import math

        self.color_cycle_time += delta_time * self.color_cycle_speed

        # Cycle through neon colors: cyan -> pink -> magenta -> green
        cycle_position = self.color_cycle_time % (2 * math.pi)  # 0 to 2π

        # Use sine waves to create smooth color transitions
        # Cyan to Pink: R increases, G stays high, B decreases
        # Pink to Magenta: R stays high, G decreases, B increases slightly
        # Magenta to Green: R decreases, G increases, B decreases
        # Green to Yellow: R increases, G stays high, B stays low
        # Yellow to Blue: R decreases, G decreases, B increases
        # Blue to Cyan: R stays low, G increases, B stays high

        # Simplified approach: cycle through primary neon colors
        if cycle_position < math.pi / 3:  # Cyan to Pink
            t = cycle_position / (math.pi / 3)
            r = int(255 * t)  # 0 -> 255
            g = 255
            b = int(255 * (1 - t))  # 255 -> 0
        elif cycle_position < 2 * math.pi / 3:  # Pink to Magenta
            t = (cycle_position - math.pi / 3) / (math.pi / 3)
            r = 255
            g = int(255 * (1 - t))  # 255 -> 0
            b = int(255 * t)  # 0 -> 255
        elif cycle_position < math.pi:  # Magenta to Green
            t = (cycle_position - 2 * math.pi / 3) / (math.pi / 3)
            r = int(255 * (1 - t))  # 255 -> 0
            g = int(255 * t)  # 0 -> 255
            b = 255
        elif cycle_position < 4 * math.pi / 3:  # Green to Yellow
            t = (cycle_position - math.pi) / (math.pi / 3)
            r = int(255 * t)  # 0 -> 255
            g = 255
            b = int(255 * (1 - t))  # 255 -> 0
        elif cycle_position < 5 * math.pi / 3:  # Yellow to Blue
            t = (cycle_position - 4 * math.pi / 3) / (math.pi / 3)
            r = int(255 * (1 - t))  # 255 -> 0
            g = int(255 * (1 - t))  # 255 -> 0
            b = 255
        else:  # Blue to Cyan
            t = (cycle_position - 5 * math.pi / 3) / (math.pi / 3)
            r = 0
            g = int(255 * t)  # 0 -> 255
            b = 255

        self.current_color = (r, g, b)

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

    def load_game_over_sprite(self):
        """Load the game over menu sprite"""
        try:
            self.game_over_sprite = pygame.image.load(
                "sprites/game-over-menu.png"
            ).convert_alpha()
            self.game_over_sprite_loaded = True
            logger.info("Game over sprite loaded successfully")
        except (pygame.error, FileNotFoundError) as e:
            logger.warning(f"Failed to load game over sprite: {e}")
            self.game_over_sprite_loaded = False

    def load_level_clear_sprite(self):
        """Load the level clear menu sprite"""
        try:
            self.level_clear_sprite = pygame.image.load(
                "sprites/level-clear.png"
            ).convert_alpha()
            self.level_clear_sprite_loaded = True
            logger.info("Level clear sprite loaded successfully")
        except (pygame.error, FileNotFoundError) as e:
            logger.warning(f"Failed to load level clear sprite: {e}")
            self.level_clear_sprite_loaded = False

    def load_star_sprite(self):
        """Load the star sprite for ratings"""
        try:
            self.star_sprite = pygame.image.load("sprites/star2.png").convert_alpha()
            # Set black as transparent color in case alpha channel isn't properly set
            self.star_sprite.set_colorkey((0, 0, 0))
            self.star_sprite_loaded = True
            logger.info("Star sprite loaded successfully")
        except (pygame.error, FileNotFoundError) as e:
            logger.warning(f"Failed to load star sprite: {e}")
            self.star_sprite_loaded = False

    def load_main_menu_sprite(self):
        """Load the main menu sprite"""
        try:
            self.main_menu_sprite = pygame.image.load(
                "sprites/main-menu.png"
            ).convert_alpha()
            self.main_menu_sprite_loaded = True
            logger.info("Main menu sprite loaded successfully")
        except (pygame.error, FileNotFoundError) as e:
            logger.warning(f"Failed to load main menu sprite: {e}")
            self.main_menu_sprite_loaded = False

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

    def render_game_over_sprite(self, screen: pygame.Surface):
        """Render the game over sprite"""
        if self.game_over_sprite_loaded and hasattr(self, "game_over_sprite_rect"):
            screen.blit(self.game_over_sprite, self.game_over_sprite_rect)

    def render_level_clear_sprite(self, screen: pygame.Surface):
        """Render the level clear sprite and overlaid text/sprite elements"""
        if self.level_clear_sprite_loaded and hasattr(self, "level_clear_sprite_rect"):
            screen.blit(self.level_clear_sprite, self.level_clear_sprite_rect)

            # Render overlaid text and sprite elements (excluding dynamic text)
            for element, position in self.level_clear_texts:
                screen.blit(element, position)

            # Render dynamic "Push The Any Key" text with cycling colors
            if hasattr(self, "press_key_position"):
                small_font = self.config.get_font("medium")
                press_key_text = small_font.render(
                    "Push The Any Key", True, self.current_color
                )
                screen.blit(press_key_text, self.press_key_position)

    def render_main_menu(self, screen: pygame.Surface):
        """Render the main menu sprite and 'Push Any Key' text"""
        if self.main_menu_sprite_loaded:
            # Center the sprite on screen
            sprite_x = (
                self.config.SCREEN_WIDTH // 2 - self.main_menu_sprite.get_width() // 2
            )
            sprite_y = (
                self.config.SCREEN_HEIGHT // 2 - self.main_menu_sprite.get_height() // 2
            )
            screen.blit(self.main_menu_sprite, (sprite_x, sprite_y))

        # Render "Push Any Key" text with cycling colors in the center bottom
        medium_font = self.config.get_font("medium")
        press_key_text = medium_font.render("Push Any Key", True, self.current_color)
        text_x = self.config.SCREEN_WIDTH // 2 - press_key_text.get_width() // 2
        text_y = self.config.SCREEN_HEIGHT - 275  # Position 175 pixels up from bottom
        screen.blit(press_key_text, (text_x, text_y))

    def show_win_screen(self, score_system: ScoreSystem):
        """Show victory screen with level clear sprite and overlaid text"""
        score_summary = score_system.get_score_summary()

        # Position sprite in center of screen
        sprite_x = (
            self.config.SCREEN_WIDTH // 2 - self.level_clear_sprite.get_width() // 2
        )
        sprite_y = (
            self.config.SCREEN_HEIGHT // 2 - self.level_clear_sprite.get_height() // 2
        )
        self.level_clear_sprite_rect = pygame.Rect(
            sprite_x,
            sprite_y,
            self.level_clear_sprite.get_width(),
            self.level_clear_sprite.get_height(),
        )

        # Create text surfaces for overlay
        self.level_clear_texts = []

        # Score details - position them in the middle of the sprite
        small_font = self.config.get_font("medium")
        details = [
            f"Time: {score_summary['time']}",
            f"Mask Uses: {score_summary['mask_uses']}",
            f"Rating: {score_summary['rating']}",
        ]

        text_y = sprite_y + self.level_clear_sprite.get_height() // 2 - 40

        # Add time and mask uses as text
        for detail in details:
            detail_text = small_font.render(detail, True, (255, 255, 255))
            detail_x = self.config.SCREEN_WIDTH // 2 - detail_text.get_width() // 2
            self.level_clear_texts.append((detail_text, (detail_x, text_y)))
            text_y += 35

        # Add stars with "Stars:" label
        if self.star_sprite_loaded and score_summary["stars_count"] > 0:
            # Render "Stars:" text
            stars_label = small_font.render("Stars:", True, (255, 255, 255))
            label_x = self.config.SCREEN_WIDTH // 2 - stars_label.get_width() // 2 - 50
            self.level_clear_texts.append((stars_label, (label_x, text_y)))

            # Calculate star size to match text height
            text_height = small_font.get_height()
            star_width = self.star_sprite.get_width()
            star_height = self.star_sprite.get_height()

            # Scale to match text height while maintaining aspect ratio
            scale_factor = text_height / star_height
            scaled_star_width = int(star_width * scale_factor)
            scaled_star_height = text_height

            # Create transparent star surface to ensure background is transparent
            scaled_star = pygame.transform.scale(
                self.star_sprite, (scaled_star_width, scaled_star_height)
            )
            # Ensure the scaled surface maintains transparency
            scaled_star.set_colorkey((0, 0, 0))

            # Position stars to the right of the label
            label_end_x = label_x + stars_label.get_width()
            start_x = label_end_x + 20  # 20px gap between label and stars
            star_spacing = 10  # 10px spacing between stars

            for i in range(score_summary["stars_count"]):
                star_x = start_x + (scaled_star_width + star_spacing) * i
                self.level_clear_texts.append((scaled_star, (star_x, text_y)))

        # Position buttons from the bottom of the sprite
        sprite_height = self.level_clear_sprite.get_height()
        button_y = (
            sprite_y + sprite_height - 50 - 100 - 75 + 50 - 25
        )  # Position from bottom of sprite, 100 + 75 higher, then 50 down, then 25 up

        self.restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (sprite_x + 50 + 100 + 50 + 25 - 10, button_y), (130, 40)
            ),
            text="Try Again",
            manager=self.ui_manager,
        )

        self.continue_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (sprite_x + 200 + 100 - 50 + 20 - 10, button_y), (120, 40)
            ),
            text="Continue",
            manager=self.ui_manager,
        )

        self.editor_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (sprite_x + 350 + 300 - 50 + 20 - 10, button_y), (150, 40)
            ),
            text="Level Editor",
            manager=self.ui_manager,
        )

        # Store position for dynamic "Push The Any Key" text
        dummy_text = small_font.render("Push The Any Key", True, (200, 200, 200))
        key_text_x = self.config.SCREEN_WIDTH // 2 - dummy_text.get_width() // 2
        key_text_y = button_y + 60 - 100  # Position below buttons, moved up 100 pixels
        self.press_key_position = (key_text_x, key_text_y)

        # Make buttons transparent by overriding all appearance
        def make_transparent(button):
            if button:
                # Create a fully transparent surface for the button background
                transparent_bg = pygame.Surface(
                    (button.rect.width, button.rect.height), pygame.SRCALPHA
                )
                transparent_bg.fill((0, 0, 0, 0))
                button.set_image(transparent_bg)

                # Override text color to white
                button.text_colour = pygame.Color(255, 255, 255, 255)

                # Disable the default button appearance completely
                button.shape = "rectangle"
                button.colours = button.colours.copy()
                # Set all background colors to transparent
                for key in button.colours:
                    if "bg" in key:
                        button.colours[key] = pygame.Color(0, 0, 0, 0)
                    elif "border" in key:
                        button.colours[key] = pygame.Color(0, 0, 0, 0)
                    elif "text" in key:
                        button.colours[key] = pygame.Color(255, 255, 255, 255)

                button.rebuild()

        make_transparent(self.restart_button)
        make_transparent(self.continue_button)
        make_transparent(self.editor_button)

    def show_game_over_screen(self, score_system: ScoreSystem):
        """Show game over screen"""
        # Position sprite in center of screen
        sprite_x = (
            self.config.SCREEN_WIDTH // 2 - self.game_over_sprite.get_width() // 2
        )
        sprite_y = (
            self.config.SCREEN_HEIGHT // 2 - self.game_over_sprite.get_height() // 2
        )
        self.game_over_sprite_rect = pygame.Rect(
            sprite_x,
            sprite_y,
            self.game_over_sprite.get_width(),
            self.game_over_sprite.get_height(),
        )

        # Position buttons from the bottom of the sprite
        sprite_height = self.game_over_sprite.get_height()
        button_y = (
            sprite_y + sprite_height - 50 - 100 - 75 + 50 - 25
        )  # Position from bottom of sprite, 100 + 75 higher, then 50 down, then 25 up

        self.restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (sprite_x + 50 + 100 + 50 + 25 - 10, button_y), (130, 40)
            ),
            text="Try Again",
            manager=self.ui_manager,
        )

        self.restart_level_1_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (sprite_x + 250 + 300 - 50 + 20 - 10, button_y), (150, 40)
            ),
            text="Restart",
            manager=self.ui_manager,
        )

        # Make buttons transparent by overriding all appearance
        def make_transparent(button):
            if button:
                # Create a fully transparent surface for the button background
                transparent_bg = pygame.Surface(
                    (button.rect.width, button.rect.height), pygame.SRCALPHA
                )
                transparent_bg.fill((0, 0, 0, 0))
                button.set_image(transparent_bg)

                # Override text color to white
                button.text_colour = pygame.Color(255, 255, 255, 255)

                # Disable the default button appearance completely
                button.shape = "rectangle"
                button.colours = button.colours.copy()
                # Set all background colors to transparent
                for key in button.colours:
                    if "bg" in key:
                        button.colours[key] = pygame.Color(0, 0, 0, 0)
                    elif "border" in key:
                        button.colours[key] = pygame.Color(0, 0, 0, 0)
                    elif "text" in key:
                        button.colours[key] = pygame.Color(255, 255, 255, 255)

                button.rebuild()

        make_transparent(self.restart_button)
        make_transparent(self.restart_level_1_button)

    def hide_result_screen(self):
        """Hide result screen elements"""
        if self.result_panel:
            self.result_panel.kill()
            self.result_panel = None
            self.win_text = None
            self.game_over_text = None

        # Kill individual buttons
        if self.restart_button:
            self.restart_button.kill()
            self.restart_button = None
        if self.restart_level_1_button:
            self.restart_level_1_button.kill()
            self.restart_level_1_button = None
        if self.continue_button:
            self.continue_button.kill()
            self.continue_button = None
        if self.editor_button:
            self.editor_button.kill()
            self.editor_button = None

        # Clean up sprite-related attributes and text
        if hasattr(self, "game_over_sprite_rect"):
            delattr(self, "game_over_sprite_rect")
        if hasattr(self, "level_clear_sprite_rect"):
            delattr(self, "level_clear_sprite_rect")
        if hasattr(self, "press_key_position"):
            delattr(self, "press_key_position")
        self.level_clear_texts = []

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
                elif self.continue_button and event.ui_element == self.continue_button:
                    logger.info("Continue button clicked - loading next level")
                    # Trigger continue to next level (handled in main game loop)
                    pygame.event.post(pygame.event.Event(CONTINUE_TO_NEXT_LEVEL_EVENT))
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
