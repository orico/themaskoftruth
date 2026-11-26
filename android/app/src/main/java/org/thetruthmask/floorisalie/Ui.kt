package org.thetruthmask.floorisalie

import android.graphics.Bitmap
import android.graphics.Canvas
import android.util.Log
import org.thetruthmask.floorisalie.gui.IntRect
import org.thetruthmask.floorisalie.gui.UIButton
import org.thetruthmask.floorisalie.gui.UILabel
import org.thetruthmask.floorisalie.gui.UIManager
import kotlin.math.PI

/** Isolated controller for the mask text label (ui.py MaskTextController). */
class MaskTextController(private val uiLabel: UILabel) {
    private var currentText = "Mask: Ready"

    fun updateFromMaskStatus(maskStatus: MaskStatus) {
        val newText = when {
            maskStatus.active -> "Mask: Active (${fmt1(maskStatus.timer)}s)"
            !maskStatus.available -> "Mask: Recharging (${fmt1(maskStatus.rechargeTimer)}s)"
            else -> "Mask: Ready"
        }
        uiLabel.setText(newText)
        currentText = newText
    }

    fun getCurrentText() = currentText

    fun reset() {
        uiLabel.setText("Mask: Ready")
        currentText = "Mask: Ready"
    }

    companion object {
        /** Python's f"{value:.1f}" (round-half-even on the exact binary value, like Java's HALF_EVEN on BigDecimal). */
        fun fmt1(value: Double): String =
            java.math.BigDecimal(value).setScale(1, java.math.RoundingMode.HALF_EVEN).toPlainString()
    }
}

/** A pre-rendered piece of the level clear overlay (ui.py stores rendered surfaces). */
private sealed class Overlay {
    abstract val x: Int
    abstract val y: Int

    class Text(val font: PgFont, val text: String, val color: Int, override val x: Int, override val y: Int) : Overlay()
    class Image(val bitmap: Bitmap?, override val x: Int, override val y: Int) : Overlay()
}

/** Port of ui.py's UI class. */
class UI(val config: Config, val uiManager: UIManager) {
    // UI elements
    var maskTimerText: UILabel? = null
    var maskRechargeText: UILabel? = null
    var timeText: UILabel? = null
    var maskUsesText: UILabel? = null

    var maskTextController: MaskTextController? = null

    // Result screen elements
    var restartButton: UIButton? = null
    var restartLevel1Button: UIButton? = null
    var editorButton: UIButton? = null
    var continueButton: UIButton? = null

    // Sprites for result screens (sizes stand in for the pygame surfaces)
    private var gameOverSpriteLoaded = false
    private var levelClearSpriteLoaded = false
    private var starSpriteLoaded = false
    private var mainMenuSpriteLoaded = false

    private var gameOverSpriteRect: IntRect? = null
    private var levelClearSpriteRect: IntRect? = null
    private var pressKeyPosition: Pair<Int, Int>? = null

    // Level clear text elements
    private var levelClearTexts = mutableListOf<Overlay>()

    // Color cycling for "Push The Any Key" text
    var colorCycleTime = 0.0
    val colorCycleSpeed = 2.0 // Speed of color transition
    var currentColor = Rgb(0, 255, 255) // Start with cyan

    // Mask image for display
    private var maskImageLoaded = false
    private var smallMaskIcon: Bitmap? = null
    private var maskIconLoaded = false

    init {
        createUiElements()
        loadSpritesFromAssetManager()
    }

    /** Update the color cycling for the 'Push The Any Key' text */
    fun updateColorCycle(deltaTime: Double) {
        colorCycleTime += deltaTime * colorCycleSpeed

        // Cycle through neon colors: cyan -> pink -> magenta -> green -> yellow -> blue
        val cyclePosition = colorCycleTime % (2 * PI) // 0 to 2π
        val r: Int
        val g: Int
        val b: Int
        if (cyclePosition < PI / 3) { // Cyan to Pink
            val t = cyclePosition / (PI / 3)
            r = (255 * t).toInt(); g = 255; b = (255 * (1 - t)).toInt()
        } else if (cyclePosition < 2 * PI / 3) { // Pink to Magenta
            val t = (cyclePosition - PI / 3) / (PI / 3)
            r = 255; g = (255 * (1 - t)).toInt(); b = (255 * t).toInt()
        } else if (cyclePosition < PI) { // Magenta to Green
            val t = (cyclePosition - 2 * PI / 3) / (PI / 3)
            r = (255 * (1 - t)).toInt(); g = (255 * t).toInt(); b = 255
        } else if (cyclePosition < 4 * PI / 3) { // Green to Yellow
            val t = (cyclePosition - PI) / (PI / 3)
            r = (255 * t).toInt(); g = 255; b = (255 * (1 - t)).toInt()
        } else if (cyclePosition < 5 * PI / 3) { // Yellow to Blue
            val t = (cyclePosition - 4 * PI / 3) / (PI / 3)
            r = (255 * (1 - t)).toInt(); g = (255 * (1 - t)).toInt(); b = 255
        } else { // Blue to Cyan
            val t = (cyclePosition - 5 * PI / 3) / (PI / 3)
            r = 0; g = (255 * t).toInt(); b = 255
        }
        currentColor = Rgb(r, g, b)
    }

