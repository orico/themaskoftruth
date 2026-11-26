package org.thetruthmask.floorisalie

import android.content.Context
import android.graphics.Canvas
import android.os.SystemClock
import android.util.Log
import android.view.MotionEvent
import android.view.SurfaceHolder
import android.view.SurfaceView
import java.util.concurrent.ConcurrentLinkedQueue

/**
 * Hosts the game: a dedicated thread runs Game.run()'s loop (pygame's clock.tick(60) pacing,
 * dt from the real elapsed milliseconds), and each frame is drawn in the game's 1200x850
 * coordinates, scaled to fit the screen and centred.
 */
class GameView(context: Context) : SurfaceView(context), SurfaceHolder.Callback {
    private sealed class Input {
        data class Touch(val action: Int, val pointerId: Int, val x: Int, val y: Int) : Input()
        data class Key(val down: Boolean, val key: Int) : Input()
    }

    private val inputs = ConcurrentLinkedQueue<Input>()
    private val physicalKeys = HashSet<Int>() // game thread only
    private var mousePos = Pair(0, 0) // pygame.mouse.get_pos(); game thread only
    private var mousePointer: Int? = null

    @Volatile private var game: Game? = null
    private var controls: TouchControls? = null

    @Volatile private var surfaceReady = false
    @Volatile private var resumed = false
    @Volatile private var running = false
    private var thread: Thread? = null
    private var pausedAt = 0L

    // Logical-to-screen transform, written by the game thread, read by the UI thread
    @Volatile private var scale = 1f
    @Volatile private var offsetX = 0f
    @Volatile private var offsetY = 0f

    /** The current game state, for the Back button. */
    val gameState: String? get() = game?.gameState

    init {
        holder.addCallback(this)
        isFocusable = true
        keepScreenOn = true
    }

    // --- lifecycle -----------------------------------------------------------------------------

    override fun surfaceCreated(holder: SurfaceHolder) {
        surfaceReady = true
        startIfReady()
    }

    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {}

    override fun surfaceDestroyed(holder: SurfaceHolder) {
        surfaceReady = false
        stopThread()
    }

    fun onResume() {
        resumed = true
        startIfReady()
    }

    fun onPause() {
        resumed = false
        stopThread()
    }

    private fun startIfReady() {
        if (!surfaceReady || !resumed || running) return
        running = true
        thread = Thread(::loop, "GameLoop").also { it.start() }
    }

    private fun stopThread() {
        if (!running) return
        running = false
        thread?.join(2000)
        thread = null
    }

    // --- game loop -----------------------------------------------------------------------------

    private fun loop() {
        var g = game
        if (g == null) {
            drawBlank()
            val mixer = AndroidMixer(context.assets)
            Mixer.current = mixer
            Assets.instance = Assets(context.assets, mixer)
            g = Game(keys = KeyState { physicalKeys.contains(it) || controls?.heldKeys?.contains(it) == true }, mouse = { mousePos })
            controls = TouchControls(g.events)
            game = g
        } else {
            // Coming back from the background: timers measure play time, input restarts clean.
            g.timers.shift(SystemClock.uptimeMillis() - pausedAt)
            Mixer.current.onAppResume()
        }

        val frameMs = (1000 / g.config.FPS).toLong() // pygame's tick(60) uses int(1000 / 60) = 16 ms
        var last = SystemClock.uptimeMillis()
        while (running) {
            // clock.tick(FPS): wait out the rest of the frame, return elapsed milliseconds
            var now = SystemClock.uptimeMillis()
            val wait = frameMs - (now - last)
            if (wait > 0) {
                SystemClock.sleep(wait)
                now = SystemClock.uptimeMillis()
            }
            val timeDelta = (now - last) / 1000.0
            last = now

            pumpInput(g)
            try {
                g.step(timeDelta)
            } catch (e: Exception) {
                Log.e(TAG, "Game crashed with error: $e", e)
                throw e
            }
            drawFrame(g)
        }

        // Paused: release held touch keys and silence audio until resumed
        controls?.releaseAll()
        physicalKeys.clear()
        mousePointer = null
        pausedAt = SystemClock.uptimeMillis()
        Mixer.current.onAppPause()
    }

    /** Turn queued Android input into pygame events (SDL's event pump). */
    private fun pumpInput(g: Game) {
        val controls = controls ?: return
        while (true) {
            when (val input = inputs.poll() ?: break) {
                is Input.Key -> {
                    if (input.down) {
                        physicalKeys.add(input.key)
                        g.events.post(GameEvent.KeyDown(input.key))
                    } else {
                        physicalKeys.remove(input.key)
                        g.events.post(GameEvent.KeyUp(input.key))
                    }
                }
                is Input.Touch -> handleTouch(g, controls, input)
            }
        }
    }

