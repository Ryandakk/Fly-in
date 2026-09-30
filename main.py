from simulation import Scheduler, Drone
from renderer import play, FlyWindow
from algorithm import Dijk
from parsing import ParseError, Parsing

def main() -> None:
    parse1 = Parsing("maps/easy/01_linear_path.txt")
    graphfile1 = parse1.parsing()
    algo1 = Dijk()
    dronelist = []
    path = algo1.cheapest_path(
    graphfile1,
    graphfile1.start_zone.name,
    graphfile1.end_zone.name)
    for i in range(1, graphfile1.nb_drones + 1):
        droneid = Drone(i, 0, path)
        dronelist.append(droneid)

    schedule1 = Scheduler(graphfile1.nb_drones, dronelist, graphfile1)
    turnslist = schedule1.run()
    simulator1 = FlyWindow(graphfile1, turnslist)
    play(graphfile1, turnslist)


if __name__ == "__main__":
    main()