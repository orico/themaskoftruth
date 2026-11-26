package org.thetruthmask.floorisalie.gui

import android.graphics.Canvas
import org.thetruthmask.floorisalie.EventQueue
import org.thetruthmask.floorisalie.GameEvent
import org.thetruthmask.floorisalie.Gfx
import org.thetruthmask.floorisalie.GuiFont

/**
 * The part of pygame_gui 0.6.9 this game uses: UIManager, UILabel, UIButton and UIPanel with the
 * default theme. Drawing and hit-testing reproduce what pygame_gui renders (measured from the
 * desktop game): a 2 px shadow ring, a 1 px border, the background, and FiraCode 14 text.
 */
data class IntRect(val x: Int, val y: Int, val w: Int, val h: Int) {
    val right get() = x + w
    val bottom get() = y + h
    fun contains(px: Int, py: Int) = px >= x && px < x + w && py >= y && py < y + h
}

/** Default theme colours from pygame_gui/data/default_theme.json */
object Theme {
    const val NORMAL_BG = 0xFF4C5052.toInt()
    const val HOVERED_BG = 0xFF63686B.toInt()
    const val ACTIVE_BG = 0xFF365880.toInt()
    const val DARK_BG = 0xFF21282D.toInt()
    const val NORMAL_TEXT = 0xFFBBBBBB.toInt()
    const val NORMAL_BORDER = 0xFF5C6062.toInt()
    const val HOVERED_BORDER = 0xFF73787B.toInt()
    const val ACTIVE_BORDER = 0xFF466890.toInt()
    const val SHADOW_WIDTH = 2
    const val BORDER_WIDTH = 1

    // The default shadow colour is #10101070, drawn as a soft gradient; measured on the editor
    // panel it darkens the outer ring very slightly and the inner ring a little more.
    const val SHADOW_OUTER = 0x0A101010
    const val SHADOW_INNER = 0x1F101010
}

class UIManager(val width: Int, val height: Int, private val events: EventQueue, private val mouse: () -> Pair<Int, Int>) {
    internal val elements = ArrayList<UIElement>()

    internal fun add(element: UIElement) {
        elements.add(element)
    }

    internal fun remove(element: UIElement) {
        elements.remove(element)
    }

    /** pygame.event.post */
    fun postEvent(event: GameEvent) = events.post(event)

    /** process_events: offered to the top-most elements first; returns True if consumed. */
    fun processEvents(event: GameEvent): Boolean {
        for (element in elements.asReversed().toList()) {
            if (!element.alive || !element.visible) continue
            if (element.processEvent(event)) return true
        }
        return false
    }

    /** update: work out which element (only the top-most one) is hovered by the mouse. */
    fun update(@Suppress("UNUSED_PARAMETER") timeDelta: Double) {
        val (mx, my) = mouse()
        var handled = false
        for (element in elements.asReversed()) {
            if (!element.visible) {
                element.hovered = false
                continue
            }
            val over = !handled && element.blocksHover && element.rect.contains(mx, my)
            element.hovered = over && element.canHover()
            if (over) handled = true
        }
    }

    fun drawUi(canvas: Canvas) {
        for (element in elements) if (element.visible) element.draw(canvas)
    }

    /** The UIManager's theme file loader; theme files only add object ids this game never uses. */
    fun loadThemeFile(@Suppress("UNUSED_PARAMETER") path: String) {}
}

abstract class UIElement(val manager: UIManager, relativeRect: IntRect, val container: UIPanel?) {
    /** Absolute rect: panel children are offset by the panel's shadow + border (3 px). */
    val rect: IntRect = if (container != null) {
        val inset = Theme.SHADOW_WIDTH + Theme.BORDER_WIDTH
        IntRect(container.rect.x + inset + relativeRect.x, container.rect.y + inset + relativeRect.y, relativeRect.w, relativeRect.h)
    } else {
        relativeRect
    }
    var visible = true
    var alive = true
    var hovered = false
    open val blocksHover = true

    init {
        manager.add(this)
        container?.children?.add(this)
    }

