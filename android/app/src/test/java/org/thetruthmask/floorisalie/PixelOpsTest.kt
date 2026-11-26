package org.thetruthmask.floorisalie

import org.junit.Assert.assertArrayEquals
import org.junit.Test

/** pygame.transform.scale sample positions, recorded from pygame-ce 2.5.6. */
class PixelOpsTest {
    @Test fun matchesPygameScale() {
        assertArrayEquals(intArrayOf(6, 19, 31, 44, 57, 70), PixelOps.sdlNearestIndices(1024, 80).copyOf(6))
        assertArrayEquals(intArrayOf(1, 5, 9, 13, 16, 20), PixelOps.sdlNearestIndices(227, 61).copyOf(6))
        assertArrayEquals(intArrayOf(2, 7, 12, 17, 22, 26), PixelOps.sdlNearestIndices(377, 77).copyOf(6))
        assertArrayEquals(intArrayOf(11, 34, 58, 81, 104, 127), PixelOps.sdlNearestIndices(768, 33).copyOf(6))
        assertArrayEquals(intArrayOf(0, 0, 1, 2, 2, 3), PixelOps.sdlNearestIndices(13, 20).copyOf(6))
        assertArrayEquals(intArrayOf(512), PixelOps.sdlNearestIndices(1024, 1))
    }

    @Test fun flipMirrorsBeforeScaling() {
        val src = intArrayOf(1, 2, 3, 4)
        assertArrayEquals(intArrayOf(4, 3, 2, 1), PixelOps.scaleRegion(src, 4, 0, 0, 4, 1, 4, 1, flipX = true))
    }
}
