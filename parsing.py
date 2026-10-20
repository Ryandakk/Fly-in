from typing import Optional


class ParseError(Exception):
    """Raised when a map file line is malformed,
     carrying its line number and cause."""

    def __init__(self, lineno: int, reason: str) -> None:
        """Store the offending line number and a human-readable reason."""
        self.lineno = lineno
        self.reason = reason
        super().__init__(f"line {lineno}: {reason}")


class Zone:
    """A single named zone (hub) on the map:
     its position, type, color and capacity."""

    def __init__(self, name: str,
                 x: int, y: int,
                 zone: str, color: str, max_drones: int) -> None:
        """Build a zone from its parsed attributes;
         is_start/is_end default to False."""
        self.name = name
        self.x = x
        self.y = y
        self.zone = zone
        self.color = color
        self.max_drones = max_drones
        self.is_start = False
        self.is_end = False


class Graph:
    """The parsed map: zones,
    their connections and adjacency, ready for pathfinding."""

    def __init__(self) -> None:
        """Start with an empty map and the default drone count of 1."""
        self.nb_drones = 1
        self.zones: dict[str, Zone] = {}
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None
        self.connections: dict[tuple[str, str], int] = {}
        self.neighbors: dict[str, list[str]] = {}

    def add_zone(self, zone: Zone) -> None:
        """Register a zone on the map and give it an empty neighbor list."""
        self.zones[zone.name] = zone
        self.neighbors[zone.name] = []

    def add_connection(self, name1: str, name2: str, capacity: int) -> None:
        """Record a bidirectional connection between
        two zones with its link capacity."""
        sorted_name1, sorted_name2 = sorted((name1, name2))
        self.connections[(sorted_name1, sorted_name2)] = capacity
        self.neighbors[name1].append(name2)
        self.neighbors[name2].append(name1)


