#!/bin/sh
# Build The Floor Is a Lie for Android and install it on the phone connected over USB.
#
#   android/deploy.sh            build, install, launch
#   android/deploy.sh apk        build only, print the APK path
#   android/deploy.sh frames     also run the scripted parity scenario on the phone and compare
#                                its frames with the desktop game (tools/compare_frames.py)
#
# The phone needs Developer options > USB debugging turned on, and the "Allow USB debugging"
# prompt accepted once.
set -eu
here=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
repo=$(dirname "$here")
mode="${1:-install}"

if [ -z "${JAVA_HOME:-}" ]; then
  if [ -x /usr/libexec/java_home ]; then
    JAVA_HOME=$(/usr/libexec/java_home -v 17 2>/dev/null || true)
  fi
  if [ -z "${JAVA_HOME:-}" ] && [ -d "$HOME/Library/Java/JavaVirtualMachines/jdk-17.0.2+8/Contents/Home" ]; then
    JAVA_HOME="$HOME/Library/Java/JavaVirtualMachines/jdk-17.0.2+8/Contents/Home"
  fi
fi
if [ -z "${JAVA_HOME:-}" ]; then
  echo "Set JAVA_HOME to a JDK 17 install, then run this again."
  exit 1
fi
export JAVA_HOME

if [ -z "${ANDROID_HOME:-}" ]; then
  ANDROID_HOME="$HOME/Library/Android/sdk"
fi
if [ ! -d "$ANDROID_HOME" ]; then
  echo "Android SDK not found. Set ANDROID_HOME, then run this again."
  exit 1
fi
export ANDROID_HOME
[ -f "$here/local.properties" ] || echo "sdk.dir=$ANDROID_HOME" > "$here/local.properties"
adb="$ANDROID_HOME/platform-tools/adb"
pkg=org.thetruthmask.floorisalie

cd "$here"
./gradlew :app:assembleDebug
apk="$here/app/build/outputs/apk/debug/app-debug.apk"
echo "APK: $apk"
[ "$mode" = "apk" ] && exit 0

if ! "$adb" get-state >/dev/null 2>&1; then
  echo "No phone found. Plug it in with USB debugging on, accept the prompt on the phone, then run this again."
  "$adb" devices
  exit 1
fi

"$adb" install -r "$apk"

if [ "$mode" = "frames" ]; then
  out="$repo/build/parity"
  rm -rf "$out" && mkdir -p "$out/android" "$out/desktop"
  "$adb" logcat -c
  "$adb" shell am start -W -n "$pkg/.MainActivity" --ez scenario true >/dev/null
  echo "Running the scripted scenario on the phone..."
  i=0
  until "$adb" logcat -d -s ScenarioRunner:I | grep -q "SCENARIO DONE"; do
    i=$((i + 1))
    if [ "$i" -gt 180 ]; then echo "Timed out waiting for the scenario."; exit 1; fi
    sleep 1
  done
  "$adb" logcat -d -s ScenarioRunner:I | grep -v "SCENARIO DONE" | sed 's/^.*ScenarioRunner: //' | grep ": state=" || true
  "$adb" pull "/sdcard/Android/data/$pkg/files/frames/." "$out/android" >/dev/null
  "$repo/.venv/bin/python" "$repo/tools/reference_frames.py" "$out/desktop" | grep -v -E "^pygame|Hello from" || true
  "$repo/.venv/bin/python" "$repo/tools/compare_frames.py" "$out/desktop" "$out/android"
  exit 0
fi

"$adb" shell am start -n "$pkg/.MainActivity" >/dev/null
echo "Installed and launched."
