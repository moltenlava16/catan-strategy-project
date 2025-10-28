# Catan Tracker Mode

## Overview

This is the game state tracker for our Catan project. It helps a player track resources, buildings, and game state while playing a real-life game. 

## Features

### Setup Phase
- **Player Management**: Set nicknames for all 4 players (defaults to "Player X")
- **User Identification**: Identify which player you are for accurate tracking
- **Board Configuration**: Input terrain types and roll values for all 19 hexagons
- **Initial Placement**: Track starting settlements and roads with validation
- **Resource Distribution**: Automatically distribute starting resources

### Game Tracking
- **Resource Management**: Track all resources for all players
- **Mystery Cards**: Probabilistic tracking of unknown resources and development cards
- **Robber Mechanics**: Handle robber movement and resource stealing
- **Development Cards**: Track both known and unknown cards with resolution
- **Building Validation**: Enforce all placement rules and resource costs
- **Victory Points**: Automatic calculation including special achievements

### Mystery Card System
The tracker uses an innovative mystery card system for unknown information:

- **Unknown Steals**: When you don't know what was stolen, creates probability distributions
  - Example: If victim has 2 ore and 1 wool, shows as "⅔ ore | ⅓ wool"
- **Unknown Development Cards**: Tracks probabilities based on remaining bank cards
- **Resolution**: Automatically resolves mysteries when information is revealed
- **Stacking**: Combines identical mystery cards for cleaner display

## Commands

### Resource Commands
- `!resources [player]` - Show resources for a player (includes mystery cards)
- `!trade [player] [give] [receive]` - Record a trade between players
- `!maritimeTrade [give] [receive]` - Record a bank trade

### Building Commands
- `!build road [path]` - Build a road on specified path
- `!build settlement [plot]` - Build a settlement on specified plot
- `!upgrade [plot]` - Upgrade settlement to city

### Development Card Commands
- `!buyDev [type/unknown]` - Buy a development card
- `!playDev [type]` - Play a development card

### Information Commands
- `!vp [player]` - Show victory points
- `!find largeArmy` - Show who has Largest Army
- `!find longRoad` - Show who has Longest Road
- `!board` - Show current board state
- `!ports [player]` - Show accessible ports
- `!whoseTurn` - Show whose turn it is
- `!history` - Show command history

### Control Commands
- `!commands` - Show all available commands
- `!undo` - Undo last command
- `!save [filename]` - Save game state
- `!load [filename]` - Load game state
- `!endTurn` - End current turn

## Resource Format

When entering resources in commands, use underscore-separated format:
- `3_wool_2_wood` = 3 wool and 2 wood
- `4_ore` = 4 ore
- `1_wheat_1_ore_1_wool` = 1 of each

## Usage Example

```bash
# Start tracker mode
python -m catan.main
# Select option 2

# During setup
Enter nickname for Player 1: Alice
Enter nickname for Player 2: Bob
Which player are you? Alice

# During game
> !resources Alice
Alice's resources: brick: 2, wood: 1, wool: 3

> !trade Bob 2_wool 1_ore
Trade completed between Alice and Bob

> !build road 42
Built road at path 42

> !buyDev unknown
Alice bought unknown development card

> !vp Alice
Alice: 5 Victory Points
  Settlements: 2 VP
  Cities: 2 VP
  Longest Road: 2 VP
```

## Rules Enforced

### Building Rules
- Settlements must be 2+ paths apart
- Buildings must connect to existing roads/settlements
- Cities can only upgrade existing settlements
- Resource costs are validated

### Trading Rules
- Cannot trade identical resources (anti-collusion)
- Port ratios are enforced (4:1, 3:1, or 2:1)
- Bank must have resources available

### Development Cards
- Can only play one per turn (except Victory Points)
- Cannot play cards bought same turn (except Victory Points)
- Knight cards count toward Largest Army (3+ required)

### Special Achievements
- **Longest Road**: Minimum 5 continuous segments, no doubling back
- **Largest Army**: Minimum 3 Knight cards played
- Both worth 2 Victory Points

## Mystery Card Examples

### Unknown Resource Steal
```
Player 2 (has 2 ore, 1 wool) is robbed by Player 3
Did you see what was stolen? no

Player 2 resources: ore: 2, wool: 0
  - Mystery losses: -[⅔ ore | ⅓ wool]

Player 3 resources: brick: 1
  + Mystery gains: [⅔ ore | ⅓ wool]
```

### Unknown Development Card
```
Player 2 buys unknown development card

Player 2 dev cards: [56% knight | 20% victory_point | 8% road_building | 8% invention | 8% monopoly]

# After playing a Knight:
Player 2 dev cards: knight (resolved)
```

## Tips

1. **Be Precise**: Plot and path numbers must match the board setup exactly
2. **Track Everything**: The more information you provide, the better the tracking
3. **Use Unknown**: When you don't know something, mark it as "unknown"
4. **Regular Saves**: Use `!save` periodically to preserve game state
5. **Check Victory Points**: Use `!vp` to monitor the race to 10 points

## Limitations

- **GUI**: Currently text-based; visual board coming in future updates
- **Plot/Path Numbering**: Requires manual mapping to physical board
- **Save/Load**: Framework exists but full persistence not implemented
- **Undo**: Limited undo functionality for complex actions

## Future Enhancements

- Visual board representation
- AI assistant for strategy suggestions
- Statistical analysis of game patterns
- Network multiplayer support
- Mobile app integration