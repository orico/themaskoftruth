"""Main entry point for The Floor Is a Lie game."""

import logging
import platform
import sys

from .game import Game

# Set up logging
# Note: FileHandler doesn't work in web/WASM environment, use StreamHandler only
is_web = "emscripten" in platform.system().lower() or hasattr(sys, "_emscripten_info")

if is_web:
    # Web environment - only use StreamHandler
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    print("Running in web environment - logging to console only")
else:
    # Desktop environment - use both file and stream handlers
    try:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("game_debug.log"), logging.StreamHandler()],
        )
    except (OSError, PermissionError):
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )


def main():
    """Main entry point for the game."""
    print("=" * 80)
    print("MAIN: Starting game initialization...")
    print("=" * 80)
    try:
        print("MAIN: Creating Game instance...")
        game = Game()
        print("MAIN: Game instance created successfully!")
        print("MAIN: Starting game.run()...")
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
        sys.exit(0)
    except Exception as e:
        print("=" * 80)
        print(f"MAIN: ERROR - Game crashed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("=" * 80)
        import traceback

        traceback.print_exc()
        logging.error(f"Game crashed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
