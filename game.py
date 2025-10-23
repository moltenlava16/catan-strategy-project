"""
Main game logic for Settlers of Catan
"""
import random
from typing import List, Optional, Tuple, Dict
from models import Resource, Terrain, DevelopmentCardType
from board import Board, Plot, Path, Hexagon
from player import Player
from buildings import Settlement, City, Road
from cards import DevelopmentCardDeck


class Bank:
    """Represents the bank which holds resources"""
    
    def __init__(self):
        # Initialize with 19 of each resource
        self.resources: Dict[Resource, int] = {r: 19 for r in Resource}
    
    def has_resource(self, resource: Resource, amount: int = 1) -> bool:
        """Check if bank has enough of a resource"""
        return self.resources[resource] >= amount
    
    def trade_with_player(self, player: Player, give_resource: Resource, 
                         give_amount: int, receive_resource: Resource) -> bool:
        """Execute a trade between the bank and a player"""
        # Check if player has enough resources
        if player.resources[give_resource] < give_amount:
            return False
        
        # Check if bank has resource to give
        if not self.has_resource(receive_resource):
            return False
        
        # Execute trade
        player.resources[give_resource] -= give_amount
        self.resources[give_resource] += give_amount
        player.resources[receive_resource] += 1
        self.resources[receive_resource] -= 1
        
        return True
    
    def __repr__(self):
        total = sum(self.resources.values())
        return f"Bank({total} total resources)"


