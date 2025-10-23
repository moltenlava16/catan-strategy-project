"""
Settlers of Catan - Python Implementation

A complete object-oriented implementation of the board game Settlers of Catan.
"""

from .models import Resource, Terrain, PortType, DevelopmentCardType
from .board import Board, Hexagon, Plot, Path, Port
from .buildings import Building, Settlement, City, Road
from .player import Player
from .cards import (
    DevelopmentCard,
    MonopolyCard,
    RoadBuildingCard,
    InventionCard,
    VictoryPointCard,
    KnightCard,
    DevelopmentCardDeck
)
from .game import Game, Bank

__version__ = "1.0.0"
__author__ = "Claude"

__all__ = [
    # Models
    "Resource",
    "Terrain",
    "PortType",
    "DevelopmentCardType",
    
    # Board components
    "Board",
    "Hexagon",
    "Plot",
    "Path",
    "Port",
    
    # Buildings
    "Building",
    "Settlement",
    "City",
    "Road",
    
    # Player
    "Player",
    
    # Cards
    "DevelopmentCard",
    "MonopolyCard",
    "RoadBuildingCard",
    "InventionCard",
    "VictoryPointCard",
    "KnightCard",
    "DevelopmentCardDeck",
    
    # Game
    "Game",
    "Bank",
]