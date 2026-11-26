#!/usr/bin/env python3
"""
Build script for creating Windows executable of The Floor Is a Lie game.
Run this script on Windows with Python and PyInstaller installed.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and check for errors."""
    print(f"\n{description}...")
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✓ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main():
    """Main build function."""
    print("Building Windows executable for 'The Floor Is a Lie'...")

    # Check if we're on Windows
    if os.name != "nt":
        print(
            "Warning: This script is designed for Windows. You may need to adjust paths and commands for other platforms."
        )

    # Install dependencies if needed
    if not run_command(
        "pip install pyinstaller pygame pygame_gui pydub",
        "Installing PyInstaller and dependencies",
    ):
        return False

    # Create dist directory if it doesn't exist
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    # Build the executable
    cmd = [
        "pyinstaller",
        "--onefile",  # Single executable file
        "--windowed",  # No console window
        "--name=TheFloorIsALie",  # Output name
        "--add-data=sprites;sprites",  # Include sprites directory
        "--add-data=sound;sound",  # Include sound directory
        "--add-data=music;music",  # Include music directory
        "--add-data=levels;levels",  # Include levels directory
        "--add-data=themes;themes",  # Include themes directory
        "main.py",  # Entry point
    ]

    # Join command for shell execution
    cmd_str = " ".join(cmd)

    if run_command(cmd_str, "Building executable with PyInstaller"):
        print("\n✓ Build completed successfully!")
        print(
            "The executable 'TheFloorIsALie.exe' has been created in the 'dist' folder."
        )
        print("\nTo distribute the game:")
        print("1. Copy the entire 'dist' folder")
        print(
            "2. The .exe file can run on any Windows machine without Python installed"
        )
        return True
    else:
        print("\n✗ Build failed. Check the error messages above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
