#!/usr/bin/env python3
"""
Player module for The Floor Is a Lie
Handles player movement, mask mechanics, and collision detection
"""

from enum import Enum
from typing import Tuple

import pygame

from .assets import get_asset_manager
from .config import Config
from .sound_effects import SoundEffects


class AnimationState(Enum):
    """Animation states for player movement"""

    IDLE = "idle"
    TRANSITIONING_TO_RUN = "transitioning_to_run"
    RUNNING = "running"
    TRANSITIONING_TO_IDLE = "transitioning_to_idle"
    MASK_ACTIVATING = "mask_activating"
    MASK_ACTIVE = "mask_active"
    MASK_DEACTIVATING = "mask_deactivating"
    DEATH = "death"


class Animation:
    """Helper class to manage sprite animations"""

    def __init__(
        self,
        sprite_sheet: pygame.Surface,
        rows: int,
        cols: int,
        frame_duration: float = 0.1,
        frame_indices: list = None,
        loop: bool = True,
    ):
        """
        Initialize animation with frame skipping support.

        Args:
            sprite_sheet: Preloaded sprite sheet surface
            rows: Number of rows in sprite sheet
            cols: Number of columns in sprite sheet
            frame_duration: Time per frame in seconds
            frame_indices: List of specific frame indices to use
                          (e.g., [0, 6, 12, 18, 24, 30])
                          If None, uses all frames sequentially
            loop: Whether to loop the animation (False for play-once animations)
        """
        self.sprite_sheet = sprite_sheet
        self.rows = rows
        self.cols = cols
        self.total_frames = rows * cols
        self.frame_duration = frame_duration
        self.loop = loop
        self.frames = []

        # Calculate frame dimensions
        sheet_width = self.sprite_sheet.get_width()
        sheet_height = self.sprite_sheet.get_height()
        self.frame_width = sheet_width // cols
        self.frame_height = sheet_height // rows

        # Determine which frames to extract
        if frame_indices is not None:
            indices_to_extract = frame_indices
        else:
            indices_to_extract = list(range(self.total_frames))

        # Extract frames from sprite sheet
        for frame_index in indices_to_extract:
            if frame_index >= self.total_frames:
                break

            row = frame_index // cols
            col = frame_index % cols

            frame_rect = pygame.Rect(
                col * self.frame_width,
                row * self.frame_height,
                self.frame_width,
                self.frame_height,
            )
            frame = self.sprite_sheet.subsurface(frame_rect)
            self.frames.append(frame)

        self.num_frames = len(self.frames)
        self.current_frame = 0
        self.timer = 0.0
        self.playing = False
        self.reverse = False
        self.completed = False

    def update(self, delta_time: float, animating: bool = True):
        """Update animation frame"""
        if not self.playing or not animating:
            return

        self.timer += delta_time
        if self.timer >= self.frame_duration:
            self.timer = 0.0

            # Update frame based on direction
            if self.reverse:
                self.current_frame -= 1
                if self.current_frame < 0:
                    if self.loop:
                        self.current_frame = self.num_frames - 1
                    else:
                        self.current_frame = 0
                        self.playing = False
                        self.completed = True
            else:
                self.current_frame += 1
                if self.current_frame >= self.num_frames:
                    if self.loop:
                        self.current_frame = 0
                    else:
                        self.current_frame = self.num_frames - 1
                        self.playing = False
                        self.completed = True

    def play(self, reverse: bool = False):
        """
        Start playing animation.

        Args:
            reverse: If True, play animation in reverse
        """
        self.playing = True
        self.reverse = reverse
        self.completed = False

        if reverse:
            self.current_frame = self.num_frames - 1
        else:
            self.current_frame = 0

        self.timer = 0.0

    def stop(self):
        """Stop playing animation and reset to first frame"""
        self.playing = False
        self.current_frame = 0
        self.timer = 0.0
        self.completed = False
        self.reverse = False

    def get_current_frame(self, flip_x: bool = False) -> pygame.Surface:
        """Get current animation frame, optionally flipped horizontally"""
        frame = self.frames[self.current_frame]
        if flip_x:
            return pygame.transform.flip(frame, True, False)
        return frame

    def is_playing(self) -> bool:
        """Check if animation is currently playing"""
        return self.playing

    def is_completed(self) -> bool:
        """Check if non-looping animation has completed"""
        return self.completed


