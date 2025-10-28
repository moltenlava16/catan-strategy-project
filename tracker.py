"""
Tracker mode for Settlers of Catan - assists a player in tracking game state
"""
import random
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
from game import Game
from models import Resource, Terrain, DevelopmentCardType
from board import Plot, Path, Hexagon
from buildings import Settlement, City, Road
from player import Player
from cards import (
    DevelopmentCard, 
    MonopolyCard, 
    RoadBuildingCard,
    InventionCard, 
    VictoryPointCard, 
    KnightCard
)


class MysteryCard:
    """Represents an unknown resource or development card with probability"""
    
    def __init__(self, probabilities: Dict[str, float], is_positive: bool = True):
        self.probabilities = probabilities  # Resource/card type -> probability
        self.is_positive = is_positive  # True if gained, False if lost
        self.resolved = False
        self.resolved_type = None
    
    def resolve(self, actual_type: str):
        """Resolve the mystery to a known type"""
        self.resolved = True
        self.resolved_type = actual_type
    
    def get_display(self) -> str:
        """Get display string for the mystery card"""
        if self.resolved:
            return self.resolved_type if self.resolved_type is not None else "unknown"
        
        # Sort by probability
        items = sorted(self.probabilities.items(), key=lambda x: (-x[1], x[0]))
        parts = []
        
        for item_type, prob in items:
            if prob == 1.0:
                parts.append(item_type)
            elif prob >= 0.01:  # Only show if at least 1% chance
                # Format as fraction if simple
                if abs(prob - 0.5) < 0.01:
                    parts.append(f"½ {item_type}")
                elif abs(prob - 1/3) < 0.01:
                    parts.append(f"⅓ {item_type}")
                elif abs(prob - 2/3) < 0.01:
                    parts.append(f"⅔ {item_type}")
                elif abs(prob - 0.25) < 0.01:
                    parts.append(f"¼ {item_type}")
                elif abs(prob - 0.75) < 0.01:
                    parts.append(f"¾ {item_type}")
                else:
                    parts.append(f"{prob:.0%} {item_type}")
        
        prefix = "" if self.is_positive else "-"
        return f"{prefix}[{' | '.join(parts)}]"
    
    def matches(self, other: 'MysteryCard') -> bool:
        """Check if two mystery cards are identical"""
        if self.is_positive != other.is_positive:
            return False
        if self.resolved != other.resolved:
            return False
        if self.resolved and self.resolved_type != other.resolved_type:
            return False
        
        # Check probabilities match
        for key in set(self.probabilities.keys()) | set(other.probabilities.keys()):
            if abs(self.probabilities.get(key, 0) - other.probabilities.get(key, 0)) > 0.001:
                return False
        return True


