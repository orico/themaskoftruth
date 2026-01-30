"""The Floor Is a Lie - A top-down memory puzzle game."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .config import Config
from .level import Level
from .player import Player
from .score import ScoreSystem
from .tile import Tile, TileType
from .ui import UI

__all__ = [
    "Config",
    "Player",
    "Tile",
    "TileType",
    "Level",
    "ScoreSystem",
    "UI",
]
