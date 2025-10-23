"""
Main entry point for Settlers of Catan game
"""
import random
from game import Game
from models import Resource


def demo_setup_phase(game: Game):
    """Demo the setup phase with automatic placement"""
    print("\n=== SETUP PHASE DEMO ===")
    
    # Each player places 2 settlements and 2 roads
    while game.phase == "setup":
        player = game.get_current_player()
        
        # Find a valid plot for settlement
        valid_plots = []
        for plot in game.board.plots.values():
            if game.board.can_build_settlement(player, plot, initial_placement=True):
                valid_plots.append(plot)
        
        if valid_plots:
            # Choose a random valid plot
            chosen_plot = random.choice(valid_plots)
            if game.place_initial_settlement(player, chosen_plot):
                print(f"Player {player.id} placed settlement at Plot {chosen_plot.id}")
                
                # Find valid paths for road (must connect to settlement)
                valid_paths = []
                for path in chosen_plot.adjacent_paths:
                    if game.board.can_build_road(player, path, initial_placement=True):
                        valid_paths.append(path)
                
                if valid_paths:
                    chosen_path = random.choice(valid_paths)
                    if game.place_initial_road(player, chosen_path):
                        print(f"Player {player.id} placed road on Path {chosen_path.id}")
    
    # Show starting resources
    print("\nStarting resources:")
    for player in game.players:
        resources_str = ", ".join([f"{r.value}: {amt}" for r, amt in player.resources.items() if amt > 0])
        if resources_str:
            print(f"  Player {player.id}: {resources_str}")
        else:
            print(f"  Player {player.id}: no resources")


def demo_main_game(game: Game, num_turns: int = 10):
    """Demo the main game phase"""
    print("\n=== MAIN GAME DEMO ===")
    
    for turn in range(num_turns):
        if game.phase != "main":
            break
        
        player = game.get_current_player()
        print(f"\n--- Turn {turn + 1}: Player {player.id} ---")
        
        # Roll dice
        die1, die2, total = game.start_turn()
        
        if total == 7:
            # Demo robber movement (move to random hex)
            valid_hexes = [h for h in game.board.hexagons if h != game.board.robber_location]
            new_hex = random.choice(valid_hexes)
            
            # Find potential victims
            victims = set()
            for plot in new_hex.plots:
                if plot.building and plot.building.player != player:
                    victims.add(plot.building.player)
            
            victim = random.choice(list(victims)) if victims else None
            game.move_robber_action(player, new_hex, victim)
            print(f"Player {player.id} moved robber to Hex {new_hex.id}")
        
        # Try to build something if possible
        built_something = False
        
        # Try to buy development card first (25% chance if affordable)
        if player.can_afford_development_card() and random.random() < 0.25:
            card_type = game.buy_development_card(player)
            if card_type:
                print(f"Player {player.id} bought a {card_type.value} card")
                built_something = True
        
        # Try to build city if possible (high priority)
        if not built_something and player.can_afford_city():
            for settlement in player.settlements[:]:  # Copy list since we modify it
                if game.build_city(player, settlement.plot):
                    print(f"Player {player.id} upgraded settlement to city at Plot {settlement.plot.id}")
                    built_something = True
                    break
        
        # Try to build settlement if possible
        if not built_something and player.can_afford_settlement():
            # Find valid plots connected to roads
            valid_plots = []
            for plot in game.board.plots.values():
                if game.board.can_build_settlement(player, plot):
                    valid_plots.append(plot)
            
            if valid_plots:
                chosen_plot = random.choice(valid_plots)
                if game.build_settlement(player, chosen_plot):
                    print(f"Player {player.id} built settlement at Plot {chosen_plot.id}")
                    built_something = True
        
        # Try to build road if possible
        if not built_something and player.can_afford_road():
            valid_paths = []
            for path in game.board.paths.values():
                if game.board.can_build_road(player, path):
                    valid_paths.append(path)
            
            if valid_paths and random.random() < 0.5:  # 50% chance to build road
                chosen_path = random.choice(valid_paths[:5])  # Choose from first 5 to keep it reasonable
                if game.build_road(player, chosen_path):
                    print(f"Player {player.id} built road on Path {chosen_path.id}")
                    built_something = True
        
        # Try bank trade if have too many of one resource (simplified demo)
        for resource in Resource:
            if player.resources[resource] >= 4:
                # Trade for a random other resource
                other_resources = [r for r in Resource if r != resource]
                target_resource = random.choice(other_resources)
                if game.bank_trade(player, resource, target_resource):
                    ratio = player.get_best_trade_ratio(resource)
                    print(f"Player {player.id} traded {ratio[0]} {resource.value} for 1 {target_resource.value}")
                    break
        
        # Play a development card if available (simplified - just play first available)
        playable_cards = player.get_playable_development_cards(game.turn_number)
        if playable_cards and random.random() < 0.3:  # 30% chance to play a card
            card_index = player.development_cards.index(playable_cards[0])
            if game.play_development_card(player, card_index):
                print(f"Player {player.id} played a {playable_cards[0].card_type.value} card")
        
        # End turn
        game.end_turn()
        
        # Check for winner
        if game.winner:
            break
    
    # Final status
    print(game.get_game_state_summary())


def main():
    """Main function to run the game"""
    print("=" * 60)
    print("SETTLERS OF CATAN - Game Demo")
    print("=" * 60)
    
    # Create and setup game
    game = Game(num_players=4)
    game.setup_game()
    
    # Show initial board state
    print(f"\nBoard created with {len(game.board.hexagons)} hexagons")
    print(f"Desert is at Hexagon {game.board.robber_location}")
    
    # Run setup phase
    demo_setup_phase(game)
    
    # Run main game for demo
    demo_main_game(game, num_turns=20)
    
    # Show final statistics
    if game.winner:
        print(f"\n{'='*60}")
        print(f"CONGRATULATIONS! Player {game.winner.id} has won the game!")
        print(f"Final Victory Points: {game.winner.calculate_victory_points()}")
        print(f"{'='*60}")
    else:
        print("\nGame demo completed (no winner yet)")
        print("\nFinal standings:")
        standings = sorted(game.players, key=lambda p: p.calculate_victory_points(), reverse=True)
        for i, player in enumerate(standings, 1):
            vp = player.calculate_victory_points()
            print(f"  {i}. Player {player.id}: {vp} Victory Points")


if __name__ == "__main__":
    # Set random seed for reproducibility (comment out for random games)
    # random.seed(42)
    
    main()