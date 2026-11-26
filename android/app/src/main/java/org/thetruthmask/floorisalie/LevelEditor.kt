package org.thetruthmask.floorisalie

import android.graphics.Canvas
import android.util.Log
import org.thetruthmask.floorisalie.gui.IntRect
import org.thetruthmask.floorisalie.gui.UIButton
import org.thetruthmask.floorisalie.gui.UIManager
import org.thetruthmask.floorisalie.gui.UIPanel

/** Port of level_editor.py: GUI for creating and editing levels. */
class LevelEditor(
    val config: Config,
    val uiManager: UIManager,
    val level: Level,
    private val mouse: () -> Pair<Int, Int>,
) {
    var modified = false

    // Editor state
    var selectedTileType = TileType.REAL
    var brushSize = 1

    // UI elements
    var toolbarPanel: UIPanel? = null
    val tileButtons = LinkedHashMap<TileType, UIButton>()
    var saveButton: UIButton? = null
    var loadButton: UIButton? = null
    var backButton: UIButton? = null

    init {
        createUi()
    }

    /** Create editor UI elements */
    fun createUi() {
        // Toolbar panel
        val panel = UIPanel(
            uiManager,
            IntRect(config.SCREEN_WIDTH - config.EDITOR_TOOLBAR_WIDTH, 0, config.EDITOR_TOOLBAR_WIDTH, config.SCREEN_HEIGHT),
        )
        toolbarPanel = panel

        // Tile type buttons
        val tileTypes = listOf(
            "Real" to TileType.REAL,
            "Fake" to TileType.FAKE,
            "Empty" to TileType.EMPTY,
            "Start" to TileType.START,
            "Exit" to TileType.EXIT,
        )
        val buttonWidth = config.EDITOR_TOOLBAR_WIDTH - 20
        var yOffset = 10
        for ((name, tileType) in tileTypes) {
            tileButtons[tileType] = UIButton(uiManager, IntRect(10, yOffset, buttonWidth, config.EDITOR_BUTTON_HEIGHT), name, panel)
            yOffset += config.EDITOR_BUTTON_HEIGHT + 5
        }

        // Action buttons
        yOffset += 20
        saveButton = UIButton(uiManager, IntRect(10, yOffset, buttonWidth, config.EDITOR_BUTTON_HEIGHT), "Save Level", panel)
        yOffset += config.EDITOR_BUTTON_HEIGHT + 5
        loadButton = UIButton(uiManager, IntRect(10, yOffset, buttonWidth, config.EDITOR_BUTTON_HEIGHT), "Load Level", panel)
        yOffset += config.EDITOR_BUTTON_HEIGHT + 5
        backButton = UIButton(uiManager, IntRect(10, yOffset, buttonWidth, config.EDITOR_BUTTON_HEIGHT), "Back to Game", panel)
    }

    /** Update editor state */
    @Suppress("UNUSED_PARAMETER")
    fun update(deltaTime: Double) {}

    /** Handle editor-specific events */
    fun handleEvents(event: GameEvent) {
        if (event is GameEvent.MouseButtonDown && event.button == 1) {
            // Left click - place tile (at the current mouse position)
            val gridPos = screenToGrid(mouse())
            if (gridPos != null && level.isValidPosition(gridPos)) {
                level.setTileType(gridPos, selectedTileType)
                modified = true
            }
        } else if (event is GameEvent.UiButtonPressed) {
            for ((tileType, button) in tileButtons) {
                if (event.uiElement === button) {
                    selectedTileType = tileType
                    break
                }
            }
            when {
                event.uiElement === saveButton -> saveLevel()
                event.uiElement === loadButton -> loadLevel()
                // Back to game (handled in main loop)
                event.uiElement === backButton -> uiManager.postEvent(GameEvent.KeyDown(Keys.ESCAPE))
            }
        }
    }

    /** Convert screen coordinates to grid coordinates (null when on the toolbar) */
    fun screenToGrid(screenPos: Pair<Int, Int>): GridPos? {
        val (x, y) = screenPos
        if (x >= config.SCREEN_WIDTH - config.EDITOR_TOOLBAR_WIDTH) return null // Clicked in toolbar
        return GridPos(Math.floorDiv(x, config.TILE_SIZE), Math.floorDiv(y, config.TILE_SIZE))
    }

    /** Save current level to levels/<name>.json (app storage on Android) */
    fun saveLevel() {
        val filename = "levels/${level.name.lowercase().replace(" ", "_")}.json"
        if (level.saveLevel(filename)) {
            println("Level saved to $filename")
            Log.i(TAG, "Level saved to $filename")
        } else {
            println("Failed to save level")
        }
    }

    /** Load a level (placeholder, as in the desktop game) */
    fun loadLevel() {
        println("Load level functionality not implemented yet")
    }

    /** Render the level editor */
    fun render(screen: Canvas) {
        // Render level showing the true layout
        level.render(screen, maskActive = true)

        // Draw preview of tile to be placed under the cursor
        val gridPos = screenToGrid(mouse())
        if (gridPos != null && level.isValidPosition(gridPos)) {
            val previewColor = level.getTile(gridPos)!!.colors.getValue(selectedTileType)
            val (sx, sy) = config.gridToScreen(gridPos)
            Gfx.fillRect(screen, Rgba(previewColor.r, previewColor.g, previewColor.b, 128).argb, sx, sy, config.TILE_SIZE, config.TILE_SIZE)
        }
    }

    /** Clean up editor UI elements */
    fun cleanup() {
        toolbarPanel?.kill()
        toolbarPanel = null
        for (button in tileButtons.values) if (button.alive) button.kill()
        tileButtons.clear()
        saveButton?.let { if (it.alive) it.kill() }; saveButton = null
        loadButton?.let { if (it.alive) it.kill() }; loadButton = null
        backButton?.let { if (it.alive) it.kill() }; backButton = null
    }

    companion object {
        private const val TAG = "LevelEditor"
    }
}
