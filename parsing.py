import sys
from typing import Optional


class ParseError(Exception):
    def __init__(self, lineno: int, reason: str) -> None:
        self.lineno = lineno
        self.reason = reason
        super().__init__(f"line {lineno}: {reason}")


class Zone:
    def __init__(self, name: str, x: int, y: int, zone: str, color: str, max_drones: int) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.zone = zone
        self.color = color
        self.max_drones = max_drones
        self.is_start = False
        self.is_end = False


class Graph:
    def __init__(self) -> None:
        self.nb_drones = 1
        self.zones: dict[str, Zone] = {}
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None
        self.connections: dict[tuple[str, str], int] = {}


class Parsing:
    def __init__(self, path: str) -> None:
        self.path = path

    def parsing(self) -> Graph:
        graph1 = Graph()
        nb_drones_seen = False

        try:
            with open(self.path, "r") as f:
                for lineno, rawline in enumerate(f, start=1):
                    line = rawline.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("nb_drones"):
                        if nb_drones_seen:
                            raise ParseError(
                                lineno, "duplicate 'nb_drone' line")
                        if ":" not in line:
                            raise ParseError(
                                lineno, "missing ':' after 'nb_drones'")
                        value = line.split(":", 1)[1].strip()
                        try:
                            nb_drones = int(value)
                        except ValueError:
                            raise ParseError(
                                lineno, f"number of drones should be an integer , got {value}")
                        if nb_drones <= 0:
                            raise ParseError(
                                lineno, f"Number MUST be positive")
                        graph1.nb_drones = nb_drones
                        nb_drones_seen = True
                    elif line.startswith("start_hub"):
                        if not nb_drones_seen:
                            raise ParseError(
                                lineno, "nb_drones must be declared before any start/end zone")
                        if graph1.start_zone is not None:
                            raise ParseError(
                                lineno, "there must only be one start zone")
                        if ":" not in line:
                            raise ParseError(
                                lineno, "missing ':' after 'start_hub'")
                        body = line.split(":", 1)[1].strip()
                        if "[" in body:
                            if not body.endswith("]"):
                                raise ParseError(
                                    lineno, ": metablock unterminated")
                            fields_part, meta_part = body.split("[", 1)
                            meta_part = meta_part[:-1]
                        else:
                            fields_part, meta_part = body, ""
                        parts = fields_part.split()
                        if len(parts) != 3:
                            raise ParseError(
                                lineno, f"Format should be '<name> <x> <y>', got '{fields_part}'")
                        name, x_str, y_str = parts
                        if "-" in name:
                            raise ParseError(
                                lineno, f"zone name '{name}' must not contain '-'")
                        if name in graph1.zones:
                            raise ParseError(
                                lineno, f"duplicate zone name '{name}'")
                        try:
                            x, y = int(x_str), int(y_str)
                        except ValueError:
                            raise ParseError(
                                lineno, f"coordinates must be integers, got '{x_str}', '{y_str}'")
                        color, zone_type, max_drones = "none", "normal", 1
                        if meta_part:
                            for tag in meta_part.split():
                                if "=" not in tag:
                                    raise ParseError(
                                        lineno, f"invalid metadata '{tag}'")
                                key, value = tag.split("=", 1)
                                if key == "color":
                                    color = value
                                elif key == "max_drones":
                                    try:
                                        max_drones = int(value)
                                    except ValueError:
                                        raise ParseError(
                                            lineno, f"max_drones must be an int, caught {value}")
                                    if max_drones <= 0:
                                        raise ParseError(
                                            lineno, "max_drones should be postive")
                                elif key == "zone":
                                    if value not in ("normal", "blocked", "restricted", "priority"):
                                        raise ParseError(
                                            lineno, f"invalid zone type '{value}'")
                                    zone_type = value
                                else:
                                    raise ParseError(
                                        lineno, f"unknown metadata key '{key}'")
                        start_zone = Zone(
                            name, x, y, zone_type, color, max_drones)
                        start_zone.is_start = True
                        graph1.start_zone = start_zone
                        graph1.zones[name] = start_zone

                    elif line.startswith("end_hub"):
                        if not nb_drones_seen:
                            raise ParseError(
                                lineno, "nb_drones must be declared before any start/end zone")
                        if graph1.end_zone is not None:
                            raise ParseError(
                                lineno, "There must only be one End hub")
                        if ":" not in line:
                            raise ParseError(
                                lineno, "missing ':' after 'end_hub'")
                        body = line.split(":", 1)[1].strip()
                        if "[" in body:
                            if not body.endswith("]"):
                                raise ParseError(
                                    lineno, "metablock unterminated")
                            fields_part, meta_part = body.split("[", 1)
                            meta_part = meta_part[: -1]
                        else:
                            fields_part, meta_part = body, ""
                        parts = fields_part.split()
                        if len(parts) != 3:
                            raise ParseError(
                                lineno, f"format should be <name> <x> <y>, got '{fields_part}'")
                        name, x_str, y_str = parts
                        if "-" in name:
                            raise ParseError(
                                lineno, f"Zone name cannot contain '-'")
                        if name in graph1.zones:
                            raise ParseError(
                                lineno, f"Cannot have duplicate Zone names")
                        try:
                            x, y = int(x_str), int(y_str)
                        except ValueError:
                            raise ParseError(
                                lineno, f"coordinates must be integers, got {x_str} & {y_str}")
                        color, zone_type, max_drones = "none", "normal", 1
                        if meta_part:
                            for tag in meta_part.split():
                                if "=" not in tag:
                                    raise ParseError(
                                        lineno, f"invalid metablock format {tag}")
                                key, value = tag.split("=", 1)
                                if key == "color":
                                    color = value
                                elif key == "max_drones":
                                    try:
                                        max_drones = int(value)
                                    except ValueError:
                                        raise ParseError(
                                            lineno, f"max_drones should be an integer , caught {value}")
                                    if max_drones <= 0:
                                        raise ParseError(
                                            lineno, "max_drones should be positive")
                                elif key == "zone":
                                    if value not in ("normal", "blocked", "restricted", "priority"):
                                        raise ParseError(
                                            lineno, f"invalid zone type '{value}'")
                                    zone_type = value
                                else:
                                    raise ParseError(
                                        lineno, f"unknown metadata key '{key}'")
                        end_zone = Zone(name, x, y, zone_type,
                                        color, max_drones)
                        end_zone.is_end = True
                        graph1.zones[name] = end_zone
                        graph1.end_zone = end_zone

                    elif line.startswith("hub"):
                        if not nb_drones_seen:
                            raise ParseError(
                                lineno, "nb_drones must be declared before hub")
                        if ":" not in line:
                            raise ParseError(lineno, "missing ':' after 'hub'")
                        body = line.split(":", 1)[1].strip()
                        if "[" in body:
                            if not body.endswith("]"):
                                raise ParseError(
                                    lineno, "metablock unterminated")
                            fields_part, meta_part = body.split("[", 1)
                            meta_part = meta_part[: -1]
                        else:
                            fields_part, meta_part = body, ""
                        parts = fields_part.split()
                        if len(parts) != 3:
                            raise ParseError(
                                lineno, f"format should be <name> <x> <y>, got '{fields_part}'")
                        name, x_str, y_str = parts
                        if "-" in name:
                            raise ParseError(
                                lineno, "Zone name cannot contain '-'")
                        if name in graph1.zones:
                            raise ParseError(
                                lineno, f"cannot have duplicate zone names, caught '{name}'")
                        try:
                            x, y = int(x_str), int(y_str)
                        except ValueError:
                            raise ParseError(
                                lineno, f"coordinates must be integers, got {x_str} & {y_str}")
                        zone_type, color, max_drones = "normal", "none", 1
                        if meta_part:
                            for tag in meta_part.split():
                                if "=" not in tag:
                                    raise ParseError(
                                        lineno, f"invalid metablock format {tag}")
                                key, value = tag.split("=", 1)
                                if key == "zone":
                                    if value not in ("normal", "blocked", "restricted", "priority"):
                                        raise ParseError(
                                            lineno, f"invalid zone type '{value}'")
                                    zone_type = value
                                elif key == "color":
                                    color = value
                                elif key == "max_drones":
                                    try:
                                        max_drones = int(value)
                                    except ValueError:
                                        raise ParseError(
                                            lineno, f"max_drones should be an integer , caught {value}")
                                    if max_drones <= 0:
                                        raise ParseError(
                                            lineno, f"max_drones number must be an postive")
                        hub_object = Zone(
                            name, x, y, zone_type, color, max_drones)
                        graph1.zones[name] = hub_object
                    elif line.startswith("connection"):
                        if not nb_drones_seen:
                            raise ParseError(
                                lineno, "nb drones must be declared before connections")
                        if ":" not in line:
                            raise ParseError(
                                lineno, "missing ':' after 'connection'")
                        body = line.split(":", 1)[1].strip()
                        if "[" in body:
                            if not body.endswith("]"):
                                raise ParseError(
                                    lineno, "metablock unterminated")
                            fields_part, meta_part = body.split("[", 1)
                            meta_part = meta_part[: -1]
                        else:
                            fields_part, meta_part = body, ""
                        parts = fields_part.split()
                        if len(parts) != 1:
                            raise ParseError(
                                lineno, f"Format should be '<name1>-<name2>' , got {fields_part}")
                        if "-" not in fields_part:
                            raise ParseError(
                                lineno, f"connection must be '<name1>-<name2>', got '{fields_part}'")
                        name1, name2 = fields_part.split("-", 1)
                        name1 = name1.strip()
                        name2 = name2.strip()
                        if name1 not in graph1.zones or name2 not in graph1.zones:
                            raise ParseError(
                                lineno, f"{name1} and {name2} must be already created to be used in connection")
                        conn_key = tuple(sorted((name1, name2)))
                        if conn_key in graph1.connections:
                            raise ParseError(
                                lineno, f"duplicate connection '{name1}-{name2}'")
                        max_link_capacity = 1
                        if meta_part:
                            for tag in meta_part.split():
                                if "=" not in tag:
                                    raise ParseError(
                                        lineno, f"invalid metadata '{tag}'")
                                key, value = tag.split("=", 1)
                                if key == "max_link_capacity":
                                    try:
                                        max_link_capacity = int(value)
                                    except ValueError:
                                        raise ParseError(
                                            lineno, f"max_link_capacity must be an integer, got {value}")
                                    if max_link_capacity <= 0:
                                        raise ParseError(
                                            lineno, "max_link_capacity must be positive")
                                else:
                                    raise ParseError(
                                        lineno, f"unknown metadata key '{key}'")
                        graph1.connections[conn_key] = max_link_capacity
        except FileNotFoundError:
            raise ParseError(0, f"file '{self.path}' not found")

        if graph1.start_zone is None:
            raise ParseError(lineno, "start_zone is missing")
        if graph1.end_zone is None:
            raise ParseError(lineno, "end_zone is missing")

        return graph1


if __name__ == "__main__":
    path: str = sys.argv[1]
    pars1 = Parsing(path)
    print(pars1.path)
    graph1 = pars1.parsing()
    print(graph1)