    /** Load all UI sprites from the asset manager. */
    fun loadSpritesFromAssetManager() {
        val assetManager = Assets.instance

        // Mask image and small icon version (64x64 pixels, aspect preserved)
        val maskSize = assetManager?.size("mask_image")
        maskImageLoaded = maskSize != null
        if (maskSize != null) {
            val iconSize = 64
            val (imgWidth, imgHeight) = maskSize
            val scaleFactor = minOf(iconSize.toDouble() / imgWidth, iconSize.toDouble() / imgHeight)
            smallMaskIcon = assetManager.scaled("mask_image", (imgWidth * scaleFactor).toInt(), (imgHeight * scaleFactor).toInt())
            maskIconLoaded = smallMaskIcon != null
        } else {
            maskIconLoaded = false
            Log.w(TAG, "Failed to load mask image from asset manager")
        }

        gameOverSpriteLoaded = assetManager?.size("game_over_menu") != null
        levelClearSpriteLoaded = assetManager?.size("level_clear") != null
        // Star sprite: black is set as the transparent color key
        starSpriteLoaded = assetManager?.size("star") != null
        mainMenuSpriteLoaded = assetManager?.size("main_menu") != null
    }

    /** Create initial UI elements */
    fun createUiElements() {
        // Time display (top-right)
        timeText = UILabel(uiManager, IntRect(config.SCREEN_WIDTH - 210, 10, 200, 30), "Time: 00:00")
        // Mask timer display (below time on right side)
        maskTimerText = UILabel(uiManager, IntRect(config.SCREEN_WIDTH - 210, 40, 200, 30), "Mask: Ready")
        maskTextController = MaskTextController(maskTimerText!!)
        // Mask uses display (below mask timer on right side)
        maskUsesText = UILabel(uiManager, IntRect(config.SCREEN_WIDTH - 210, 70, 200, 30), "Uses: 0")
        // Instructions (bottom); not stored as we don't need to update it
        UILabel(
            uiManager,
            IntRect(10, config.SCREEN_HEIGHT - 60, config.SCREEN_WIDTH - 20, 50),
            "M: Mask | B: Music | U: Mute Music | S: Mute SFX | Arrows: Move",
        )
    }

    /** Render game UI elements */
    fun renderGameUi(screen: Canvas, player: Player, scoreSystem: ScoreSystem) {
        val maskStatus = player.getMaskStatus()
        val stats = scoreSystem.getCurrentStats()

        // Update mask timer display using the isolated controller
        maskTextController?.updateFromMaskStatus(maskStatus)

        // Render mask icon if available and loaded, 20 px left of the mask text, centred vertically
        val icon = smallMaskIcon
        if (maskStatus.available && maskIconLoaded && icon != null) {
            val textX = config.SCREEN_WIDTH - 210
            val textY = 40
            val iconX = textX - 20
            val iconY = textY + Math.floorDiv(30 - icon.height, 2) // 30 is approximate text height
            Gfx.blit(screen, icon, iconX, iconY)
        }

        // Update time display
        timeText?.setText("Time: ${scoreSystem.getTimeFormatted()}")
        // Update mask uses
        maskUsesText?.setText("Mask Uses: ${stats["mask_uses"]}")
    }

    /** Render the mask image for the first half of mask duration, fading out */
    fun renderMaskImage(screen: Canvas, maskStatus: MaskStatus) {
        if (!maskImageLoaded || !maskStatus.active) return

        val remainingTime = maskStatus.timer
        val totalDuration = maskStatus.duration
        val halfDuration = totalDuration / 2
        if (remainingTime <= halfDuration) return

        // Fade opacity: 1.0 at start of display, 0.0 at end
        val timeInDisplayPeriod = remainingTime - halfDuration
        val fadeRatio = timeInDisplayPeriod / halfDuration
        val alpha = (255 * fadeRatio).toInt()

        // Scale to fit screen while maintaining aspect ratio, centred
        val (imgWidth, imgHeight) = Assets.instance?.size("mask_image") ?: return
        val scaleFactor = minOf(config.SCREEN_WIDTH.toDouble() / imgWidth, config.SCREEN_HEIGHT.toDouble() / imgHeight)
        val scaledWidth: Int
        val scaledHeight: Int
        if (scaleFactor != 1.0) {
            scaledWidth = (imgWidth * scaleFactor).toInt()
            scaledHeight = (imgHeight * scaleFactor).toInt()
        } else {
            scaledWidth = imgWidth
            scaledHeight = imgHeight
        }
        val image = Assets.instance?.scaled("mask_image", scaledWidth, scaledHeight) ?: return
        val x = Math.floorDiv(config.SCREEN_WIDTH - scaledWidth, 2)
        val y = Math.floorDiv(config.SCREEN_HEIGHT - scaledHeight, 2)
        Gfx.blit(screen, image, x, y, alpha)
    }

