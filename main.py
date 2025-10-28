"""
Main entry point for Settlers of Catan game
"""
import random
from game import Game
from models import Resource
from tracker import TrackerMode


def show_menu():
    """Show the main menu"""
    print("\n" + "=" * 60)
    print(" " * 20 + "SETTLERS OF CATAN")
    print("=" * 60)
    print("\nSelect Mode:")
    print("  1. Demo Mode - Watch an automated game")
    print("  2. Tracker Mode - Track a real game as you play")
    print("  3. Exit")
    print()
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        if choice in ['1', '2', '3']:
            return int(choice)
        print("Invalid choice. Please enter 1, 2, or 3.")


def run_demo_mode():
    """Run the automated demo game"""
    print("\n" + "=" * 60)
    print(" " * 15 + "DEMO MODE - Automated Game")
    print("=" * 60)
    
    # Create and setup game
    game = Game(num_players=4)
    game.setup_game()
    
    print(f"\nBoard created with {len(game.board.hexagons)} hexagons")
    print(f"Desert is at Hexagon {game.board.robber_location.id if game.board.robber_location else 'unknown'}")
    
    # Run setup phase
    print("\n=== SETUP PHASE ===")
    demo_setup_phase(game)
    
    # Run main game
    print("\n=== MAIN GAME ===")
    demo_main_game(game, num_turns=20)
    
    # Show results
    show_final_results(game)


def demo_setup_phase(game: Game):
    """Automated setup phase with settlements and roads"""
    placement_count = 0
    
    while game.phase == "setup":
        player = game.get_current_player()
        
        # Find valid settlement locations
        valid_plots = []
        for plot in game.board.plots.values():
            if game.board.can_build_settlement(player, plot, initial_placement=True):
                valid_plots.append(plot)
        
        if not valid_plots:
            print(f"Warning: No valid plots for Player {player.id}")
            break
        
        # Place settlement
        chosen_plot = random.choice(valid_plots)
        if game.place_initial_settlement(player, chosen_plot):
            placement_count += 1
            settlement_num = 1 if placement_count <= 4 else 2
            print(f"Player {player.id} placed settlement #{settlement_num} at Plot {chosen_plot.id}")
            
            # Find valid road locations
            valid_paths = []
            for path in chosen_plot.adjacent_paths:
                if path.road is None:
                    valid_paths.append(path)
            
            if valid_paths:
                chosen_path = random.choice(valid_paths)
                if game.place_initial_road(player, chosen_path):
                    print(f"Player {player.id} placed road at Path {chosen_path.id}")
    
    # Show starting resources
    print("\nStarting resources:")
    for player in game.players:
        resources_list = []
        for resource in Resource:
            if player.resources[resource] > 0:
                resources_list.append(f"{player.resources[resource]} {resource.value}")
        
        if resources_list:
            print(f"  Player {player.id}: {', '.join(resources_list)}")
        else:
            print(f"  Player {player.id}: no resources")


def demo_main_game(game: Game, num_turns: int = 20):
    """Automated main game phase"""
    
    for turn_num in range(1, num_turns + 1):
        if game.phase != "main":
            break
        
        player = game.get_current_player()
        print(f"\n--- Turn {turn_num}: Player {player.id} ---")
        
        # Roll dice
        die1, die2, total = game.start_turn()
        
        # Handle roll
        if total == 7:
            handle_robber_demo(game, player)
        
        # Try some actions
        perform_demo_actions(game, player)
        
        # End turn
        game.end_turn()
        
        # Check for winner
        if game.winner:
            break


def handle_robber_demo(game: Game, player):
    """Handle robber movement in demo"""
    # Move to random hex
    valid_hexes = [h for h in game.board.hexagons if h != game.board.robber_location]
    if valid_hexes:
        new_hex = random.choice(valid_hexes)
        
        # Find victims
        victims = set()
        for plot in new_hex.plots:
            if plot.building and plot.building.player != player:
                victims.add(plot.building.player)
        
        victim = random.choice(list(victims)) if victims else None
        if game.move_robber_action(player, new_hex, victim):
            print(f"Player {player.id} moved robber to Hex {new_hex.id}")
            if victim:
                print(f"  Stole from Player {victim.id}")


