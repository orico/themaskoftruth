package org.thetruthmask.floorisalie

import android.content.res.AssetManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Log

/** A player animation frame, pre-scaled to its on-screen size, plus its mirrored version. */
class FrameImage(val normal: Bitmap, val flipped: Bitmap)

/** Frames cut from a sprite sheet the way Animation.__init__ does, with the source frame size. */
class SlicedSheet(val frameWidth: Int, val frameHeight: Int, val frames: List<FrameImage?>)

/**
 * Port of assets.py's AssetManager: one instance, created once at startup, that knows every
 * sprite and sound. pygame keeps full-size surfaces and rescales them while drawing; here the
 * scaled results (identical pixels, see PixelOps) are computed once and cached instead, so the
 * multi-megapixel sheets never have to stay in memory.
 */
class Assets(private val am: AssetManager, private val mixer: Mixer) {
    private val spriteFiles = linkedMapOf(
        // Player animations
        "player_idle" to "sprites/Direct-overhead-2D-perspective-of-a-young-boy-with-256px-36 (3).png",
        "player_transition" to "sprites/transition-from-idle-to-running.png",
        "player_running" to "sprites/Direct-overhead-2D-perspective-of-a-young-boy-with-256px-36 (1).png",
        "player_mask" to "sprites/Direct-overhead-2D-perspective-of-a-young-boy-with-256px-36 (2).png",
        "player_death" to "sprites/falling death.png",
        "player_walk_forward" to "sprites/walk forward.png",
        "player_walk_backward" to "sprites/walk backward.png",
        // Tile sprites
        "tile_real" to "sprites/gen-df79415f-5e74-4ac9-86f6-5ee620955741.png",
        "tile_fake" to "sprites/gen-9468de96-df80-4f4d-b92f-4a063b5c86b5.png",
        "tile_start" to "sprites/door.png",
        "tile_exit" to "sprites/open-door.png",
        // UI sprites
        "mask_image" to "sprites/gen-a8f9dc3d-d020-40c2-bb6d-22e58d5d0390.png",
        "game_over_menu" to "sprites/game-over-menu.png",
        "level_clear" to "sprites/level-clear.png",
        "star" to "sprites/star2.png",
        "main_menu" to "sprites/main-menu.png",
    )

    private val soundFiles = linkedMapOf(
        "fake_tile_fall" to "sound/aww.mp3",
        "fake_tile_fall_thump" to "sound/aww.mp3",
        "level_complete" to "sound/audio-multiple-instruments-in-an-orchestra-doing-for-lev.mp3",
        "mask_activate" to "sound/audio-mortal-kombat-announcer-shouting-.mp3",
        "mask_ready" to "sound/mask-ready.mp3",
        "mask_recharging" to "sound/mask-recharging.mp3",
        "reach_the_exit" to "sound/reach-the-exit-3-press_speed_25pct.mp3",
    )

    /** Width and height of every sprite that loaded (None-equivalent: absent). */
    private val sizes = HashMap<String, Pair<Int, Int>>()
    private val fullBitmaps = HashMap<String, Bitmap>()
    private val scaledCache = HashMap<String, Bitmap>()
    private val sheetCache = HashMap<String, SlicedSheet>()
    val sounds = HashMap<String, Mixer.Sound?>()

    init {
        Log.i(TAG, "Initializing AssetManager - preloading all assets...")
        preloadSprites()
        preloadSounds()
        Log.i(TAG, "AssetManager initialization complete!")
    }

    private fun preloadSprites() {
        for ((id, path) in spriteFiles) {
            try {
                val opts = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                am.open(path).use { BitmapFactory.decodeStream(it, null, opts) }
                if (opts.outWidth > 0) sizes[id] = Pair(opts.outWidth, opts.outHeight)
                else Log.w(TAG, "Failed to load sprite '$id' from $path")
            } catch (e: Exception) {
                Log.w(TAG, "Failed to load sprite '$id' from $path: $e")
            }
        }
    }

    private fun preloadSounds() {
        for ((id, path) in soundFiles) {
            sounds[id] = mixer.loadSound(path).also { if (it == null) Log.w(TAG, "Failed to load sound '$id' from $path") }
        }
        mixer.awaitSoundsLoaded()
    }

    fun isSpriteLoaded(id: String) = sizes.containsKey(id)