    open fun canHover() = true

    open fun processEvent(event: GameEvent): Boolean = false

    abstract fun draw(canvas: Canvas)

    open fun kill() {
        alive = false
        manager.remove(this)
    }

    protected fun drawShape(canvas: Canvas, bg: Int, border: Int) {
        val r = rect
        val s = Theme.SHADOW_WIDTH
        // Shadow ring
        ring(canvas, Theme.SHADOW_OUTER, r.x, r.y, r.w, r.h)
        ring(canvas, Theme.SHADOW_INNER, r.x + 1, r.y + 1, r.w - 2, r.h - 2)
        // Border, then background
        ring(canvas, border, r.x + s, r.y + s, r.w - 2 * s, r.h - 2 * s)
        val inset = s + Theme.BORDER_WIDTH
        Gfx.fillRect(canvas, bg, r.x + inset, r.y + inset, r.w - 2 * inset, r.h - 2 * inset)
    }

    private fun ring(canvas: Canvas, argb: Int, x: Int, y: Int, w: Int, h: Int) = Gfx.rectOutline(canvas, argb, x, y, w, h)
}

class UILabel(manager: UIManager, relativeRect: IntRect, text: String, container: UIPanel? = null) :
    UIElement(manager, relativeRect, container) {
    var text: String = text
        private set

    // Labels do not take part in hovering in a way that changes anything this game draws.
    override val blocksHover = false

    fun setText(text: String) {
        this.text = text
    }

    override fun draw(canvas: Canvas) {
        GuiFont.drawCentered(canvas, text, Theme.NORMAL_TEXT, rect.x, rect.y, rect.w, rect.h)
    }
}

class UIButton(manager: UIManager, relativeRect: IntRect, var text: String, container: UIPanel? = null) :
    UIElement(manager, relativeRect, container) {
    var held = false
    var isEnabled = true

    /** Set by ui.py's make_transparent(): no background, border or shadow, white text. */
    var transparent = false

    override fun canHover() = !held

    override fun processEvent(event: GameEvent): Boolean {
        var consumed = false
        if (event is GameEvent.MouseButtonDown && event.button == 1) {
            if (rect.contains(event.x, event.y)) {
                if (isEnabled) {
                    held = true
                    hovered = false
                }
                consumed = true
            }
        }
        if (event is GameEvent.MouseButtonUp && event.button == 1) {
            if (isEnabled && rect.contains(event.x, event.y) && held) {
                held = false
                consumed = true
                manager.postEvent(GameEvent.UiButtonPressed(this))
            }
            if (isEnabled && held) {
                held = false
                consumed = true
            }
        }
        return consumed
    }

    override fun draw(canvas: Canvas) {
        if (transparent) {
            GuiFont.drawCentered(canvas, text, 0xFFFFFFFF.toInt(), rect.x, rect.y, rect.w, rect.h)
            return
        }
        val (bg, border) = when {
            held -> Theme.ACTIVE_BG to Theme.ACTIVE_BORDER
            hovered -> Theme.HOVERED_BG to Theme.HOVERED_BORDER
            else -> Theme.NORMAL_BG to Theme.NORMAL_BORDER
        }
        drawShape(canvas, bg, border)
        GuiFont.drawCentered(canvas, text, Theme.NORMAL_TEXT, rect.x, rect.y, rect.w, rect.h)
    }
}

class UIPanel(manager: UIManager, relativeRect: IntRect) : UIElement(manager, relativeRect, null) {
    val children = ArrayList<UIElement>()

    override fun canHover() = false

    /** Panels swallow clicks that land on them. */
    override fun processEvent(event: GameEvent): Boolean =
        event is GameEvent.MouseButtonDown && rect.contains(event.x, event.y)

    override fun draw(canvas: Canvas) {
        drawShape(canvas, Theme.DARK_BG, Theme.NORMAL_BORDER)
    }

    override fun kill() {
        super.kill()
        for (child in children.toList()) if (child.alive) child.kill()
    }
}
