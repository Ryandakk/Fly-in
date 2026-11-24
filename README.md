*This project has been created as part of the 42 curriculum by radakrou.*

# fly-in

## Description

**fly-in** is a drone routing and scheduling project. The goal is to move a
fleet of drones from a start zone to an end zone through a graph of connected
zones, in the smallest possible number of simulation turns, while respecting
every movement and capacity constraint.

The program reads a map file describing the zones, their types and their
connections, plans a path for every drone, then simulates the fleet turn by
turn. Drones move simultaneously, so the difficulty is not finding *a* path
but scheduling many drones at once without exceeding zone or connection
capacities. Each turn is printed as one line, and the finished simulation is
replayed in a graphical window.

## Zone Types

Every zone has a type that decides what it costs to enter it:

- `normal` (default) : costs 1 turn to enter.
- `priority` : costs 1 turn, but is preferred by the pathfinder.
- `restricted` : costs 2 turns. The drone occupies the connection for one
  turn and **must** land on the following turn; it cannot wait mid-flight.
- `blocked` : impassable. No path may use it.

Zones and connections also carry capacities: `max_drones=<N>` limits how many
drones may occupy a zone at the same turn (default 1), and
`max_link_capacity=<N>` limits how many drones may traverse a connection
simultaneously (default 1). The start and end zones are exempt from occupancy
limits, since all drones begin in one and accumulate in the other.

## Instructions

### Installation

To create the virtual environment and install the dependencies, run:

```bash
make install
```

This creates `.venv/` (only if it does not already exist) and installs
`arcade`, `Pillow`, `flake8` and `mypy` from `requirements.txt`.

### Running

```bash
make run
```

This runs the default map. To choose another map, override `MAP`:

```bash
make run MAP=maps/hard/03_ultimate_challenge.txt
```

The program can also be called directly:

```bash
python3 main.py <map_file>
```

### Debugging

To run the program under Python's built-in debugger:

```bash
make debug MAP=maps/medium/02_circular_loop.txt
```

### Linting

```bash
make lint
```

Runs `flake8 .` and `mypy .` with the flags required by the subject. A
stricter variant is also available:

```bash
make lint-strict
```

### Cleaning

```bash
make clean
```

Removes `__pycache__` directories, `.pyc` files and `.mypy_cache`.

## Output Format

One line is printed per simulation turn, listing the movements that happened
during that turn, space separated:

- `D<ID>-<zone>` : the drone arrived in that zone.
- `D<ID>-<zone1>-<zone2>` : the drone is in flight on that connection,
  heading toward a restricted zone.

Drones that do not move during a turn are omitted from the line, and drones
that reach the end zone are delivered and no longer reported.

```
D1-roof1 D2-corridorA
D1-roof2 D2-tunnelB
D1-goal D2-goal
```

## Algorithm

The project is split into three independent stages: parsing, path planning,
and scheduling. Keeping them separate is what makes the scheduler easy to
reason about, because by the time it runs, every drone already knows its
route.

### Parsing — `parsing.py`

The parser reads the map line by line and fails on the **first** malformed
line, reporting both the line number and the cause. It validates the drone
count, that exactly one start and one end zone exist, that zone names are
unique and free of dashes, that coordinates are integers, that metadata
blocks are syntactically valid, that zone types are among the four allowed
ones, that capacities are positive integers, and that connections reference
already-defined zones without duplicates in either direction. Missing,
unreadable and non-file paths are all reported as clean errors rather than
crashing.

The result is a `Graph` holding the zones, an adjacency list, and the
capacity of every connection.

### Path planning — `algorithm.py`

Paths are computed with **Dijkstra's algorithm**, implemented from scratch
with a binary heap (`heapq`). No graph library is used.

The cost of a path is a **pair** `(turns, non_priority)` compared
lexicographically:

```python
ZONE_COST = {
    "normal":     (1, 1),
    "priority":   (1, 0),
    "restricted": (2, 1),
}
```

The first component is the real cost in turns, so Dijkstra minimises the
number of turns first. The second component counts the zones that are *not*
priority zones, so among several routes of equal length the pathfinder
prefers the one going through priority zones. This is how the subject's
"priority zones should be prioritized" rule is satisfied without distorting
the turn count. `blocked` zones are simply never offered as neighbours, so no
path can use them. Dijkstra stays valid here because every step increases the
first component by at least 1, which keeps the costs monotonic.

### Load report for multi-path distribution

A single Dijkstra run would send **every** drone down the same shortest path,
which is the wrong answer when zones and connections have capacities: the
drones would queue up behind each other and the turn count would be dominated
by waiting.

To avoid that, `plan_paths` keeps a **load report** — a dictionary counting,
for every zone, how many already-planned drones pass through it. Paths are
planned one drone at a time, and after each drone is routed, every
intermediate zone on its path gets its load incremented. The next call to
Dijkstra adds a congestion penalty to each candidate zone:

```python
turns += load.get(name, 0) // neighbor_zone.max_drones
```

The penalty is divided by the zone's own capacity, so a wide zone tolerates
more traffic before it starts looking expensive, while a `max_drones=1`
bottleneck becomes costly as soon as one drone is already routed through it.
The effect is that the first drones take the shortest route and later drones
are progressively pushed onto alternative routes, spreading the fleet across
the graph instead of funnelling it. The start and end zones are excluded from
the load report, since they are capacity-exempt.

This is what produces genuine multi-path routing on maps like
`capacity_hell`, which are built specifically to punish single-path
solutions.

