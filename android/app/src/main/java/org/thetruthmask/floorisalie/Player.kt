package org.thetruthmask.floorisalie

import android.graphics.Canvas
import android.util.Log

/** Animation states for player movement */
enum class AnimationState {
    IDLE,
    TRANSITIONING_TO_RUN,
    RUNNING,
    TRANSITIONING_TO_IDLE,
    MASK_ACTIVATING,
    MASK_ACTIVE,
    MASK_DEACTIVATING,
    DEATH,
}

/**
 * Port of player.py's Animation. The sprite sheet is identified by its asset id; frames are cut
 * (and pre-scaled to [displaySize]) by the asset manager. Without an asset manager (JVM tests)
 * the frame list is empty images of the same count, so the timing logic is unchanged.
 */
class Animation(
    spriteId: String,
    val rows: Int,
    val cols: Int,
    val frameDuration: Double = 0.1,
    frameIndices: List<Int>? = null,
    val loop: Boolean = true,
    displaySize: Int,
) {
    val totalFrames = rows * cols
    val frames: List<FrameImage?>
    val frameWidth: Int
    val frameHeight: Int

    init {
        val indices = frameIndices ?: (0 until totalFrames).toList()
        val sheet = Assets.instance?.sliceSheet(spriteId, rows, cols, indices, displaySize)
        if (sheet != null) {
            frames = sheet.frames
            frameWidth = sheet.frameWidth
            frameHeight = sheet.frameHeight
        } else {
            frames = indices.takeWhile { it < totalFrames }.map { null }
            frameWidth = 0
            frameHeight = 0
        }
    }

    val numFrames = frames.size
    var currentFrame = 0
    var timer = 0.0
    var playing = false
    var reverse = false
    var completed = false

    /** Update animation frame */
    fun update(deltaTime: Double, animating: Boolean = true) {
        if (!playing || !animating) return

        timer += deltaTime
        if (timer >= frameDuration) {
            timer = 0.0

            // Update frame based on direction
            if (reverse) {
                currentFrame -= 1
                if (currentFrame < 0) {
                    if (loop) {
                        currentFrame = numFrames - 1
                    } else {
                        currentFrame = 0
                        playing = false
                        completed = true
                    }
                }
            } else {
                currentFrame += 1
                if (currentFrame >= numFrames) {
                    if (loop) {
                        currentFrame = 0
                    } else {
                        currentFrame = numFrames - 1
                        playing = false
                        completed = true
                    }
                }
            }
        }
    }

    /** Start playing animation, optionally in reverse */
    fun play(reverse: Boolean = false) {
        playing = true
        this.reverse = reverse
        completed = false
        currentFrame = if (reverse) numFrames - 1 else 0
        timer = 0.0
    }

    /** Stop playing animation and reset to first frame */
    fun stop() {
        playing = false
        currentFrame = 0
        timer = 0.0
        completed = false
        reverse = false
    }

    /** Get current animation frame, optionally flipped horizontally */
    fun getCurrentFrame(flipX: Boolean = false): android.graphics.Bitmap? {
        val frame = frames[currentFrame] ?: return null
        return if (flipX) frame.flipped else frame.normal
    }

    fun isPlaying() = playing

    fun isCompleted() = completed
}

data class MaskStatus(
    val active: Boolean,
    val timer: Double,
    val duration: Double,
    val rechargeTimer: Double,
    val cooldown: Double,
    val available: Boolean,
    val uses: Int,
)

/** Port of player.py's Player: movement, mask mechanics and the animation state machine. */
class Player(val config: Config, startPos: GridPos, val soundEffects: SoundEffects? = null) {
    // Position (screen coordinates)
    var x: Double
    var y: Double
    var gridX: Int
    var gridY: Int

    // Movement
    val speed = config.PLAYER_SPEED
    var velocityX = 0.0
    var velocityY = 0.0