def perform_demo_actions(game: Game, player):
    """Perform random actions in demo"""
    # Try to buy development card
    if player.can_afford_development_card() and random.random() < 0.25:
        card_type = game.buy_development_card(player)
        if card_type:
            print(f"Player {player.id} bought a {card_type.value} card")
    
    # Try to build city
    if player.can_afford_city() and player.settlements:
        for settlement in player.settlements[:]:
            if game.build_city(player, settlement.plot):
                print(f"Player {player.id} upgraded to city at Plot {settlement.plot.id}")
                break
    
    # Try to build settlement
    if player.can_afford_settlement():
        valid_plots = []
        for plot in game.board.plots.values():
            if game.board.can_build_settlement(player, plot):
                valid_plots.append(plot)
        
        if valid_plots:
            chosen = random.choice(valid_plots[:3])  # Limit choices
            if game.build_settlement(player, chosen):
                print(f"Player {player.id} built settlement at Plot {chosen.id}")
    
    # Try to build road
    if player.can_afford_road() and random.random() < 0.5:
        valid_paths = []
        for path in game.board.paths.values():
            if game.board.can_build_road(player, path):
                valid_paths.append(path)
        
        if valid_paths:
            chosen = random.choice(valid_paths[:5])  # Limit choices
            if game.build_road(player, chosen):
                print(f"Player {player.id} built road on Path {chosen.id}")
    
    # Try bank trade if too many resources
    for resource in Resource:
        if player.resources[resource] >= 4:
            other_resources = [r for r in Resource if r != resource]
            if other_resources:
                target = random.choice(other_resources)
                if game.bank_trade(player, resource, target):
                    ratio = player.get_best_trade_ratio(resource)
                    print(f"Player {player.id} traded {ratio[0]} {resource.value} for 1 {target.value}")
                    break
    
    # Try to play development card
    playable = player.get_playable_development_cards(game.turn_number)
    if playable and random.random() < 0.3:
        card_index = player.development_cards.index(playable[0])
        if game.play_development_card(player, card_index):
            print(f"Player {player.id} played {playable[0].card_type.value} card")


def show_final_results(game: Game):
    """Show final game results"""
    print("\n" + "=" * 60)
    
    if game.winner:
        print(f"GAME OVER! Player {game.winner.id} wins!")
        print(f"Victory Points: {game.winner.calculate_victory_points()}")
    else:
        print("Game ended without a winner")
        print("\nFinal Standings:")
        standings = sorted(game.players, 
                         key=lambda p: p.calculate_victory_points(), 
                         reverse=True)
        for i, player in enumerate(standings, 1):
            vp = player.calculate_victory_points()
            print(f"  {i}. Player {player.id}: {vp} Victory Points")
    
    print("=" * 60)


def run_tracker_mode():
    """Run the tracker mode for real game tracking"""
    try:
        tracker = TrackerMode()
        tracker.start()
    except KeyboardInterrupt:
        print("\nTracker mode interrupted.")
    except Exception as e:
        print(f"\nError in tracker mode: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print(" " * 18 + "WELCOME TO CATAN")
    print("=" * 60)
    
    while True:
        choice = show_menu()
        
        if choice == 1:
            try:
                run_demo_mode()
            except Exception as e:
                print(f"\nError in demo mode: {e}")
            
            input("\nPress Enter to return to menu...")
        
        elif choice == 2:
            try:
                run_tracker_mode()
            except Exception as e:
                print(f"\nError in tracker mode: {e}")
            
            input("\nPress Enter to return to menu...")
        
        elif choice == 3:
            print("\nThanks for playing Settlers of Catan!")
            print("Goodbye!")
            break


if __name__ == "__main__":
    # Optional: Set seed for reproducible demos
    # random.seed(42)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Goodbye!")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()