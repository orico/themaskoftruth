package org.thetruthmask.floorisalie

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.io.File

/** Port of tests/test_level.py */
class LevelTest {
    private lateinit var config: Config
    private lateinit var level: Level

    @Before
    fun setUp() {
        GameFiles.current = JvmFiles(File("."))
        config = Config()
        level = Level(config)
    }

    @Test fun initialization() {
        assertEquals("Default Level", level.name)
        assertEquals(0, level.grid.size)
    }

    @Test fun loadLevelSuccess() {
        val data = JSONObject()
            .put("name", "Test Level")
            .put("grid", JSONArray(listOf(listOf("start", "real", "fake"), listOf("real", "empty", "exit")).map { JSONArray(it) }))
            .put(
                "config",
                JSONObject().put("mask_duration", 3.0).put("mask_cooldown", 4.0)
                    .put("time_thresholds", JSONArray(listOf(20, 40, 80))).put("mask_threshold", 3),
            )
        val temp = File.createTempFile("level", ".json").apply { writeText(data.toString()) }
        try {
            assertTrue(level.loadLevel(temp.absolutePath))
            assertEquals("Test Level", level.name)
            assertEquals(2, level.grid.size)
            assertEquals(3, level.grid[0].size)
            assertEquals(GridPos(0, 0), level.startPos)
            assertEquals(GridPos(2, 1), level.exitPos)
            assertEquals(3.0, level.maskDuration, 0.0)
            assertEquals(4.0, level.maskCooldown, 0.0)
            assertEquals(listOf(20.0, 40.0, 80.0), level.timeThresholds)
            assertEquals(3, level.maskThreshold)
        } finally {
            temp.delete()
        }
    }

    @Test fun loadLevelInvalidFile() {
        assertFalse(level.loadLevel("nonexistent.json"))
    }

    @Test fun saveLevel() {
        level.name = "Save Test"
        level.startPos = GridPos(0, 0)
        level.exitPos = GridPos(2, 2)
        val types = listOf(
            listOf(TileType.START, TileType.REAL, TileType.FAKE),
            listOf(TileType.REAL, TileType.EMPTY, TileType.REAL),
            listOf(TileType.FAKE, TileType.REAL, TileType.EXIT),
        )
        level.grid = types.mapIndexed { y, row -> row.mapIndexed { x, t -> Tile(config, t, GridPos(x, y)) as Tile? }.toMutableList() }.toMutableList()
        val temp = File.createTempFile("save", ".json")
        try {
            assertTrue(level.saveLevel(temp.absolutePath))
            val newLevel = Level(config)
            assertTrue(newLevel.loadLevel(temp.absolutePath))
            assertEquals("Save Test", newLevel.name)
            assertEquals(GridPos(0, 0), newLevel.startPos)
            assertEquals(GridPos(2, 2), newLevel.exitPos)
        } finally {
            temp.delete()
        }
    }

    @Test fun validPosition() {
        level.grid = mutableListOf(mutableListOf<Tile?>(null, null), mutableListOf<Tile?>(null, null))
        assertTrue(level.isValidPosition(GridPos(0, 0)))
        assertTrue(level.isValidPosition(GridPos(1, 1)))
        assertFalse(level.isValidPosition(GridPos(-1, 0)))
        assertFalse(level.isValidPosition(GridPos(2, 0)))
        assertFalse(level.isValidPosition(GridPos(0, 2)))
    }

    @Test fun walkableTiles() {
        level.grid = mutableListOf(
            mutableListOf(Tile(config, TileType.REAL, GridPos(0, 0)), Tile(config, TileType.FAKE, GridPos(1, 0)), Tile(config, TileType.EMPTY, GridPos(2, 0))),
            mutableListOf(Tile(config, TileType.START, GridPos(0, 1)), null, null),
        )
        assertTrue(level.isWalkable(GridPos(0, 0), false))
        assertTrue(level.isWalkable(GridPos(1, 0), false))
        assertFalse(level.isWalkable(GridPos(2, 0), false))
        assertTrue(level.isWalkable(GridPos(0, 1), false))
        assertTrue(level.isWalkable(GridPos(0, 0), true))
        assertTrue(level.isWalkable(GridPos(1, 0), true))
        assertFalse(level.isWalkable(GridPos(2, 0), true))
    }

    @Test fun safeTiles() {
        level.grid = mutableListOf(
            mutableListOf(Tile(config, TileType.REAL, GridPos(0, 0)), Tile(config, TileType.FAKE, GridPos(1, 0)), Tile(config, TileType.EMPTY, GridPos(2, 0))),
        )
        assertTrue(level.isSafe(GridPos(0, 0), false))
        assertFalse(level.isSafe(GridPos(1, 0), false))
        assertFalse(level.isSafe(GridPos(2, 0), false))
        assertTrue(level.isSafe(GridPos(0, 0), true))
        assertFalse(level.isSafe(GridPos(1, 0), true))
        assertFalse(level.isSafe(GridPos(2, 0), true))
    }

    @Test fun exitDetection() {
        level.exitPos = GridPos(2, 1)
        assertTrue(level.isExitTile(GridPos(2, 1)))
        assertFalse(level.isExitTile(GridPos(0, 0)))
        assertFalse(level.isExitTile(GridPos(1, 1)))
    }

    @Test fun setTileType() {
        level.grid = mutableListOf(mutableListOf<Tile?>(Tile(config, TileType.REAL, GridPos(0, 0))))
        level.setTileType(GridPos(0, 0), TileType.FAKE)
        assertEquals(TileType.FAKE, level.grid[0][0]!!.type)
        level.setTileType(GridPos(0, 0), TileType.START)
        assertEquals(TileType.START, level.grid[0][0]!!.type)
        assertEquals(GridPos(0, 0), level.startPos)
        level.setTileType(GridPos(0, 0), TileType.EXIT)
        assertEquals(TileType.EXIT, level.grid[0][0]!!.type)
        assertEquals(GridPos(0, 0), level.exitPos)
    }

    @Test fun levelInfo() {
        level.name = "Test Level"
        level.startPos = GridPos(1, 2)
        level.exitPos = GridPos(3, 4)
        level.maskDuration = 2.5
        val info = level.getLevelInfo()
        assertEquals("Test Level", info["name"])
        assertEquals(GridPos(1, 2), info["start_pos"])
        assertEquals(GridPos(3, 4), info["exit_pos"])
        assertEquals(2.5, info["mask_duration"])
    }

    /** The bundled levels load exactly as on desktop (grids printed from the Python game). */
    @Test fun bundledLevelsLoad() {
        GameFiles.current = JvmFiles(File("../.."))
        for ((file, start, exit) in listOf(
            Triple("level1.json", GridPos(0, 0), GridPos(10, 0)),
            Triple("level2.json", GridPos(0, 0), GridPos(10, 0)),
            Triple("level4.json", GridPos(0, 0), GridPos(5, 4)),
            Triple("level0.json", GridPos(0, 0), GridPos(10, 9)),
            Triple("level3.json", GridPos(0, 0), GridPos(6, 9)),
        )) {
            val l = Level(config)
            assertTrue(file, l.loadLevel("levels/$file"))
            assertEquals(file, 10, l.grid.size)
            assertEquals(file, 11, l.grid[0].size)
            assertEquals(file, start, l.startPos)
            assertEquals(file, exit, l.exitPos)
        }
    }
}