    // Mask mechanics
    var maskActive = false
    var maskTimer = 0.0
    var maskDuration = config.MASK_DURATION
    var maskCooldown = config.MASK_COOLDOWN
    var maskRechargeTimer = 0.0
    var maskAvailable = true
    var maskUses = 0

    // Player appearance
    val size = config.PLAYER_SIZE
    val color = config.PLAYER_COLOR

    // Movement state
    var moving = false
    var targetGridPos: GridPos? = null
    var movementKeysPressed = false // Track if movement keys are currently held
    var canAcceptInput = true // Track if we can accept new movement input

    // Animation setup
    var facingRight = true // Default facing direction
    var movementDirection: String? = null // 'horizontal', 'up', 'down'

    // Animation state tracking
    var animationState = AnimationState.IDLE
    val idleTransitionDelay = 0.15 // Wait 150ms before transitioning to idle
    var timeSinceMovementStopped = 0.0

    // Idle animation (full 36-frame cycle)
    val idleAnimation = Animation(
        "player_idle", rows = 6, cols = 6, frameIndices = (0 until 36).toList(),
        frameDuration = 0.08, loop = true, displaySize = size,
    )

    // Transition animation (full sequence from idle to running), 0.25 s for 16 frames
    val transitionAnimation = Animation(
        "player_transition", rows = 4, cols = 4, frameIndices = (0 until 16).toList(),
        frameDuration = 0.015625, loop = false, displaySize = size,
    )

    // Running animation (continuous running cycle)
    val runningAnimation = Animation(
        "player_running", rows = 6, cols = 6, frameIndices = (0 until 36).toList(),
        frameDuration = 0.04, loop = true, displaySize = size,
    )

    // Walk forward animation (moving down): every 6th frame, ~0.2 s per tile
    val walkForwardAnimation = Animation(
        "player_walk_forward", rows = 6, cols = 6, frameIndices = listOf(0, 6, 12, 18, 24, 30),
        frameDuration = 0.033, loop = true, displaySize = size,
    )

    // Walk backward animation (moving up): every 6th frame, ~0.2 s per tile
    val walkBackwardAnimation = Animation(
        "player_walk_backward", rows = 6, cols = 6, frameIndices = listOf(0, 6, 12, 18, 24, 30),
        frameDuration = 0.033, loop = true, displaySize = size,
    )

    // Mask activation/deactivation animation: 0.5 seconds for 36 frames, play once (reversible)
    val maskAnimation = Animation(
        "player_mask", rows = 6, cols = 6, frameIndices = (0 until 36).toList(),
        frameDuration = 0.5 / 36, loop = false, displaySize = size,
    )

    // Death animation using the falling death sprite
    val deathAnimation = Animation(
        "player_death", rows = 6, cols = 6, frameIndices = (0 until 36).toList(),
        frameDuration = 0.08, loop = false, displaySize = size,
    )

    var currentAnimation: Animation

    init {
        val (cx, cy) = config.getGridCenter(startPos)
        x = cx.toDouble()
        y = cy.toDouble()
        gridX = startPos.x
        gridY = startPos.y
        // Start with idle animation
        currentAnimation = idleAnimation
        currentAnimation.play()
    }

    /** Update player state */
    fun update(deltaTime: Double) {
        updateMovement(deltaTime)
        updateMask(deltaTime)
    }

