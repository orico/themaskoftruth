package org.thetruthmask.floorisalie

import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import org.thetruthmask.floorisalie.gui.IntRect

/**
 * Android-only on-screen keys, drawn in the empty 320 px column to the right of the 880 px board,
 * below the HUD. They stand in for the keyboard: the D-pad is held like the arrow keys
 * (pygame.key.get_pressed), and every other button sends the same KEYDOWN the desktop key does.
 * Shown only while playing (and during the death animation); the editor and result screens are
 * driven by their own buttons and taps.
 */
class TouchControls(private val events: EventQueue) {
    class Button(val rect: IntRect, val label: String, val key: Int, val isDpad: Boolean)

    val buttons = listOf(
        // Key row: R, E, B, U, C
        Button(IntRect(890, 118, 96, 40), "Restart", Keys.R, false),
        Button(IntRect(992, 118, 96, 40), "Editor", Keys.E, false),
        Button(IntRect(1094, 118, 96, 40), "Music", Keys.B, false),
        Button(IntRect(890, 164, 147, 40), "Mute", Keys.U, false),
        Button(IntRect(1043, 164, 147, 40), "Cheat", Keys.C, false),
        // D-pad
        Button(IntRect(992, 222, 96, 96), "▲", Keys.UP, true),
        Button(IntRect(892, 318, 100, 96), "◀", Keys.LEFT, true),
        Button(IntRect(1088, 318, 100, 96), "▶", Keys.RIGHT, true),
        Button(IntRect(992, 414, 96, 96), "▼", Keys.DOWN, true),
        // Mask
        Button(IntRect(900, 540, 280, 160), "MASK", Keys.M, false),
    )

    /** Which button each touching finger is on (null = finger owned by a control but off it). */
    private val owners = HashMap<Int, Button?>()

    /** Movement keys currently held through the D-pad. */
    val heldKeys: Set<Int>
        get() = owners.values.filterNotNull().filter { it.isDpad }.map { it.key }.toSet()

    fun isVisible(gameState: String) = gameState == "playing" || gameState == "dying"

    fun owns(pointerId: Int) = owners.containsKey(pointerId)

    private fun hit(x: Int, y: Int, dpadOnly: Boolean = false) =
        buttons.firstOrNull { (!dpadOnly || it.isDpad) && it.rect.contains(x, y) }

    /** A finger touched down; returns true when a control takes it. */
    fun onPointerDown(pointerId: Int, x: Int, y: Int, gameState: String): Boolean {
        if (!isVisible(gameState)) return false
        val button = hit(x, y) ?: return false
        owners[pointerId] = button
        events.post(GameEvent.KeyDown(button.key))
        return true
    }

    /** Sliding a finger across the D-pad changes direction, like rolling a thumb over arrow keys. */
    fun onPointerMove(pointerId: Int, x: Int, y: Int) {
        if (!owners.containsKey(pointerId)) return
        val current = owners[pointerId]
        if (current != null && !current.isDpad) return
        val next = hit(x, y, dpadOnly = true)
        if (next !== current) {
            current?.let { events.post(GameEvent.KeyUp(it.key)) }
            next?.let { events.post(GameEvent.KeyDown(it.key)) }
            owners[pointerId] = next
        }
    }

    fun onPointerUp(pointerId: Int) {
        if (!owners.containsKey(pointerId)) return
        owners.remove(pointerId)?.let { events.post(GameEvent.KeyUp(it.key)) }
    }

    fun releaseAll() {
        for (id in owners.keys.toList()) onPointerUp(id)
    }

    private val fill = Paint().apply { isAntiAlias = true; style = Paint.Style.FILL }
    private val stroke = Paint().apply { isAntiAlias = true; style = Paint.Style.STROKE; strokeWidth = 2f }
    private val text = Paint().apply {
        isAntiAlias = true
        textAlign = Paint.Align.CENTER
    }

    fun draw(canvas: Canvas, gameState: String, maskAvailable: Boolean) {
        if (!isVisible(gameState)) return
        val pressed = owners.values.filterNotNull().toSet()
        text.typeface = Gfx.typeface("fonts/FiraCode-Regular.ttf")
        for (b in buttons) {
            val r = RectF(b.rect.x.toFloat(), b.rect.y.toFloat(), b.rect.right.toFloat(), b.rect.bottom.toFloat())
            val isPressed = b in pressed
            val dim = b.key == Keys.M && !maskAvailable
            fill.color = when {
                isPressed -> 0x80FFFFFF.toInt()
                b.key == Keys.M && !dim -> 0x4DE6C84A // golden, like the mask
                else -> 0x26FFFFFF
            }
            stroke.color = if (dim) 0x40FFFFFF else 0x99FFFFFF.toInt()
            val radius = if (b.isDpad) 18f else 12f
            canvas.drawRoundRect(r, radius, radius, fill)
            canvas.drawRoundRect(r, radius, radius, stroke)
            text.color = if (dim) 0x66FFFFFF else 0xE6FFFFFF.toInt()
            text.textSize = when {
                b.key == Keys.M -> 40f
                b.isDpad -> 38f
                else -> 17f
            }
            val fm = text.fontMetrics
            val baseline = r.centerY() - (fm.ascent + fm.descent) / 2
            canvas.drawText(b.label, r.centerX(), baseline, text)
        }
    }
}
