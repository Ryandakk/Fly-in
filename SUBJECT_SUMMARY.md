# Fly-in — Subject Summary

> A planning reference distilled from `en.subject.pdf` (v1.4). This is **not** the
> submission `README.md` (see [Required README.md content](#required-readmemd-content-for-submission)
> below for that) — it's just here to make the big picture easy to scan while planning.

## What it is

Build a system that routes a fleet of drones from a **start zone** to an **end
zone** through a graph of connected zones, in the **fewest total simulation
turns**, while respecting movement/capacity constraints. Drones move
simultaneously turn-by-turn; you must avoid collisions, respect zone/connection
capacities, and produce visual feedback of the simulation.

---

## 🚫 Forbidden

- **Any graph-logic library** (e.g. `networkx`, `graphlib`, etc.) — you must implement pathfinding/graph logic yourself.
- Program crashing on unhandled exceptions during review (counts as non-functional).
- Non-object-oriented design — the project **must be fully object-oriented**.
- Non-typesafe code — `flake8` and `mypy` compliance is mandatory, not optional.
- Duplicate connections (`a-b` and `b-a` count as duplicates).
- Dashes or spaces in zone names.
- Drones entering/passing through `blocked` zones.
- Waiting on a connection mid-transit to a `restricted` zone — once committed, the drone **must** arrive next turn (no stalling for a free destination slot).
- Exceeding a zone's `max_drones` or a connection's `max_link_capacity`.
- Invalid zone types (only `normal`, `blocked`, `restricted`, `priority` allowed) — must raise a parsing error.
- Skipping peer review prep — you must be able to explain/justify all code, including AI-assisted parts (see AI Instructions below).

## ✅ Mandatory requirements

### General / language
- Python **3.10+**, flake8-compliant, fully typed (type hints + `mypy` clean).
- Graceful exception handling (try/except), context managers for resource cleanup.
- Docstrings (PEP 257 / Google or NumPy style) on functions & classes.
- `Makefile` with targets: `install`, `run`, `debug`, `clean`, `lint` (must run `flake8 .` and `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs`), optional `lint-strict` (`--strict`).
- `.gitignore` for Python artifacts.
- Fully object-oriented architecture.

### Input file parsing
- First line: `nb_drones: <positive_integer>`.
- Exactly one `start_hub:` and one `end_hub:` zone.
- Zones: `hub: <name> <x> <y> [metadata]` (or `start_hub:`/`end_hub:` variants). Unique names, integer coords, no dashes/spaces in names.
- Optional metadata (any order): `zone=<type>` (default `normal`), `color=<value>` (default none, any single word), `max_drones=<N>` (default 1).
- Connections: `connection: <name1>-<name2> [max_link_capacity=<N>]`, bidirectional, must reference already-defined zones, no duplicates.
- Comments start with `#`.
- Any malformed line → **stop the program** with a clear error message (line + cause).
- Zone types: `normal` (1 turn), `restricted` (2 turns, see multi-turn rule below), `priority` (1 turn, should be prioritized in pathfinding), `blocked` (impassable).

### Simulation / movement rules
- Each turn, every drone: moves to an adjacent zone (if capacity allows), enters transit toward a restricted zone, or stays in place.
- Zone occupancy: 1 drone by default, up to `max_drones` if set. Start/end zones are exempt (shared/unlimited).
- Connection occupancy limited by `max_link_capacity`.
- Drones vacating a zone free capacity **the same turn** for incoming drones.
- Restricted-zone transit takes exactly 2 turns; drone occupies the connection and **must** land on arrival turn (no waiting).
- Drones that reach the end zone are "delivered" and no longer tracked/output.

### Pathfinding / algorithm
- Must schedule multiple drones' paths simultaneously to maximize throughput (not one at a time).
- Must handle: distribution across multiple paths, strategic waiting, avoidance of conflicts/deadlocks.
- Must account for: zone-type movement costs, turn scheduling, graph topology, capacity constraints (zone + connection).
- Should adapt strategy to different map topologies.
- Be ready to discuss: complexity (O(n), O(log n)...), scalability to many drones, caching/recalculation, memory impact.

### Visual representation
- Must show live simulation feedback via **colored terminal output** and/or a **graphical interface** (either counts; both is "enhanced").

### Output format
- One line per simulation turn.
- Each line: space-separated `D<ID>-<zone>` (destination zone) or `D<ID>-<connection>` (in-transit to a restricted zone).
- Drones that don't move that turn are omitted from the line.
- Simulation ends when all drones reach the end zone.
```
D1-roof1 D2-corridorA
D1-roof2 D2-tunnelB
D1-goal D2-goal
```

### Performance benchmarks (must meet, drive your grade)
| Difficulty | Target |
|---|---|
| Easy maps | < 10 turns |
| Medium maps | 10–30 turns |
| Hard maps | < 60 turns |

Reference targets per provided test map:
- Easy: linear/2 drones ≤ 6, simple fork/4 drones ≤ 8, basic capacity/4 drones ≤ 6
- Medium: dead end trap/5 drones ≤ 12, circular loop/6 drones ≤ 15, priority puzzle/5 drones ≤ 12
- Hard: maze nightmare/8 drones ≤ 30, capacity hell/12 drones ≤ 35, ultimate challenge/15 drones ≤ 45

### Scoring
- Primary metric: **total simulation turns** to deliver all drones (lower = better).
- Must comply with all movement/occupancy/capacity rules to count as valid.
- Secondary (optional, not graded automatically but nice to display): drones moved per turn, average turns per drone, total weighted path cost, quality of visual representation.
- Ties broken by secondary metrics or code quality.

### `README.md` requirements (for the real submission file)
Must live at repo root, written in English, and include:
- First line, **italicized**, exact text: *This project has been created as part of the 42 curriculum by \<login1\>[, \<login2\>[, \<login3\>[...]]].*
- **Description** section (goal + overview).
- **Instructions** section (compile/install/run).
- **Resources** section (references + how AI was used, for which tasks/parts).
- A detailed explanation of your algorithm choices & implementation strategy.
- Documentation of your visual representation and how it helps UX.
- Additional sections as needed (usage examples, feature list, technical choices...).

### Submission
- Everything at the **root** of the git repo.
- Fully working: parser, simulation engine, pathfinding algorithm(s), visual system, correctly formatted output.
- Be ready to **explain or write code live** during evaluation.
- Evaluation maps may differ from the ones provided in the subject.
- Be ready for a small **on-the-spot modification request** (a few lines / an easy feature) during peer review — should be doable in a few minutes unless stated otherwise.

---

## 🎁 Optional / Bonus (only reviewed if mandatory part is 100% done)

- **Exceptional performance**: match or beat every reference target turn count ("perfectly" meet them).
- **Challenger map** — "The Impossible Dream" (25 drones): beat the reference record of **45 turns**. Purely optional, doesn't affect grade either way.
- `lint-strict` Makefile target (`mypy --strict`) is explicitly called out as "strongly recommended" though optional.
- Secondary scoring metrics (drones/turn, avg turns/drone, weighted path cost) — optional to compute but encouraged to display.

---

## AI Instructions (evaluation-relevant, not code requirements)

- AI use is allowed/encouraged for reducing tedious work and building prompting skill — **but** you must fully understand and be able to justify anything AI-generated; you will be evaluated on that understanding, not just on working code.
- Always critically review AI output; don't blindly copy-paste whole functions.
- Seek peer review, don't rely solely on self-checking or AI validation.
- Explicitly document (in the README Resources section) which parts of the project used AI and for what tasks.

---

## Input file format cheat sheet

```
nb_drones: 5

start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```

Zone types & movement cost to enter:
| Type | Cost | Notes |
|---|---|---|
| `normal` (default) | 1 turn | |
| `priority` | 1 turn | should be preferred by the pathfinder |
| `restricted` | 2 turns | drone occupies the connection, must land next turn, can't wait mid-transit |
| `blocked` | — | impassable, invalid if used in any path |

Coordinates are always integers; there is always exactly one unique start and one unique end zone.