    /** Update player movement and animation state machine */
    fun updateMovement(deltaTime: Double) {
        // Handle mask animation transitions
        when (animationState) {
            AnimationState.MASK_ACTIVATING -> {
                if (currentAnimation.isCompleted()) {
                    // Mask activation complete - stay on last frame while mask is active
                    animationState = AnimationState.MASK_ACTIVE
                }
            }
            AnimationState.MASK_ACTIVE -> {
                if (!maskActive) {
                    // Mask expired - start deactivation animation
                    animationState = AnimationState.MASK_DEACTIVATING
                    currentAnimation = maskAnimation
                    currentAnimation.play(reverse = true)
                }
            }
            AnimationState.MASK_DEACTIVATING -> {
                if (currentAnimation.isCompleted()) {
                    // Mask deactivation complete - return to idle
                    animationState = AnimationState.IDLE
                    currentAnimation = idleAnimation
                    currentAnimation.play()
                }
            }
            else -> {} // DEATH completion is checked externally by Game
        }

        // Handle movement physics
        val target = targetGridPos
        if (target != null) {
            val (targetX, targetY) = config.getGridCenter(target)
            val dx = targetX - x
            val dy = targetY - y
            val distance = Math.pow(dx * dx + dy * dy, 0.5)

            if (distance < 5) { // Close enough to target
                x = targetX.toDouble()
                y = targetY.toDouble()
                gridX = target.x
                gridY = target.y
                targetGridPos = null
                velocityX = 0.0
                velocityY = 0.0
                moving = false
                // Allow accepting new input now that we've reached the target
                canAcceptInput = true
            } else {
                // Move towards target
                velocityX = (dx / distance) * speed
                velocityY = (dy / distance) * speed
                moving = true

                // Update position
                x += velocityX * deltaTime
                y += velocityY * deltaTime

                // Update grid position (for collision detection): int(self.x // TILE_SIZE)
                gridX = Math.floor(x / config.TILE_SIZE).toInt()
                gridY = Math.floor(y / config.TILE_SIZE).toInt()
            }
        } else {
            // No target - ensure we can accept input
            if (!moving) canAcceptInput = true
        }

        // Track time since movement stopped (for delayed idle transition)
        if (moving) timeSinceMovementStopped = 0.0 else timeSinceMovementStopped += deltaTime

        // Current movement, recently stopped movement, or keys being held
        val isActivelyMoving = moving || movementKeysPressed || timeSinceMovementStopped < idleTransitionDelay

        // Animation state machine
        when (animationState) {
            AnimationState.IDLE -> {
                if (isActivelyMoving) {
                    when (movementDirection) {
                        "up" -> {
                            // Go directly to walk backward animation (no transition)
                            animationState = AnimationState.RUNNING
                            currentAnimation = walkBackwardAnimation
                            currentAnimation.play()
                        }
                        "down" -> {
                            // Go directly to walk forward animation (no transition)
                            animationState = AnimationState.RUNNING
                            currentAnimation = walkForwardAnimation
                            currentAnimation.play()
                        }
                        else -> {
                            // Horizontal movement - use transition animation
                            animationState = AnimationState.TRANSITIONING_TO_RUN
                            currentAnimation = transitionAnimation
                            currentAnimation.play()
                        }
                    }
                }
            }
            AnimationState.TRANSITIONING_TO_RUN -> {
                if (currentAnimation.isCompleted()) {
                    // Transition complete - switch to running animation
                    animationState = AnimationState.RUNNING
                    currentAnimation = runningAnimation
                    currentAnimation.play()
                } else if (!isActivelyMoving) {
                    // Movement stopped during transition - reverse back to idle
                    animationState = AnimationState.TRANSITIONING_TO_IDLE
                    currentAnimation = transitionAnimation
                    currentAnimation.play(reverse = true)
                }
            }
            AnimationState.RUNNING -> {
                if (isActivelyMoving) {
                    val desiredAnimation = when (movementDirection) {
                        "up" -> walkBackwardAnimation
                        "down" -> walkForwardAnimation
                        else -> runningAnimation // horizontal or None
                    }
                    // Switch animation if direction changed
                    if (desiredAnimation !== currentAnimation) {
                        currentAnimation = desiredAnimation
                        currentAnimation.play()
                    }
                }
                if (!isActivelyMoving) {
                    if (movementDirection == "up" || movementDirection == "down") {
                        // For vertical movement, go directly to idle (no transition)
                        animationState = AnimationState.IDLE
                        currentAnimation = idleAnimation
                        currentAnimation.play()
                        movementDirection = null
                    } else {
                        // For horizontal movement, use transition back to idle
                        animationState = AnimationState.TRANSITIONING_TO_IDLE
                        currentAnimation = transitionAnimation
                        currentAnimation.play(reverse = true)
                    }
                }
            }
            AnimationState.TRANSITIONING_TO_IDLE -> {
                if (currentAnimation.isCompleted()) {
                    // Transition complete - back to idle
                    animationState = AnimationState.IDLE
                    currentAnimation = idleAnimation
                    currentAnimation.play()
                    // Clear movement direction when returning to idle
                    movementDirection = null
                } else if (isActivelyMoving) {
                    // Started moving again during reverse - go back to running
                    animationState = AnimationState.TRANSITIONING_TO_RUN
                    currentAnimation = transitionAnimation
                    currentAnimation.play()
                }
            }
            else -> {}
        }

        // Always update current animation
        currentAnimation.update(deltaTime, animating = true)
    }

