package org.thetruthmask.floorisalie

/** Grid coordinates; equal to Python's (x, y) tuples. */
data class GridPos(val x: Int, val y: Int)

/** Port of config.py: all game constants and settings. */
class Config {
    // Display settings
    val SCREEN_WIDTH = 1200
    val SCREEN_HEIGHT = 850
    val FPS = 60

    // Colors
    val BACKGROUND_COLOR = Rgb(20, 20, 30)
    val TILE_REAL_COLOR = Rgb(100, 150, 100) // Green for real tiles
    val TILE_FAKE_COLOR = Rgb(150, 100, 100) // Red for fake tiles (when visible)
    val TILE_EMPTY_COLOR = Rgb(50, 50, 70) // Dark for empty tiles
    val TILE_START_COLOR = Rgb(100, 100, 200) // Blue for start
    val TILE_EXIT_COLOR = Rgb(200, 200, 100) // Yellow for exit
    val PLAYER_COLOR = Rgb(255, 255, 255) // White player
    val MASK_OVERLAY_COLOR = Rgba(0, 0, 0, 128) // Semi-transparent black

    // Tile settings
    val TILE_SIZE = 80
    val GRID_WIDTH = 11
    val GRID_HEIGHT = 10

    // Player settings
    val PLAYER_SPEED = 400.0 // pixels per second
    val PLAYER_SIZE = 77

    // Mask settings (default values, can be overridden by level)
    val MASK_DURATION = 2.0 // seconds mask stays active
    val MASK_COOLDOWN = 5.0 // seconds to recharge after use

    // Scoring settings (default values, can be overridden by level)
    val TIME_THRESHOLDS = listOf(30.0, 60.0, 120.0) // seconds for 3, 2, 1 stars
    val MASK_USE_THRESHOLD = 5 // maximum mask uses before star penalty

    // UI settings
    val FONT_SIZE_SMALL = 32
    val FONT_SIZE_MEDIUM = 48
    val FONT_SIZE_LARGE = 64
    val UI_PADDING = 20

    // Level editor settings
    val EDITOR_BUTTON_HEIGHT = 60
    val EDITOR_TOOLBAR_WIDTH = 400

    // Music settings
    val MUSIC_FILE = "music/audio-energetic-anime-music.mp3"
    val MUSIC_VOLUME = 0.3f // Default volume (0.0 to 1.0)

    /** pygame.font.Font(None, size) with the size map from config.py. */
    fun getFont(size: String = "medium"): PgFont {
        val px = when (size) {
            "small" -> FONT_SIZE_SMALL
            "medium" -> FONT_SIZE_MEDIUM
            "large" -> FONT_SIZE_LARGE
            else -> FONT_SIZE_MEDIUM
        }
        return PgFont.default(px)
    }

    /** Convert screen coordinates to grid coordinates */
    fun screenToGrid(screenPos: Pair<Int, Int>): GridPos =
        GridPos(Math.floorDiv(screenPos.first, TILE_SIZE), Math.floorDiv(screenPos.second, TILE_SIZE))

    /** Convert grid coordinates to screen coordinates */
    fun gridToScreen(gridPos: GridPos): Pair<Int, Int> =
        Pair(gridPos.x * TILE_SIZE, gridPos.y * TILE_SIZE)

    /** Get screen coordinates for center of grid tile */
    fun getGridCenter(gridPos: GridPos): Pair<Int, Int> {
        val (screenX, screenY) = gridToScreen(gridPos)
        return Pair(screenX + TILE_SIZE / 2, screenY + TILE_SIZE / 2)
    }
}

data class Rgb(val r: Int, val g: Int, val b: Int) {
    val argb: Int get() = (0xFF shl 24) or (r shl 16) or (g shl 8) or b
}

data class Rgba(val r: Int, val g: Int, val b: Int, val a: Int) {
    val argb: Int get() = (a shl 24) or (r shl 16) or (g shl 8) or b
}