    private fun handleTouch(g: Game, controls: TouchControls, t: Input.Touch) {
        when (t.action) {
            MotionEvent.ACTION_DOWN -> {
                if (controls.onPointerDown(t.pointerId, t.x, t.y, g.gameState)) return
                if (mousePointer == null) {
                    // One finger at a time acts as the mouse
                    mousePointer = t.pointerId
                    mousePos = Pair(t.x, t.y)
                    g.events.post(GameEvent.MouseMotion(t.x, t.y))
                    g.events.post(GameEvent.MouseButtonDown(t.x, t.y))
                }
            }
            MotionEvent.ACTION_MOVE -> {
                if (controls.owns(t.pointerId)) {
                    controls.onPointerMove(t.pointerId, t.x, t.y)
                } else if (mousePointer == t.pointerId && mousePos != Pair(t.x, t.y)) {
                    mousePos = Pair(t.x, t.y)
                    g.events.post(GameEvent.MouseMotion(t.x, t.y))
                }
            }
            MotionEvent.ACTION_UP -> {
                if (controls.owns(t.pointerId)) {
                    controls.onPointerUp(t.pointerId)
                } else if (mousePointer == t.pointerId) {
                    mousePointer = null
                    mousePos = Pair(t.x, t.y)
                    g.events.post(GameEvent.MouseButtonUp(t.x, t.y))
                }
            }
            MotionEvent.ACTION_CANCEL -> {
                if (controls.owns(t.pointerId)) controls.onPointerUp(t.pointerId)
                if (mousePointer == t.pointerId) mousePointer = null
            }
        }
    }

    private fun updateTransform(width: Int, height: Int, config: Config) {
        val s = minOf(width.toFloat() / config.SCREEN_WIDTH, height.toFloat() / config.SCREEN_HEIGHT)
        scale = s
        offsetX = (width - config.SCREEN_WIDTH * s) / 2f
        offsetY = (height - config.SCREEN_HEIGHT * s) / 2f
    }

    private fun drawFrame(g: Game) {
        val canvas = lockCanvas() ?: return
        try {
            updateTransform(canvas.width, canvas.height, g.config)
            canvas.drawColor(g.config.BACKGROUND_COLOR.argb)
            canvas.save()
            canvas.translate(offsetX, offsetY)
            canvas.scale(scale, scale)
            canvas.clipRect(0, 0, g.config.SCREEN_WIDTH, g.config.SCREEN_HEIGHT)
            g.render(canvas)
            val maskAvailable = g.gameState != "playing" || g.player.maskAvailable || g.player.maskActive
            controls?.draw(canvas, g.gameState, maskAvailable)
            canvas.restore()
        } finally {
            holder.unlockCanvasAndPost(canvas)
        }
    }

    private fun drawBlank() {
        val canvas = lockCanvas() ?: return
        canvas.drawColor(Config().BACKGROUND_COLOR.argb)
        holder.unlockCanvasAndPost(canvas)
    }

    private fun lockCanvas(): Canvas? = try {
        holder.lockHardwareCanvas()
    } catch (e: Exception) {
        null
    }

    // --- input (UI thread) ---------------------------------------------------------------------

    override fun onTouchEvent(event: MotionEvent): Boolean {
        val action = event.actionMasked
        fun push(index: Int, a: Int) {
            val lx = ((event.getX(index) - offsetX) / scale).toInt()
            val ly = ((event.getY(index) - offsetY) / scale).toInt()
            inputs.add(Input.Touch(a, event.getPointerId(index), lx, ly))
        }
        when (action) {
            MotionEvent.ACTION_DOWN, MotionEvent.ACTION_POINTER_DOWN -> push(event.actionIndex, MotionEvent.ACTION_DOWN)
            MotionEvent.ACTION_UP, MotionEvent.ACTION_POINTER_UP -> push(event.actionIndex, MotionEvent.ACTION_UP)
            MotionEvent.ACTION_MOVE -> for (i in 0 until event.pointerCount) push(i, MotionEvent.ACTION_MOVE)
            MotionEvent.ACTION_CANCEL -> for (i in 0 until event.pointerCount) push(i, MotionEvent.ACTION_CANCEL)
        }
        return true
    }

    /** A physical/Bluetooth keyboard key, already mapped to [Keys]. */
    fun onGameKey(down: Boolean, key: Int) {
        inputs.add(Input.Key(down, key))
    }

    companion object {
        private const val TAG = "GameView"
    }
}
