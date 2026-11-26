plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// The game's own files (sprites, sounds, music, levels) live at the repo root and are shared
// with the desktop build. They are copied unchanged into the APK's assets, keeping the same
// relative paths the Python code opens (e.g. "sprites/door.png", "levels/level1.json").
val repoRoot = rootProject.projectDir.parentFile
val gameAssetsDir = layout.buildDirectory.dir("generated/gameAssets")

val syncGameAssets by tasks.registering(Sync::class) {
    from(repoRoot) {
        include(
            // Sprites referenced by assets.py
            "sprites/Direct-overhead-2D-perspective-of-a-young-boy-with-256px-36 (1).png",
            "sprites/Direct-overhead-2D-perspective-of-a-young-boy-with-256px-36 (2).png",
            "sprites/Direct-overhead-2D-perspective-of-a-young-boy-with-256px-36 (3).png",
            "sprites/transition-from-idle-to-running.png",
            "sprites/falling death.png",
            "sprites/walk forward.png",
            "sprites/walk backward.png",
            "sprites/gen-df79415f-5e74-4ac9-86f6-5ee620955741.png",
            "sprites/gen-9468de96-df80-4f4d-b92f-4a063b5c86b5.png",
            "sprites/door.png",
            "sprites/open-door.png",
            "sprites/gen-a8f9dc3d-d020-40c2-bb6d-22e58d5d0390.png",
            "sprites/game-over-menu.png",
            "sprites/level-clear.png",
            "sprites/star2.png",
            "sprites/main-menu.png",
            // Sounds referenced by assets.py, plus the background music from config.py
            "sound/aww.mp3",
            "sound/audio-multiple-instruments-in-an-orchestra-doing-for-lev.mp3",
            "sound/audio-mortal-kombat-announcer-shouting-.mp3",
            "sound/mask-ready.mp3",
            "sound/mask-recharging.mp3",
            "sound/reach-the-exit-3-press_speed_25pct.mp3",
            "music/audio-energetic-anime-music.mp3",
            "levels/*.json",
            // Scripted scenarios for the debug parity runner (see tools/reference_frames.py)
            "tools/scenarios.json",
        )
    }
    into(gameAssetsDir)
}

android {
    namespace = "org.thetruthmask.floorisalie"
    compileSdk = 35

    defaultConfig {
        applicationId = "org.thetruthmask.floorisalie"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }

    sourceSets["main"].assets.srcDir(gameAssetsDir)

    // Sound files are already compressed; storing them uncompressed lets SoundPool and
    // MediaPlayer open them straight from the APK.
    androidResources {
        noCompress += listOf("mp3")
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    testOptions {
        unitTests.isReturnDefaultValues = true
    }
}

kotlin {
    compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) }
}

tasks.named("preBuild") { dependsOn(syncGameAssets) }

dependencies {
    testImplementation("junit:junit:4.13.2")
    // org.json ships with Android; unit tests on the JVM need a real implementation.
    testImplementation("org.json:json:20240303")
}
