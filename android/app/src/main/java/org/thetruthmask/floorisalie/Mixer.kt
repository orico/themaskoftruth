package org.thetruthmask.floorisalie

import android.content.res.AssetManager
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.media.SoundPool
import android.util.Log
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/** pygame.mixer: Sound objects plus the single mixer.music stream. */
interface Mixer {
    /** pygame.mixer.Sound */
    interface Sound {
        fun play()
        fun stop()
        fun setVolume(volume: Float)
    }

    fun loadSound(path: String): Sound?
    fun awaitSoundsLoaded() {}

    // pygame.mixer.music
    fun musicLoad(path: String): Boolean
    fun musicPlay(loops: Int)
    fun musicPause()
    fun musicUnpause()
    fun musicStop()
    fun musicSetVolume(volume: Float)

    /** App went to the background / came back (no pygame equivalent; desktop windows keep playing). */
    fun onAppPause() {}
    fun onAppResume() {}
    fun release() {}

    companion object {
        @Volatile
        var current: Mixer = SilentMixer()
    }
}

/** Used by JVM tests and scripted parity runs (the Python harness uses SDL's dummy audio driver). */
class SilentMixer : Mixer {
    private class SilentSound : Mixer.Sound {
        override fun play() {}
        override fun stop() {}
        override fun setVolume(volume: Float) {}
    }

    override fun loadSound(path: String): Mixer.Sound = SilentSound()
    override fun musicLoad(path: String) = true
    override fun musicPlay(loops: Int) {}
    override fun musicPause() {}
    override fun musicUnpause() {}
    override fun musicStop() {}
    override fun musicSetVolume(volume: Float) {}
}

/**
 * SoundPool for effects (8 streams, like pygame's 8 default mixer channels; playing the same
 * Sound twice overlaps, as pygame does) and one MediaPlayer for mixer.music.
 */
class AndroidMixer(private val am: AssetManager) : Mixer {
    private val attributes = AudioAttributes.Builder()
        .setUsage(AudioAttributes.USAGE_GAME)
        .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
        .build()
    private val pool = SoundPool.Builder().setMaxStreams(8).setAudioAttributes(attributes).build()
    private val pendingLoads = HashSet<Int>()
    private val lock = Object()

    init {
        pool.setOnLoadCompleteListener { _, sampleId, _ ->
            synchronized(lock) {
                pendingLoads.remove(sampleId)
                lock.notifyAll()
            }
        }
    }

    private inner class PoolSound(private val sampleId: Int) : Mixer.Sound {
        private var volume = 1f
        private val streams = ArrayList<Int>()

        override fun play() {
            val stream = pool.play(sampleId, volume, volume, 1, 0, 1f)
            if (stream != 0) {
                streams.add(stream)
                if (streams.size > 8) streams.removeAt(0)
            }
        }

        override fun stop() {
            for (s in streams) pool.stop(s)
            streams.clear()
        }

        override fun setVolume(volume: Float) {
            this.volume = volume
        }
    }

    override fun loadSound(path: String): Mixer.Sound? = try {
        val id = am.openFd(path).use { fd -> pool.load(fd, 1) }
        synchronized(lock) { pendingLoads.add(id) }
        PoolSound(id)
    } catch (e: Exception) {
        Log.w(TAG, "Failed to load sound $path: $e")
        null
    }

    override fun awaitSoundsLoaded() {
        val deadline = System.currentTimeMillis() + 10_000
        synchronized(lock) {
            while (pendingLoads.isNotEmpty()) {
                val left = deadline - System.currentTimeMillis()
                if (left <= 0) break
                lock.wait(left)
            }
        }
    }

    // --- mixer.music -------------------------------------------------------------------------

    private var player: MediaPlayer? = null
    private var loadedPath: String? = null
    private var musicVolume = 1f
    private var playing = false // started and not paused/stopped
    private var resumeOnAppResume = false

    /**
     * pygame.mixer.music.load stops whatever is playing and leaves the new track at its start.
     * Reloading the same file rewinds the already-prepared player instead of decoding it again.
     */
    override fun musicLoad(path: String): Boolean {
        return try {
            val existing = player
            if (existing != null && loadedPath == path) {
                if (existing.isPlaying) existing.pause()
                existing.seekTo(0)
            } else {
                existing?.release()
                val mp = MediaPlayer()
                mp.setAudioAttributes(attributes)
                am.openFd(path).use { fd -> mp.setDataSource(fd.fileDescriptor, fd.startOffset, fd.length) }
                mp.prepare()
                player = mp
                loadedPath = path
            }
            playing = false
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to load music $path: $e")
            false
        }
    }

    override fun musicPlay(loops: Int) {
        val mp = player ?: return
        mp.isLooping = loops == -1
        mp.seekTo(0)
        mp.setVolume(musicVolume, musicVolume)
        mp.start()
        playing = true
    }

    override fun musicPause() {
        val mp = player ?: return
        if (mp.isPlaying) mp.pause()
        playing = false
    }

    override fun musicUnpause() {
        val mp = player ?: return
        mp.start()
        playing = true
    }

    override fun musicStop() {
        val mp = player ?: return
        if (mp.isPlaying) mp.pause()
        mp.seekTo(0)
        playing = false
    }

    override fun musicSetVolume(volume: Float) {
        musicVolume = volume
        player?.setVolume(volume, volume)
    }

    override fun onAppPause() {
        pool.autoPause()
        val mp = player
        resumeOnAppResume = mp != null && playing && mp.isPlaying
        if (resumeOnAppResume) mp?.pause()
    }

    override fun onAppResume() {
        pool.autoResume()
        if (resumeOnAppResume) player?.start()
        resumeOnAppResume = false
    }

    override fun release() {
        pool.release()
        player?.release()
        player = null
    }

    companion object {
        private const val TAG = "Mixer"
    }
}
