import sys
from simulation import Scheduler, Drone
from renderer import play
from algorithm import Dijk
from parsing import ParseError, Parsing

def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python3 main.py <map_file>")
        sys.exit(1)
    try:
        parse1 = Parsing(sys.argv[1])
        graphfile1 = parse1.parsing()
        algo1 = Dijk()
        dronelist = []
        paths = algo1.plan_paths(graphfile1)
        for i in range(1, graphfile1.nb_drones + 1):
            droneid = Drone(i, 0, paths[i - 1])
            dronelist.append(droneid)
        schedule1 = Scheduler(dronelist, graphfile1)
        turnslist = schedule1.run()
        for turn in turnslist:
            print(" ".join(turn))
    except (ValueError, ParseError) as e:
        print(e)
        sys.exit(1)
    play(graphfile1, turnslist)


if __name__ == "__main__":
    main()