package org.thetruthmask.floorisalie

/** Port of score.py: time tracking, mask usage counting, and star calculation. */
class ScoreSystem(val config: Config) {
    // Current level statistics
    var elapsedTime = 0.0
    var maskUses = 0
    var completed = false
    var finalTime = 0.0
    var finalMaskUses = 0
    var stars = 0

    // Configuration (can be updated from level)
    var timeThresholds: List<Double> = config.TIME_THRESHOLDS.toList() // seconds for 3, 2, 1 stars
    var maskThreshold: Int = config.MASK_USE_THRESHOLD // max uses before penalty

    /** Update elapsed time */
    fun update(deltaTime: Double) {
        if (!completed) elapsedTime += deltaTime
    }

    /** Increment mask usage counter */
    fun addMaskUse() {
        maskUses += 1
    }

    /** Mark level as completed and calculate final score */
    fun completeLevel() {
        completed = true
        finalTime = elapsedTime
        finalMaskUses = maskUses
        stars = calculateStars()
    }

    /** Calculate star rating based on time and mask usage */
    fun calculateStars(): Int {
        if (!completed) return 0

        // Start with maximum stars
        var stars = 3

        // Reduce stars based on completion time
        for (threshold in timeThresholds.sortedDescending()) {
            if (finalTime > threshold) stars -= 1
        }

        // Apply mask usage penalty
        if (finalMaskUses > maskThreshold) {
            stars -= 1
            if (stars < 0) stars = 0
        }

        return stars.coerceIn(0, 3) // Clamp between 0 and 3
    }

    /** Reset score for new level attempt */
    fun reset() {
        elapsedTime = 0.0
        maskUses = 0
        completed = false
        finalTime = 0.0
        finalMaskUses = 0
        stars = 0
    }

    /** Update scoring configuration */
    fun setConfig(timeThresholds: List<Double>? = null, maskThreshold: Int? = null) {
        if (timeThresholds != null) this.timeThresholds = timeThresholds.toList()
        if (maskThreshold != null) this.maskThreshold = maskThreshold
    }

    /** Get current game statistics */
    fun getCurrentStats(): Map<String, Any> = mapOf(
        "elapsed_time" to elapsedTime,
        "mask_uses" to maskUses,
        "completed" to completed,
        "final_time" to finalTime,
        "final_mask_uses" to finalMaskUses,
        "stars" to stars,
    )

    /** Format time in MM:SS format */
    fun getTimeFormatted(timeSeconds: Double? = null): String {
        val t = timeSeconds ?: elapsedTime
        val minutes = Math.floor(t / 60).toInt() // int(t // 60)
        val seconds = (((t % 60) + 60) % 60).toInt() // int(t % 60): Python's modulo is never negative
        return String.format(java.util.Locale.US, "%02d:%02d", minutes, seconds)
    }

    /** Get star rating display string */
    fun getStarDisplay(stars: Int? = null): String {
        val s = stars ?: this.stars
        val starSymbols = "★★★"
        val emptySymbols = "☆☆☆"
        return starSymbols.substring(0, s.coerceIn(0, 3)) + emptySymbols.substring(s.coerceIn(0, 3))
    }

    /** Get performance rating description */
    fun getPerformanceRating(): String = when (stars) {
        3 -> "Perfect!"
        2 -> "Good!"
        1 -> "OK"
        else -> "Try again!"
    }

    /** Get complete score summary for display */
    fun getScoreSummary(): Map<String, Any> = mapOf(
        "time" to getTimeFormatted(finalTime),
        "mask_uses" to finalMaskUses,
        "stars" to getStarDisplay(),
        "stars_count" to stars,
        "rating" to getPerformanceRating(),
        "time_thresholds" to timeThresholds.map { getTimeFormatted(it) },
        "mask_threshold" to maskThreshold,
    )
}