class TrackerMode:
    """Main tracker mode for assisting a player in tracking a real Catan game"""
    
    def __init__(self):
        self.game = Game(num_players=4)
        self.nicknames: Dict[int, str] = {}
        self.user_player_id: Optional[int] = None
        
        # Mystery tracking
        self.mystery_resources: Dict[int, List[MysteryCard]] = defaultdict(list)
        self.mystery_dev_cards: Dict[int, List[MysteryCard]] = defaultdict(list)
        
        # Known tracking for non-user players
        self.known_resources: Dict[int, Dict[Resource, int]] = {}
        self.known_dev_cards: Dict[int, int] = {}  # Player -> count of dev cards
        
        # Command history
        self.command_history: List[str] = []
        self.turn_commands: List[str] = []  # Commands in current turn
        
        # Initialize known resources
        for i in range(1, 5):
            self.known_resources[i] = {r: 0 for r in Resource}
            self.known_dev_cards[i] = 0
    
    def start(self):
        """Start the tracker mode"""
        print("\n" + "=" * 60)
        print(" " * 18 + "CATAN TRACKER MODE")
        print("=" * 60)
        print("\nThis mode helps you track a real game of Catan.")
        print("Follow the prompts to set up the game.\n")
        
        try:
            # Setup
            self._setup_players()
            self._setup_board()
            self._setup_initial_placements()
            
            # Main game
            self._run_game_loop()
            
        except KeyboardInterrupt:
            print("\n\nTracker mode interrupted.")
        except Exception as e:
            print(f"\n\nError: {e}")
            import traceback
            traceback.print_exc()
    
    def _setup_players(self):
        """Set up player nicknames and identify the user"""
        print("=== PLAYER SETUP ===\n")
        
        # Get nicknames
        for i in range(1, 5):
            nickname = input(f"Enter nickname for Player {i} (or press Enter for 'Player {i}'): ").strip()
            self.nicknames[i] = nickname if nickname else f"Player {i}"
        
        print(f"\nPlayers: {', '.join(self.nicknames.values())}")
        
        # Identify user
        while self.user_player_id is None:
            user_input = input("\nWhich player are you? (name or number 1-4): ").strip()
            
            # Try by number
            if user_input.isdigit():
                num = int(user_input)
                if 1 <= num <= 4:
                    self.user_player_id = num
            else:
                # Try by name
                for pid, name in self.nicknames.items():
                    if name.lower() == user_input.lower():
                        self.user_player_id = pid
                        break
            
            if self.user_player_id is None:
                print("Invalid input. Please try again.")
        
        print(f"You are playing as: {self.nicknames[self.user_player_id]}")
    
    def _setup_board(self):
        """Set up the board configuration"""
        print("\n=== BOARD SETUP ===\n")
        print("Enter terrain and roll value for each hexagon.")
        print("Terrain options: hills, mountains, forests, pastures, fields, desert\n")
        
        for hex_num in range(1, 20):
            # Get terrain
            while True:
                terrain_str = input(f"Hexagon {hex_num} terrain: ").strip().lower()
                terrain = None
                
                for t in Terrain:
                    if t.terrain_name == terrain_str:
                        terrain = t
                        break
                
                if terrain:
                    hex = self.game.board.hexagons[hex_num - 1]
                    hex.set_terrain(terrain)
                    
                    # Get roll value if not desert
                    if terrain == Terrain.DESERT:
                        hex.has_robber = True
                        self.game.board.robber_location = hex
                        print(f"  Desert - robber placed here")
                    else:
                        while True:
                            roll_str = input(f"Hexagon {hex_num} roll value (2-12, no 7): ").strip()
                            if roll_str.isdigit():
                                roll = int(roll_str)
                                if roll in [2,3,4,5,6,8,9,10,11,12]:
                                    hex.set_roll_value(roll)
                                    break
                            print("Invalid roll value.")
                    break
                else:
                    print(f"Invalid terrain. Options: {', '.join([t.terrain_name for t in Terrain])}")
        
        print("\nBoard setup complete!")
    
    def _setup_initial_placements(self):
        """Set up initial settlements and roads"""
        print("\n=== INITIAL PLACEMENTS ===\n")
        print("Enter the plot numbers for settlements and path numbers for roads.")
        print("Order: Player 1, 2, 3, 4, then 4, 3, 2, 1\n")
        
        self.game.phase = "setup"
        self.game.current_player_index = 0
        
        # Placement order
        order = [1, 2, 3, 4, 4, 3, 2, 1]
        
        for round_num, player_id in enumerate(order):
            player = self.game.players[player_id - 1]
            settlement_num = 1 if round_num < 4 else 2
            
            print(f"\n{self.nicknames[player_id]}'s placement #{settlement_num}:")
            
            # Get settlement
            while True:
                plot_str = input(f"  Settlement plot number: ").strip()
                if plot_str.isdigit():
                    plot_id = int(plot_str)
                    if plot_id in self.game.board.plots:
                        plot = self.game.board.plots[plot_id]
                        if self.game.place_initial_settlement(player, plot):
                            print(f"    ✓ Settlement placed at plot {plot_id}")
                            break
                        else:
                            print("    Invalid placement (check distance rules)")
                    else:
                        print(f"    Plot {plot_id} doesn't exist")
                else:
                    print("    Please enter a number")
            
            # Get road
            while True:
                path_str = input(f"  Road path number: ").strip()
                if path_str.isdigit():
                    path_id = int(path_str)
                    if path_id in self.game.board.paths:
                        path = self.game.board.paths[path_id]
                        if self.game.place_initial_road(player, path):
                            print(f"    ✓ Road placed at path {path_id}")
                            break
                        else:
                            print("    Road must connect to the settlement")
                    else:
                        print(f"    Path {path_id} doesn't exist")
                else:
                    print("    Please enter a number")
        
        # Distribute starting resources
        print("\nStarting resources distributed:")
        for i, player in enumerate(self.game.players, 1):
            self.known_resources[i] = player.resources.copy()
            
            res_list = []
            for r in Resource:
                if player.resources[r] > 0:
                    res_list.append(f"{player.resources[r]} {r.value}")
            
            if res_list:
                print(f"  {self.nicknames[i]}: {', '.join(res_list)}")
            else:
                print(f"  {self.nicknames[i]}: no resources")
        
        # Start main game
        self.game.phase = "main"
        self.game.turn_number = 1
        self.game.current_player_index = 0
        
        print("\n" + "=" * 60)
        print("Setup complete! Main game begins.")
        print("Type '!commands' for help.")
        print("=" * 60)
    
    def _run_game_loop(self):
        """Main game tracking loop"""
        while self.game.phase == "main" and not self.game.winner:
            current = self.game.get_current_player()
            print(f"\n=== Turn {self.game.turn_number}: {self.nicknames[current.id]} ===")
            
            # Get dice roll
            while True:
                roll_str = input("Dice roll total (2-12): ").strip()
                if roll_str.isdigit():
                    roll = int(roll_str)
                    if 2 <= roll <= 12:
                        break
                print("Invalid roll.")
            
            # Handle the roll
            print(f"Rolled: {roll}")
            
            if roll == 7:
                self._handle_seven(current)
            else:
                self._distribute_resources(roll)
            
            # Process commands
            self.turn_commands = []
            while True:
                command = input("> ").strip()
                if command:
                    self.command_history.append(command)
                    self.turn_commands.append(command)
                    
                    if self._process_command(command):
                        break  # Turn ended
        
        # Game over
        if self.game.winner:
            print("\n" + "=" * 60)
            print(f"GAME OVER! {self.nicknames[self.game.winner.id]} WINS!")
            print(f"Victory Points: {self.game.winner.calculate_victory_points()}")
            print("=" * 60)
    
    def _handle_seven(self, current_player):
        """Handle when a 7 is rolled"""
        # Discards
        for player in self.game.players:
            if player.must_discard_on_seven():
                count = player.get_discard_count()
                print(f"{self.nicknames[player.id]} must discard {count} resources")
                
                if player.id == self.user_player_id:
                    # User discards - we know what they discard
                    self._user_discard(player, count)
                else:
                    # Non-user discards - random
                    self.game.force_random_discard(player, count)
                    # We don't know what was discarded
        
        # Move robber
        while True:
            hex_str = input("Robber moved to hexagon (1-19): ").strip()
            if hex_str.isdigit():
                hex_id = int(hex_str)
                if 1 <= hex_id <= 19:
                    new_hex = self.game.board.hexagons[hex_id - 1]
                    if new_hex != self.game.board.robber_location:
                        self.game.board.move_robber(new_hex)
                        print(f"Robber moved to hexagon {hex_id}")
                        
                        # Check for steal
                        self._handle_steal(current_player, new_hex)
                        break
                    else:
                        print("Robber must move to a different hex")
    
    def _user_discard(self, player, count):
        """Handle user discarding resources"""
        discarded = 0
        to_discard = {r: 0 for r in Resource}
        
        print("Choose resources to discard:")
        while discarded < count:
            self._show_player_resources(player.id, show_mystery=False)
            
            res_str = input(f"Resource to discard ({count - discarded} remaining): ").strip().lower()
            resource = self._parse_resource(res_str)
            
            if resource and player.resources[resource] > to_discard[resource]:
                to_discard[resource] += 1
                discarded += 1
            else:
                print("Invalid or insufficient resource")
        
        # Apply discards
        for r, amt in to_discard.items():
            player.resources[r] -= amt
            self.game.bank.resources[r] += amt
            if player.id == self.user_player_id:
                self.known_resources[player.id][r] -= amt
    
    def _handle_steal(self, thief, hex):
        """Handle resource stealing"""
        # Find victims
        victims = set()
        for plot in hex.plots:
            if plot.building and plot.building.player != thief:
                if plot.building.player.get_total_resources() > 0:
                    victims.add(plot.building.player)
        
        if not victims:
            return
        
        if len(victims) == 1:
            victim = victims.pop()
        else:
            # Choose victim
            print(f"Possible victims: {', '.join([self.nicknames[v.id] for v in victims])}")
            while True:
                victim_str = input("Who was robbed? ").strip()
                victim = self._get_player_by_name(victim_str)
                if victim and victim in victims:
                    break
                print("Invalid victim")
        
        # Steal resource
        if thief.id == self.user_player_id or victim.id == self.user_player_id:
            # User involved - ask what was stolen
            res_str = input("What resource was stolen? (or 'unknown'): ").strip().lower()
            
            if res_str == "unknown":
                self._create_mystery_steal(thief, victim)
            else:
                resource = self._parse_resource(res_str)
                if resource:
                    # Known steal
                    victim.resources[resource] -= 1
                    thief.resources[resource] += 1
                    self.game.bank.resources[resource] = self.game.bank.resources.get(resource, 0)
                    
                    # Update known
                    if thief.id != self.user_player_id:
                        self.known_resources[thief.id][resource] += 1
                    if victim.id != self.user_player_id:
                        self.known_resources[victim.id][resource] -= 1
                    
                    print(f"{self.nicknames[thief.id]} stole {resource.value} from {self.nicknames[victim.id]}")
        else:
            # Neither is user
            saw = input("Did you see what was stolen? (yes/no): ").strip().lower()
            if saw == "yes":
                res_str = input("What resource? ").strip().lower()
                resource = self._parse_resource(res_str)
                if resource:
                    victim.resources[resource] -= 1
                    thief.resources[resource] += 1
                    self.known_resources[thief.id][resource] += 1
                    self.known_resources[victim.id][resource] -= 1
                    print(f"{self.nicknames[thief.id]} stole {resource.value}")
            else:
                self._create_mystery_steal(thief, victim)
    
    def _create_mystery_steal(self, thief, victim):
        """Create mystery cards for unknown steal"""
        # Calculate probabilities based on victim's known resources
        total = sum(self.known_resources[victim.id].values())
        if total == 0:
            return
        
        probs = {}
        for r in Resource:
            if self.known_resources[victim.id][r] > 0:
                probs[r.value] = self.known_resources[victim.id][r] / total
        
        # Create mystery cards
        self.mystery_resources[thief.id].append(MysteryCard(probs, is_positive=True))
        self.mystery_resources[victim.id].append(MysteryCard(probs, is_positive=False))
        
        # Actually steal random resource in game
        available = []
        for r in Resource:
            available.extend([r] * victim.resources[r])
        
        if available:
            stolen = random.choice(available)
            victim.resources[stolen] -= 1
            thief.resources[stolen] += 1
        
        print(f"{self.nicknames[thief.id]} stole unknown resource from {self.nicknames[victim.id]}")
    
    def _distribute_resources(self, roll):
        """Distribute resources for a dice roll"""
        # Track before
        before = {}
        for p in self.game.players:
            before[p.id] = p.resources.copy()
        
        # Distribute
        self.game.distribute_resources(roll)
        
        # Track gains
        for p in self.game.players:
            for r in Resource:
                gained = p.resources[r] - before[p.id][r]
                if gained > 0:
                    if p.id != self.user_player_id:
                        self.known_resources[p.id][r] += gained
                    
                    if gained == 1:
                        print(f"  {self.nicknames[p.id]} gained 1 {r.value}")
                    else:
                        print(f"  {self.nicknames[p.id]} gained {gained} {r.value}")
    
    def _process_command(self, command: str) -> bool:
        """Process a command. Returns True if turn ends."""
        parts = command.lower().split()
        if not parts:
            return False
        
        cmd = parts[0]
        
        # Command handlers
        if cmd == "!commands":
            self._show_commands()
        elif cmd == "!resources":
            player_str = parts[1] if len(parts) > 1 else None
            self._cmd_resources(player_str)
        elif cmd == "!trade":
            self._cmd_trade(parts[1:])
        elif cmd == "!maritimetrade":
            self._cmd_maritime_trade(parts[1:])
        elif cmd == "!build":
            self._cmd_build(parts[1:])
        elif cmd == "!upgrade":
            self._cmd_upgrade(parts[1:])
        elif cmd == "!buydev":
            self._cmd_buy_dev(parts[1] if len(parts) > 1 else "unknown")
        elif cmd == "!playdev":
            self._cmd_play_dev(parts[1] if len(parts) > 1 else None)
        elif cmd == "!vp":
            player_str = parts[1] if len(parts) > 1 else None
            self._cmd_victory_points(player_str)
        elif cmd == "!find":
            self._cmd_find(parts[1] if len(parts) > 1 else None)
        elif cmd == "!board":
            self._cmd_board()
        elif cmd == "!ports":
            player_str = parts[1] if len(parts) > 1 else None
            self._cmd_ports(player_str)
        elif cmd == "!whoseturn":
            print(f"Current turn: {self.nicknames[self.game.get_current_player().id]}")
        elif cmd == "!history":
            self._cmd_history()
        elif cmd == "!undo":
            print("Undo not implemented yet")
        elif cmd == "!save":
            print("Save not implemented yet")
        elif cmd == "!load":
            print("Load not implemented yet")
        elif cmd == "!endturn":
            self.game.end_turn()
            self._stack_mysteries()
            print(f"Turn ended for {self.nicknames[self.game.get_current_player().id - 1]}")
            return True
        else:
            print(f"Unknown command: {cmd}")
            print("Type '!commands' for help")
        
        return False
    
    def _show_commands(self):
        """Show available commands"""
        print("\n=== AVAILABLE COMMANDS ===")
        print("!commands              - Show this help")
        print("!resources [player]    - Show resources")
        print("!trade [other] [give] [receive] - Record trade")
        print("!maritimeTrade [give] [receive] - Bank trade")
        print("!build road [path]     - Build road")
        print("!build settlement [plot] - Build settlement")
        print("!upgrade [plot]        - Upgrade to city")
        print("!buyDev [type/unknown] - Buy dev card")
        print("!playDev [type]        - Play dev card")
        print("!vp [player]           - Show victory points")
        print("!find largeArmy/longRoad - Find achievements")
        print("!board                 - Show board state")
        print("!ports [player]        - Show ports")
        print("!whoseTurn             - Current turn")
        print("!history               - Command history")
        print("!undo                  - Undo last command")
        print("!save/!load            - Save/load game")
        print("!endTurn               - End turn")
        print()
        print("Resource format: '3_wool_2_ore' = 3 wool + 2 ore")
        print()
    
    def _cmd_resources(self, player_str: Optional[str]):
        """Show resources command"""
        if player_str:
            player = self._get_player_by_name(player_str)
            if not player:
                print(f"Unknown player: {player_str}")
                return
            player_id = player.id
        else:
            player_id = self.game.get_current_player().id
        
        self._show_player_resources(player_id)
    
    def _show_player_resources(self, player_id: int, show_mystery: bool = True):
        """Show a player's resources"""
        player = self.game.players[player_id - 1]
        
        if player_id == self.user_player_id:
            # Show exact for user
            res_list = []
            for r in Resource:
                if player.resources[r] > 0:
                    res_list.append(f"{r.value}: {player.resources[r]}")
            
            print(f"{self.nicknames[player_id]}: {', '.join(res_list) if res_list else 'no resources'}")
            
            if player.development_cards:
                print(f"  Development cards: {len(player.development_cards)}")
        else:
            # Show known + mystery for others
            res_list = []
            for r in Resource:
                if self.known_resources[player_id][r] > 0:
                    res_list.append(f"{r.value}: {self.known_resources[player_id][r]}")
            
            print(f"{self.nicknames[player_id]} known: {', '.join(res_list) if res_list else 'none'}")
            
            if show_mystery:
                # Show mysteries
                mysteries = self.mystery_resources[player_id]
                if mysteries:
                    pos = [m.get_display() for m in mysteries if m.is_positive]
                    neg = [m.get_display() for m in mysteries if not m.is_positive]
                    
                    if pos:
                        print(f"  + Mystery: {', '.join(pos)}")
                    if neg:
                        print(f"  - Mystery: {', '.join(neg)}")
                
                # Dev cards
                if self.known_dev_cards[player_id] > 0:
                    print(f"  Dev cards: {self.known_dev_cards[player_id]}")
                
                dev_mysteries = self.mystery_dev_cards[player_id]
                if dev_mysteries:
                    print(f"  Mystery dev: {', '.join([m.get_display() for m in dev_mysteries])}")
    
    def _cmd_trade(self, args: List[str]):
        """Trade command"""
        if len(args) < 3:
            print("Usage: !trade [other_player] [give_resources] [receive_resources]")
            return
        
        current = self.game.get_current_player()
        other = self._get_player_by_name(args[0])
        
        if not other:
            print(f"Unknown player: {args[0]}")
            return
        
        give = self._parse_resources(args[1])
        receive = self._parse_resources(args[2])
        
        # Execute trade
        if self.game.propose_trade(current, other, give, receive):
            # Update known
            for r, amt in give.items():
                if current.id != self.user_player_id:
                    self.known_resources[current.id][r] -= amt
                if other.id != self.user_player_id:
                    self.known_resources[other.id][r] += amt
            
            for r, amt in receive.items():
                if current.id != self.user_player_id:
                    self.known_resources[current.id][r] += amt
                if other.id != self.user_player_id:
                    self.known_resources[other.id][r] -= amt
            
            print("Trade completed")
        else:
            print("Invalid trade")
    
    def _cmd_maritime_trade(self, args: List[str]):
        """Maritime/bank trade command"""
        if len(args) < 2:
            print("Usage: !maritimeTrade [give_resources] [receive_resource]")
            return
        
        current = self.game.get_current_player()
        give = self._parse_resources(args[0])
        
        # Should be single resource type
        give_res = None
        give_amt = 0
        for r, amt in give.items():
            if amt > 0:
                give_res = r
                give_amt = amt
                break
        
        if not give_res:
            print("Invalid give resources")
            return
        
        receive_res = self._parse_resource(args[1])
        if not receive_res:
            print("Invalid receive resource")
            return
        
        # Check ratio
        ratio = current.get_best_trade_ratio(give_res)
        if give_amt != ratio[0]:
            print(f"Invalid: must trade {ratio[0]} {give_res.value} (your ratio: {ratio[0]}:1)")
            return
        
        if self.game.bank_trade(current, give_res, receive_res):
            if current.id != self.user_player_id:
                self.known_resources[current.id][give_res] -= give_amt
                self.known_resources[current.id][receive_res] += 1
            print(f"Traded {give_amt} {give_res.value} for 1 {receive_res.value}")
        else:
            print("Invalid trade: bank out of resources")
    
    def _cmd_build(self, args: List[str]):
        """Build command"""
        if len(args) < 2:
            print("Usage: !build road [path] OR !build settlement [plot]")
            return
        
        current = self.game.get_current_player()
        build_type = args[0].lower()
        
        if build_type == "road":
            if not args[1].isdigit():
                print("Invalid path number")
                return
            
            path_id = int(args[1])
            if path_id not in self.game.board.paths:
                print(f"Path {path_id} doesn't exist")
                return
            
            path = self.game.board.paths[path_id]
            if self.game.build_road(current, path):
                if current.id != self.user_player_id:
                    self.known_resources[current.id][Resource.BRICK] -= 1
                    self.known_resources[current.id][Resource.WOOD] -= 1
                print(f"Road built at path {path_id}")
                self.game.check_longest_road()
            else:
                print("Invalid: check resources and connections")
        
        elif build_type == "settlement":
            if not args[1].isdigit():
                print("Invalid plot number")
                return
            
            plot_id = int(args[1])
            if plot_id not in self.game.board.plots:
                print(f"Plot {plot_id} doesn't exist")
                return
            
            plot = self.game.board.plots[plot_id]
            if self.game.build_settlement(current, plot):
                if current.id != self.user_player_id:
                    self.known_resources[current.id][Resource.BRICK] -= 1
                    self.known_resources[current.id][Resource.WOOD] -= 1
                    self.known_resources[current.id][Resource.WOOL] -= 1
                    self.known_resources[current.id][Resource.WHEAT] -= 1
                print(f"Settlement built at plot {plot_id}")
                self.game.check_victory()
            else:
                print("Invalid: check resources, distance, and connections")
        else:
            print(f"Unknown build type: {build_type}")
    
    def _cmd_upgrade(self, args: List[str]):
        """Upgrade to city command"""
        if len(args) < 1:
            print("Usage: !upgrade [plot]")
            return
        
        if not args[0].isdigit():
            print("Invalid plot number")
            return
        
        plot_id = int(args[0])
        if plot_id not in self.game.board.plots:
            print(f"Plot {plot_id} doesn't exist")
            return
        
        current = self.game.get_current_player()
        plot = self.game.board.plots[plot_id]
        
        if self.game.build_city(current, plot):
            if current.id != self.user_player_id:
                self.known_resources[current.id][Resource.WHEAT] -= 2
                self.known_resources[current.id][Resource.ORE] -= 3
            print(f"Upgraded to city at plot {plot_id}")
            self.game.check_victory()
        else:
            print("Invalid: check ownership and resources")
    
    def _cmd_buy_dev(self, card_type: str):
        """Buy development card command"""
        current = self.game.get_current_player()
        
        actual_type = self.game.buy_development_card(current)
        if actual_type:
            if current.id != self.user_player_id:
                self.known_resources[current.id][Resource.WOOL] -= 1
                self.known_resources[current.id][Resource.WHEAT] -= 1
                self.known_resources[current.id][Resource.ORE] -= 1
                self.known_dev_cards[current.id] += 1
                
                # Add mystery if unknown
                if card_type == "unknown":
                    # Calculate probabilities from deck
                    remaining = self.game.development_deck.cards_remaining()
                    if remaining > 0:
                        probs = {
                            "knight": 0.56,  # Approximate
                            "victory_point": 0.2,
                            "road_building": 0.08,
                            "invention": 0.08,
                            "monopoly": 0.08
                        }
                        self.mystery_dev_cards[current.id].append(MysteryCard(probs))
            
            print(f"{self.nicknames[current.id]} bought {'unknown' if card_type == 'unknown' else card_type} dev card")
        else:
            print("Invalid: check resources or deck empty")
    
    def _cmd_play_dev(self, card_type: Optional[str]):
        """Play development card command"""
        if not card_type:
            print("Usage: !playDev [card_type]")
            return
        
        current = self.game.get_current_player()
        
        # Find matching card
        card_map = {
            "knight": DevelopmentCardType.KNIGHT,
            "victory_point": DevelopmentCardType.VICTORY_POINT,
            "monopoly": DevelopmentCardType.MONOPOLY,
            "invention": DevelopmentCardType.INVENTION,
            "road_building": DevelopmentCardType.ROAD_BUILDING
        }
        
        if card_type not in card_map:
            print(f"Unknown card type: {card_type}")
            return
        
        dev_type = card_map[card_type]
        
        # Try to play
        played = False
        for i, card in enumerate(current.development_cards):
            if card.card_type == dev_type and not card.has_been_played:
                if self.game.play_development_card(current, i):
                    played = True
                    break
        
        if played:
            print(f"Played {card_type} card")
            
            # Handle special effects
            if card_type == "knight":
                self._handle_knight()
            elif card_type == "monopoly":
                self._handle_monopoly()
            elif card_type == "invention":
                self._handle_invention()
            elif card_type == "road_building":
                current.free_roads_remaining = 2
                print("Can now build 2 free roads")
            
            self.game.check_victory()
        else:
            print("Invalid: don't have card or already played this turn")
    
    def _handle_knight(self):
        """Handle knight card play"""
        current = self.game.get_current_player()
        
        # Move robber
        while True:
            hex_str = input("Move robber to hexagon (1-19): ").strip()
            if hex_str.isdigit():
                hex_id = int(hex_str)
                if 1 <= hex_id <= 19:
                    new_hex = self.game.board.hexagons[hex_id - 1]
                    if new_hex != self.game.board.robber_location:
                        self.game.board.move_robber(new_hex)
                        self._handle_steal(current, new_hex)
                        break
    
    def _handle_monopoly(self):
        """Handle monopoly card play"""
        current = self.game.get_current_player()
        
        res_str = input("Which resource to monopolize? ").strip().lower()
        resource = self._parse_resource(res_str)
        
        if resource:
            total = 0
            for p in self.game.players:
                if p != current:
                    amt = p.resources[resource]
                    p.resources[resource] = 0
                    total += amt
                    
                    if p.id != self.user_player_id:
                        self.known_resources[p.id][resource] = 0
            
            current.resources[resource] += total
            if current.id != self.user_player_id:
                self.known_resources[current.id][resource] += total
            
            print(f"Collected {total} {resource.value}")
    
    def _handle_invention(self):
        """Handle invention/year of plenty card"""
        current = self.game.get_current_player()
        
        res1_str = input("First resource: ").strip().lower()
        res2_str = input("Second resource: ").strip().lower()
        
        res1 = self._parse_resource(res1_str)
        res2 = self._parse_resource(res2_str)
        
        if res1 and res2:
            if self.game.bank.resources[res1] > 0:
                current.resources[res1] += 1
                self.game.bank.resources[res1] -= 1
                if current.id != self.user_player_id:
                    self.known_resources[current.id][res1] += 1
            
            if self.game.bank.resources[res2] > 0:
                current.resources[res2] += 1
                self.game.bank.resources[res2] -= 1
                if current.id != self.user_player_id:
                    self.known_resources[current.id][res2] += 1
            
            print(f"Took {res1.value} and {res2.value}")
    
    def _cmd_victory_points(self, player_str: Optional[str]):
        """Show victory points command"""
        if player_str:
            player = self._get_player_by_name(player_str)
            if not player:
                print(f"Unknown player: {player_str}")
                return
        else:
            player = self.game.get_current_player()
        
        vp = player.calculate_victory_points()
        print(f"{self.nicknames[player.id]}: {vp} Victory Points")
        
        # Breakdown
        settlements = len(player.settlements)
        cities = len(player.cities)
        
        if settlements > 0:
            print(f"  Settlements: {settlements} VP")
        if cities > 0:
            print(f"  Cities: {cities * 2} VP")
        if player.victory_point_cards_played > 0:
            print(f"  Victory cards: {player.victory_point_cards_played} VP")
        if player.has_largest_army:
            print(f"  Largest Army: 2 VP ({player.knights_played} knights)")
        if player.has_longest_road:
            road_len = self.game.board.get_longest_road(player)
            print(f"  Longest Road: 2 VP ({road_len} segments)")
    
    def _cmd_find(self, what: Optional[str]):
        """Find achievements command"""
        if not what:
            print("Usage: !find largeArmy OR !find longRoad")
            return
        
        what = what.lower()
        
        if what == "largearmy":
            holder = None
            for p in self.game.players:
                if p.has_largest_army:
                    holder = p
                    break
            
            if holder:
                print(f"Largest Army: {self.nicknames[holder.id]} ({holder.knights_played} knights)")
            else:
                print("Largest Army: nobody (need 3+ knights)")
        
        elif what == "longroad":
            holder = None
            for p in self.game.players:
                if p.has_longest_road:
                    holder = p
                    break
            
            if holder:
                length = self.game.board.get_longest_road(holder)
                print(f"Longest Road: {self.nicknames[holder.id]} ({length} segments)")
            else:
                print("Longest Road: nobody (need 5+ segments)")
        else:
            print(f"Unknown: {what}")
    
    def _cmd_board(self):
        """Show board state command"""
        print("\n=== BOARD STATE ===")
        
        for i, p in enumerate(self.game.players, 1):
            print(f"\n{self.nicknames[i]}:")
            
            # Settlements
            settlements = []
            for plot_id, plot in self.game.board.plots.items():
                if plot.building and isinstance(plot.building, Settlement):
                    if plot.building.player.id == i:
                        settlements.append(plot_id)
            
            if settlements:
                print(f"  Settlements: {', '.join(map(str, settlements))}")
            
            # Cities
            cities = []
            for plot_id, plot in self.game.board.plots.items():
                if plot.building and isinstance(plot.building, City):
                    if plot.building.player.id == i:
                        cities.append(plot_id)
            
            if cities:
                print(f"  Cities: {', '.join(map(str, cities))}")
            
            # Roads
            roads = len(p.roads)
            if roads > 0:
                print(f"  Roads: {roads} built")
        
        print(f"\nRobber: Hexagon {self.game.board.robber_location}")
    
    def _cmd_ports(self, player_str: Optional[str]):
        """Show ports command"""
        if player_str:
            player = self._get_player_by_name(player_str)
            if not player:
                print(f"Unknown player: {player_str}")
                return
        else:
            player = self.game.get_current_player()
        
        ports = player.get_accessible_ports()
        if ports:
            print(f"{self.nicknames[player.id]}'s ports:")
            for port in ports:
                print(f"  - {port.port_type.value}")
        else:
            print(f"{self.nicknames[player.id]} has no ports")
    
    def _cmd_history(self):
        """Show command history"""
        print("\n=== COMMAND HISTORY (last 20) ===")
        for cmd in self.command_history[-20:]:
            print(f"  {cmd}")
        print()
    
    def _stack_mysteries(self):
        """Stack identical mystery cards"""
        for player_id in range(1, 5):
            # Stack resource mysteries
            if player_id in self.mystery_resources:
                stacked = []
                counts = {}
                
                for mystery in self.mystery_resources[player_id]:
                    display = mystery.get_display()
                    if display not in counts:
                        counts[display] = 0
                        stacked.append(mystery)
                    counts[display] += 1
                
                self.mystery_resources[player_id] = stacked
            
            # Stack dev mysteries
            if player_id in self.mystery_dev_cards:
                stacked = []
                counts = {}
                
                for mystery in self.mystery_dev_cards[player_id]:
                    display = mystery.get_display()
                    if display not in counts:
                        counts[display] = 0
                        stacked.append(mystery)
                    counts[display] += 1
                
                self.mystery_dev_cards[player_id] = stacked
    
    def _get_player_by_name(self, name: str) -> Optional[Player]:
        """Get player by name or number"""
        if name.isdigit():
            num = int(name)
            if 1 <= num <= 4:
                return self.game.players[num - 1]
        else:
            for pid, nick in self.nicknames.items():
                if nick.lower() == name.lower():
                    return self.game.players[pid - 1]
        return None
    
    def _parse_resource(self, res_str: str) -> Optional[Resource]:
        """Parse a resource string"""
        for r in Resource:
            if r.value == res_str:
                return r
        return None
    
    def _parse_resources(self, res_str: str) -> Dict[Resource, int]:
        """Parse resources string like '3_wool_2_ore'"""
        result = {r: 0 for r in Resource}
        parts = res_str.split('_')
        
        i = 0
        while i < len(parts) - 1:
            if parts[i].isdigit():
                amt = int(parts[i])
                res = self._parse_resource(parts[i + 1])
                if res:
                    result[res] = amt
                i += 2
            else:
                i += 1
        
        return result