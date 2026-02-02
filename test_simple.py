"""Simple test to verify Python runs in browser."""

print("=" * 50)
print("PYTHON IS RUNNING!")
print("=" * 50)

import sys

print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")

try:
    import pygame

    print("✓ Pygame imported successfully")
    pygame.init()
    print("✓ Pygame initialized successfully")
except Exception as e:
    print(f"✗ Pygame error: {e}")

print("=" * 50)
print("Test complete - if you see this, Python works!")
print("=" * 50)

# Keep the program running
input("Press Enter to exit...")