class Player:
    def __init__(
        self,
        config: Config,
        start_pos: Tuple[int, int],
        sound_effects: SoundEffects = None,
    ):
        self.config = config
        self.sound_effects = sound_effects

        # Position (screen coordinates)
        self.x, self.y = config.get_grid_center(start_pos)
        self.grid_x, self.grid_y = start_pos

        # Movement
        self.speed = config.PLAYER_SPEED
        self.velocity_x = 0
        self.velocity_y = 0

        # Mask mechanics
        self.mask_active = False
        self.mask_timer = 0.0
        self.mask_duration = config.MASK_DURATION
        self.mask_cooldown = config.MASK_COOLDOWN
        self.mask_recharge_timer = 0.0
        self.mask_available = True
        self.mask_uses = 0

        # Player appearance
        self.size = config.PLAYER_SIZE
        self.color = config.PLAYER_COLOR

        # Movement state
        self.moving = False
        self.target_grid_pos = None
        self.movement_keys_pressed = False  # Track if movement keys are currently held

        # Animation setup
        self.facing_right = True  # Default facing direction
        self.movement_direction = None  # 'horizontal', 'up', 'down'

        # Animation state tracking
        self.animation_state = AnimationState.IDLE
        self.idle_transition_delay = 0.15  # Wait 150ms before transitioning to idle
        self.time_since_movement_stopped = 0.0

        # Get preloaded sprites from asset manager
        asset_manager = get_asset_manager()

        # Create idle animation (full 36-frame cycle)
        idle_sprite = asset_manager.get_sprite("player_idle")
        self.idle_animation = Animation(
            idle_sprite,
            rows=6,
            cols=6,
            frame_indices=list(range(36)),  # Use all 36 frames
            frame_duration=0.08,  # Smooth idle animation cycle
            loop=True,
        )

        # Create transition animation (full sequence from idle to running)
        transition_sprite = asset_manager.get_sprite("player_transition")
        self.transition_animation = Animation(
            transition_sprite,
            rows=4,
            cols=4,
            frame_indices=list(range(16)),  # Use all 16 frames
            frame_duration=0.03125,  # 0.5 seconds total for 16 frames
            loop=False,  # Play once
        )

        # Create running animation (continuous running cycle)
        running_sprite = asset_manager.get_sprite("player_running")
        self.running_animation = Animation(
            running_sprite,
            rows=6,
            cols=6,
            frame_indices=list(range(36)),  # Use all 36 frames
            frame_duration=0.08,  # Fast running animation
            loop=True,
        )

        # Create walk forward animation (for moving down)
        walk_forward_sprite = asset_manager.get_sprite("player_walk_forward")
        self.walk_forward_animation = Animation(
            walk_forward_sprite,
            rows=6,
            cols=6,
            frame_indices=list(range(36)),  # Use all 36 frames
            frame_duration=0.08,  # Same timing as running animation
            loop=True,
        )

        # Create walk backward animation (for moving up)
        walk_backward_sprite = asset_manager.get_sprite("player_walk_backward")
        self.walk_backward_animation = Animation(
            walk_backward_sprite,
            rows=6,
            cols=6,
            frame_indices=list(range(36)),  # Use all 36 frames
            frame_duration=0.08,  # Same timing as running animation
            loop=True,
        )

        # Create mask activation/deactivation animation
        # Assuming 6x6 grid (36 frames) for the mask sprite sheet
        mask_sprite = asset_manager.get_sprite("player_mask")
        mask_frame_indices = list(range(36))  # Use all 36 frames sequentially
        self.mask_animation = Animation(
            mask_sprite,
            rows=6,
            cols=6,
            frame_indices=mask_frame_indices,
            frame_duration=0.5 / 36,  # Fast animation: 0.5 seconds for 36 frames
            loop=False,  # Play once, can be reversed
        )

        # Create death animation using the falling death sprite
        death_sprite = asset_manager.get_sprite("player_death")
        self.death_animation = Animation(
            death_sprite,
            rows=6,
            cols=6,
            frame_indices=list(range(36)),  # Use all 36 frames
            frame_duration=0.08,  # Same timing as other animations
            loop=False,  # Play once
        )

        # Start with idle animation
        self.current_animation = self.idle_animation
        self.current_animation.play()

    def update(self, delta_time: float):
        """Update player state"""
        self.update_movement(delta_time)
        self.update_mask(delta_time)

    def update_movement(self, delta_time: float):
        """Update player movement and animation state machine"""

        # Handle mask animation transitions
        if self.animation_state == AnimationState.MASK_ACTIVATING:
            # Playing mask activation animation
            if self.current_animation.is_completed():
                # Mask activation complete - stay on last frame while mask is active
                self.animation_state = AnimationState.MASK_ACTIVE
                # Animation stays on last frame (don't restart)

        elif self.animation_state == AnimationState.MASK_ACTIVE:
            # Holding on mask animation last frame while mask is active
            if not self.mask_active:
                # Mask expired - start deactivation animation
                self.animation_state = AnimationState.MASK_DEACTIVATING
                self.current_animation = self.mask_animation
                self.current_animation.play(reverse=True)

        elif self.animation_state == AnimationState.MASK_DEACTIVATING:
            # Playing mask deactivation animation (in reverse)
            if self.current_animation.is_completed():
                # Mask deactivation complete - return to idle
                self.animation_state = AnimationState.IDLE
                self.current_animation = self.idle_animation
                self.current_animation.play()

        elif self.animation_state == AnimationState.DEATH:
            # Death animation is playing - let it complete naturally
            # (completion is checked externally by game.py)
            pass

        # Handle movement physics
        if self.target_grid_pos:
            target_x, target_y = self.config.get_grid_center(self.target_grid_pos)
            dx = target_x - self.x
            dy = target_y - self.y
            distance = (dx**2 + dy**2) ** 0.5

            if distance < 5:  # Close enough to target
                self.x, self.y = target_x, target_y
                self.grid_x, self.grid_y = self.target_grid_pos
                self.target_grid_pos = None
                self.velocity_x = 0
                self.velocity_y = 0
                self.moving = False
            else:
                # Move towards target
                self.velocity_x = (dx / distance) * self.speed
                self.velocity_y = (dy / distance) * self.speed
                self.moving = True

                # Update position
                self.x += self.velocity_x * delta_time
                self.y += self.velocity_y * delta_time

                # Update grid position (for collision detection)
                self.grid_x = int(self.x // self.config.TILE_SIZE)
                self.grid_y = int(self.y // self.config.TILE_SIZE)

        # Track time since movement stopped (for delayed idle transition)
        if self.moving:
            self.time_since_movement_stopped = 0.0
        else:
            self.time_since_movement_stopped += delta_time

        # Determine if we should consider player as "actively moving"
        # Includes current movement, recently stopped movement, or keys being held
        is_actively_moving = (
            self.moving
            or self.movement_keys_pressed
            or self.time_since_movement_stopped < self.idle_transition_delay
        )

        # Animation state machine
        if self.animation_state == AnimationState.IDLE:
            # In idle state, loop idle animation
            if is_actively_moving:
                # Start moving - transition to running
                self.animation_state = AnimationState.TRANSITIONING_TO_RUN
                self.current_animation = self.transition_animation
                self.current_animation.play()

        elif self.animation_state == AnimationState.TRANSITIONING_TO_RUN:
            # Playing transition animation
            if self.current_animation.is_completed():
                # Transition complete - switch to appropriate running animation based on direction
                import logging

                logger = logging.getLogger(__name__)
                logger.info(
                    f"Transition complete, movement_direction: {self.movement_direction}"
                )

                self.animation_state = AnimationState.RUNNING
                if self.movement_direction == "up":
                    self.current_animation = self.walk_backward_animation
                    logger.info("Switching to walk_backward_animation")
                elif self.movement_direction == "down":
                    self.current_animation = self.walk_forward_animation
                    logger.info("Switching to walk_forward_animation")
                else:  # horizontal or None
                    self.current_animation = self.running_animation
                    logger.info("Switching to running_animation")
                self.current_animation.play()
            elif not is_actively_moving:
                # Movement stopped during transition - reverse back to idle
                self.animation_state = AnimationState.TRANSITIONING_TO_IDLE
                self.current_animation = self.transition_animation
                self.current_animation.play(reverse=True)

        elif self.animation_state == AnimationState.RUNNING:
            # In running state, loop running animation
            # Check if we need to switch animation based on direction change
            if is_actively_moving:
                desired_animation = None
                if self.movement_direction == "up":
                    desired_animation = self.walk_backward_animation
                elif self.movement_direction == "down":
                    desired_animation = self.walk_forward_animation
                else:  # horizontal or None
                    desired_animation = self.running_animation

                # Switch animation if direction changed
                if desired_animation != self.current_animation:
                    self.current_animation = desired_animation
                    self.current_animation.play()

            if not is_actively_moving:
                # Stop moving - transition back to idle (after delay)
                self.animation_state = AnimationState.TRANSITIONING_TO_IDLE
                self.current_animation = self.running_animation
                self.current_animation.play(reverse=True)

        elif self.animation_state == AnimationState.TRANSITIONING_TO_IDLE:
            # Playing reverse animation
            if self.current_animation.is_completed():
                # Transition complete - back to idle
                self.animation_state = AnimationState.IDLE
                self.current_animation = self.idle_animation
                self.current_animation.play()
                # Clear movement direction when returning to idle
                self.movement_direction = None
            elif is_actively_moving:
                # Started moving again during reverse - go back to running
                self.animation_state = AnimationState.TRANSITIONING_TO_RUN
                self.current_animation = self.transition_animation
                self.current_animation.play()

        # Always update current animation
        self.current_animation.update(delta_time, animating=True)

    def update_mask(self, delta_time: float):
        """Update mask timer and recharge"""
        if self.mask_active:
            self.mask_timer -= delta_time
            if (
                self.mask_timer <= 0.001
            ):  # Use small epsilon for floating point precision
                self.deactivate_mask()
        elif not self.mask_available:
            self.mask_recharge_timer -= delta_time
            if (
                self.mask_recharge_timer <= 0.001
            ):  # Use small epsilon for floating point precision
                self.mask_available = True
                self.mask_recharge_timer = 0
                # Play mask ready sound
                if self.sound_effects:
                    self.sound_effects.play_sound("mask_ready")

    def handle_input(self, keys, level=None):
        """Handle keyboard input for movement"""
        # Check for movement input
        new_grid_x, new_grid_y = self.grid_x, self.grid_y
        target_grid_x, target_grid_y = self.grid_x, self.grid_y

        # Track if any movement keys are currently pressed
        movement_key_detected = False

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            target_grid_x -= 1
            self.facing_right = False  # Face left
            movement_key_detected = True
            self.movement_direction = "horizontal"
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            target_grid_x += 1
            self.facing_right = True  # Face right
            movement_key_detected = True
            self.movement_direction = "horizontal"
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            target_grid_y -= 1
            # Keep current facing direction for up/down movement
            movement_key_detected = True
            self.movement_direction = "up"
            import logging

            logger = logging.getLogger(__name__)
            logger.info("UP key pressed, setting movement_direction to 'up'")
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            target_grid_y += 1
            # Keep current facing direction for up/down movement
            movement_key_detected = True
            self.movement_direction = "down"
            import logging

            logger = logging.getLogger(__name__)
            logger.info("DOWN key pressed, setting movement_direction to 'down'")

        # Update movement keys pressed state
        self.movement_keys_pressed = movement_key_detected

        # Don't clear movement_direction here - it needs to persist through the transition animation
        # It will be cleared when we return to IDLE state

        # If currently moving, use current grid position as starting point
        # This allows queuing next movement when near the target tile
        if self.moving and self.target_grid_pos:
            # Check if we're close to the target - if so, allow setting new target
            target_x, target_y = self.config.get_grid_center(self.target_grid_pos)
            dx = target_x - self.x
            dy = target_y - self.y
            distance = (dx**2 + dy**2) ** 0.5

            # If we're more than halfway to the target, don't accept new input yet
            tile_size = self.config.TILE_SIZE
            if distance > tile_size * 0.4:  # More than 40% of tile away
                return

            # Use target position as base for next movement
            new_grid_x, new_grid_y = self.target_grid_pos
            target_grid_x = new_grid_x + (target_grid_x - self.grid_x)
            target_grid_y = new_grid_y + (target_grid_y - self.grid_y)

        # Only move if position would change
        if (target_grid_x, target_grid_y) != (new_grid_x, new_grid_y):
            # Import logging here to avoid circular imports
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(
                f"Player moving to grid position: ({target_grid_x}, {target_grid_y})"
            )
            self.move_to_grid(target_grid_x, target_grid_y, level)

    def move_to_grid(self, grid_x: int, grid_y: int, level=None):
        """Move player to specific grid position"""
        # Validate bounds
        if (
            0 <= grid_x < self.config.GRID_WIDTH
            and 0 <= grid_y < self.config.GRID_HEIGHT
        ):
            # Check if the target tile is walkable (if level is provided)
            if level is None or level.is_walkable((grid_x, grid_y), self.mask_active):
                self.target_grid_pos = (grid_x, grid_y)
                self.moving = True

    def toggle_mask(self):
        """Toggle mask on/off"""
        import logging

        logger = logging.getLogger(__name__)

        logger.debug(
            f"Toggle mask called. Available: {self.mask_available}, "
            f"Active: {self.mask_active}"
        )

        if self.mask_available and not self.mask_active:
            logger.info("Activating mask")
            self.activate_mask()
        elif self.mask_active:
            logger.info("Deactivating mask")
            self.deactivate_mask()
        else:
            logger.warning("Mask toggle called but mask is not available")

    def activate_mask(self):
        """Activate the mask"""
        self.mask_active = True
        self.mask_available = False  # Mask is no longer available while active
        self.mask_timer = self.mask_duration
        self.mask_uses += 1

        # Trigger mask activation animation if currently idle
        if self.animation_state == AnimationState.IDLE:
            self.animation_state = AnimationState.MASK_ACTIVATING
            self.current_animation = self.mask_animation
            self.current_animation.play()

    def deactivate_mask(self):
        """Deactivate the mask and start recharge"""
        self.mask_active = False
        self.mask_timer = 0
        self.mask_available = False
        self.mask_recharge_timer = self.mask_cooldown

        # Play mask recharging sound
        if self.sound_effects:
            self.sound_effects.play_sound("mask_recharging")

        # Trigger reverse animation from MASK_ACTIVE
        if self.animation_state == AnimationState.MASK_ACTIVE:
            self.animation_state = AnimationState.MASK_DEACTIVATING
            self.current_animation = self.mask_animation
            self.current_animation.play(reverse=True)

    def get_grid_position(self) -> Tuple[int, int]:
        """Get current grid position"""
        return (self.grid_x, self.grid_y)

    def get_screen_position(self) -> Tuple[float, float]:
        """Get current screen position"""
        return (self.x, self.y)

    def set_config(self, mask_duration: float = None, mask_cooldown: float = None):
        """Update mask configuration"""
        if mask_duration is not None:
            self.mask_duration = mask_duration
        if mask_cooldown is not None:
            self.mask_cooldown = mask_cooldown

    def reset(self, start_pos: Tuple[int, int]):
        """Reset player to starting position and state"""
        self.x, self.y = self.config.get_grid_center(start_pos)
        self.grid_x, self.grid_y = start_pos
        self.velocity_x = 0
        self.velocity_y = 0
        self.moving = False
        self.target_grid_pos = None

        # Reset animation
        self.animation_state = AnimationState.IDLE
        self.time_since_movement_stopped = 0.0
        self.movement_keys_pressed = False
        self.movement_direction = None
        self.current_animation = self.idle_animation
        self.current_animation.stop()  # Stop and reset to first frame
        self.current_animation.play()  # Start playing again
        self.facing_right = True

        # Reset death animation if it was playing
        self.death_animation.stop()

        # Reset mask
        self.mask_active = False
        self.mask_timer = 0
        self.mask_recharge_timer = 0
        self.mask_available = True
        self.mask_uses = 0

    def render(self, screen: pygame.Surface):
        """Render the player"""
        # Get current animation frame
        current_frame = self.current_animation.get_current_frame(
            flip_x=not self.facing_right
        )

        # Scale current animation to fit PLAYER_SIZE maintaining aspect ratio
        frame_width = self.current_animation.frame_width
        frame_height = self.current_animation.frame_height
        scale_factor = min(self.size / frame_width, self.size / frame_height)

        if scale_factor != 1.0:
            scaled_size = (
                int(frame_width * scale_factor),
                int(frame_height * scale_factor),
            )
            scaled_frame = pygame.transform.scale(current_frame, scaled_size)
        else:
            scaled_frame = current_frame

        # Calculate position to center the sprite at the current position
        sprite_rect = scaled_frame.get_rect()
        sprite_rect.center = (int(self.x), int(self.y))

        # Render the sprite
        screen.blit(scaled_frame, sprite_rect)

        # Draw mask indicator if active
        if self.mask_active:
            # Draw mask overlay effect
            mask_surface = pygame.Surface(
                (self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT), pygame.SRCALPHA
            )
            mask_surface.fill(self.config.MASK_OVERLAY_COLOR)
            screen.blit(mask_surface, (0, 0))

    def get_mask_status(self) -> dict:
        """Get current mask status for UI display"""
        return {
            "active": self.mask_active,
            "timer": self.mask_timer,
            "duration": self.mask_duration,
            "recharge_timer": self.mask_recharge_timer,
            "cooldown": self.mask_cooldown,
            "available": self.mask_available,
            "uses": self.mask_uses,
        }

    def start_death_animation(self):
        """Start the death animation sequence"""
        self.animation_state = AnimationState.DEATH
        self.current_animation = self.death_animation
        self.current_animation.play()

    def is_death_animation_complete(self) -> bool:
        """Check if death animation has completed"""
        return (
            self.animation_state == AnimationState.DEATH
            and self.current_animation.is_completed()
        )
