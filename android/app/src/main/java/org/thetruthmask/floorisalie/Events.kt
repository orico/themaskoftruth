package org.thetruthmask.floorisalie

import org.thetruthmask.floorisalie.gui.UIButton

/** Key identifiers standing in for the pygame.K_* constants the game uses. */
object Keys {
    const val OTHER = 0 // any key without a dedicated meaning ("Push Any Key")
    const val LEFT = 1
    const val RIGHT = 2
    const val UP = 3
    const val DOWN = 4
    const val A = 5
    const val D = 6
    const val W = 7
    const val S = 8
    const val M = 9
    const val R = 10
    const val E = 11
    const val B = 12
    const val U = 13
    const val C = 14
    const val ESCAPE = 15
    const val SPACE = 16

    fun name(key: Int): String = when (key) {
        LEFT -> "left"; RIGHT -> "right"; UP -> "up"; DOWN -> "down"
        A -> "a"; D -> "d"; W -> "w"; S -> "s"; M -> "m"; R -> "r"; E -> "e"
        B -> "b"; U -> "u"; C -> "c"; ESCAPE -> "escape"; SPACE -> "space"
        else -> "unknown"
    }

    fun fromName(name: String): Int = when (name) {
        "left" -> LEFT; "right" -> RIGHT; "up" -> UP; "down" -> DOWN
        "a" -> A; "d" -> D; "w" -> W; "s" -> S; "m" -> M; "r" -> R; "e" -> E
        "b" -> B; "u" -> U; "c" -> C; "escape" -> ESCAPE; "space" -> SPACE
        else -> OTHER
    }
}

/** The result of pygame.key.get_pressed(): indexable by key. */
fun interface KeyState {
    operator fun get(key: Int): Boolean
}

/** Mirrors the pygame events the game reacts to, including its custom USEREVENTs. */
sealed class GameEvent {
    object Quit : GameEvent()
    data class KeyDown(val key: Int) : GameEvent()
    data class KeyUp(val key: Int) : GameEvent()
    data class MouseMotion(val x: Int, val y: Int) : GameEvent()
    data class MouseButtonDown(val x: Int, val y: Int, val button: Int = 1) : GameEvent()
    data class MouseButtonUp(val x: Int, val y: Int, val button: Int = 1) : GameEvent()

    /** pygame_gui.UI_BUTTON_PRESSED */
    data class UiButtonPressed(val uiElement: UIButton) : GameEvent()

    // Custom events from ui.py
    object RestartGame : GameEvent()            // RESTART_GAME_EVENT
    object RestartFromLevel1 : GameEvent()      // RESTART_FROM_LEVEL_1_EVENT
    object ContinueToNextLevel : GameEvent()    // CONTINUE_TO_NEXT_LEVEL_EVENT
    object StartMusic : GameEvent()             // START_MUSIC_EVENT
}

/**
 * The pygame event queue. post() appends; get() drains a snapshot, so events posted while a
 * snapshot is being processed are only seen on the next frame, exactly as with pygame.event.get().
 */
class EventQueue {
    private val queue = ArrayDeque<GameEvent>()

    @Synchronized
    fun post(event: GameEvent) {
        queue.addLast(event)
    }

    @Synchronized
    fun get(): List<GameEvent> {
        val snapshot = queue.toList()
        queue.clear()
        return snapshot
    }

    @Synchronized
    fun clear() = queue.clear()
}

/**
 * pygame.time.set_timer(event, millis, loops=1). Setting the same event again replaces the
 * pending timer, like SDL does. The clock is injectable so scripted runs can disable it.
 */
class EventTimers(private val events: EventQueue, private val clock: () -> Long) {
    private val pending = HashMap<GameEvent, Long>()
    var enabled = true

    @Synchronized
    fun setTimer(event: GameEvent, millis: Long) {
        if (!enabled) return
        if (millis <= 0) pending.remove(event) else pending[event] = clock() + millis
    }

    @Synchronized
    fun pump() {
        if (pending.isEmpty()) return
        val now = clock()
        val due = pending.filterValues { it <= now }.keys
        for (event in due) {
            pending.remove(event)
            events.post(event)
        }
    }

    /** Shift pending deadlines after the app was paused, so timers measure play time. */
    @Synchronized
    fun shift(millis: Long) {
        for (key in pending.keys.toList()) pending[key] = pending.getValue(key) + millis
    }
}
