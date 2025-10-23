"""
Enums and basic data models for Settlers of Catan
"""
from enum import Enum
from typing import Optional, Tuple


class Resource(Enum):
    """The five resource types in Catan"""
    BRICK = "brick"
    ORE = "ore"
    WOOD = "wood"
    WOOL = "wool"
    WHEAT = "wheat"


class Terrain(Enum):
    """Terrain types with associated resources"""
    HILLS = ("hills", Resource.BRICK)
    MOUNTAINS = ("mountains", Resource.ORE)
    FORESTS = ("forests", Resource.WOOD)
    PASTURES = ("pastures", Resource.WOOL)
    FIELDS = ("fields", Resource.WHEAT)
    DESERT = ("desert", None)
    
    def __init__(self, terrain_name: str, resource: Optional[Resource]):
        self.terrain_name = terrain_name
        self.resource = resource


class PortType(Enum):
    """Different port trading ratios"""
    THREE_ANY_TO_ONE = "3_any_to_1"
    TWO_WHEAT_TO_ONE = "2_wheat_to_1"
    TWO_ORE_TO_ONE = "2_ore_to_1"
    TWO_WOOD_TO_ONE = "2_wood_to_1"
    TWO_BRICK_TO_ONE = "2_brick_to_1"
    TWO_WOOL_TO_ONE = "2_wool_to_1"


class DevelopmentCardType(Enum):
    """Types of development cards"""
    MONOPOLY = "monopoly"
    ROAD_BUILDING = "road_building"
    INVENTION = "invention"
    VICTORY_POINT = "victory_point"
    KNIGHT = "knight"