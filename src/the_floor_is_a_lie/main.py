"""Main entry point for The Floor Is a Lie game."""

import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from .game import Game


def main():
    """Main entry point for the game."""
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Game crashed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()