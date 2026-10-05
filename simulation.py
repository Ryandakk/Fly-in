from parsing import Graph, Zone
from algorithm import Dijk, ZONE_COST

class Drone():
    def __init__(self, id: int, path_index: int,
                 current_path: list[str]) -> None:
        self.id = id
        self.path_index = path_index
        self.current_path = current_path
        self.alternate_path = None
        self.in_transit = False
        self.transit_turns = 0


class Scheduler():
    def __init__(self, nb_drones: int, drones: list[Drone], graph: Graph) -> None:
        self.drones = drones
        self.graph = graph

    def sort_connections(self, a: str, b: str) -> tuple[str, str]:
        a, b = sorted((a, b))
        return (a, b)

    def next_link(self, drone: Drone) -> tuple[str, str]:
        a = drone.current_path[drone.path_index]
        b = drone.current_path[drone.path_index + 1]
        return self.sort_connections(a, b)


    def run(self) -> list[list[str]]:
        drones = self.drones
        zone_capacity: dict [str, int]= {}
        zone_occupancy: dict [str, int]= {}
        connection_capacity: dict[tuple[str, str], int] = {}

        for name, zone in self.graph.zones.items():
            zone_capacity[name]= zone.max_drones
        for name in self.graph.zones:
            zone_occupancy[name] = 0

        start = self.graph.start_zone.name
        zone_occupancy[start] = len(drones)

        for connection, capacity in self.graph.connections.items():
            connection_capacity[connection] = capacity
        
        turns: list[list[str]] = []
        self.find_paths()
        while True:
            all_finished = True
            this_turn: list[str] = []
            connections_occupancy: dict[tuple[str, str], int] = {}

            for drone in drones:
                if drone.in_transit:
                    all_finished = False
                    next_connection = self.next_link(drone)
                    connections_occupancy[next_connection] = connections_occupancy.get(next_connection, 0) + 1
                    drone.transit_turns -= 1
                    if drone.transit_turns == 0:
                        drone.in_transit = False
                        next_zone = drone.current_path[drone.path_index + 1]
                        drone.path_index += 1
                        this_turn.append(
                            f"D{drone.id}-{next_zone}"
                        )
                    continue

                if drone.path_index == len(drone.current_path) - 1:
                    continue
                all_finished = False
                current_zone = drone.current_path[drone.path_index]
                next_zone = drone.current_path[drone.path_index + 1]
                destination = self.graph.zones[next_zone]
                unlimited = destination.is_start or destination.is_end

                if not unlimited and (zone_occupancy[next_zone] >= zone_capacity[next_zone]):
                    if drone.alternate_path is not None:
                        drone.current_path = drone.alternate_path
                    continue
                connection = self.sort_connections(current_zone, next_zone)
                if connections_occupancy.get(connection, 0) >= connection_capacity[connection]:
                    continue
                connections_occupancy[connection] = connections_occupancy.get(connection, 0) + 1
                if destination.zone == "restricted":
                    drone.in_transit = True
                    drone.transit_turns = ZONE_COST["restricted"][0]
                    drone.transit_turns -= 1
                    zone_occupancy[current_zone] -= 1
                    zone_occupancy[next_zone] += 1
                    this_turn.append(
                        f"D{drone.id}-{current_zone}-{next_zone}"
                    )
                    continue
                zone_occupancy[current_zone] -= 1
                zone_occupancy[next_zone] += 1
                drone.path_index += 1
                this_turn.append(f"D{drone.id}-{next_zone}")
            if this_turn:
                turns.append(this_turn)
            if all_finished:
                break
        return turns

    def find_paths(self) -> None:
        drones = self.drones
        algo = Dijk()
        for drone in drones:
            dronepath = drone.current_path
            start = drone.current_path[0]
            end = drone.current_path[len(dronepath) - 1]
            connection = self.sort_connections(dronepath[0], dronepath[1])
            capacity = self.graph.connections[connection]
            del self.graph.connections[connection]
            try:
                alternate_path = algo.cheapest_path(self.graph, start, end)
                drone.alternate_path = alternate_path
            except ValueError:
                drone.alternate_path = None
            finally:
                self.graph.connections[connection] = capacity

            

            