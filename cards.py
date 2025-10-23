"""
Development card system for Settlers of Catan
"""
from typing import TYPE_CHECKING, List, Optional
from models import DevelopmentCardType, Resource
import random

if TYPE_CHECKING:
    from player import Player
    from game import Game


class DevelopmentCard:
    """Base class for development cards"""
    
    def __init__(self, card_type: DevelopmentCardType):
        self.card_type = card_type
        self.has_been_played = False
    
    def can_play_this_turn(self, turn_acquired: int, current_turn: int) -> bool:
        """Check if card can be played this turn"""
        if self.card_type == DevelopmentCardType.VICTORY_POINT:
            return True  # Victory points can be played immediately
        return current_turn > turn_acquired
    
    def play(self, game: 'Game', player: 'Player'):
        """Execute the card's effect"""
        raise NotImplementedError
    
    def __repr__(self):
        return f"DevelopmentCard({self.card_type.value})"


class MonopolyCard(DevelopmentCard):
    """Takes all of one resource from all other players"""
    
    def __init__(self):
        super().__init__(DevelopmentCardType.MONOPOLY)
    
    def play(self, game: 'Game', player: 'Player'):
        """Player chooses a resource and takes all of that resource from other players"""
        # This would need UI interaction in a real game
        # For now, return the method that game will call with chosen resource
        self.has_been_played = True
        return self.execute_monopoly
    
    def execute_monopoly(self, game: 'Game', player: 'Player', resource: Resource):
        """Execute the monopoly with chosen resource"""
        total_collected = 0
        for other_player in game.players:
            if other_player != player:
                amount = other_player.resources[resource]
                other_player.resources[resource] = 0
                total_collected += amount
        
        # Check if bank has enough
        available = min(total_collected, game.bank.resources[resource])
        player.resources[resource] += available
        game.bank.resources[resource] -= available


class RoadBuildingCard(DevelopmentCard):
    """Build two roads at no cost"""
    
    def __init__(self):
        super().__init__(DevelopmentCardType.ROAD_BUILDING)
    
    def play(self, game: 'Game', player: 'Player'):
        """Allows player to build two roads for free"""
        self.has_been_played = True
        # Set flag that next two road builds are free
        player.free_roads_remaining = 2


class InventionCard(DevelopmentCard):
    """Take any two resources from the bank"""
    
    def __init__(self):
        super().__init__(DevelopmentCardType.INVENTION)
    
    def play(self, game: 'Game', player: 'Player'):
        """Player takes any two resources from bank"""
        self.has_been_played = True
        return self.execute_invention
    
    def execute_invention(self, game: 'Game', player: 'Player', 
                         resource1: Resource, resource2: Resource):
        """Execute invention with chosen resources"""
        # Take first resource if available
        if game.bank.resources[resource1] > 0:
            player.resources[resource1] += 1
            game.bank.resources[resource1] -= 1
        
        # Take second resource if available
        if game.bank.resources[resource2] > 0:
            player.resources[resource2] += 1
            game.bank.resources[resource2] -= 1


class VictoryPointCard(DevelopmentCard):
    """Provides 1 victory point"""
    
    def __init__(self):
        super().__init__(DevelopmentCardType.VICTORY_POINT)
    
    def play(self, game: 'Game', player: 'Player'):
        """Reveals the victory point card"""
        self.has_been_played = True
        player.victory_point_cards_played += 1


class KnightCard(DevelopmentCard):
    """Move the robber and steal a resource"""
    
    def __init__(self):
        super().__init__(DevelopmentCardType.KNIGHT)
    
    def play(self, game: 'Game', player: 'Player'):
        """Move robber like rolling a 7"""
        self.has_been_played = True
        player.knights_played += 1
        
        # Check for largest army
        game.check_largest_army()
        
        # Return method for moving robber
        return game.move_robber_action


class DevelopmentCardDeck:
    """Manages the deck of development cards"""
    
    def __init__(self):
        self.cards: List[DevelopmentCard] = []
        self._initialize_deck()
    
    def _initialize_deck(self):
        """Create the 25 development cards"""
        # 2 Monopoly
        for _ in range(2):
            self.cards.append(MonopolyCard())
        
        # 2 Road Building
        for _ in range(2):
            self.cards.append(RoadBuildingCard())
        
        # 2 Invention
        for _ in range(2):
            self.cards.append(InventionCard())
        
        # 5 Victory Points
        for _ in range(5):
            self.cards.append(VictoryPointCard())
        
        # 14 Knights
        for _ in range(14):
            self.cards.append(KnightCard())
        
        # Shuffle the deck
        random.shuffle(self.cards)
    
    def draw_card(self) -> Optional[DevelopmentCard]:
        """Draw a card from the deck"""
        if self.cards:
            return self.cards.pop()
        return None
    
    def cards_remaining(self) -> int:
        return len(self.cards)
    
    def __repr__(self):
        return f"DevelopmentCardDeck({len(self.cards)} cards remaining)"