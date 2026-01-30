# The Floor Is a Lie

A top-down memory puzzle game where the floor tiles lie to you. Navigate through deceptive tiles using a mask that briefly reveals the truth.

## 🎮 Gameplay

### Core Mechanics
- **Movement**: Use arrow keys or WASD to move in 4 directions
- **Mask Mechanic**: Press `M` to toggle your mask
  - Mask reveals the true floor layout for a limited time (default: 2 seconds)
  - After use, mask recharges for 3 seconds
- **Tiles**:
  - 🟢 **Real tiles**: Always safe (green when mask is on)
  - 🔴 **Fake tiles**: Appear safe when masked, dangerous when unmasked (red when mask is on)
  - ⚫ **Empty tiles**: Always dangerous - falling hazard
  - 🔵 **Start**: Your starting position
  - 🟡 **Exit**: Goal to reach

### Objective
Navigate from the start tile to the exit tile without falling into empty spaces or stepping on fake tiles while your mask is off.

### Scoring
- **Stars** (3 max): Based on completion time thresholds
- **Penalty**: Lose 1 star if you use the mask more than the threshold (default: 5 uses)
- **Time thresholds**: 30s (★★★), 60s (★★), 120s (★)

## 🛠️ Level Editor

Press `E` during gameplay to access the level editor:

### Features
- **Tile Placement**: Click tiles to cycle through types (Real, Fake, Empty, Start, Exit)
- **Visual Feedback**: Hover preview shows what tile will be placed
- **Save/Load**: Save your creations to JSON files
- **Back to Game**: Return to gameplay with your changes

### Controls
- **Mouse**: Left-click to place selected tile type
- **Toolbar**: Select tile type from right panel buttons
- **Save**: Save current level to file
- **ESC**: Return to game

## 🏗️ Technical Architecture

### Modular Design
- **Player Module**: Movement, mask mechanics, position tracking
- **Tile Module**: Tile types, visual representation, collision logic
- **Level Module**: JSON loading, grid management, level state
- **Score Module**: Time tracking, star calculation, performance metrics
- **UI Module**: HUD elements, result screens, user interface
- **Level Editor Module**: Tile placement, level creation tools

### Configuration
All game parameters are configurable via JSON:
- Mask duration and cooldown times
- Scoring thresholds and penalties
- Tile sizes and grid dimensions
- UI colors and layout

## 🚀 Installation & Development

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Quick Setup
```bash
# Clone the repository
git clone <repository-url>
cd the-floor-is-a-lie

# Install in development mode
make install

# Run the game
make run
```

### Development Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Run tests
make test

# Run the game
make run
```

### Controls
- **Arrow Keys / WASD**: Move player
- **M**: Toggle mask
- **R**: Restart level (on game over/win)
- **E**: Enter level editor (during gameplay)
- **ESC**: Exit level editor

## 🧪 Testing

The project includes comprehensive unit tests for all core modules:

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_player.py -v

# Run with coverage
python -m pytest --cov=src/the_floor_is_a_lie tests/
```

### Test Coverage
- **Player Module**: Movement, mask mechanics, input handling
- **Level Module**: Loading/saving, tile validation, collision detection
- **Score Module**: Time tracking, star calculation, performance metrics

## 📁 Project Structure

```
the-floor-is-a-lie/
├── src/the_floor_is_a_lie/     # Main package
│   ├── __init__.py            # Package initialization
│   ├── config.py              # Game configuration and constants
│   ├── player.py              # Player movement and mask mechanics
│   ├── tile.py                # Tile types and rendering
│   ├── level.py               # Level loading and grid management
│   ├── score.py               # Scoring and statistics
│   ├── ui.py                  # User interface elements
│   ├── level_editor.py        # Level creation tools
│   ├── game.py                # Main game orchestration
│   └── main.py                # Entry point
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_player.py         # Player module tests
│   ├── test_level.py          # Level module tests
│   └── test_score.py          # Score module tests
├── levels/                    # Level files directory
│   └── level1.json           # Sample level
├── main.py                    # Root entry point
├── run_tests.py               # Test runner script
├── pytest.ini                 # Pytest configuration
├── pyproject.toml             # Package configuration
├── Makefile                   # Development tasks
├── uv.lock                    # Dependency lock file
└── README.md                  # This file
```

## 🔧 Development Tasks

Use the provided Makefile for common development tasks:

```bash
make install    # Install in development mode
make test       # Run test suite
make run        # Run the game
make clean      # Clean build artifacts
make build      # Build distribution packages
make lint       # Run code quality checks
make format     # Format code with black
```

## 📊 Debugging

The game includes comprehensive logging for troubleshooting:

- **Key presses**: Logged when M key is pressed and mask state changes
- **Player movement**: Grid position changes are logged
- **Rendering**: Screen updates and mask effects are tracked
- **Game state**: State transitions and win/lose conditions

Check `game_debug.log` for detailed debug information.

## 🎯 Features Implemented

✅ **Core Gameplay**
- Top-down grid-based movement
- Mask toggle with timer and recharge
- Three tile types with proper collision
- Win/lose conditions

✅ **Scoring & UI**
- Star-based scoring system
- Mask usage penalty
- Real-time HUD with timers
- Result screens with performance metrics

✅ **Level Editor**
- Tile placement interface
- Level saving/loading
- Visual feedback system

✅ **Development**
- Modular architecture
- Comprehensive test suite
- Production-ready packaging
- Logging and debugging tools

## 🔮 Future Expansions

- Multiple levels with increasing difficulty
- Moving hazards and enemies
- Power-ups and special abilities
- Level packs and sharing
- Sound effects and music
- Advanced level editor features
- Performance statistics and leaderboards

## 🎨 Game Design Notes

The core tension comes from the memory puzzle: players must memorize safe paths during brief mask activations, then navigate blindly while the deceptive floor tries to lead them astray. The mask mechanic creates a rhythm of "peek, memorize, execute" that rewards strategic thinking and spatial memory.

---

**Enjoy the deception!** 🕵️‍♂️
