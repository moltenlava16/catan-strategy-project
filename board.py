"""
Board-related classes for Settlers of Catan
"""
from typing import Optional, List, Set, Dict, Tuple, TYPE_CHECKING
from models import Resource, Terrain, PortType
import random

if TYPE_CHECKING:
    from buildings import Building, Settlement, City, Road
    from player import Player


class Plot:
    """Represents a vertex/corner where settlements and cities can be built"""
    _id_counter = 0
    
    def __init__(self):
        Plot._id_counter += 1
        self.id = Plot._id_counter
        self.building: Optional['Building'] = None
        self.adjacent_hexagons: Set['Hexagon'] = set()
        self.adjacent_paths: Set['Path'] = set()
        self.adjacent_plots: Set['Plot'] = set()  # Plots connected by a single path
        self.port: Optional['Port'] = None
    
    def is_occupied(self) -> bool:
        return self.building is not None
    
    def has_adjacent_settlement(self) -> bool:
        """Check if any adjacent plot has a settlement/city"""
        for adj_plot in self.adjacent_plots:
            if adj_plot.is_occupied():
                return True
        return False
    
    def __repr__(self):
        return f"Plot({self.id})"


class Path:
    """Represents an edge where roads can be built"""
    _id_counter = 0
    
    def __init__(self, plot1: Plot, plot2: Plot):
        Path._id_counter += 1
        self.id = Path._id_counter
        self.plots: Tuple[Plot, Plot] = (plot1, plot2)
        self.road: Optional['Road'] = None
        self.adjacent_hexagons: Set['Hexagon'] = set()
        
        # Register this path with its plots
        plot1.adjacent_paths.add(self)
        plot2.adjacent_paths.add(self)
        
        # Register plots as adjacent to each other
        plot1.adjacent_plots.add(plot2)
        plot2.adjacent_plots.add(plot1)
    
    def is_occupied(self) -> bool:
        return self.road is not None
    
    def get_other_plot(self, plot: Plot) -> Optional[Plot]:
        """Given one plot, return the other plot on this path"""
        if plot == self.plots[0]:
            return self.plots[1]
        elif plot == self.plots[1]:
            return self.plots[0]
        return None
    
    def __repr__(self):
        return f"Path({self.id}: {self.plots[0].id}-{self.plots[1].id})"


class Hexagon:
    """Represents a hexagon tile on the board"""
    
    def __init__(self, hex_id: int):
        self.id = hex_id
        self.terrain: Optional[Terrain] = None
        self.roll_value: Optional[int] = None
        self.has_robber: bool = False
        self.plots: List[Plot] = []  # 6 plots, indexed 0-5
        self.paths: List[Path] = []  # 6 paths connecting the plots
    
    def set_terrain(self, terrain: Terrain):
        self.terrain = terrain
    
    def set_roll_value(self, value: Optional[int]):
        if self.terrain != Terrain.DESERT:
            self.roll_value = value
    
    def get_resource(self) -> Optional[Resource]:
        """Get the resource this hexagon produces"""
        if self.terrain:
            return self.terrain.resource
        return None
    
    def __repr__(self):
        return f"Hexagon({self.id}, {self.terrain.terrain_name if self.terrain else 'None'}, roll={self.roll_value})"


class Port:
    """Represents a trading port on the board"""
    
    def __init__(self, port_type: PortType, plots: List[Plot]):
        self.port_type = port_type
        self.plots = plots
        
        # Register this port with its plots
        for plot in plots:
            plot.port = self
    
    def get_trade_ratio(self, resource: Resource) -> Optional[Tuple[int, int]]:
        """Returns (give, receive) ratio for trading the specified resource"""
        if self.port_type == PortType.THREE_ANY_TO_ONE:
            return (3, 1)
        elif self.port_type.value.startswith("2_"):
            # Check if this is the matching resource for 2:1 trade
            resource_name = self.port_type.value.split("_")[1]
            if resource.value == resource_name:
                return (2, 1)
        return None
    
    def __repr__(self):
        return f"Port({self.port_type.value})"


