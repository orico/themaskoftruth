package org.thetruthmask.floorisalie

import android.util.Log

/** Port of sound_effects.py: plays the preloaded sound effects. */
class SoundEffects {
    val sounds = LinkedHashMap<String, Mixer.Sound>()
    var volume = 0.7f // Default volume for sound effects
        private set

    init {
        loadSoundsFromAssetManager()
    }

    private fun loadSoundsFromAssetManager() {
        val assetManager = Assets.instance ?: return
        val soundMappings = linkedMapOf(
            "fake_tile_fall" to "fake_tile_fall",
            "fake_tile_fall_thump" to "fake_tile_fall_thump",
            "level_complete" to "level_complete",
            "mask_activate" to "mask_activate",
            "mask_ready" to "mask_ready",
            "mask_recharging" to "mask_recharging",
            "reach_the_exit" to "reach_the_exit",
        )
        for ((soundId, assetId) in soundMappings) {
            val sound = assetManager.getSound(assetId)
            if (sound != null) {
                sounds[soundId] = sound
                sound.setVolume(volume)
            } else {
                Log.w(TAG, "Failed to load sound '$soundId' from asset manager")
            }
        }
    }

    /** Kept for parity with the deprecated Python method: sounds come from the asset manager. */
    fun loadSound(soundId: String, @Suppress("UNUSED_PARAMETER") soundFile: String) = sounds.containsKey(soundId)

    fun playSound(soundId: String): Boolean {
        val sound = sounds[soundId]
        if (sound == null) {
            Log.w(TAG, "Sound effect '$soundId' not found")
            return false
        }
        sound.play()
        return true
    }

    fun setVolume(volume: Float) {
        this.volume = volume.coerceIn(0f, 1f)
        for (sound in sounds.values) sound.setVolume(this.volume)
    }

    fun stopAllSounds() {
        for (sound in sounds.values) sound.stop()
    }

    fun getLoadedSounds(): List<String> = sounds.keys.toList()

    companion object {
        private const val TAG = "SoundEffects"
    }
}

/** Port of music.py: background music on the single mixer.music stream. */
class Music(val musicFile: String, initialVolume: Float = 0.5f) {
    var volume: Float = initialVolume
        private set
    var savedVolume = volume // Remember volume before muting
    var isPlaying = false
    var isPaused = false
    var muted = false

    private val mixer get() = Mixer.current

    init {
        loadMusic()
    }

    fun loadMusic(): Boolean {
        if (!GameFiles.current.exists(musicFile)) {
            Log.w(TAG, "Music file not found: $musicFile")
            return false
        }
        if (!mixer.musicLoad(musicFile)) return false
        mixer.musicSetVolume(volume)
        Log.i(TAG, "Loaded music: $musicFile")
        return true
    }

    fun play(loops: Int = -1) {
        if (!isPlaying) {
            mixer.musicPlay(loops)
            isPlaying = true
            isPaused = false
            Log.i(TAG, "Started playing background music")
        }
    }

    fun pause() {
        if (isPlaying && !isPaused) {
            mixer.musicPause()
            isPaused = true
        }
    }

    fun unpause() {
        if (isPlaying && isPaused) {
            mixer.musicUnpause()
            isPaused = false
        }
    }

    fun stop() {
        if (isPlaying) {
            mixer.musicStop()
            isPlaying = false
            isPaused = false
        }
    }

    fun setVolume(volume: Float) {
        this.volume = volume.coerceIn(0f, 1f)
        if (!muted) mixer.musicSetVolume(this.volume) else savedVolume = this.volume
    }

    fun togglePause() {
        if (isPaused) unpause() else pause()
    }

    fun toggleMute() {
        if (muted) unmute() else mute()
    }

    fun mute() {
        if (!muted) {
            savedVolume = volume
            mixer.musicSetVolume(0f)
            muted = true
        }
    }

    fun unmute() {
        if (muted) {
            mixer.musicSetVolume(savedVolume)
            volume = savedVolume
            muted = false
        }
    }

    fun getStatus(): Map<String, Any> = mapOf(
        "is_playing" to isPlaying,
        "is_paused" to isPaused,
        "volume" to volume,
        "muted" to muted,
        "music_file" to musicFile,
    )

    companion object {
        private const val TAG = "Music"
    }
}
