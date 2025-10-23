"""
Player class for Settlers of Catan
"""
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from models import Resource, DevelopmentCardType
from buildings import Settlement, City, Road

if TYPE_CHECKING:
    from board import Port, Plot, Path
    from cards import DevelopmentCard


class Player:
    """Represents a player in the game"""
    
    def __init__(self, player_id: int):
        self.id = player_id
        
        # Resources
        self.resources: Dict[Resource, int] = {r: 0 for r in Resource}
        
        # Development cards
        self.development_cards: List['DevelopmentCard'] = []
        self.cards_bought_this_turn: List['DevelopmentCard'] = []
        self.development_card_played_this_turn: bool = False
        
        # Victory point tracking
        self.victory_point_cards_played: int = 0
        self.knights_played: int = 0
        self.has_largest_army: bool = False
        self.has_longest_road: bool = False
        
        # Building pieces available
        self.available_settlements: int = 5
        self.available_cities: int = 4
        self.available_roads: int = 15
        
        # Buildings on the board
        self.settlements: List[Settlement] = []
        self.cities: List[City] = []
        self.roads: List[Road] = []
        
        # Special flags
        self.free_roads_remaining: int = 0  # From Road Building card
    
    def get_total_resources(self) -> int:
        """Get total number of resources held"""
        return sum(self.resources.values())
    
    def must_discard_on_seven(self) -> bool:
        """Check if player must discard half their cards when 7 is rolled"""
        return self.get_total_resources() > 7
    
    def get_discard_count(self) -> int:
        """Get number of resources to discard when 7 is rolled"""
        return self.get_total_resources() // 2
    
    def discard_resources(self, to_discard: Dict[Resource, int]) -> bool:
        """Discard specified resources"""
        # Validate discard
        for resource, amount in to_discard.items():
            if self.resources[resource] < amount:
                return False
        
        # Perform discard
        for resource, amount in to_discard.items():
            self.resources[resource] -= amount
        
        return True
    
    def get_accessible_ports(self) -> List['Port']:
        """Returns list of ports this player has access to"""
        ports = []
        all_buildings = self.settlements + self.cities
        
        for building in all_buildings:
            if building.plot.port and building.plot.port not in ports:
                ports.append(building.plot.port)
        
        return ports
    
    def get_best_trade_ratio(self, resource: Resource) -> Tuple[int, int]:
        """Returns best available trade ratio for the given resource"""
        best_ratio = (4, 1)  # Default bank trade ratio
        
        for port in self.get_accessible_ports():
            ratio = port.get_trade_ratio(resource)
            if ratio and ratio[0] < best_ratio[0]:
                best_ratio = ratio
        
        return best_ratio
    
    def can_afford_road(self) -> bool:
        """Check if player can afford a road"""
        if self.free_roads_remaining > 0:
            return True
        return (self.resources[Resource.BRICK] >= 1 and 
                self.resources[Resource.WOOD] >= 1)
    
    def can_afford_settlement(self) -> bool:
        """Check if player can afford a settlement"""
        return (self.resources[Resource.BRICK] >= 1 and
                self.resources[Resource.WOOD] >= 1 and
                self.resources[Resource.WOOL] >= 1 and
                self.resources[Resource.WHEAT] >= 1)
    
    def can_afford_city(self) -> bool:
        """Check if player can afford a city"""
        return (self.resources[Resource.WHEAT] >= 2 and
                self.resources[Resource.ORE] >= 3)
    
    def can_afford_development_card(self) -> bool:
        """Check if player can afford a development card"""
        return (self.resources[Resource.WOOL] >= 1 and
                self.resources[Resource.WHEAT] >= 1 and
                self.resources[Resource.ORE] >= 1)
    
    def pay_for_road(self, bank) -> bool:
        """Pay resources for a road"""
        if self.free_roads_remaining > 0:
            self.free_roads_remaining -= 1
            return True
        
        if not self.can_afford_road():
            return False
        
        self.resources[Resource.BRICK] -= 1
        self.resources[Resource.WOOD] -= 1
        bank.resources[Resource.BRICK] += 1
        bank.resources[Resource.WOOD] += 1
        return True
    
    def pay_for_settlement(self, bank) -> bool:
        """Pay resources for a settlement"""
        if not self.can_afford_settlement():
            return False
        
        self.resources[Resource.BRICK] -= 1
        self.resources[Resource.WOOD] -= 1
        self.resources[Resource.WOOL] -= 1
        self.resources[Resource.WHEAT] -= 1
        
        bank.resources[Resource.BRICK] += 1
        bank.resources[Resource.WOOD] += 1
        bank.resources[Resource.WOOL] += 1
        bank.resources[Resource.WHEAT] += 1
        return True
    
    def pay_for_city(self, bank) -> bool:
        """Pay resources for a city"""
        if not self.can_afford_city():
            return False
        
        self.resources[Resource.WHEAT] -= 2
        self.resources[Resource.ORE] -= 3
        
        bank.resources[Resource.WHEAT] += 2
        bank.resources[Resource.ORE] += 3
        return True
    
    def pay_for_development_card(self, bank) -> bool:
        """Pay resources for a development card"""
        if not self.can_afford_development_card():
            return False
        
        self.resources[Resource.WOOL] -= 1
        self.resources[Resource.WHEAT] -= 1
        self.resources[Resource.ORE] -= 1
        
        bank.resources[Resource.WOOL] += 1
        bank.resources[Resource.WHEAT] += 1
        bank.resources[Resource.ORE] += 1
        return True
    
    def calculate_victory_points(self) -> int:
        """Calculate total victory points"""
        points = 0
        
        # Buildings
        points += len(self.settlements) * 1
        points += len(self.cities) * 2
        
        # Development cards
        points += self.victory_point_cards_played
        
        # Special achievements
        if self.has_largest_army:
            points += 2
        if self.has_longest_road:
            points += 2
        
        return points
    
    def get_playable_development_cards(self, current_turn: int) -> List['DevelopmentCard']:
        """Get list of development cards that can be played this turn"""
        if self.development_card_played_this_turn:
            # Can only play victory point cards after playing another card
            return [card for card in self.development_cards 
                   if not card.has_been_played and 
                   card.card_type == DevelopmentCardType.VICTORY_POINT]
        
        playable = []
        for card in self.development_cards:
            if card.has_been_played:
                continue
            
            # Check if bought this turn (except victory points)
            if card in self.cards_bought_this_turn:
                if card.card_type != DevelopmentCardType.VICTORY_POINT:
                    continue
            
            playable.append(card)
        
        return playable
    
    def __repr__(self):
        vp = self.calculate_victory_points()
        res = self.get_total_resources()
        return f"Player({self.id}, VP={vp}, Resources={res})"