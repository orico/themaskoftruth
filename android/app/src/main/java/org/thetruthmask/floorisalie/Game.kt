package org.thetruthmask.floorisalie

import android.graphics.Canvas
import android.util.Log
import org.json.JSONObject
import org.thetruthmask.floorisalie.gui.UIManager

/**
 * Port of game.py's Game: the state machine (menu, playing, dying, game_over, level_clear,
 * level_editor) and module orchestration. [step] is one iteration of Game.run()'s loop body
 * (events, update, ui update) and [render] is Game.render().
 *
 * @param keys pygame.key.get_pressed()
 * @param mouse pygame.mouse.get_pos()
 * @param tapIsAnyKey Android addition: a tap that no button takes counts as a key press on the
 *   "Push Any Key" screens (menu and level clear), since a phone has no keyboard.
 */
class Game(
    private val keys: KeyState,
    private val mouse: () -> Pair<Int, Int>,
    val events: EventQueue = EventQueue(),
    val timers: EventTimers = EventTimers(events) { System.currentTimeMillis() },
    private val tapIsAnyKey: Boolean = true,
) {
    val config = Config()

    // GUI manager (pygame_gui.UIManager); theme file load kept for parity
    val uiManager = UIManager(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, events, mouse).also {
        try {
            it.loadThemeFile("themes/transparent_buttons.json")
        } catch (e: Exception) {
            Log.w(TAG, "Failed to load transparent button theme: $e")
        }
    }

    // Game state: menu, playing, dying, game_over, level_clear, level_editor
    var gameState = "menu"

    // Death animation state
    var deathPosition: GridPos? = null

    // Level management
    var levelsConfig: List<JSONObject> = emptyList()
    var currentLevelIndex = 0

    // Game modules
    lateinit var player: Player
    lateinit var level: Level
    lateinit var scoreSystem: ScoreSystem
    var ui: UI? = null
    var levelEditor: LevelEditor? = null
    var music: Music? = null
    var soundEffects: SoundEffects? = null

    /** Window caption; Android has no title bar, kept for parity and logging. */
    var caption = "The Floor Is a Lie"
        private set

    private var mouseDownConsumed = false

    init {
        Log.i(TAG, "Initializing game...")
        initializeGame()
        Log.i(TAG, "Game initialized successfully")
    }

    /** Load levels configuration from file. */
    fun loadLevelsConfig(): Boolean {
        return try {
            val data = JSONObject(GameFiles.current.readText("levels/levels_config.json"))
            val arr = data.optJSONArray("levels")
            levelsConfig = if (arr == null) emptyList() else (0 until arr.length()).map { arr.getJSONObject(it) }
            Log.i(TAG, "Loaded ${levelsConfig.size} levels from config")
            true
        } catch (e: Exception) {
            Log.w(TAG, "Failed to load levels config: $e")
            false
        }
    }

    /** Load a specific level by index from the levels config. */
    fun loadLevelByIndex(levelIndex: Int): Boolean {
        if (levelsConfig.isEmpty()) {
            Log.w(TAG, "No levels config loaded")
            return false
        }
        if (levelIndex < 0 || levelIndex >= levelsConfig.size) {
            Log.w(TAG, "Invalid level index: $levelIndex")
            return false
        }
        val levelData = levelsConfig[levelIndex]
        val levelFile = "levels/${levelData.getString("file")}"
        Log.i(TAG, "Loading level ${levelIndex + 1}: ${levelData.getString("name")} ($levelFile)")
        // Update window title with level name
        caption = "${levelData.getString("name")} - Level ${levelIndex + 1}"
        return level.loadLevel(levelFile)
    }

    /** Get the index of the next level, or null if no more levels. */
    fun getNextLevelIndex(): Int? {
        val next = currentLevelIndex + 1
        return if (next < levelsConfig.size) next else null
    }

    /** Load the next level in sequence. */
    fun loadNextLevel() {
        val next = getNextLevelIndex()
        if (next != null) {
            currentLevelIndex = next
            if (!loadLevelByIndex(currentLevelIndex)) {
                Log.e(TAG, "Failed to load next level $currentLevelIndex")
                gameOver()
                return
            }
            player.reset(level.startPos)
            scoreSystem.reset()
        } else {
            Log.i(TAG, "No more levels to load")
        }
    }

    /** Initialize or reset game modules; loads [levelIndex] if given, else the current level. */
    fun initializeGame(levelIndex: Int? = null) {
        // Clean up old UI if it exists
        ui?.cleanup()

        level = Level(config)
        scoreSystem = ScoreSystem(config)
        ui = UI(config, uiManager)
        music = Music(config.MUSIC_FILE, config.MUSIC_VOLUME)
        soundEffects = SoundEffects() // loads from asset manager automatically

        if (!loadLevelsConfig()) {
            Log.w(TAG, "Failed to load levels config, falling back to default level")
            createDefaultLevel()
            player = Player(config, level.startPos, soundEffects)
            return
        }

        if (levelIndex != null) currentLevelIndex = levelIndex

        if (!loadLevelByIndex(currentLevelIndex)) {
            Log.w(TAG, "Failed to load level $currentLevelIndex, creating default level...")
            createDefaultLevel()
        }

        // Create player AFTER level is loaded so it gets the correct start position
        player = Player(config, level.startPos, soundEffects)
    }

    /** Create a basic default level if none exists. */
    fun createDefaultLevel() {
        val files = GameFiles.current
        files.makeDirs("levels")
        val defaultLevel = files.readText("levels/default_level.json")
        // Write to level1.json as the actual level file
        files.writeText("levels/level1.json", JSONObject(defaultLevel).toString(2))
        level.loadLevel("levels/level1.json")
        caption = "The Floor Is a Lie - Level 1 (Default)"
    }

    /** One iteration of Game.run(): handle events, update the current state, update the UI. */
    fun step(timeDelta: Double) {
        timers.pump()
        for (event in events.get()) {
            if (event is GameEvent.Quit) Log.i(TAG, "Quit event received")

            // Handle UI events
            val consumed = uiManager.processEvents(event)

            // Handle UI-specific events
            ui?.handleUiEvents(event)

            // Start music event (timer after intro sound)
            if (event is GameEvent.StartMusic) {
                Log.i(TAG, "Intro sound finished - starting background music")
                music?.play()
            }

            dispatchStateEvent(event)

            // Android: tapping outside any button acts as "the any key" on the Push Any Key screens
            if (event is GameEvent.MouseButtonDown) mouseDownConsumed = consumed
            if (tapIsAnyKey && event is GameEvent.MouseButtonUp && !consumed && !mouseDownConsumed &&
                (gameState == "menu" || gameState == "level_clear")
            ) {
                dispatchStateEvent(GameEvent.KeyDown(Keys.OTHER))
            }
        }

        // Update game state
        when (gameState) {
            "playing" -> updatePlaying(timeDelta)
            "dying" -> updateDying(timeDelta)
            "level_editor" -> levelEditor?.update(timeDelta)
        }

        // Update UI
        uiManager.update(timeDelta)
        // Update color cycle for menu and other states that use it
        ui?.updateColorCycle(timeDelta)
    }

    /** The per-state branch of the event loop in Game.run(). */
    private fun dispatchStateEvent(event: GameEvent) {
        when (gameState) {
            "menu" -> handleMenuEvents(event)
            "playing" -> handleGameEvents(event)
            "level_editor" -> handleEditorEvents(event)
            "game_over" -> {
                if ((event is GameEvent.KeyDown && event.key == Keys.R) || event is GameEvent.RestartGame) {
                    Log.i(TAG, "Restarting current level ${currentLevelIndex + 1}")
                    restartGame()
                } else if (event is GameEvent.RestartFromLevel1) {
                    restartFromLevel1()
                } else if (event is GameEvent.ContinueToNextLevel) {
                    continueToNextLevel()
                }
            }
            "level_clear" -> {
                // Any key press continues to next level
                if (event is GameEvent.KeyDown) {
                    continueToNextLevel()
                } else if (event is GameEvent.ContinueToNextLevel) {
                    continueToNextLevel()
                }
            }
        }
    }

    /** Start the music sequence: play intro sound first, then music. */
    private fun startMusicSequence() {
        soundEffects?.playSound("reach_the_exit")
        // Start music after 2.175 s (25% shorter than the 2.9 s intro)
        timers.setTimer(GameEvent.StartMusic, 2175)
    }

    /** Handle events in the main menu. */
    fun handleMenuEvents(event: GameEvent) {
        if (event is GameEvent.KeyDown) {
            Log.i(TAG, "Any key pressed in menu - starting game")
            initializeGame(levelIndex = 0)
            gameState = "playing"
            startMusicSequence()
        }
    }

    /** Handle events during gameplay. */
    fun handleGameEvents(event: GameEvent) {
        if (event !is GameEvent.KeyDown) return
        when (event.key) {
            Keys.M -> {
                val wasActive = player.maskActive
                player.toggleMask()
                val maskStatus = player.getMaskStatus()
                // If mask was just activated (not deactivated), count it and play the sound
                if (!wasActive && maskStatus.active) {
                    scoreSystem.addMaskUse()
                    soundEffects?.playSound("mask_activate")
                }
            }
            Keys.R -> restartGame()
            Keys.E -> enterLevelEditor()
            Keys.B -> music?.togglePause()
            Keys.U -> music?.toggleMute()
            Keys.C -> {
                // Cheat: teleport player instantly to the exit
                player.gridX = level.exitPos.x
                player.gridY = level.exitPos.y
                val (cx, cy) = config.getGridCenter(level.exitPos)
                player.x = cx.toDouble()
                player.y = cy.toDouble()
                player.targetGridPos = null
                player.velocityX = 0.0
                player.velocityY = 0.0
                player.moving = false
            }
        }
    }

    /** Handle events in level editor. */
    fun handleEditorEvents(event: GameEvent) {
        if (event is GameEvent.KeyDown && event.key == Keys.ESCAPE) {
            Log.i(TAG, "ESC key pressed - exiting level editor")
            exitLevelEditor()
        }
        levelEditor?.handleEvents(event)
    }

    /** Update game logic during play. */
    fun updatePlaying(deltaTime: Double) {
        player.update(deltaTime)

        // Movement input AFTER update so the next movement can be queued immediately
        player.handleInput(keys, level)

        scoreSystem.update(deltaTime)

        // Check collisions and game state
        val playerPos = player.getGridPosition()
        if (level.isExitTile(playerPos)) {
            Log.i(TAG, "Player reached exit - game won!")
            gameWin()
        } else if (level.isEmptyTile(playerPos)) {
            Log.w(TAG, "Player fell on empty tile - starting death sequence!")
            startDeathSequence(playerPos)
        } else if (level.isFakeTile(playerPos)) {
            Log.w(TAG, "Player stepped on fake tile - starting death sequence!")
            soundEffects?.playSound("fake_tile_fall")
            soundEffects?.playSound("fake_tile_fall_thump")
            startDeathSequence(playerPos)
        }
    }

    /** Start the death animation sequence */
    fun startDeathSequence(deathPos: GridPos) {
        deathPosition = deathPos
        gameState = "dying"

        // Move player to the death position (12 pixels up)
        val (cx, cy) = config.getGridCenter(deathPos)
        player.x = cx.toDouble()
        player.y = (cy - 12).toDouble()
        player.gridX = deathPos.x
        player.gridY = deathPos.y
        player.targetGridPos = null
        player.velocityX = 0.0
        player.velocityY = 0.0
        player.moving = false

        player.startDeathAnimation()
    }

    /** Update death animation sequence */
    fun updateDying(deltaTime: Double) {
        player.update(deltaTime)
        if (player.isDeathAnimationComplete()) {
            Log.i(TAG, "Death animation complete - game over!")
            gameOver()
        }
    }

    /** Handle game win condition. */
    fun gameWin() {
        soundEffects?.playSound("level_complete")
        scoreSystem.completeLevel()
        Log.i(TAG, "Level ${currentLevelIndex + 1} completed!")
        ui?.showWinScreen(scoreSystem)
        gameState = "level_clear"
    }

    /** Handle game over condition. */
    fun gameOver() {
        Log.i(TAG, "Game over on level ${currentLevelIndex + 1}")
        ui?.showGameOverScreen(scoreSystem)
        gameState = "game_over"
    }

    /** Restart the current level. */
    fun restartGame() {
        val currentIdx = currentLevelIndex
        ui?.hideResultScreen()
        ui?.cleanup()
        initializeGame(levelIndex = currentIdx)
        gameState = "playing"
        startMusicSequence()
    }

    /** Continue to the next level, or restart from level 1 after the final level. */
    fun continueToNextLevel() {
        ui?.hideResultScreen()
        val next = getNextLevelIndex()
        if (next != null) {
            Log.i(TAG, "Continuing to level ${next + 1}")
            initializeGame(levelIndex = next)
        } else {
            Log.i(TAG, "All levels completed! Restarting from level 1")
            initializeGame(levelIndex = 0)
        }
        gameState = "playing"
        startMusicSequence()
    }

    /** Restart from level 1. */
    fun restartFromLevel1() {
        ui?.hideResultScreen()
        ui?.cleanup()
        initializeGame(levelIndex = 0)
        gameState = "playing"
        startMusicSequence()
    }

    /** Switch to level editor mode (always a fresh editor instance). */
    fun enterLevelEditor() {
        levelEditor?.cleanup()
        levelEditor = LevelEditor(config, uiManager, level, mouse)
        gameState = "level_editor"
    }

    /** Exit level editor and return to game. */
    fun exitLevelEditor() {
        levelEditor?.cleanup()
        gameState = "playing"
        // Reload level if it was modified
        if (levelEditor?.modified == true) {
            Log.i(TAG, "Level was modified, reloading...")
            initializeGame()
            startMusicSequence()
        }
    }

    /** Render the current game state. */
    fun render(screen: Canvas) {
        Gfx.fillRect(screen, config.BACKGROUND_COLOR.argb, 0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        val ui = ui

        when (gameState) {
            "menu" -> ui?.renderMainMenu(screen)
            "playing" -> {
                level.render(screen, player.maskActive)
                player.render(screen)
                ui?.renderGameUi(screen, player, scoreSystem)
                ui?.renderMaskImage(screen, player.getMaskStatus())
            }
            "dying" -> {
                // Render level normally (don't reveal all fake tiles)
                level.render(screen, player.maskActive)
                // Render the specific death tile as red
                deathPosition?.let { level.renderTileAsFake(screen, it) }
                player.render(screen)
                ui?.renderGameUi(screen, player, scoreSystem)
            }
            "level_editor" -> levelEditor?.render(screen)
            "game_over" -> ui?.renderGameOverSprite(screen)
            "level_clear" -> ui?.renderLevelClearSprite(screen)
        }

        // Render UI manager (buttons, labels, panels)
        uiManager.drawUi(screen)
    }

    companion object {
        private const val TAG = "Game"
    }
}
