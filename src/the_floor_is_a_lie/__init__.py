"""The Floor Is a Lie - A top-down memory puzzle game."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .config import Config
from .player import Player
from .tile import Tile, TileType
from .level import Level
from .score import ScoreSystem
from .ui import UI
from .level_editor import LevelEditor

__all__ = [
    "Config",
    "Player",
    "Tile",
    "TileType",
    "Level",
    "ScoreSystem",
    "UI",
    "LevelEditor",
]