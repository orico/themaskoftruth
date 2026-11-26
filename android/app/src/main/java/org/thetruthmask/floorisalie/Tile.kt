package org.thetruthmask.floorisalie

import android.graphics.Bitmap
import android.graphics.Canvas

/** Enumeration of tile types */
enum class TileType(val value: String) {
    EMPTY("empty"),
    REAL("real"),
    FAKE("fake"),
    START("start"),
    EXIT("exit"),
}

/** Port of tile.py: an individual tile in the game grid. */
class Tile(val config: Config, val type: TileType, gridPos: GridPos) {
    val gridX = gridPos.x
    val gridY = gridPos.y
    val screenX = gridPos.x * config.TILE_SIZE
    val screenY = gridPos.y * config.TILE_SIZE

    // Colors for different tile types
    val colors: Map<TileType, Rgb> = mapOf(
        TileType.EMPTY to config.TILE_EMPTY_COLOR,
        TileType.REAL to config.TILE_REAL_COLOR,
        TileType.FAKE to config.TILE_FAKE_COLOR,
        TileType.START to config.TILE_START_COLOR,
        TileType.EXIT to config.TILE_EXIT_COLOR,
    )

    // Scaled tile sprites from the shared cache
    val realSprite = getScaledSprite("tile_real", config.TILE_SIZE)
    val fakeSprite = getScaledSprite("tile_fake", config.TILE_SIZE)
    val startSprite = getScaledSprite("tile_start", config.TILE_SIZE)
    val exitSprite = getScaledSprite("tile_exit", config.TILE_SIZE)

    /** Check if tile is walkable given mask state */
    @Suppress("UNUSED_PARAMETER")
    fun isWalkable(maskActive: Boolean = false): Boolean = when (type) {
        TileType.EMPTY -> false
        TileType.REAL -> true
        TileType.FAKE -> true // Fake tiles are always walkable, but they're deadly
        TileType.START, TileType.EXIT -> true
    }

    /** Check if tile is safe to walk on (won't cause death) */
    fun isSafe(maskActive: Boolean = false): Boolean {
        if (type == TileType.FAKE) return false // Fake tiles are always dangerous
        return isWalkable(maskActive)
    }

    /** Get the color to display for this tile */
    fun getDisplayColor(maskActive: Boolean = false): Rgb {
        if (maskActive) return colors.getValue(type)
        return when (type) {
            TileType.FAKE -> colors.getValue(TileType.REAL)
            TileType.REAL -> colors.getValue(TileType.REAL)
            else -> colors.getValue(type)
        }
    }

    /** Render the tile */
    fun render(screen: Canvas, maskActive: Boolean = false) {
        val color = getDisplayColor(maskActive)
        // Draw tile rectangle (background)
        Gfx.fillRect(screen, color.argb, screenX, screenY, config.TILE_SIZE, config.TILE_SIZE)

        // When mask is inactive, fake tiles appear as real tiles (show real sprite)
        // When mask is active, fake tiles show their true appearance (show fake sprite)
        val displaySprite: Bitmap? = when (type) {
            TileType.REAL -> realSprite
            TileType.FAKE -> if (maskActive) fakeSprite else realSprite
            TileType.START -> startSprite
            TileType.EXIT -> exitSprite
            TileType.EMPTY -> null
        }

        if (displaySprite != null) {
            // Center the sprite in the tile
            val spriteX = screenX + Math.floorDiv(config.TILE_SIZE - displaySprite.width, 2)
            val spriteY = screenY + Math.floorDiv(config.TILE_SIZE - displaySprite.height, 2)
            Gfx.blit(screen, displaySprite, spriteX, spriteY)
        }

        // Draw grid lines
        Gfx.rectOutline(screen, Rgb(60, 60, 80).argb, screenX, screenY, config.TILE_SIZE, config.TILE_SIZE)
    }

    companion object {
        /** Class-level cache for scaled sprites (shared across all tile instances) */
        private val scaledSpriteCache = HashMap<String, Bitmap?>()

        /** Get a scaled sprite from cache or create and cache it. */
        @Synchronized
        fun getScaledSprite(spriteId: String, tileSize: Int): Bitmap? {
            val cacheKey = "${spriteId}_$tileSize"
            if (scaledSpriteCache.containsKey(cacheKey)) return scaledSpriteCache[cacheKey]

            val assetManager = Assets.instance ?: return null
            val size = assetManager.size(spriteId)
            if (size == null) {
                scaledSpriteCache[cacheKey] = null
                return null
            }
            val (spriteWidth, spriteHeight) = size
            val scale = minOf(tileSize.toDouble() / spriteWidth, tileSize.toDouble() / spriteHeight)
            val newWidth = (spriteWidth * scale).toInt()
            val newHeight = (spriteHeight * scale).toInt()
            val scaled = assetManager.scaled(spriteId, newWidth, newHeight)
            scaledSpriteCache[cacheKey] = scaled
            return scaled
        }

        /** Create tile from string representation */
        fun fromString(config: Config, tileString: String, gridPos: GridPos): Tile {
            val tileTypeMap = mapOf(
                "empty" to TileType.EMPTY,
                "real" to TileType.REAL,
                "fake" to TileType.FAKE,
                "start" to TileType.START,
                "exit" to TileType.EXIT,
                "." to TileType.EMPTY, // Alternative representation
                "#" to TileType.REAL, // Alternative representation
                "■" to TileType.REAL, // Unicode representation
                "▫" to TileType.FAKE, // Unicode representation
            )
            val tileType = tileTypeMap[tileString.lowercase()] ?: TileType.EMPTY
            return Tile(config, tileType, gridPos)
        }
    }
}
