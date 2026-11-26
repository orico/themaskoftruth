package org.thetruthmask.floorisalie

/**
 * Pixel operations that reproduce pygame exactly. Pure Kotlin on ARGB IntArrays, so they are
 * unit-testable on the JVM.
 */
object PixelOps {
    /**
     * pygame.transform.scale (nearest neighbour). pygame-ce delegates to SDL's soft stretch,
     * which walks the source in 16.16 fixed point starting half a step in:
     *   inc = (src << 16) / dst; pos = inc / 2; srcIndex = pos >> 16; pos += inc
     * Verified bit-exact against pygame-ce 2.5.6 on 309 random size pairs.
     */
    fun sdlNearestIndices(srcSize: Int, dstSize: Int): IntArray {
        val out = IntArray(dstSize)
        if (dstSize <= 0) return out
        val inc = (srcSize.toLong() shl 16) / dstSize
        var pos = inc / 2
        for (i in 0 until dstSize) {
            out[i] = (pos shr 16).toInt()
            pos += inc
        }
        return out
    }

    /**
     * Copy the sub-rectangle (sx, sy, sw, sh) of [src] (width [srcStride]) and scale it to
     * dw x dh. When [flipX] is true the sub-rectangle is mirrored first, which is what
     * pygame.transform.flip(frame, True, False) followed by a scale produces.
     */
    fun scaleRegion(
        src: IntArray, srcStride: Int,
        sx: Int, sy: Int, sw: Int, sh: Int,
        dw: Int, dh: Int,
        flipX: Boolean = false,
    ): IntArray {
        val xs = sdlNearestIndices(sw, dw)
        val ys = sdlNearestIndices(sh, dh)
        val out = IntArray(dw * dh)
        for (y in 0 until dh) {
            val row = (sy + ys[y]) * srcStride + sx
            val outRow = y * dw
            for (x in 0 until dw) {
                val fx = if (flipX) sw - 1 - xs[x] else xs[x]
                out[outRow + x] = src[row + fx]
            }
        }
        return out
    }

    /** set_colorkey((0, 0, 0)): pixels whose RGB is exactly black are not drawn. */
    fun applyBlackColorKey(pixels: IntArray) {
        for (i in pixels.indices) {
            if (pixels[i] and 0x00FFFFFF == 0) pixels[i] = 0
        }
    }
}
