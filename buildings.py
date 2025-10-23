"""
Building classes for Settlers of Catan
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from board import Plot, Path


class Building:
    """Base class for settlements and cities"""
    
    def __init__(self, player: 'Player', plot: 'Plot'):
        self.player = player
        self.plot = plot
    
    def get_resource_multiplier(self) -> int:
        """Returns how many resources this building generates"""
        raise NotImplementedError
    
    def get_victory_points(self) -> int:
        """Returns victory points this building provides"""
        raise NotImplementedError


class Settlement(Building):
    """Represents a settlement on the board"""
    
    def get_resource_multiplier(self) -> int:
        return 1  # Settlements generate 1 resource
    
    def get_victory_points(self) -> int:
        return 1  # Settlements are worth 1 victory point
    
    def __repr__(self):
        return f"Settlement(Player {self.player.id} at Plot {self.plot.id})"


class City(Building):
    """Represents a city on the board"""
    
    def get_resource_multiplier(self) -> int:
        return 2  # Cities generate 2 resources
    
    def get_victory_points(self) -> int:
        return 2  # Cities are worth 2 victory points
    
    def __repr__(self):
        return f"City(Player {self.player.id} at Plot {self.plot.id})"


class Road:
    """Represents a road on the board"""
    
    def __init__(self, player: 'Player', path: 'Path'):
        self.player = player
        self.path = path
    
    def __repr__(self):
        return f"Road(Player {self.player.id} on Path {self.path.id})"