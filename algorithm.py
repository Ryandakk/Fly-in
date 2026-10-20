import heapq
from parsing import Graph, Zone
from typing import Optional

Cost = tuple[int, int]
ZONE_COST: dict[str, Cost] = {
    "normal": (1, 1),
    "priority": (1, 0),
    "restricted": (2, 1)
    }


class Dijk:
    """Dijkstra-based pathfinder that accounts
    for zone-type cost and congestion load."""

    def cheapest_path(self, graph: Graph,
                      start: str,
                      end: str,
                      load: Optional[dict[str, int]] = None) -> list[str]:
        """Return the cheapest sequence of zone names from start to end."""
        best_cost = {start: (0, 0)}
        came_from: dict[str, str] = {}
        queue: list[tuple[Cost, str]] = [((0, 0), start)]
        while queue:
            cost, current = heapq.heappop(queue)
            if cost > best_cost[current]:
                continue
            if current == end:
                break
            for neighbor, move_cost in self.neighbors(graph, current, load):
                new_cost = (cost[0] + move_cost[0], cost[1] + move_cost[1])
                if neighbor in best_cost and new_cost >= best_cost[neighbor]:
                    continue
                best_cost[neighbor] = new_cost
                came_from[neighbor] = current
                heapq.heappush(queue, (new_cost, neighbor))
        if end != start and end not in came_from:
            raise ValueError(f"no route from '{start}' to '{end}'")
        path = [end]
        while path[-1] != start:
            path.append(came_from[path[-1]])
        path.reverse()
        return path

    def neighbors(self, graph: Graph, zone_name: str,
                  load: Optional[
                   dict[str, int]] = None) -> list[tuple[str, Cost]]:
        """Return (neighbor_name, move_cost) pairs reachable from zone_name."""
        result: list[tuple[str, Cost]] = []
        for name in graph.neighbors[zone_name]:
            neighbor_zone: Zone = graph.zones[name]
            if neighbor_zone.zone == "blocked":
                continue
            turns, non_priority = ZONE_COST[neighbor_zone.zone]
            if load is not None:
                turns += load.get(name, 0) // neighbor_zone.max_drones
            result.append((name, (turns, non_priority)))
        return result

    def plan_paths(self, graph: Graph) -> list[list[str]]:
        """Plan one path per drone from start to end,
        spreading drones to ease congestion.

        Each planned path adds load to the zones it crosses,so later drones are
        nudged toward less-congested alternatives.
        """
        assert graph.start_zone is not None
        assert graph.end_zone is not None
        start: str = graph.start_zone.name
        end: str = graph.end_zone.name

        load: dict[str, int] = {}
        collected_paths: list[list[str]] = []

        for _ in range(graph.nb_drones):
            path = self.cheapest_path(graph, start, end, load)
            for zone in path[1:-1]:
                load[zone] = load.get(zone, 0) + 1
            collected_paths.append(path)
        return collected_paths
