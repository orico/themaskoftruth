package org.thetruthmask.floorisalie

import java.io.File
import java.io.FileNotFoundException

/**
 * The file access the Python code does with open(). Paths are the same relative paths
 * ("levels/level1.json"). Android plugs in an overlay: writable app storage first, then the
 * read-only files bundled in the APK. Tests use the plain JVM filesystem.
 */
interface GameFiles {
    /** Read a text file; throws FileNotFoundException like open() raises FileNotFoundError. */
    fun readText(path: String): String

    fun writeText(path: String, text: String)

    fun exists(path: String): Boolean

    fun makeDirs(path: String)

    companion object {
        @Volatile
        var current: GameFiles = JvmFiles(File("."))
    }
}

class JvmFiles(private val root: File) : GameFiles {
    private fun resolve(path: String) = File(path).let { if (it.isAbsolute) it else File(root, path) }

    override fun readText(path: String): String {
        val file = resolve(path)
        if (!file.isFile) throw FileNotFoundException(path)
        return file.readText()
    }

    override fun writeText(path: String, text: String) {
        resolve(path).writeText(text)
    }

    override fun exists(path: String) = resolve(path).exists()

    override fun makeDirs(path: String) {
        resolve(path).mkdirs()
    }
}
