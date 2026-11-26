package org.thetruthmask.floorisalie

import android.graphics.Canvas
import org.json.JSONArray
import org.json.JSONException
import org.json.JSONObject

/** Port of level.py: level loading, tile grid management, and level state. */
class Level(val config: Config) {
    var name = "Default Level"
    var grid: MutableList<MutableList<Tile?>> = mutableListOf()
    var startPos = GridPos(0, 0)
    var exitPos = GridPos(0, 0)

    // Level configuration (can be overridden by level JSON)
    var maskDuration = config.MASK_DURATION
    var maskCooldown = config.MASK_COOLDOWN
    var timeThresholds: List<Double> = config.TIME_THRESHOLDS.toList()
    var maskThreshold = config.MASK_USE_THRESHOLD

    // Level metadata
    var levelConfig: JSONObject = JSONObject()

    /** Load level from JSON file */
    fun loadLevel(filename: String): Boolean {
        return try {
            val levelData = JSONObject(GameFiles.current.readText(filename))
            name = levelData.optString("name", "Unnamed Level")
            levelConfig = levelData.optJSONObject("config") ?: JSONObject()

            // Load grid (a missing "grid" key is a KeyError in Python)
            val gridData = levelData.getJSONArray("grid")
            createGridFromData(gridData)

            // Load configuration
            loadConfig()
            true
        } catch (e: java.io.FileNotFoundException) {
            println("Error loading level $filename: $e")
            false
        } catch (e: JSONException) {
            println("Error loading level $filename: $e")
            false
        }
    }

    private fun createGridFromData(gridData: JSONArray) {
        grid = mutableListOf()
        for (y in 0 until gridData.length()) {
            val row = gridData.getJSONArray(y)
            val tileRow = mutableListOf<Tile?>()
            for (x in 0 until row.length()) {
                val tile = Tile.fromString(config, row.getString(x), GridPos(x, y))
                // Track start and exit positions
                if (tile.type == TileType.START) startPos = GridPos(x, y)
                else if (tile.type == TileType.EXIT) exitPos = GridPos(x, y)
                tileRow.add(tile)
            }
            grid.add(tileRow)
        }
    }

    private fun loadConfig() {
        maskDuration = if (levelConfig.has("mask_duration")) levelConfig.getDouble("mask_duration") else config.MASK_DURATION
        maskCooldown = if (levelConfig.has("mask_cooldown")) levelConfig.getDouble("mask_cooldown") else config.MASK_COOLDOWN
        timeThresholds = levelConfig.optJSONArray("time_thresholds")
            ?.let { arr -> (0 until arr.length()).map { arr.getDouble(it) } }
            ?: config.TIME_THRESHOLDS.toList()
        maskThreshold = if (levelConfig.has("mask_threshold")) levelConfig.getInt("mask_threshold") else config.MASK_USE_THRESHOLD
    }

    /** Save current level to JSON file */
    fun saveLevel(filename: String): Boolean {
        return try {
            val tileStrMap = mapOf(
                TileType.EMPTY to "empty",
                TileType.REAL to "real",
                TileType.FAKE to "fake",
                TileType.START to "start",
                TileType.EXIT to "exit",
            )
            val gridData = JSONArray()
            for (row in grid) {
                val rowData = JSONArray()
                for (tile in row) rowData.put(tileStrMap.getValue(tile!!.type))
                gridData.put(rowData)
            }
            val levelData = JSONObject()
            levelData.put("name", name)
            levelData.put("grid", gridData)
            levelData.put(
                "config",
                JSONObject().apply {
                    put("mask_duration", maskDuration)
                    put("mask_cooldown", maskCooldown)
                    put("time_thresholds", JSONArray(timeThresholds.map { jsonNumber(it) }))
                    put("mask_threshold", maskThreshold)
                },
            )
            GameFiles.current.writeText(filename, levelData.toString(2))
            true
        } catch (e: Exception) {
            println("Error saving level $filename: $e")
            false
        }
    }

    /** Whole-number thresholds are written as ints, like the bundled level files. */
    private fun jsonNumber(value: Double): Any = if (value == Math.floor(value)) value.toLong() else value

    /** Check if grid position is within bounds */
    fun isValidPosition(gridPos: GridPos): Boolean {
        val (x, y) = gridPos
        return x >= 0 && x < grid[0].size && y >= 0 && y < grid.size
    }

    /** Get tile at grid position */
    fun getTile(gridPos: GridPos): Tile? {
        if (!isValidPosition(gridPos)) return null
        return grid[gridPos.y][gridPos.x]
    }

    /** Check if position is walkable */
    fun isWalkable(gridPos: GridPos, maskActive: Boolean = false): Boolean {
        val tile = getTile(gridPos) ?: return false
        return tile.isWalkable(maskActive)
    }

    /** Check if position is safe (won't cause death) */
    fun isSafe(gridPos: GridPos, maskActive: Boolean = false): Boolean {
        val tile = getTile(gridPos) ?: return false
        return tile.isSafe(maskActive)
    }

    /** Check if tile at position is empty (causes death) */
    fun isEmptyTile(gridPos: GridPos): Boolean = getTile(gridPos)?.type == TileType.EMPTY

    /** Check if tile at position is fake */
    fun isFakeTile(gridPos: GridPos): Boolean = getTile(gridPos)?.type == TileType.FAKE

    /** Check if tile at position is the exit */
    fun isExitTile(gridPos: GridPos): Boolean = gridPos == exitPos

    /** Check if tile at position is the start */
    fun isStartTile(gridPos: GridPos): Boolean = gridPos == startPos

    /** Set tile type at grid position */
    fun setTileType(gridPos: GridPos, tileType: TileType) {
        if (!isValidPosition(gridPos)) return
        val oldTile = grid[gridPos.y][gridPos.x]

        // Update start/exit positions if necessary
        if (tileType == TileType.START) {
            startPos = gridPos
        } else if (tileType == TileType.EXIT) {
            exitPos = gridPos
        } else if (oldTile?.type == TileType.START) {
            startPos = GridPos(0, 0) // Reset to default if start tile is changed
        } else if (oldTile?.type == TileType.EXIT) {
            exitPos = GridPos(0, 0) // Reset to default if exit tile is changed
        }

        // Create new tile
        grid[gridPos.y][gridPos.x] = Tile(config, tileType, gridPos)
    }

    /** Render the entire level */
    fun render(screen: Canvas, maskActive: Boolean = false) {
        for (row in grid) for (tile in row) tile?.render(screen, maskActive)
    }

    /** Render a specific tile with its fake/red appearance revealed */
    fun renderTileAsFake(screen: Canvas, gridPos: GridPos) {
        getTile(gridPos)?.render(screen, maskActive = true)
    }

    /** Get level information for display */
    fun getLevelInfo(): Map<String, Any> {
        val width = if (grid.isNotEmpty()) grid[0].size else 0
        val height = grid.size
        return mapOf(
            "name" to name,
            "dimensions" to Pair(width, height),
            "start_pos" to startPos,
            "exit_pos" to exitPos,
            "mask_duration" to maskDuration,
            "mask_cooldown" to maskCooldown,
            "time_thresholds" to timeThresholds,
            "mask_threshold" to maskThreshold,
        )
    }

    /** Reset level state (for restarting): nothing to do, Player.reset() handles position. */
    fun reset() {}
}