    /** Update mask timer and recharge */
    fun updateMask(deltaTime: Double) {
        if (maskActive) {
            maskTimer -= deltaTime
            if (maskTimer <= 0.001) deactivateMask() // small epsilon for floating point precision
        } else if (!maskAvailable) {
            maskRechargeTimer -= deltaTime
            if (maskRechargeTimer <= 0.001) {
                maskAvailable = true
                maskRechargeTimer = 0.0
                // Play mask ready sound
                soundEffects?.playSound("mask_ready")
            }
        }
    }

    /** Handle keyboard input for movement */
    fun handleInput(keys: KeyState, level: Level? = null) {
        // Block movement input during mask animations
        if (animationState == AnimationState.MASK_ACTIVATING ||
            animationState == AnimationState.MASK_ACTIVE ||
            animationState == AnimationState.MASK_DEACTIVATING
        ) {
            // Clear movement keys pressed state during mask animations
            movementKeysPressed = false
            return
        }

        // Track if any movement keys are currently pressed
        var movementKeyDetected = false
        var targetGridX = gridX
        var targetGridY = gridY

        if (keys[Keys.LEFT] || keys[Keys.A]) {
            targetGridX -= 1
            facingRight = false // Face left
            movementKeyDetected = true
            movementDirection = "horizontal"
        } else if (keys[Keys.RIGHT] || keys[Keys.D]) {
            targetGridX += 1
            facingRight = true // Face right
            movementKeyDetected = true
            movementDirection = "horizontal"
        } else if (keys[Keys.UP] || keys[Keys.W]) {
            targetGridY -= 1
            // Keep current facing direction for up/down movement
            movementKeyDetected = true
            movementDirection = "up"
        } else if (keys[Keys.DOWN] || keys[Keys.S]) {
            targetGridY += 1
            // Keep current facing direction for up/down movement
            movementKeyDetected = true
            movementDirection = "down"
        }

        // Update movement keys pressed state
        movementKeysPressed = movementKeyDetected

        if (!movementKeyDetected) return
        if (!canAcceptInput) return

        // Only move if position would change
        if (targetGridX != gridX || targetGridY != gridY) {
            // Try to move - only block input if move was successful
            val moveSuccessful = moveToGrid(targetGridX, targetGridY, level)
            if (moveSuccessful) {
                // Block further input until we reach the target
                canAcceptInput = false
            }
        }
    }

    /** Move player to specific grid position; returns true if the move was initiated. */
    fun moveToGrid(gridX: Int, gridY: Int, level: Level? = null): Boolean {
        // Validate bounds
        if (gridX >= 0 && gridX < config.GRID_WIDTH && gridY >= 0 && gridY < config.GRID_HEIGHT) {
            // Check if the target tile is walkable (if level is provided)
            if (level == null || level.isWalkable(GridPos(gridX, gridY), maskActive)) {
                targetGridPos = GridPos(gridX, gridY)
                moving = true
                return true
            }
        }
        return false
    }

