package org.thetruthmask.floorisalie

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.util.Log
import org.json.JSONObject
import java.io.File

/**
 * Debug-only parity check: replays tools/scenarios.json exactly like tools/reference_frames.py
 * does on desktop (fixed dt, scripted keys and mouse, no audio, music timer off) and saves each
 * "snap" as a 1200x850 PNG in the app's external files dir under frames/.
 *
 *   adb shell am start -n org.thetruthmask.floorisalie/.MainActivity --ez scenario true
 */
object ScenarioRunner {
    private const val TAG = "ScenarioRunner"

    fun runAsync(context: Context, done: () -> Unit) {
        Thread({
            try {
                run(context)
            } catch (e: Exception) {
                Log.e(TAG, "Scenario failed", e)
            }
            Log.i(TAG, "SCENARIO DONE")
            (context as? android.app.Activity)?.runOnUiThread(done)
        }, "Scenario").start()
    }

    private fun run(context: Context) {
        val outDir = File(context.getExternalFilesDir(null), "frames").apply {
            deleteRecursively()
            mkdirs()
        }
        Mixer.current = SilentMixer()
        Assets.instance = Assets(context.assets, Mixer.current)

        val script = JSONObject(context.assets.open("tools/scenarios.json").bufferedReader().use { it.readText() })
        val dt = script.getDouble("dt")
        val held = HashSet<Int>()
        var mouse = Pair(0, 0)
        val events = EventQueue()
        val timers = EventTimers(events) { 0L }.apply { enabled = false }
        val game = Game(KeyState { held.contains(it) }, { mouse }, events, timers, tapIsAnyKey = false)

        val config = game.config
        val bitmap = Bitmap.createBitmap(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)

        val steps = script.getJSONArray("steps")
        for (i in 0 until steps.length()) {
            val step = steps.getJSONObject(i)
            when (step.getString("op")) {
                "frames" -> repeat(step.getInt("n")) {
                    game.step(dt)
                    game.render(canvas)
                }
                "key" -> {
                    val key = Keys.fromName(step.getString("key"))
                    events.post(GameEvent.KeyDown(key))
                    events.post(GameEvent.KeyUp(key))
                }
                "hold" -> {
                    val key = Keys.fromName(step.getString("key"))
                    held.add(key)
                    events.post(GameEvent.KeyDown(key))
                }
                "release" -> {
                    val key = Keys.fromName(step.getString("key"))
                    held.remove(key)
                    events.post(GameEvent.KeyUp(key))
                }
                "mouse" -> {
                    val x = step.getInt("x")
                    val y = step.getInt("y")
                    mouse = Pair(x, y)
                    when (step.getString("action")) {
                        "move" -> events.post(GameEvent.MouseMotion(x, y))
                        "down" -> events.post(GameEvent.MouseButtonDown(x, y))
                        else -> events.post(GameEvent.MouseButtonUp(x, y))
                    }
                }
                "snap" -> {
                    val name = step.getString("name")
                    File(outDir, "$name.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
                    Log.i(
                        TAG,
                        "$name: state=${game.gameState} player=(${game.player.gridX}, ${game.player.gridY}) " +
                            "anim=${game.player.animationState} frame=${game.player.currentAnimation.currentFrame}",
                    )
                }
            }
        }
    }
}