    /** Render the game over sprite */
    fun renderGameOverSprite(screen: Canvas) {
        val rect = gameOverSpriteRect
        if (gameOverSpriteLoaded && rect != null) {
            Assets.instance?.full("game_over_menu")?.let { Gfx.blit(screen, it, rect.x, rect.y) }
        }
    }

    /** Render the level clear sprite and overlaid text/sprite elements */
    fun renderLevelClearSprite(screen: Canvas) {
        val rect = levelClearSpriteRect
        if (levelClearSpriteLoaded && rect != null) {
            Assets.instance?.full("level_clear")?.let { Gfx.blit(screen, it, rect.x, rect.y) }

            // Overlaid text and sprite elements (excluding dynamic text)
            for (element in levelClearTexts) {
                when (element) {
                    is Overlay.Text -> element.font.draw(screen, element.text, element.color, element.x, element.y)
                    is Overlay.Image -> element.bitmap?.let { Gfx.blit(screen, it, element.x, element.y) }
                }
            }

            // Dynamic "Push The Any Key" text with cycling colors
            val pos = pressKeyPosition
            if (pos != null) {
                val smallFont = config.getFont("medium")
                smallFont.draw(screen, "Push The Any Key", currentColor.argb, pos.first, pos.second)
            }
        }
    }

    /** Render the main menu sprite and 'Push Any Key' text */
    fun renderMainMenu(screen: Canvas) {
        if (mainMenuSpriteLoaded) {
            val (w, h) = Assets.instance!!.size("main_menu")!!
            val spriteX = config.SCREEN_WIDTH / 2 - w / 2
            val spriteY = config.SCREEN_HEIGHT / 2 - h / 2
            Assets.instance?.full("main_menu")?.let { Gfx.blit(screen, it, spriteX, spriteY) }
        }

        // "Push Any Key" with cycling colors in the center bottom
        val mediumFont = config.getFont("medium")
        val text = "Push Any Key"
        val textX = config.SCREEN_WIDTH / 2 - mediumFont.width(text) / 2
        val textY = config.SCREEN_HEIGHT - 275 // Position 175 pixels up from bottom
        mediumFont.draw(screen, text, currentColor.argb, textX, textY)
    }

    /** Show victory screen with level clear sprite and overlaid text */
    fun showWinScreen(scoreSystem: ScoreSystem) {
        val scoreSummary = scoreSystem.getScoreSummary()
        val (spriteW, spriteH) = Assets.instance?.size("level_clear") ?: Pair(0, 0)

        // Position sprite in center of screen
        val spriteX = config.SCREEN_WIDTH / 2 - spriteW / 2
        val spriteY = config.SCREEN_HEIGHT / 2 - spriteH / 2
        levelClearSpriteRect = IntRect(spriteX, spriteY, spriteW, spriteH)

        levelClearTexts = mutableListOf()

        // Score details in the middle of the sprite
        val smallFont = config.getFont("medium")
        val details = listOf(
            "Time: ${scoreSummary["time"]}",
            "Mask Uses: ${scoreSummary["mask_uses"]}",
            "Rating: ${scoreSummary["rating"]}",
        )
        var textY = spriteY + spriteH / 2 - 40
        val white = Rgb(255, 255, 255).argb
        for (detail in details) {
            val detailX = config.SCREEN_WIDTH / 2 - smallFont.width(detail) / 2
            levelClearTexts.add(Overlay.Text(smallFont, detail, white, detailX, textY))
            textY += 35
        }

        // Stars with "Stars:" label
        val starsCount = scoreSummary["stars_count"] as Int
        val starSize = Assets.instance?.size("star")
        if (starSpriteLoaded && starsCount > 0 && starSize != null) {
            val label = "Stars:"
            val labelX = config.SCREEN_WIDTH / 2 - smallFont.width(label) / 2 - 50
            levelClearTexts.add(Overlay.Text(smallFont, label, white, labelX, textY))

            // Scale to match text height while maintaining aspect ratio
            val textHeight = smallFont.getHeight()
            val (starWidth, starHeight) = starSize
            val scaleFactor = textHeight.toDouble() / starHeight
            val scaledStarWidth = (starWidth * scaleFactor).toInt()
            val scaledStarHeight = textHeight
            val scaledStar = Assets.instance?.scaled("star", scaledStarWidth, scaledStarHeight, blackColorKey = true)

            // Stars to the right of the label, 20 px gap, 10 px spacing
            val labelEndX = labelX + smallFont.width(label)
            val startX = labelEndX + 20
            val starSpacing = 10
            for (i in 0 until starsCount) {
                val starX = startX + (scaledStarWidth + starSpacing) * i
                levelClearTexts.add(Overlay.Image(scaledStar, starX, textY))
            }
        }

        // Buttons positioned from the bottom of the sprite
        val buttonY = spriteY + spriteH - 50 - 100 - 75 + 50 - 25

        restartButton = UIButton(uiManager, IntRect(spriteX + 50 + 100 + 50 + 25 - 10, buttonY, 130, 40), "Try Again")
        continueButton = UIButton(uiManager, IntRect(spriteX + 200 + 100 - 50 + 20 - 10, buttonY, 120, 40), "Continue")
        editorButton = UIButton(uiManager, IntRect(spriteX + 350 + 300 - 50 + 20 - 10, buttonY, 150, 40), "Level Editor")

        // Position for dynamic "Push The Any Key" text
        val keyTextX = config.SCREEN_WIDTH / 2 - smallFont.width("Push The Any Key") / 2
        val keyTextY = buttonY + 60 - 100 // Position below buttons, moved up 100 pixels
        pressKeyPosition = Pair(keyTextX, keyTextY)

        // Make buttons transparent
        restartButton?.transparent = true
        continueButton?.transparent = true
        editorButton?.transparent = true
    }