class Game:
    """Main game class that manages the overall game state"""
    
    def __init__(self, num_players: int = 4):
        self.board = Board()
        self.bank = Bank()
        self.development_deck = DevelopmentCardDeck()
        self.players: List[Player] = [Player(i) for i in range(1, num_players + 1)]
        
        # Game state
        self.current_player_index: int = 0
        self.turn_number: int = 0
        self.phase: str = "setup"  # setup, rolling, main, end
        self.winner: Optional[Player] = None
        
        # Setup phase tracking
        self.setup_round: int = 1
        self.setup_forward: bool = True
        self.settlements_placed_this_setup: int = 0
    
    def setup_game(self):
        """Initialize the game with random board setup"""
        self.board.setup_random_board()
        
        # Randomize player order
        random.shuffle(self.players)
        
        # Reset player IDs based on new order
        for i, player in enumerate(self.players):
            player.id = i + 1
        
        print(f"Player order: {', '.join([f'Player {p.id}' for p in self.players])}")
        print("\nBeginning setup phase...")
        self.phase = "setup"
    
    def get_current_player(self) -> Player:
        """Get the current player"""
        return self.players[self.current_player_index]
    
    def roll_dice(self) -> Tuple[int, int, int]:
        """Roll two dice and return individual values plus sum"""
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        return die1, die2, die1 + die2
    
    def place_initial_settlement(self, player: Player, plot: Plot) -> bool:
        """Place a settlement during setup phase"""
        if self.phase != "setup":
            return False
        
        if not self.board.can_build_settlement(player, plot, initial_placement=True):
            return False
        
        settlement = Settlement(player, plot)
        plot.building = settlement
        player.settlements.append(settlement)
        player.available_settlements -= 1
        
        # If this is the second settlement, collect starting resources
        if self.setup_round == 2:
            self.collect_starting_resources(player, plot)
        
        self.settlements_placed_this_setup += 1
        return True
    
    def place_initial_road(self, player: Player, path: Path) -> bool:
        """Place a road during setup phase"""
        if self.phase != "setup":
            return False
        
        # Check that road connects to player's most recent settlement
        last_settlement = player.settlements[-1] if player.settlements else None
        if not last_settlement:
            return False
        
        # Road must connect to the settlement just placed
        if last_settlement.plot not in path.plots:
            return False
        
        if not self.board.can_build_road(player, path, initial_placement=True):
            return False
        
        road = Road(player, path)
        path.road = road
        player.roads.append(road)
        player.available_roads -= 1
        
        # Move to next player in setup
        self.advance_setup_turn()
        return True
    
    def advance_setup_turn(self):
        """Advance to the next player in setup phase"""
        if self.setup_forward:
            if self.current_player_index < len(self.players) - 1:
                self.current_player_index += 1
            else:
                # Reached end, reverse direction
                self.setup_forward = False
                self.setup_round = 2
        else:
            if self.current_player_index > 0:
                self.current_player_index -= 1
            else:
                # Setup complete, begin main game
                self.phase = "main"
                self.turn_number = 1
                print("\nSetup complete! Beginning main game...")
    
    def collect_starting_resources(self, player: Player, plot: Plot):
        """Collect starting resources for second settlement"""
        for hex in plot.adjacent_hexagons:
            if hex.terrain and hex.terrain != Terrain.DESERT:
                resource = hex.get_resource()
                if resource and self.bank.has_resource(resource):
                    player.resources[resource] += 1
                    self.bank.resources[resource] -= 1
    
    def start_turn(self) -> Tuple[int, int, int]:
        """Start a new turn - roll dice and distribute resources"""
        if self.phase != "main":
            return (0, 0, 0)
        
        player = self.get_current_player()
        
        # Roll dice
        die1, die2, total = self.roll_dice()
        print(f"\nPlayer {player.id} rolled {die1} + {die2} = {total}")
        
        if total == 7:
            self.handle_seven_rolled(player)
        else:
            self.distribute_resources(total)
        
        return die1, die2, total
    
    def handle_seven_rolled(self, rolling_player: Player):
        """Handle when a 7 is rolled"""
        print("A 7 was rolled! Activating robber...")
        
        # All players with >7 resources must discard half
        for player in self.players:
            if player.must_discard_on_seven():
                discard_count = player.get_discard_count()
                print(f"Player {player.id} must discard {discard_count} resources")
                # In a real game, this would prompt for player input
                self.force_random_discard(player, discard_count)
        
        # Rolling player must move robber (handled by UI in real game)
    
    def force_random_discard(self, player: Player, count: int):
        """Force a random discard of resources (placeholder for UI)"""
        discarded = 0
        resources_list = []
        
        # Build list of all resources
        for resource in Resource:
            resources_list.extend([resource] * player.resources[resource])
        
        # Randomly discard
        random.shuffle(resources_list)
        for i in range(min(count, len(resources_list))):
            resource = resources_list[i]
            player.resources[resource] -= 1
            self.bank.resources[resource] += 1
            discarded += 1
    
    def move_robber_action(self, player: Player, new_hex: Hexagon, 
                          victim: Optional[Player] = None) -> bool:
        """Move the robber and potentially steal a resource"""
        if new_hex == self.board.robber_location:
            return False  # Can't move to same location
        
        self.board.move_robber(new_hex)
        
        # Steal from victim if specified and valid
        if victim:
            # Check victim has building on this hex
            has_building = False
            for plot in new_hex.plots:
                if plot.building and plot.building.player == victim:
                    has_building = True
                    break
            
            if has_building and victim.get_total_resources() > 0:
                # Steal random resource
                available_resources = []
                for resource in Resource:
                    available_resources.extend([resource] * victim.resources[resource])
                
                if available_resources:
                    stolen = random.choice(available_resources)
                    victim.resources[stolen] -= 1
                    player.resources[stolen] += 1
                    print(f"Player {player.id} stole 1 {stolen.value} from Player {victim.id}")
        
        return True
    
    def distribute_resources(self, roll_value: int):
        """Distribute resources based on dice roll"""
        # Find all hexagons with this roll value (excluding robber hexes)
        for hex in self.board.hexagons:
            if hex.roll_value == roll_value and not hex.has_robber:
                resource = hex.get_resource()
                if not resource:
                    continue
                
                # Find all buildings on this hex
                for plot in hex.plots:
                    if plot.building:
                        multiplier = plot.building.get_resource_multiplier()
                        player = plot.building.player
                        
                        # Give resources if bank has them
                        amount_to_give = min(multiplier, self.bank.resources[resource])
                        if amount_to_give > 0:
                            player.resources[resource] += amount_to_give
                            self.bank.resources[resource] -= amount_to_give
    
    def build_road(self, player: Player, path: Path) -> bool:
        """Build a road"""
        if self.phase != "main" or player != self.get_current_player():
            return False
        
        if not self.board.can_build_road(player, path):
            return False
        
        if not player.pay_for_road(self.bank):
            return False
        
        road = Road(player, path)
        path.road = road
        player.roads.append(road)
        player.available_roads -= 1
        
        # Check for longest road
        self.check_longest_road()
        
        return True
    
    def build_settlement(self, player: Player, plot: Plot) -> bool:
        """Build a settlement"""
        if self.phase != "main" or player != self.get_current_player():
            return False
        
        if not self.board.can_build_settlement(player, plot):
            return False
        
        if not player.pay_for_settlement(self.bank):
            return False
        
        settlement = Settlement(player, plot)
        plot.building = settlement
        player.settlements.append(settlement)
        player.available_settlements -= 1
        
        # Check for victory
        self.check_victory()
        
        return True
    
    def build_city(self, player: Player, plot: Plot) -> bool:
        """Upgrade a settlement to a city"""
        if self.phase != "main" or player != self.get_current_player():
            return False
        
        if not self.board.can_build_city(player, plot):
            return False
        
        if not player.pay_for_city(self.bank):
            return False
        
        # Remove settlement - we know it's a Settlement from can_build_city check
        old_settlement = plot.building
        if not isinstance(old_settlement, Settlement):
            # This shouldn't happen given can_build_city check, but satisfies type checker
            return False
        
        player.settlements.remove(old_settlement)
        player.available_settlements += 1
        
        # Add city
        city = City(player, plot)
        plot.building = city
        player.cities.append(city)
        player.available_cities -= 1
        
        # Check for victory
        self.check_victory()
        
        return True
    
    def buy_development_card(self, player: Player) -> Optional[DevelopmentCardType]:
        """Buy a development card"""
        if self.phase != "main" or player != self.get_current_player():
            return None
        
        if not player.pay_for_development_card(self.bank):
            return None
        
        card = self.development_deck.draw_card()
        if not card:
            # Return resources if no cards left
            player.resources[Resource.WOOL] += 1
            player.resources[Resource.WHEAT] += 1
            player.resources[Resource.ORE] += 1
            self.bank.resources[Resource.WOOL] -= 1
            self.bank.resources[Resource.WHEAT] -= 1
            self.bank.resources[Resource.ORE] -= 1
            return None
        
        player.development_cards.append(card)
        player.cards_bought_this_turn.append(card)
        
        return card.card_type
    
    def play_development_card(self, player: Player, card_index: int) -> bool:
        """Play a development card"""
        if self.phase != "main" or player != self.get_current_player():
            return False
        
        if card_index >= len(player.development_cards):
            return False
        
        card = player.development_cards[card_index]
        
        # Check if card can be played
        playable_cards = player.get_playable_development_cards(self.turn_number)
        if card not in playable_cards:
            return False
        
        # Mark as played (except victory points can play multiple)
        if card.card_type != DevelopmentCardType.VICTORY_POINT:
            player.development_card_played_this_turn = True
        
        # Execute card effect
        result = card.play(self, player)
        
        # Handle any follow-up actions based on card type
        # (In a real game, this would involve UI for player choices)
        
        # Check for victory after playing victory point cards
        if card.card_type == DevelopmentCardType.VICTORY_POINT:
            self.check_victory()
        
        return True
    
    def propose_trade(self, proposer: Player, target: Player,
                     offer: Dict[Resource, int], request: Dict[Resource, int]) -> bool:
        """Propose a trade between players"""
        if self.phase != "main" or proposer != self.get_current_player():
            return False
        
        # Check for identical resource trade (not allowed)
        for resource in offer.keys():
            if resource in request:
                return False  # Can't trade same resource type
        
        # Check proposer has resources to offer
        for resource, amount in offer.items():
            if proposer.resources[resource] < amount:
                return False
        
        # Check target has resources requested
        for resource, amount in request.items():
            if target.resources[resource] < amount:
                return False
        
        # In a real game, target would accept/decline
        # For now, execute trade (assuming acceptance)
        
        # Transfer offered resources
        for resource, amount in offer.items():
            proposer.resources[resource] -= amount
            target.resources[resource] += amount
        
        # Transfer requested resources
        for resource, amount in request.items():
            target.resources[resource] -= amount
            proposer.resources[resource] += amount
        
        return True
    
    def bank_trade(self, player: Player, give_resource: Resource, 
                  receive_resource: Resource) -> bool:
        """Trade with the bank"""
        if self.phase != "main" or player != self.get_current_player():
            return False
        
        # Get best trade ratio
        ratio = player.get_best_trade_ratio(give_resource)
        give_amount = ratio[0]
        
        return self.bank.trade_with_player(player, give_resource, 
                                          give_amount, receive_resource)
    
    def check_longest_road(self):
        """Update longest road holder"""
        current_longest = 0
        current_holder = None
        
        # Find current holder's road length
        for player in self.players:
            if player.has_longest_road:
                current_holder = player
                current_longest = self.board.get_longest_road(player)
                break
        
        # Check all players' road lengths
        for player in self.players:
            road_length = self.board.get_longest_road(player)
            
            if road_length >= 5:  # Minimum 5 for longest road
                if current_holder is None:
                    # First to reach 5
                    player.has_longest_road = True
                    print(f"Player {player.id} earned Longest Road! ({road_length} segments)")
                elif player != current_holder and road_length > current_longest:
                    # New longest road holder
                    current_holder.has_longest_road = False
                    player.has_longest_road = True
                    print(f"Player {player.id} took Longest Road! ({road_length} segments)")
        
        self.check_victory()
    
    def check_largest_army(self):
        """Update largest army holder"""
        current_largest = 0
        current_holder = None
        
        # Find current holder
        for player in self.players:
            if player.has_largest_army:
                current_holder = player
                current_largest = player.knights_played
                break
        
        # Check all players' knight counts
        for player in self.players:
            if player.knights_played >= 3:  # Minimum 3 for largest army
                if current_holder is None:
                    # First to reach 3
                    player.has_largest_army = True
                    print(f"Player {player.id} earned Largest Army! ({player.knights_played} knights)")
                elif player != current_holder and player.knights_played > current_largest:
                    # New largest army holder
                    current_holder.has_largest_army = False
                    player.has_largest_army = True
                    print(f"Player {player.id} took Largest Army! ({player.knights_played} knights)")
        
        self.check_victory()
    
    def check_victory(self):
        """Check if any player has won"""
        for player in self.players:
            if player.calculate_victory_points() >= 10:
                self.winner = player
                self.phase = "end"
                print(f"\nGAME OVER! Player {player.id} wins with {player.calculate_victory_points()} victory points!")
                return True
        return False
    
    def end_turn(self):
        """End the current player's turn"""
        if self.phase != "main":
            return
        
        # Clear turn-specific flags
        player = self.get_current_player()
        player.development_card_played_this_turn = False
        player.cards_bought_this_turn.clear()
        
        # Move to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.turn_number += 1
    
    def get_game_state_summary(self) -> str:
        """Get a summary of the current game state"""
        summary = f"\n{'='*50}\n"
        summary += f"Turn {self.turn_number} - "
        
        if self.phase == "setup":
            summary += f"Setup Phase (Round {self.setup_round})\n"
            summary += f"Current Player: Player {self.get_current_player().id}\n"
        elif self.phase == "main":
            summary += f"Main Game\n"
            summary += f"Current Player: Player {self.get_current_player().id}\n"
        elif self.phase == "end":
            summary += f"Game Over! Winner: Player {self.winner}\n"
        
        summary += f"\nPlayer Status:\n"
        for player in self.players:
            vp = player.calculate_victory_points()
            resources = player.get_total_resources()
            summary += f"  Player {player.id}: {vp} VP, {resources} resources"
            if player.has_longest_road:
                summary += " [Longest Road]"
            if player.has_largest_army:
                summary += " [Largest Army]"
            summary += "\n"
        
        summary += f"\nDevelopment Cards Remaining: {self.development_deck.cards_remaining()}\n"
        summary += f"{'='*50}\n"
        
        return summary
    
    def __repr__(self):
        return f"Game(Phase: {self.phase}, Turn: {self.turn_number}, Current Player: {self.get_current_player().id})"