    /** Toggle mask on/off */
    fun toggleMask() {
        if (maskAvailable && !maskActive) {
            Log.i(TAG, "Activating mask")
            activateMask()
        } else if (maskActive) {
            Log.i(TAG, "Deactivating mask")
            deactivateMask()
        } else {
            Log.w(TAG, "Mask toggle called but mask is not available")
        }
    }

    /** Activate the mask */
    fun activateMask() {
        maskActive = true
        maskAvailable = false // Mask is no longer available while active
        maskTimer = maskDuration
        maskUses += 1

        // Trigger mask activation animation if currently idle
        if (animationState == AnimationState.IDLE) {
            animationState = AnimationState.MASK_ACTIVATING
            currentAnimation = maskAnimation
            currentAnimation.play()
        }
    }

    /** Deactivate the mask and start recharge */
    fun deactivateMask() {
        maskActive = false
        maskTimer = 0.0
        maskAvailable = false
        maskRechargeTimer = maskCooldown

        // Play mask recharging sound
        soundEffects?.playSound("mask_recharging")

        // Trigger reverse animation from MASK_ACTIVE
        if (animationState == AnimationState.MASK_ACTIVE) {
            animationState = AnimationState.MASK_DEACTIVATING
            currentAnimation = maskAnimation
            currentAnimation.play(reverse = true)
        }
    }

    fun getGridPosition() = GridPos(gridX, gridY)

    fun getScreenPosition() = Pair(x, y)

    /** Update mask configuration */
    fun setConfig(maskDuration: Double? = null, maskCooldown: Double? = null) {
        if (maskDuration != null) this.maskDuration = maskDuration
        if (maskCooldown != null) this.maskCooldown = maskCooldown
    }

    /** Reset player to starting position and state */
    fun reset(startPos: GridPos) {
        val (cx, cy) = config.getGridCenter(startPos)
        x = cx.toDouble()
        y = cy.toDouble()
        gridX = startPos.x
        gridY = startPos.y
        velocityX = 0.0
        velocityY = 0.0
        moving = false
        targetGridPos = null
        canAcceptInput = true

        // Reset animation
        animationState = AnimationState.IDLE
        timeSinceMovementStopped = 0.0
        movementKeysPressed = false
        movementDirection = null
        currentAnimation = idleAnimation
        currentAnimation.stop() // Stop and reset to first frame
        currentAnimation.play() // Start playing again
        facingRight = true

        // Reset death animation if it was playing
        deathAnimation.stop()

        // Reset mask
        maskActive = false
        maskTimer = 0.0
        maskRechargeTimer = 0.0
        maskAvailable = true
        maskUses = 0
    }

    /** Render the player */
    fun render(screen: Canvas) {
        // Current animation frame, already scaled to fit PLAYER_SIZE (see Assets.sliceSheet)
        val frame = currentAnimation.getCurrentFrame(flipX = !facingRight)
        if (frame != null) {
            // Center the sprite at the current position (pygame Rect.center assignment)
            val left = x.toInt() - frame.width / 2
            val top = y.toInt() - frame.height / 2
            Gfx.blit(screen, frame, left, top)
        }

        // Draw mask indicator if active: full-screen overlay
        if (maskActive) {
            Gfx.fillRect(screen, config.MASK_OVERLAY_COLOR.argb, 0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        }
    }

    /** Get current mask status for UI display */
    fun getMaskStatus() = MaskStatus(
        active = maskActive,
        timer = maskTimer,
        duration = maskDuration,
        rechargeTimer = maskRechargeTimer,
        cooldown = maskCooldown,
        available = maskAvailable,
        uses = maskUses,
    )

    /** Start the death animation sequence */
    fun startDeathAnimation() {
        animationState = AnimationState.DEATH
        currentAnimation = deathAnimation
        currentAnimation.play()
    }

    /** Check if death animation has completed */
    fun isDeathAnimationComplete() =
        animationState == AnimationState.DEATH && currentAnimation.isCompleted()

    companion object {
        private const val TAG = "Player"
    }
}
