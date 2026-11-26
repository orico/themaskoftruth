package org.thetruthmask.floorisalie

import android.content.res.AssetManager
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Typeface
import kotlin.math.ceil

/** Drawing primitives with pygame semantics on an Android Canvas in 1200x850 logical pixels. */
object Gfx {
    @Volatile
    var assets: AssetManager? = null

    private val fillPaint = Paint().apply { isAntiAlias = false; style = Paint.Style.FILL }
    private val bitmapPaint = Paint().apply { isFilterBitmap = true; isAntiAlias = false }

    /** screen.fill(color) / Surface.fill on a rectangle (alpha in the colour blends, like SRCALPHA blits). */
    fun fillRect(canvas: Canvas, argb: Int, x: Int, y: Int, w: Int, h: Int) {
        fillPaint.color = argb
        canvas.drawRect(x.toFloat(), y.toFloat(), (x + w).toFloat(), (y + h).toFloat(), fillPaint)
    }

    /** pygame.draw.rect(surface, color, rect, 1): a one-pixel outline inside the rect. */
    fun rectOutline(canvas: Canvas, argb: Int, x: Int, y: Int, w: Int, h: Int) {
        if (w <= 0 || h <= 0) return
        fillRect(canvas, argb, x, y, w, 1)
        fillRect(canvas, argb, x, y + h - 1, w, 1)
        fillRect(canvas, argb, x, y + 1, 1, h - 2)
        fillRect(canvas, argb, x + w - 1, y + 1, 1, h - 2)
    }

    /** screen.blit(image, (x, y)), optionally with a surface alpha (Surface.set_alpha). */
    fun blit(canvas: Canvas, image: Bitmap, x: Int, y: Int, alpha: Int = 255) {
        bitmapPaint.alpha = alpha.coerceIn(0, 255)
        canvas.drawBitmap(image, x.toFloat(), y.toFloat(), bitmapPaint)
    }

    private val typefaces = HashMap<String, Typeface>()

    /** Null only off-device (JVM unit tests), where nothing is drawn. */
    @Synchronized
    fun typeface(path: String): Typeface? {
        typefaces[path]?.let { return it }
        val am = assets ?: return null
        return Typeface.createFromAsset(am, path).also { typefaces[path] = it }
    }
}

/**
 * pygame.font.Font(None, size): pygame's default font is freesansbold.ttf, and pygame scales the
 * requested size by 0.6875 for it (48 -> 33 px). Metrics were measured from pygame-ce 2.5.6:
 * get_height() == pixel size and get_ascent() == ceil(0.8 * pixel size) (sizes 22/33/44 -> 18/27/36).
 */
class PgFont private constructor(requestedSize: Int) {
    val pixelSize: Int = (requestedSize * 0.6875).toInt()
    val ascent: Int = ceil(pixelSize * 0.8).toInt()

    private val paint: Paint by lazy {
        Paint().apply {
            isAntiAlias = true
            typeface = Gfx.typeface("fonts/freesansbold.ttf")
            textSize = pixelSize.toFloat()
        }
    }

    /** Font.get_height() */
    fun getHeight(): Int = pixelSize

    /** Font.size(text)[0], the width of the rendered surface. */
    fun width(text: String): Int = Math.round(paint.measureText(text))

    /** screen.blit(font.render(text, True, color), (x, y)): (x, y) is the top-left of the text box. */
    fun draw(canvas: Canvas, text: String, color: Int, x: Int, y: Int) {
        paint.color = color
        canvas.drawText(text, x.toFloat(), (y + ascent).toFloat(), paint)
    }

    companion object {
        private val cache = HashMap<Int, PgFont>()

        @Synchronized
        fun default(requestedSize: Int): PgFont = cache.getOrPut(requestedSize) { PgFont(requestedSize) }
    }
}

/**
 * pygame_gui's default font: FiraCode Regular at 14 px through pygame.freetype
 * (ascender 14, line height 18). Text is centred in its element: measured against pygame_gui
 * 0.6.9, x = rect.x + (rect.w - width) / 2 and baseline = rect.y + floor((rect.h - 18) / 2 + 14).
 */
object GuiFont {
    const val SIZE = 14
    const val ASCENDER = 14
    const val LINE_HEIGHT = 18

    private val paint: Paint by lazy {
        Paint().apply {
            isAntiAlias = true
            typeface = Gfx.typeface("fonts/FiraCode-Regular.ttf")
            textSize = SIZE.toFloat()
        }
    }

    fun width(text: String): Float = paint.measureText(text)

    fun drawCentered(canvas: Canvas, text: String, color: Int, x: Int, y: Int, w: Int, h: Int) {
        if (text.isEmpty()) return
        paint.color = color
        val originX = x + Math.floorDiv(w - Math.round(width(text)), 2)
        val baseline = y + kotlin.math.floor((h - LINE_HEIGHT) / 2.0 + ASCENDER).toInt()
        canvas.drawText(text, originX.toFloat(), baseline.toFloat(), paint)
    }
}
