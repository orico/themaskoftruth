package org.thetruthmask.floorisalie

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/** Port of tests/test_score.py */
class ScoreSystemTest {
    private lateinit var config: Config
    private lateinit var score: ScoreSystem

    @Before
    fun setUp() {
        config = Config()
        score = ScoreSystem(config)
    }

    @Test fun initialization() {
        assertEquals(0.0, score.elapsedTime, 0.0)
        assertEquals(0, score.maskUses)
        assertFalse(score.completed)
        assertEquals(0, score.stars)
        assertEquals(config.TIME_THRESHOLDS, score.timeThresholds)
        assertEquals(config.MASK_USE_THRESHOLD, score.maskThreshold)
    }

    @Test fun timeTracking() {
        repeat(300) { score.update(1.0 / 60) }
        assertTrue(Math.abs(score.elapsedTime - 5.0) < 0.1)
    }

    @Test fun maskUsageTracking() {
        assertEquals(0, score.maskUses)
        score.addMaskUse()
        assertEquals(1, score.maskUses)
        score.addMaskUse(); score.addMaskUse()
        assertEquals(3, score.maskUses)
    }

    @Test fun starCalculationPerfect() {
        score.elapsedTime = 10.0; score.maskUses = 0
        score.completeLevel()
        assertEquals(3, score.stars)
        assertEquals(10.0, score.finalTime, 0.0)
        assertEquals(0, score.finalMaskUses)
        assertTrue(score.completed)
    }

    @Test fun starCalculationGood() {
        score.elapsedTime = 40.0; score.completeLevel(); assertEquals(2, score.stars)
    }

    @Test fun starCalculationOk() {
        score.elapsedTime = 70.0; score.completeLevel(); assertEquals(1, score.stars)
    }

    @Test fun starCalculationPoor() {
        score.elapsedTime = 150.0; score.completeLevel(); assertEquals(0, score.stars)
    }

    @Test fun maskPenalty() {
        score.elapsedTime = 10.0; score.maskUses = 10; score.completeLevel(); assertEquals(2, score.stars)
    }

    @Test fun combinedPenalties() {
        score.elapsedTime = 70.0; score.maskUses = 10; score.completeLevel(); assertEquals(0, score.stars)
    }

    @Test fun timeFormatting() {
        assertEquals("00:00", score.getTimeFormatted(0.0))
        assertEquals("00:59", score.getTimeFormatted(59.0))
        assertEquals("01:00", score.getTimeFormatted(60.0))
        assertEquals("02:05", score.getTimeFormatted(125.0))
        assertEquals("61:01", score.getTimeFormatted(3661.0))
        score.elapsedTime = 90.5
        assertEquals("01:30", score.getTimeFormatted())
    }

    @Test fun starDisplay() {
        assertEquals("☆☆☆", score.getStarDisplay(0))
        assertEquals("★☆☆", score.getStarDisplay(1))
        assertEquals("★★☆", score.getStarDisplay(2))
        assertEquals("★★★", score.getStarDisplay(3))
        score.stars = 2
        assertEquals("★★☆", score.getStarDisplay())
    }

    @Test fun performanceRating() {
        score.stars = 3; assertEquals("Perfect!", score.getPerformanceRating())
        score.stars = 2; assertEquals("Good!", score.getPerformanceRating())
        score.stars = 1; assertEquals("OK", score.getPerformanceRating())
        score.stars = 0; assertEquals("Try again!", score.getPerformanceRating())
    }

    @Test fun scoreSummary() {
        score.elapsedTime = 45.0; score.maskUses = 2; score.stars = 2
        score.completeLevel()
        val summary = score.getScoreSummary()
        assertEquals("00:45", summary["time"])
        assertEquals(2, summary["mask_uses"])
        assertEquals("★★☆", summary["stars"])
        assertEquals("Good!", summary["rating"])
        assertEquals(listOf("00:30", "01:00", "02:00"), summary["time_thresholds"])
        assertEquals(5, summary["mask_threshold"])
    }

    @Test fun reset() {
        score.elapsedTime = 100.0; score.maskUses = 5; score.completeLevel()
        score.reset()
        assertEquals(0.0, score.elapsedTime, 0.0)
        assertEquals(0, score.maskUses)
        assertFalse(score.completed)
        assertEquals(0, score.stars)
        assertEquals(0.0, score.finalTime, 0.0)
        assertEquals(0, score.finalMaskUses)
    }

    @Test fun configUpdates() {
        score.setConfig(timeThresholds = listOf(15.0, 30.0, 60.0))
        assertEquals(listOf(15.0, 30.0, 60.0), score.timeThresholds)
        score.setConfig(maskThreshold = 8)
        assertEquals(8, score.maskThreshold)
        score.setConfig(timeThresholds = listOf(20.0, 40.0, 80.0), maskThreshold = 3)
        assertEquals(listOf(20.0, 40.0, 80.0), score.timeThresholds)
        assertEquals(3, score.maskThreshold)
    }

    @Test fun getCurrentStats() {
        score.elapsedTime = 25.0; score.maskUses = 2
        val stats = score.getCurrentStats()
        assertEquals(25.0, stats["elapsed_time"])
        assertEquals(2, stats["mask_uses"])
        assertEquals(false, stats["completed"])
        assertEquals(0.0, stats["final_time"])
        assertEquals(0, stats["final_mask_uses"])
        assertEquals(0, stats["stars"])
    }
}
