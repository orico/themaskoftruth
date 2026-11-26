package org.thetruthmask.floorisalie

import android.content.Context
import java.io.File
import java.io.FileNotFoundException

/**
 * The desktop game reads and writes files relative to its folder. On Android the bundled files
 * are read-only APK assets, so writes (the editor's Save Level, the default-level fallback) go to
 * app storage, and reads look there first. This keeps Python's open() behaviour: a file the game
 * wrote is the one it reads back, and it is still there next launch.
 */
class AndroidFiles(context: Context) : GameFiles {
    private val am = context.assets
    private val root: File = context.filesDir

    private fun local(path: String) = File(root, path)

    private fun assetExists(path: String): Boolean = try {
        am.open(path).close()
        true
    } catch (e: Exception) {
        false
    }

    override fun readText(path: String): String {
        val file = local(path)
        if (file.isFile) return file.readText()
        return try {
            am.open(path).bufferedReader().use { it.readText() }
        } catch (e: Exception) {
            throw FileNotFoundException(path)
        }
    }

    override fun writeText(path: String, text: String) {
        val file = local(path)
        file.parentFile?.mkdirs()
        file.writeText(text)
    }

    override fun exists(path: String) = local(path).exists() || assetExists(path)

    override fun makeDirs(path: String) {
        local(path).mkdirs()
    }
}
