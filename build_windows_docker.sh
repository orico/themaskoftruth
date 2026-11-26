#!/bin/bash

# Script to build Windows executable using Docker from macOS
# This uses Wine to run Windows Python and PyInstaller

set -e

echo "Building Windows executable for 'The Floor Is a Lie' using Docker..."
echo "This may take 15-30 minutes on first run (downloading and setting up Wine/Python)"
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop for Mac:"
    echo "   https://docs.docker.com/desktop/install/mac-install/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "🐳 Building Docker image with Wine and Python..."
docker build -f Dockerfile.windows -t thefloorisalie-windows-builder .

echo
echo "🏗️  Building Windows executable..."
docker run --rm -v "$(pwd)/dist:/output" thefloorisalie-windows-builder

echo
echo "✅ Build completed!"
echo
echo "📁 Output location: $(pwd)/dist/"
echo
echo "Files created:"
ls -la dist/

echo
echo "🎮 The executable 'TheFloorIsALie.exe' can now be run on Windows machines"
echo "   without requiring Python installation."
echo
echo "📦 To distribute: Copy the entire 'dist' folder to Windows machines."
