package org.thetruthmask.floorisalie

import android.app.Activity
import android.content.pm.ApplicationInfo
import android.os.Bundle
import android.view.KeyEvent
import android.view.WindowInsets
import android.view.WindowInsetsController
import android.view.WindowManager

class MainActivity : Activity() {
    private var gameView: GameView? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Gfx.assets = assets
        GameFiles.current = AndroidFiles(this)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        // Debug builds only: replay tools/scenarios.json and save frames for parity checks.
        val debuggable = applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0
        if (debuggable && intent.getBooleanExtra("scenario", false)) {
            ScenarioRunner.runAsync(this) { finish() }
            return
        }

        val view = GameView(this)
        gameView = view
        setContentView(view)
        hideSystemBars()
    }

    private fun hideSystemBars() {
        window.insetsController?.let {
            it.hide(WindowInsets.Type.systemBars())
            it.systemBarsBehavior = WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        }
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) hideSystemBars()
    }

    override fun onResume() {
        super.onResume()
        gameView?.onResume()
    }

    override fun onPause() {
        gameView?.onPause()
        super.onPause()
    }

    override fun onDestroy() {
        if (isFinishing && gameView != null) Mixer.current.release()
        super.onDestroy()
    }

    /** Back = Esc in the level editor (its only use on desktop); elsewhere, leave the game running in the background. */
    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        val view = gameView
        if (view != null && view.gameState == "level_editor") {
            view.onGameKey(true, Keys.ESCAPE)
            view.onGameKey(false, Keys.ESCAPE)
        } else {
            moveTaskToBack(true)
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK) return super.onKeyDown(keyCode, event)
        val key = mapKey(keyCode) ?: return super.onKeyDown(keyCode, event)
        if (event.repeatCount == 0) gameView?.onGameKey(true, key) // pygame has key repeat off
        return true
    }

    override fun onKeyUp(keyCode: Int, event: KeyEvent): Boolean {
        if (keyCode == KeyEvent.KEYCODE_BACK) return super.onKeyUp(keyCode, event)
        val key = mapKey(keyCode) ?: return super.onKeyUp(keyCode, event)
        gameView?.onGameKey(false, key)
        return true
    }

    /** Keyboard keys to the pygame keys the game checks; any other typing key is "any key". */
    private fun mapKey(keyCode: Int): Int? = when (keyCode) {
        KeyEvent.KEYCODE_DPAD_LEFT -> Keys.LEFT
        KeyEvent.KEYCODE_DPAD_RIGHT -> Keys.RIGHT
        KeyEvent.KEYCODE_DPAD_UP -> Keys.UP
        KeyEvent.KEYCODE_DPAD_DOWN -> Keys.DOWN
        KeyEvent.KEYCODE_A -> Keys.A
        KeyEvent.KEYCODE_D -> Keys.D
        KeyEvent.KEYCODE_W -> Keys.W
        KeyEvent.KEYCODE_S -> Keys.S
        KeyEvent.KEYCODE_M -> Keys.M
        KeyEvent.KEYCODE_R -> Keys.R
        KeyEvent.KEYCODE_E -> Keys.E
        KeyEvent.KEYCODE_B -> Keys.B
        KeyEvent.KEYCODE_U -> Keys.U
        KeyEvent.KEYCODE_C -> Keys.C
        KeyEvent.KEYCODE_ESCAPE -> Keys.ESCAPE
        KeyEvent.KEYCODE_SPACE -> Keys.SPACE
        KeyEvent.KEYCODE_VOLUME_UP, KeyEvent.KEYCODE_VOLUME_DOWN, KeyEvent.KEYCODE_VOLUME_MUTE,
        KeyEvent.KEYCODE_HOME, KeyEvent.KEYCODE_POWER, KeyEvent.KEYCODE_APP_SWITCH,
        -> null
        else -> Keys.OTHER
    }
}
