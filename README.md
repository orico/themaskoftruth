# The Floor Is a Lie

A top-down memory puzzle game where the floor visually lies to you. Navigate through deceptive tiles using a mask that briefly reveals the truth.

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

## 🚀 Installation & Running

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

### Controls
- **Arrow Keys / WASD**: Move player
- **M**: Toggle mask
- **R**: Restart level (on game over/win)
- **E**: Enter level editor (during gameplay)
- **ESC**: Exit level editor

## 📁 Project Structure

```
thetruthmask/
├── main.py              # Main game loop and state management
├── config.py            # Game configuration and constants
├── player.py            # Player movement and mask mechanics
├── tile.py              # Tile types and rendering
├── level.py             # Level loading and grid management
├── score.py             # Scoring and statistics
├── ui.py                # User interface elements
├── level_editor.py      # Level creation tools
├── test_gameplay.py     # Gameplay verification tests
├── requirements.txt     # Python dependencies
├── levels/              # Level files directory
│   └── level1.json     # Sample level
└── README.md           # This file
```

## 🎯 Features Implemented

✅ **Core Gameplay**
- Top-down grid-based movement
- Mask toggle with timer and recharge
- Three tile types with proper collision
- Win/lose conditions

✅ **Scoring System**
- Time-based star ratings
- Mask usage penalty
- Completion statistics

✅ **Level Editor**
- Tile placement interface
- Level saving/loading
- Visual feedback

✅ **UI/UX**
- Real-time HUD (mask timer, time, uses)
- Result screens with star ratings
- Clean, readable interface

✅ **Technical**
- Modular architecture
- JSON-based level configuration
- Configurable parameters
- Comprehensive testing

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