### Scheduling — `simulation.py`

The scheduler advances the whole fleet one turn at a time. It tracks the
occupancy of every zone and, per turn, the occupancy of every connection.
For each drone it tries the next hop on its path and refuses the move if the
destination zone is full or the connection is saturated; in that case the
drone simply stays where it is, which is how "strategic waiting" happens.
Because a drone leaving a zone decrements the occupancy immediately, a zone
freed this turn can be entered by another drone the same turn.

Moving into a `restricted` zone is handled as a two-turn flight: the drone is
marked in transit, occupies the connection, and lands on the next turn. The
destination slot is reserved when the flight starts, which is necessary
rather than merely cautious — since a drone in flight is not allowed to wait,
the scheduler has to guarantee the slot will still be free when it arrives.

The simulation ends when every drone has reached the end zone.

## Complexity

### Path planning

One Dijkstra run over a graph with `V` zones and `E` connections costs
**O((V + E) log V)** with a binary heap. Because a path is planned per drone
so that the load report can influence the next one, planning the whole fleet
of `D` drones costs **O(D · (V + E) log V)**. In practice this is negligible:
planning stays in the millisecond range even for thousands of drones, since
the maps are small.

### Scheduling

Each turn iterates over every drone, so the simulation costs
**O(T · D)** for `T` turns. The number of turns itself depends on the map: on
a capacity-constrained map, only a limited number of drones can enter the
graph per turn, so `T` grows with `D` and the scheduling stage becomes the
dominant cost for very large fleets.

### Space

The graph is stored as an adjacency list, **O(V + E)**, and each drone stores
its own path, **O(D · L)** for paths of length `L`. The printed output holds
one entry per turn, **O(T · D)** in the worst case.

## Visual Representation

The simulation is replayed in a graphical window built with `arcade`
(`renderer.py`). The window is only a *viewer*: the simulation is already
finished when it opens, so the animation can never disagree with the printed
output.

Zones are drawn as circles at their map coordinates, filled with the colour
given by the `color` metadata, and connections are drawn as lines between
them. The view is automatically scaled and centred to fit whatever
coordinate range the map uses, so no map needs manual tuning. Drones are
drawn as small markers on their current zone, slightly offset from each other
so several drones in the same zone remain distinguishable. A drone in flight
toward a restricted zone is drawn at the **midpoint of the connection**,
which makes the two-turn flight visible as a real intermediate state rather
than a teleport. One turn is applied every 0.55 seconds.

This helps understanding in a way the text output cannot: congestion appears
directly as markers piling up on a zone, and the multi-path distribution
produced by the load report is visible as the fleet splitting across
different branches of the graph instead of following a single line. Colour
values that `Pillow` does not recognise fall back to light gray instead of
failing, so an unusual colour in a map never prevents the replay. If no
display is available, the program reports it and still prints the full
simulation.

## Performance

Turn counts obtained on the maps provided with the subject:

| Map | Drones | Turns | Target |
|---|---|---|---|
| `easy/01_linear_path` | 2 | 4 | ≤ 6 |
| `easy/02_simple_fork` | 4 | 4 | ≤ 8 |
| `easy/03_basic_capacity` | 4 | 4 | ≤ 6 |
| `medium/01_dead_end_trap` | 5 | 8 | ≤ 12 |
| `medium/02_circular_loop` | 6 | 15 | ≤ 15 |
| `medium/03_priority_puzzle` | 5 | 7 | ≤ 12 |
| `hard/01_maze_nightmare` | 8 | 13 | ≤ 30 |
| `hard/02_capacity_hell` | 12 | 16 | ≤ 35 |
| `hard/03_ultimate_challenge` | 15 | 32 | ≤ 45 |
| `challenger/01_the_impossible_dream` | 25 | 50 | 45 (bonus) |

Every mandatory target is met. The optional challenger map is not beaten.

## Technical Choices

- **Object-oriented throughout.** `Parsing` builds a `Graph` of `Zone`
  objects, `Dijk` plans paths, and `Scheduler` moves `Drone` objects.
- **No graph library.** Dijkstra, the adjacency list and all graph logic are
  implemented by hand, as required.
- **Fully typed**, and checked with `mypy` using the flags from the subject.
- **Parsing is strict and fails early**, so an invalid map is reported with a
  precise reason instead of producing a silently wrong simulation.
- **The renderer is decoupled** from the simulation and receives only the
  finished list of turns, so a display problem can never affect the result.

## Resources

- The subject (`en.subject.pdf`) for the map format, movement rules and
  benchmarks.
- The `arcade` and `Pillow` documentation for the drawing primitives and for
  colour-name conversion.
- Dijkstra's algorithm was revised from course material and from the Python
  `heapq` documentation for the priority-queue implementation.

AI was used as an assistant on the following parts:

- Explaining how to shape Dijkstra's cost as a comparable tuple so that turn
  count and priority-zone preference could be optimised together, and
  reviewing the congestion-penalty idea behind the load report.
- Reviewing error handling in the parser, in particular which file-level
  exceptions (missing file, permission denied, path being a directory) need
  to be caught so the program never crashes.
- Reviewing `flake8` and `mypy` findings and explaining the cause of specific
  type errors, such as narrowing `Optional` values and annotating container
  types precisely.
- Discussing the complexity of the scheduling loop and how it scales with the
  number of drones.

Every AI suggestion was reviewed and tested before being kept, and the code
in this repository is understood and can be explained and modified on
request.