    fun isSoundLoaded(id: String) = sounds[id] != null

    fun getSound(id: String): Mixer.Sound? = sounds[id].also { if (it == null) Log.w(TAG, "Sound '$id' not found in asset cache") }

    /** get_width()/get_height() of a sprite, or null when the sprite failed to load. */
    fun size(id: String): Pair<Int, Int>? = sizes[id]

    private fun decode(id: String, premultiplied: Boolean): Bitmap? {
        val path = spriteFiles[id] ?: return null
        val opts = BitmapFactory.Options().apply {
            inScaled = false
            inPremultiplied = premultiplied
            inPreferredConfig = Bitmap.Config.ARGB_8888
        }
        return try {
            am.open(path).use { BitmapFactory.decodeStream(it, null, opts) }
        } catch (e: Exception) {
            Log.w(TAG, "Failed to decode sprite '$id': $e")
            null
        }
    }

    private fun pixelsOf(id: String): Triple<IntArray, Int, Int>? {
        val bmp = decode(id, premultiplied = false) ?: return null
        val w = bmp.width
        val h = bmp.height
        val px = IntArray(w * h)
        bmp.getPixels(px, 0, w, 0, 0, w, h)
        bmp.recycle()
        return Triple(px, w, h)
    }

    /** The sprite at its original size, for sprites the game blits without scaling. */
    @Synchronized
    fun full(id: String): Bitmap? {
        fullBitmaps[id]?.let { return it }
        val bmp = decode(id, premultiplied = true) ?: return null
        fullBitmaps[id] = bmp
        return bmp
    }

    /** pygame.transform.scale(sprite, (w, h)), optionally followed by set_colorkey((0, 0, 0)). */
    @Synchronized
    fun scaled(id: String, w: Int, h: Int, blackColorKey: Boolean = false): Bitmap? {
        val key = "$id@${w}x$h/$blackColorKey"
        scaledCache[key]?.let { return it }
        val (px, sw, sh) = pixelsOf(id) ?: return null
        val out = PixelOps.scaleRegion(px, sw, 0, 0, sw, sh, w, h)
        if (blackColorKey) PixelOps.applyBlackColorKey(out)
        val bmp = Bitmap.createBitmap(out, w, h, Bitmap.Config.ARGB_8888)
        scaledCache[key] = bmp
        return bmp
    }

    /**
     * Animation.__init__ slicing (frame = sheet_w // cols by sheet_h // rows, subsurfaces in
     * frame_indices order) combined with Player.render's scaling to fit a [box] x [box] square.
     */
    @Synchronized
    fun sliceSheet(id: String, rows: Int, cols: Int, frameIndices: List<Int>, box: Int): SlicedSheet? {
        val key = "$id/$rows/$cols/${frameIndices.joinToString(",")}/$box"
        sheetCache[key]?.let { return it }
        val (px, sw, sh) = pixelsOf(id) ?: return null
        val fw = sw / cols
        val fh = sh / rows
        val scale = minOf(box.toDouble() / fw, box.toDouble() / fh)
        val dw: Int
        val dh: Int
        if (scale != 1.0) {
            dw = (fw * scale).toInt()
            dh = (fh * scale).toInt()
        } else {
            dw = fw
            dh = fh
        }
        val total = rows * cols
        val frames = ArrayList<FrameImage?>()
        for (index in frameIndices) {
            if (index >= total) break
            val sx = (index % cols) * fw
            val sy = (index / cols) * fh
            val normal = PixelOps.scaleRegion(px, sw, sx, sy, fw, fh, dw, dh, flipX = false)
            val flipped = PixelOps.scaleRegion(px, sw, sx, sy, fw, fh, dw, dh, flipX = true)
            frames.add(
                FrameImage(
                    Bitmap.createBitmap(normal, dw, dh, Bitmap.Config.ARGB_8888),
                    Bitmap.createBitmap(flipped, dw, dh, Bitmap.Config.ARGB_8888),
                ),
            )
        }
        val sheet = SlicedSheet(fw, fh, frames)
        sheetCache[key] = sheet
        return sheet
    }

    companion object {
        private const val TAG = "Assets"

        /** get_asset_manager(): null until the Android runtime creates it (and in JVM unit tests). */
        @Volatile
        var instance: Assets? = null
    }
}