    /** Show game over screen */
    fun showGameOverScreen(@Suppress("UNUSED_PARAMETER") scoreSystem: ScoreSystem) {
        val (spriteW, spriteH) = Assets.instance?.size("game_over_menu") ?: Pair(0, 0)
        val spriteX = config.SCREEN_WIDTH / 2 - spriteW / 2
        val spriteY = config.SCREEN_HEIGHT / 2 - spriteH / 2
        gameOverSpriteRect = IntRect(spriteX, spriteY, spriteW, spriteH)

        // Buttons positioned from the bottom of the sprite
        val buttonY = spriteY + spriteH - 50 - 100 - 75 + 50 - 25

        restartButton = UIButton(uiManager, IntRect(spriteX + 50 + 100 + 50 + 25 - 10, buttonY, 130, 40), "Try Again")
        restartLevel1Button = UIButton(uiManager, IntRect(spriteX + 250 + 300 - 50 + 20 - 10, buttonY, 150, 40), "Restart")

        restartButton?.transparent = true
        restartLevel1Button?.transparent = true
    }

    /** Hide result screen elements */
    fun hideResultScreen() {
        restartButton?.kill(); restartButton = null
        restartLevel1Button?.kill(); restartLevel1Button = null
        continueButton?.kill(); continueButton = null
        editorButton?.kill(); editorButton = null

        gameOverSpriteRect = null
        levelClearSpriteRect = null
        pressKeyPosition = null
        levelClearTexts = mutableListOf()
    }

    /** Clean up all UI elements */
    fun cleanup() {
        maskTimerText?.kill(); maskTimerText = null
        maskTextController = null
        maskRechargeText?.kill(); maskRechargeText = null
        timeText?.kill(); timeText = null
        maskUsesText?.kill(); maskUsesText = null

        // Kill result screen elements
        hideResultScreen()
    }

    /** Handle UI-specific events */
    fun handleUiEvents(event: GameEvent) {
        if (event is GameEvent.UiButtonPressed) {
            val element = event.uiElement
            when {
                restartButton != null && element === restartButton -> {
                    Log.i(TAG, "Try Again button clicked - restarting current level")
                    uiManager.postEvent(GameEvent.RestartGame)
                }
                restartLevel1Button != null && element === restartLevel1Button -> {
                    Log.i(TAG, "Restart from Level 1 button clicked")
                    uiManager.postEvent(GameEvent.RestartFromLevel1)
                }
                continueButton != null && element === continueButton -> {
                    Log.i(TAG, "Continue button clicked - loading next level")
                    uiManager.postEvent(GameEvent.ContinueToNextLevel)
                }
                editorButton != null && element === editorButton -> {
                    Log.i(TAG, "Level Editor button clicked")
                    uiManager.postEvent(GameEvent.KeyDown(Keys.E))
                }
            }
        }
    }

    @Suppress("UNUSED_PARAMETER")
    fun updateFromLevelConfig(levelConfig: Map<String, Any>) {}

    companion object {
        private const val TAG = "UI"
    }
}