class Parsing:
    """Reads a map file and turns it into a validated Graph."""

    def __init__(self, path: str) -> None:
        """Remember the path to the map file to parse."""
        self.path = path

    def parsing(self) -> Graph:
        """Parse the map file line by line,
        raising ParseError on the first bad line."""
        graph1 = Graph()
        nb_drones_seen = False
        lineno = 0

        try:
            with open(self.path, "r") as f:
                for lineno, rawline in enumerate(f, start=1):
                    line = rawline.strip()
                    if not line or line.startswith("#"):
                        continue
                    keyword = line.split(":")[0].strip()
                    if keyword == "nb_drones":
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
                                lineno,
                                "number of drones should "
                                f"be an integer , got {value}")
                        if nb_drones <= 0:
                            raise ParseError(
                                lineno, "Number MUST be positive")
                        graph1.nb_drones = nb_drones
                        nb_drones_seen = True
                    elif keyword == "start_hub":
                        if not nb_drones_seen:
                            raise ParseError(
                                lineno, "nb_drones must be declared "
                                "before any start/end zone")
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
                                    lineno, "metablock unterminated")
                            fields_part, meta_part = body.split("[", 1)
                            meta_part = meta_part[:-1]
                            if "[" in meta_part or "]" in meta_part:
                                raise ParseError(
                                    lineno, "Invalid Brackets in metadata"
                                )
                        else:
                            fields_part, meta_part = body, ""
                        parts = fields_part.split()
                        if len(parts) != 3:
                            raise ParseError(
                                lineno, "Format should be '<name> <x> <y>', "
                                f"got '{fields_part}'")
                        name, x_str, y_str = parts
                        if "-" in name:
                            raise ParseError(
                                lineno, f"zone name '{name}'"
                                " must not contain '-'")
                        if name in graph1.zones:
                            raise ParseError(
                                lineno, f"duplicate zone name '{name}'")
                        try:
                            x, y = int(x_str), int(y_str)
                        except ValueError:
                            raise ParseError(
                                lineno, "coordinates must be integers, "
                                f"got '{x_str}', '{y_str}'")
                        color, zone_type, max_drones = "none", "normal", 1
                        if meta_part:
                            keys: set[str] = set()
                            for tag in meta_part.split():
                                if tag.count("=") != 1:
                                    raise ParseError(
                                        lineno, f"invalid metadata '{tag}'")
                                key, value = tag.split("=", 1)
                                if key in keys:
                                    raise ParseError(
                                        lineno, "duplicate metadata key"
                                        f" '{key}'")
                                keys.add(key)
                                if value == "":
                                    raise ParseError(
                                        lineno, "Empty metadata"
                                    )
                                if key == "color":
                                    color = value
                                elif key == "max_drones":
                                    try:
                                        max_drones = int(value)
                                    except ValueError:
                                        raise ParseError(
                                            lineno, "max_drones must be an int"
                                            f", caught {value}")
                                    if max_drones <= 0:
                                        raise ParseError(
                                            lineno, "max_drones"
                                            "should be positive")
                                elif key == "zone":
                                    if value not in ("normal", "blocked",
                                                     "restricted", "priority"):
                                        raise ParseError(
                                            lineno, "invalid zone"
                                            f"type '{value}'")
                                    zone_type = value
                                else:
                                    raise ParseError(
                                        lineno, "unknown metadata key"
                                        f"'{key}'")
                        start_zone = Zone(
                            name, x, y, zone_type, color, max_drones)
                        start_zone.is_start = True
                        graph1.start_zone = start_zone
                        graph1.add_zone(start_zone)

                    elif keyword == "end_hub":
                        if not nb_drones_seen:
                            raise ParseError(
                                lineno, "nb_drones must be declared"
                                "before any start/end zone")
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
                            if "[" in meta_part or "]" in meta_part:
                                raise ParseError(
                                    lineno, "Invalid Brackets in metadata"
                                )
                        else:
                            fields_part, meta_part = body, ""
                        parts = fields_part.split()
                        if len(parts) != 3:
                            raise ParseError(
                                lineno, f"format should be <name> <x> <y>, "
                                f"got '{fields_part}'")
                        name, x_str, y_str = parts
                        if "-" in name:
                            raise ParseError(
                                lineno, "Zone name cannot contain '-'")
                        if name in graph1.zones:
                            raise ParseError(
                                lineno, "Cannot have duplicate Zone names")
                        try:
                            x, y = int(x_str), int(y_str)
                        except ValueError:
                            raise ParseError(
                                lineno, "coordinates must be integers, "
                                f"got {x_str} & {y_str}")
                        color, zone_type, max_drones = "none", "normal", 1
                        if meta_part:
                            keys = set()
                            for tag in meta_part.split():
                                if tag.count("=") != 1:
                                    raise ParseError(
                                        lineno, "invalid metablock"
                                        f"format {tag}")
                                key, value = tag.split("=", 1)
                                if key in keys:
                                    raise ParseError(
                                        lineno, "duplicate metadata"
                                        f"key '{key}'")
                                keys.add(key)
                                if value == "":
                                    raise ParseError(
                                        lineno, "Empty metadata"
                                    )
                                if key == "color":
                                    color = value
                                elif key == "max_drones":
                                    try:
                                        max_drones = int(value)
                                    except ValueError:
                                        raise ParseError(
                                            lineno, "max_drones should"
                                            "be an integer, "
                                            f"caught {value}")
                                    if max_drones <= 0:
                                        raise ParseError(
                                            lineno, "max_drones "
                                            "should be positive")
                                elif key == "zone":
                                    if value not in ("normal", "blocked",
                                                     "restricted",
                                                     "priority"):
                                        raise ParseError(
                                            lineno, "invalid zone"
                                            f"type '{value}'")
                                    zone_type = value
                                else:
                                    raise ParseError(
                                        lineno, "unknown metadata"
                                        f"key '{key}'")
                        end_zone = Zone(name, x, y, zone_type,
                                        color, max_drones)
                        end_zone.is_end = True
                        graph1.end_zone = end_zone
                        graph1.add_zone(end_zone)

                    elif keyword == "hub":
                        if not nb_drones_seen:
                            raise ParseError(
                                lineno, "nb_drones must be"
                                "declared before hub")
                        if ":" not in line:
                            raise ParseError(lineno, "missing ':' after 'hub'")
                        body = line.split(":", 1)[1].strip()
                        if "[" in body:
                            if not body.endswith("]"):
                                raise ParseError(
                                    lineno, "metablock unterminated")
                            fields_part, meta_part = body.split("[", 1)
                            meta_part = meta_part[: -1]
                            if "[" in meta_part or "]" in meta_part:
                                raise ParseError(
                                    lineno, "Invalid Brackets in metadata"
                                )
                        else:
                            fields_part, meta_part = body, ""
                        parts = fields_part.split()
                        if len(parts) != 3:
                            raise ParseError(
                                lineno, "format should be <name> <x> <y>, "
                                f"got '{fields_part}'")
                        name, x_str, y_str = parts
                        if "-" in name:
                            raise ParseError(
                                lineno, "Zone name cannot contain '-'")
                        if name in graph1.zones:
                            raise ParseError(
                                lineno, "cannot have duplicate zone names, "
                                f"caught '{name}'")
                        try:
                            x, y = int(x_str), int(y_str)
                        except ValueError:
                            raise ParseError(
                                lineno, "coordinates must be integers, "
                                f"got {x_str} & {y_str}")
                        zone_type, color, max_drones = "normal", "none", 1
                        if meta_part:
                            keys = set()
                            for tag in meta_part.split():
                                if tag.count("=") != 1:
                                    raise ParseError(
                                        lineno, "invalid metablock"
                                        f"format {tag}")
                                key, value = tag.split("=", 1)
                                if key in keys:
                                    raise ParseError(
                                        lineno, f"duplicate metadata key {key}"
                                    )
                                else:
                                    keys.add(key)
                                if value == "":
                                    raise ParseError(
                                        lineno, "Empty metadata"
                                    )
                                if key == "zone":
                                    if value not in ("normal", "blocked",
                                                     "restricted", "priority"):
                                        raise ParseError(
                                            lineno, "invalid zone "
                                            f"type '{value}'")
                                    zone_type = value
                                elif key == "color":
                                    color = value
                                elif key == "max_drones":
                                    try:
                                        max_drones = int(value)
                                    except ValueError:
                                        raise ParseError(
                                            lineno, "max_drones should"
                                            "be an integer, "
                                            f"caught {value}")
                                    if max_drones <= 0:
                                        raise ParseError(
                                            lineno, "max_drones number "
                                            "must be a positive")
                                else:
                                    raise ParseError(
                                        lineno, "unknown metadata "
                                        f"key '{key}'")
                        hub_object = Zone(
                            name, x, y, zone_type, color, max_drones)
                        graph1.add_zone(hub_object)
                    elif keyword == "connection":
                        if not nb_drones_seen:
                            raise ParseError(
                                lineno, "nb drones must be declared "
                                "before connections")
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
                            if "[" in meta_part or "]" in meta_part:
                                raise ParseError(
                                    lineno, "Invalid Brackets in metadata"
                                )
                        else:
                            fields_part, meta_part = body, ""
                        parts = fields_part.split()
                        if len(parts) != 1:
                            raise ParseError(
                                lineno, "Format should be '<name1>-<name2>' ,"
                                f"got {fields_part}")
                        if "-" not in fields_part:
                            raise ParseError(
                                lineno, "connection must be"
                                " '<name1>-<name2>' ,"
                                f"got '{fields_part}'")
                        name1, name2 = fields_part.split("-", 1)
                        name1 = name1.strip()
                        name2 = name2.strip()
                        if name1 == name2:
                            raise ParseError(
                                lineno, f"Zone {name1} cannot"
                                "connect to itself"
                            )
                        if (name1 not in graph1.zones or
                                name2 not in graph1.zones):
                            raise ParseError(
                                lineno, f"{name1} and {name2} "
                                "must be already created "
                                "to be used in connection")
                        conn_key = tuple(sorted((name1, name2)))
                        if conn_key in graph1.connections:
                            raise ParseError(
                                lineno, "duplicate connection"
                                f"'{name1}-{name2}'")
                        max_link_capacity = 1
                        if meta_part:
                            keys = set()
                            for tag in meta_part.split():
                                if tag.count("=") != 1:
                                    raise ParseError(
                                        lineno, f"invalid metadata '{tag}'")
                                key, value = tag.split("=", 1)
                                if key in keys:
                                    raise ParseError(
                                        lineno, "duplicate metadata"
                                        f"key '{key}'")
                                keys.add(key)
                                if value == "":
                                    raise ParseError(
                                        lineno, "Empty metadata"
                                    )
                                if key == "max_link_capacity":
                                    try:
                                        max_link_capacity = int(value)
                                    except ValueError:
                                        raise ParseError(
                                            lineno, "max_link_capacity must be"
                                            f"an integer, got {value}")
                                    if max_link_capacity <= 0:
                                        raise ParseError(
                                            lineno, "max_link_capacity must"
                                            "be positive")
                                else:
                                    raise ParseError(
                                        lineno, "unknown metadata "
                                        f"key '{key}'")
                        graph1.add_connection(name1, name2, max_link_capacity)
                    else:
                        raise ParseError(
                            lineno, f"Unknown data {line}"
                        )
        except FileNotFoundError:
            raise ParseError(0, f"file '{self.path}' not found")
        if not nb_drones_seen:
            raise ParseError(lineno, "nb_drones is missing")
        if graph1.start_zone is None:
            raise ParseError(lineno, "start_zone is missing")
        if graph1.end_zone is None:
            raise ParseError(lineno, "end_zone is missing")
        return graph1
