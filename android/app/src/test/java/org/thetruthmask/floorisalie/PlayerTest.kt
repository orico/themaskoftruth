package org.thetruthmask.floorisalie

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.io.File

/** Port of tests/test_player.py, plus parity checks against values measured in the desktop game. */
class PlayerTest {
    private lateinit var config: Config
    private val startPos = GridPos(1, 1)
    private lateinit var player: Player

    private fun keys(vararg pressed: Int) = KeyState { it in pressed }

    @Before
    fun setUp() {
        Mixer.current = SilentMixer()
        GameFiles.current = JvmFiles(File("../.."))
        config = Config()
        player = Player(config, startPos)
    }

    @Test fun initialization() {
        assertEquals(startPos.x, player.gridX)
        assertEquals(startPos.y, player.gridY)
        assertFalse(player.maskActive)
        assertTrue(player.maskAvailable)
        assertEquals(0, player.maskUses)
    }

    @Test fun movementToValidPosition() {
        val newPos = GridPos(2, 2)
        player.moveToGrid(newPos.x, newPos.y)
        assertEquals(newPos, player.targetGridPos)
        assertTrue(player.moving)
        val (tx, ty) = config.getGridCenter(newPos)
        player.x = tx.toDouble(); player.y = ty.toDouble()
        player.gridX = newPos.x; player.gridY = newPos.y
        player.targetGridPos = null
        player.moving = false
        assertEquals(newPos, player.getGridPosition())
        assertFalse(player.moving)
    }

    @Test fun movementToInvalidPosition() {
        player.moveToGrid(-1, -1)
        assertEquals(startPos, player.getGridPosition())
    }

    @Test fun maskActivation() {
        player.toggleMask()
        assertTrue(player.maskActive)
        assertEquals(1, player.maskUses)
        player.toggleMask()
        assertFalse(player.maskActive)
    }

    @Test fun maskCooldown() {
        player.toggleMask(); player.toggleMask()
        assertFalse(player.maskAvailable)
        assertFalse(player.maskActive)
        player.maskRechargeTimer = 0.0
        player.update(0.1)
        assertTrue(player.maskAvailable)
    }

    @Test fun maskTimerExpiration() {
        player.toggleMask()
        assertTrue(player.maskActive)
        player.maskTimer = 0.0
        player.update(0.1)
        assertFalse(player.maskActive)
        assertFalse(player.maskAvailable)
    }

    @Test fun inputHandlingMovement() {
        player.handleInput(keys(Keys.RIGHT))
        assertEquals(GridPos(startPos.x + 1, startPos.y), player.targetGridPos)
    }

    @Test fun inputHandlingMaskToggle() {
        val initial = player.maskActive
        player.handleInput(keys(Keys.M))
        assertEquals(initial, player.maskActive)
    }

    @Test fun reset() {
        player.moveToGrid(5, 5)
        repeat(10) { player.update(1.0 / 60) }
        player.toggleMask(); player.toggleMask()
        val newStart = GridPos(3, 3)
        player.reset(newStart)
        assertEquals(newStart, player.getGridPosition())
        assertFalse(player.maskActive)
        assertTrue(player.maskAvailable)
        assertEquals(0, player.maskUses)
    }

    @Test fun getMaskStatus() {
        val s = player.getMaskStatus()
        assertEquals(false, s.active)
        assertEquals(config.MASK_DURATION, s.duration, 0.0)
        assertEquals(config.MASK_COOLDOWN, s.cooldown, 0.0)
        assertTrue(s.available)
        assertEquals(0, s.uses)
    }

    @Test fun restartFunctionality() {
        val game = Game(keys(), { Pair(0, 0) })
        game.gameState = "game_over"
        game.events.post(GameEvent.KeyDown(Keys.R))
        game.step(0.016)
        assertEquals("playing", game.gameState)
        assertNotNull(game.player)
        assertEquals(0, game.player.maskUses)
        assertFalse(game.player.maskActive)
    }

    @Test fun restartButtonTriggersEvent() {
        val events = EventQueue()
        val game = Game(keys(), { Pair(0, 0) }, events)
        val ui = game.ui!!
        ui.showGameOverScreen(game.scoreSystem)
        assertNotNull(ui.restartButton)
        events.get()
        ui.handleUiEvents(GameEvent.UiButtonPressed(ui.restartButton!!))
        assertEquals(listOf<GameEvent>(GameEvent.RestartGame), events.get())
    }

    // --- Parity with the desktop game (values measured by running the pygame build headless) ---

    /** Moving down from level 1's start onto the fake tile at (0, 1) kills on frame 6, at y = 80. */
    @Test fun fakeTileDeathFrameMatchesDesktop() {
        val level = Level(config)
        assertTrue(level.loadLevel("levels/level1.json"))
        val p = Player(config, level.startPos)
        var frames = 0
        var deathFrame = -1
        while (frames < 100) {
            p.update(1.0 / 60)
            p.handleInput(keys(Keys.DOWN), level)
            if (level.isFakeTile(p.getGridPosition())) {
                deathFrame = frames
                break
            }
            frames++
        }
        assertEquals(6, deathFrame)
        assertEquals(80.0, p.y, 1e-9)
        assertEquals(GridPos(0, 1), p.getGridPosition())
    }

    /** At level start the run transition plays once (time_since_movement_stopped starts at 0). */
    @Test fun levelStartPlaysTransitionLikeDesktop() {
        val p = Player(config, GridPos(0, 0))
        p.update(0.016)
        assertEquals(AnimationState.TRANSITIONING_TO_RUN, p.animationState)
    }

    /** On level clear, Try Again is ignored and Level Editor continues (desktop behaviour). */
    @Test fun levelClearButtonQuirksMatchDesktop() {
        val events = EventQueue()
        val game = Game(keys(), { Pair(0, 0) }, events)
        game.events.post(GameEvent.KeyDown(Keys.SPACE))
        game.step(0.016)
        game.events.post(GameEvent.KeyDown(Keys.C))
        game.step(0.016)
        assertEquals("level_clear", game.gameState)
        assertEquals(3, game.scoreSystem.stars)

        game.ui!!.handleUiEvents(GameEvent.UiButtonPressed(game.ui!!.restartButton!!))
        game.step(0.016)
        assertEquals("level_clear", game.gameState)

        game.ui!!.handleUiEvents(GameEvent.UiButtonPressed(game.ui!!.editorButton!!))
        game.step(0.016)
        assertEquals("playing", game.gameState)
        assertEquals(1, game.currentLevelIndex)
    }
}