class Board:
    """Represents the game board with all hexagons, plots, and paths"""
    
    def __init__(self):
        self.hexagons: List[Hexagon] = []
        self.plots: Dict[int, Plot] = {}
        self.paths: Dict[int, Path] = {}
        self.ports: List[Port] = []
        self.robber_location: Optional[Hexagon] = None
        
        self._create_board_structure()
        self._create_ports()
    
    def _create_board_structure(self):
        """Creates the hexagon layout with shared plots and paths"""
        # Create 19 hexagons
        self.hexagons = [Hexagon(i) for i in range(1, 20)]
        
        # Create a dictionary to look up hexagons by ID
        hex_dict = {h.id: h for h in self.hexagons}
        
        # First, create all plots for each hexagon independently
        for hex in self.hexagons:
            hex.plots = [None] * 6  # Will be filled with shared plots
            hex.paths = []
        
        # Create all unique plots
        plot_counter = 0
        all_plots_map = {}  # Map (hex_id, vertex_index) to plot
        
        # Define the standard Catan board hex adjacencies
        # Each hex shares edges (and thus vertices) with specific neighbors
        # Format: hex_id -> [(neighbor_id, edge_mapping), ...]
        # edge_mapping is (my_edge -> neighbor_edge)
        hex_adjacencies = {
            1: [(2, {2: 5}), (5, {3: 0, 4: 1}), (4, {4: 0, 5: 1})],
            2: [(1, {5: 2}), (3, {2: 5}), (6, {3: 0, 4: 1}), (5, {4: 0, 5: 1})],
            3: [(2, {5: 2}), (7, {3: 0, 4: 1}), (6, {4: 0, 5: 1})],
            4: [(1, {0: 4, 1: 5}), (5, {2: 5}), (9, {3: 0, 4: 1}), (8, {4: 0, 5: 1})],
            5: [(1, {0: 3, 1: 4}), (2, {0: 4, 1: 5}), (4, {5: 2}), (6, {2: 5}), (10, {3: 0, 4: 1}), (9, {4: 0, 5: 1})],
            6: [(2, {0: 3, 1: 4}), (3, {0: 4, 1: 5}), (5, {5: 2}), (7, {2: 5}), (11, {3: 0, 4: 1}), (10, {4: 0, 5: 1})],
            7: [(3, {0: 3, 1: 4}), (6, {5: 2}), (12, {3: 0, 4: 1}), (11, {4: 0, 5: 1})],
            8: [(4, {0: 4, 1: 5}), (9, {2: 5}), (13, {3: 0, 4: 1})],
            9: [(4, {0: 3, 1: 4}), (5, {0: 4, 1: 5}), (8, {5: 2}), (10, {2: 5}), (14, {3: 0, 4: 1}), (13, {4: 0, 5: 1})],
            10: [(5, {0: 3, 1: 4}), (6, {0: 4, 1: 5}), (9, {5: 2}), (11, {2: 5}), (15, {3: 0, 4: 1}), (14, {4: 0, 5: 1})],
            11: [(6, {0: 3, 1: 4}), (7, {0: 4, 1: 5}), (10, {5: 2}), (12, {2: 5}), (16, {3: 0, 4: 1}), (15, {4: 0, 5: 1})],
            12: [(7, {0: 3, 1: 4}), (11, {5: 2}), (16, {4: 0, 5: 1})],
            13: [(8, {0: 3, 1: 4}), (9, {0: 4, 1: 5}), (14, {2: 5}), (17, {3: 0, 4: 1})],
            14: [(9, {0: 3, 1: 4}), (10, {0: 4, 1: 5}), (13, {5: 2}), (15, {2: 5}), (18, {3: 0, 4: 1}), (17, {4: 0, 5: 1})],
            15: [(10, {0: 3, 1: 4}), (11, {0: 4, 1: 5}), (14, {5: 2}), (16, {2: 5}), (19, {3: 0, 4: 1}), (18, {4: 0, 5: 1})],
            16: [(11, {0: 3, 1: 4}), (12, {0: 4, 1: 5}), (15, {5: 2}), (19, {4: 0, 5: 1})],
            17: [(13, {0: 3, 1: 4}), (14, {0: 4, 1: 5}), (18, {2: 5})],
            18: [(14, {0: 3, 1: 4}), (15, {0: 4, 1: 5}), (17, {5: 2}), (19, {2: 5})],
            19: [(15, {0: 3, 1: 4}), (16, {0: 4, 1: 5}), (18, {5: 2})]
        }
        
        # Create plots - reuse shared ones based on adjacencies
        for hex_id in range(1, 20):
            hex = hex_dict[hex_id]
            
            for vertex in range(6):
                key = (hex_id, vertex)
                
                if key not in all_plots_map:
                    # Check if this vertex is shared with a neighbor
                    shared_plot = None
                    
                    if hex_id in hex_adjacencies:
                        for neighbor_id, edge_map in hex_adjacencies[hex_id]:
                            if neighbor_id < hex_id:  # Only check already processed hexes
                                for my_edge, neighbor_edge in edge_map.items():
                                    # Edge connects two vertices
                                    my_v1 = my_edge
                                    my_v2 = (my_edge + 1) % 6
                                    neighbor_v1 = neighbor_edge
                                    neighbor_v2 = (neighbor_edge + 1) % 6
                                    
                                    # Check if current vertex matches
                                    if vertex == my_v1:
                                        neighbor_key = (neighbor_id, neighbor_v2)
                                        if neighbor_key in all_plots_map:
                                            shared_plot = all_plots_map[neighbor_key]
                                            break
                                    elif vertex == my_v2:
                                        neighbor_key = (neighbor_id, neighbor_v1)
                                        if neighbor_key in all_plots_map:
                                            shared_plot = all_plots_map[neighbor_key]
                                            break
                                
                                if shared_plot:
                                    break
                    
                    if shared_plot:
                        all_plots_map[key] = shared_plot
                        shared_plot.adjacent_hexagons.add(hex)
                    else:
                        # Create new plot
                        plot = Plot()
                        all_plots_map[key] = plot
                        plot.adjacent_hexagons.add(hex)
                        self.plots[plot.id] = plot
                
                hex.plots[vertex] = all_plots_map[key]
        
        # Create paths between adjacent plots for each hexagon
        for hex in self.hexagons:
            for i in range(6):
                next_i = (i + 1) % 6
                plot1, plot2 = hex.plots[i], hex.plots[next_i]
                
                # Check if path already exists between these plots
                existing_path = None
                for path in plot1.adjacent_paths:
                    if plot2 in path.plots:
                        existing_path = path
                        break
                
                if existing_path:
                    hex.paths.append(existing_path)
                    existing_path.adjacent_hexagons.add(hex)
                else:
                    path = Path(plot1, plot2)
                    hex.paths.append(path)
                    self.paths[path.id] = path
                    path.adjacent_hexagons.add(hex)
    
    def _create_ports(self):
        """Creates the 9 ports at specified locations"""
        port_configs = [
            (PortType.THREE_ANY_TO_ONE, 1, [0, 5]),  # hex_1, plots 1 and 6
            (PortType.TWO_WHEAT_TO_ONE, 2, [0, 1]),  # hex_2, plots 1 and 2
            (PortType.TWO_ORE_TO_ONE, 7, [0, 1]),    # hex_7, plots 1 and 2
            (PortType.TWO_WOOD_TO_ONE, 4, [4, 5]),   # hex_4, plots 5 and 6
            (PortType.THREE_ANY_TO_ONE, 12, [1, 2]), # hex_12, plots 2 and 3
            (PortType.TWO_BRICK_TO_ONE, 13, [4, 5]), # hex_13, plots 5 and 6
            (PortType.TWO_WOOL_TO_ONE, 16, [2, 3]),  # hex_16, plots 3 and 4
            (PortType.THREE_ANY_TO_ONE, 17, [3, 4]), # hex_17, plots 4 and 5
            (PortType.THREE_ANY_TO_ONE, 18, [2, 3]), # hex_18, plots 3 and 4
        ]
        
        for port_type, hex_id, plot_indices in port_configs:
            hex = self.hexagons[hex_id - 1]
            port_plots = [hex.plots[i] for i in plot_indices]
            port = Port(port_type, port_plots)
            self.ports.append(port)
    
    def setup_random_board(self):
        """Randomly assigns terrains and roll values to hexagons"""
        # Create terrain distribution
        terrains = (
            [Terrain.HILLS] * 3 +
            [Terrain.MOUNTAINS] * 3 +
            [Terrain.FORESTS] * 4 +
            [Terrain.PASTURES] * 4 +
            [Terrain.FIELDS] * 4 +
            [Terrain.DESERT] * 1
        )
        random.shuffle(terrains)
        
        # Assign terrains to hexagons
        for hex, terrain in zip(self.hexagons, terrains):
            hex.set_terrain(terrain)
            if terrain == Terrain.DESERT:
                hex.has_robber = True
                self.robber_location = hex
        
        # Create roll value distribution (no 7)
        roll_values = (
            [2] * 1 +
            [3] * 2 +
            [4] * 2 +
            [5] * 2 +
            [6] * 2 +
            [8] * 2 +
            [9] * 2 +
            [10] * 2 +
            [11] * 2 +
            [12] * 1
        )
        random.shuffle(roll_values)
        
        # Assign roll values to non-desert hexagons
        value_index = 0
        for hex in self.hexagons:
            if hex.terrain != Terrain.DESERT:
                hex.set_roll_value(roll_values[value_index])
                value_index += 1
    
    def move_robber(self, new_hex: Hexagon):
        """Moves the robber to a new hexagon"""
        if self.robber_location:
            self.robber_location.has_robber = False
        new_hex.has_robber = True
        self.robber_location = new_hex
    
    def get_plots_for_hex_roll(self, roll_value: int) -> List[Tuple[Plot, Hexagon]]:
        """Get all plots that should receive resources for a dice roll"""
        plots_and_hexes = []
        for hex in self.hexagons:
            if hex.roll_value == roll_value and not hex.has_robber:
                for plot in hex.plots:
                    if plot.building:
                        plots_and_hexes.append((plot, hex))
        return plots_and_hexes
    
    def can_build_settlement(self, player: 'Player', plot: Plot, 
                           initial_placement: bool = False) -> bool:
        """Check if a settlement can be built at the specified plot"""
        # Check if plot is occupied
        if plot.is_occupied():
            return False
        
        # Check if player has settlements available
        if player.available_settlements <= 0:
            return False
        
        # Check two-paths-apart rule (no adjacent settlements)
        if plot.has_adjacent_settlement():
            return False
        
        # If not initial placement, must be connected to player's road
        if not initial_placement:
            connected_to_road = False
            for path in plot.adjacent_paths:
                if path.road and path.road.player == player:
                    connected_to_road = True
                    break
            if not connected_to_road:
                return False
        
        return True
    
    def can_build_city(self, player: 'Player', plot: Plot) -> bool:
        """Check if a settlement can be upgraded to a city"""
        from buildings import Settlement
        
        if not plot.building or not isinstance(plot.building, Settlement):
            return False
        if plot.building.player != player:
            return False
        if player.available_cities <= 0:
            return False
        return True
    
    def can_build_road(self, player: 'Player', path: Path, 
                      initial_placement: bool = False) -> bool:
        """Check if a road can be built on the specified path"""
        if path.is_occupied():
            return False
        if player.available_roads <= 0:
            return False
        
        # Must connect to player's settlement, city, or road
        has_connection = False
        
        # Check for settlements/cities at either plot
        for plot in path.plots:
            if plot.building and plot.building.player == player:
                has_connection = True
                break
        
        # Check for adjacent roads (unless blocked by opponent's settlement)
        if not has_connection:
            for plot in path.plots:
                # Check if this plot has an opponent's settlement/city blocking
                if plot.building and plot.building.player != player:
                    continue
                    
                for adj_path in plot.adjacent_paths:
                    if adj_path != path and adj_path.road and adj_path.road.player == player:
                        has_connection = True
                        break
        
        return has_connection
    
    def get_longest_road(self, player: 'Player') -> int:
        """Calculate the longest continuous road for a player"""
        if not player.roads:
            return 0
        
        max_length = 0
        visited_global = set()
        
        # Try starting from each road
        for road in player.roads:
            if road.path in visited_global:
                continue
            
            # DFS from this road
            visited = set()
            length = self._dfs_road_length(player, road.path, None, visited)
            max_length = max(max_length, length)
            visited_global.update(visited)
        
        return max_length
    
    def _dfs_road_length(self, player: 'Player', current_path: Path, 
                        came_from: Optional[Path], visited: Set[Path]) -> int:
        """DFS helper to find longest road from current position"""
        if current_path in visited:
            return 0
        if not current_path.road or current_path.road.player != player:
            return 0
        
        visited.add(current_path)
        max_length = 1
        
        # Explore from both ends of the current path
        for plot in current_path.plots:
            # Check if opponent's settlement/city blocks this route
            if plot.building and plot.building.player != player:
                continue
            
            # Explore adjacent paths
            for adj_path in plot.adjacent_paths:
                if adj_path != current_path and adj_path != came_from:
                    length = 1 + self._dfs_road_length(player, adj_path, current_path, visited.copy())
                    max_length = max(max_length, length)
        
        return max_length
    
    def __repr__(self):
        return f"Board({len(self.hexagons)} hexagons, {len(self.plots)} plots, {len(self.paths)} paths)"