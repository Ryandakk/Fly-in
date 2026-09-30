import heapq
from parsing import Graph, Zone

Cost = tuple[int, int]
ZONE_COST: dict[str, Cost] = {
    "normal": (1, 1),
    "priority": (1, 0),
    "restricted": (2, 1)
    }


class Dijk:
    def cheapest_path(self, graph: Graph, start: str, end: str) -> list[str]:
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
            for neighbor, move_cost in self.neighbors(graph, current):
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

    def neighbors(self, graph: Graph, zone_name: str) -> list[tuple[str, Cost]]:
        """Return (neighbor_name, move_cost) pairs reachable from zone_name."""
        result: list[tuple[str, Cost]] = []
        for name1, name2 in graph.connections:
            if zone_name == name1:
                neighbor = name2
            elif zone_name == name2:
                neighbor = name1
            else:
                continue
            neighbor_zone: Zone = graph.zones[neighbor]
            if neighbor_zone.zone == "blocked":
                continue
            result.append((neighbor, ZONE_COST[neighbor_zone.zone]))
        return result
