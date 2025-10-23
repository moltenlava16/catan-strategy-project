# catan-strategy-project
My housemates love Catan. I keep losing in Catan. Let's try to recreate the game and make an assistant that suggests strategy!

## What are the rules of the game?
[Download the rules of the game here](./Catan-Rulebook.pdf)

## Project Structure

```
catan/
├── __init__.py          # Package initialization
├── models.py            # Enums and basic data models
├── board.py             # Board, Hexagon, Plot, Path, Port classes
├── buildings.py         # Settlement, City, Road classes
├── cards.py             # Development card system
├── player.py            # Player class
├── game.py              # Main game logic
└── main.py              # Entry point and demo
```

## Features Implemented

### Core Game Mechanics
- **Board Setup**: 19 hexagons with random terrain and roll value assignment
- **Player Setup**: 4 players with initial settlement/road placement
- **Resource System**: 5 resource types with proper distribution
- **Dice Rolling**: Resource collection based on dice rolls (2-12, excluding 7)
- **Robber**: Activated on rolling 7, blocks resources and allows stealing

### Building System
- **Settlements** (1 VP): Must be 2+ paths apart, connected to roads
- **Cities** (2 VP): Upgrade from settlements
- **Roads**: Must connect to player's network
- **Resource Costs**:
  - Road: 1 brick, 1 wood
  - Settlement: 1 brick, 1 wood, 1 wool, 1 wheat
  - City: 2 wheat, 3 ore

### Development Cards (25 total)
- **Knight** (14): Move robber and steal
- **Victory Point** (5): 1 VP each
- **Monopoly** (2): Take all of one resource from others
- **Road Building** (2): Build 2 roads for free
- **Invention** (2): Take any 2 resources from bank

### Trading System
- **Player Trading**: Exchange resources between players
- **Bank Trading**: 4:1 default ratio
- **Ports**: Improved trading ratios (3:1 any or 2:1 specific)

### Victory Conditions
- **10 Victory Points** to win from:
  - Settlements (1 VP each)
  - Cities (2 VP each)
  - Longest Road (2 VP, minimum 5 segments)
  - Largest Army (2 VP, minimum 3 knights)
  - Victory Point cards (1 VP each)

## Design Principles

### Object-Oriented Programming
1. **Encapsulation**: Each class manages its own state and provides methods to interact with it
2. **Inheritance**: Buildings inherit from base `Building` class
3. **Polymorphism**: Different building types implement `get_resource_multiplier()` and `get_victory_points()`
4. **Abstraction**: Complex game logic abstracted into clear interfaces

### Key Design Decisions
- **Unique Plot/Path Objects**: Shared between hexagons for efficient building validation
- **Resource Scarcity**: Bank limited to 19 of each resource
- **Turn Management**: Clear phase separation (setup, main, end)
- **Victory Checking**: Automatic after relevant actions

## Running the Game

```bash
# Run the demo game
python catan/main.py

# Import and use in your own code
from catan import Game

game = Game(num_players=4)
game.setup_game()
```

## Example Usage

```python
from catan import Game, Resource

# Create and setup game
game = Game(num_players=4)
game.setup_game()

# Setup phase - place initial settlements and roads
player = game.get_current_player()
plot = game.board.plots[1]  # Choose a plot
if game.place_initial_settlement(player, plot):
    # Place road adjacent to settlement
    path = plot.adjacent_paths.pop()
    game.place_initial_road(player, path)

# Main game - roll dice and take actions
die1, die2, total = game.start_turn()

# Build a road
if player.can_afford_road():
    path = game.board.paths[5]
    game.build_road(player, path)

# Trade with bank
game.bank_trade(player, Resource.WOOL, Resource.BRICK)

# End turn
game.end_turn()
```

## Notes

- The current implementation uses simplified board adjacency for demonstration
- In production, exact hexagon adjacency mapping would be needed
- UI interactions (choosing resources, accepting trades) are simulated with random choices
- The demo runs an automated game with random but valid moves

## Currently working on...

- Complete hexagon adjacency mapping for accurate shared plots/paths
- Interactive Game Tracker with optional UI to input player decisions and track game states such as resources and Victory Points
- AI players
- Statistics tracking