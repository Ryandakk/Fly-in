import arcade
from PIL import ImageColor
from parsing import Graph, Zone

ZONE_MARKS: dict[str, str] = {
    "blocked": "X", "restricted": "R", "priority": "P", "normal": "",
}

WINDOW_W = 1280
WINDOW_H = 720
MARGIN = 90
SECONDS_PER_TURN = 0.55


class FlyWindow(arcade.Window):
    """Animate a finished simulation as a 2D map of zones and drones."""
    def __init__(self, graph: Graph, turns: list[list[str]]) -> None:
        super().__init__(WINDOW_W, WINDOW_H)
        self.graph = graph
        self.turns = turns
        xs = [z.x for z in graph.zones.values()]
        ys = [z.y for z in graph.zones.values()]
        self.min_x, self.min_y = min(xs), min(ys)
        self.zoom = min(
            (WINDOW_W - 2 * MARGIN) / max(max(xs) - self.min_x, 1),
            (WINDOW_H - 2 * MARGIN) / max(max(ys) - self.min_y, 1)
        )
        start = None
        for n, z in graph.zones.items():
            if z.is_start:
                start = n
                break
        self.drones = {}
        for i in range (1, graph.nb_drones + 1):
            self.drones[i] = (graph.start_zone.name,)
        self.turn = 0
        self.timer = 0.0
        
        
    def point(self, *names: str) -> tuple[float, float]:
        """Pixel centre of one zone, or the midpoint of two."""
        zones = [self.graph.zones[name] for name in names]
        x = sum(z.x for z in zones) / len(zones)
        y = sum(z.y for z in zones) / len(zones)
        return (MARGIN + (x - self.min_x) * self.zoom,
                MARGIN + (y - self.min_y) * self.zoom)

    def on_draw(self) -> None:
        """Redraw connections, zones and drones."""
        self.clear()
        for zone1, zone2 in self.graph.connections:
            arcade.draw_line(*self.point(zone1), *self.point(zone2),
            ImageColor.getrgb("dimgray"), 2)
        for name, zone in self.graph.zones.items():
            arcade.draw_circle_filled(*self.point(name), 30, ImageColor.getrgb(zone.color))
        for drone_id, location in self.drones.items():
            x, y = self.point(*location)
            offset = (drone_id - 1) * 10
            arcade.draw_circle_filled(x + offset, y, 6, ImageColor.getrgb("grey"))

    def on_update(self, delta_time: float) -> None:
        """Apply one turn each time the timer elapses."""
        self.timer += delta_time
        if self.timer < SECONDS_PER_TURN or self.turn >= len(self.turns):
            return
        for move in self.turns[self.turn]:
            parts = move.split("-")
            self.drones[int(parts[0].replace("Drone", ""))] = tuple(parts[1:])

        self.turn += 1
        self.timer = 0.0

def play(graph: Graph, turns: list[list[str]]) -> None:
    """Open the window and run the animation until it is closed."""
    # FlyWindow(graph, turns)
    arcade.run()