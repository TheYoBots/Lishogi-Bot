import logging
import subprocess

logger = logging.getLogger(__name__)

WHITE = True

# From https://github.com/niklasf/fishnet
LVL_SKILL = [0, 3, 6, 10, 14, 16, 18, 20]
LVL_MOVETIMES = [50, 100, 150, 200, 300, 400, 500, 1000]
LVL_DEPTHS = [1, 1, 2, 3, 5, 8, 13, 22]


class PopenEngine(subprocess.Popen):
    def __init__(self, commands, options, protocol="UCI"):
        subprocess.Popen.__init__(self, commands, universal_newlines=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE)
        self.protocol = protocol
        self.name = ""
        self.supported_options = []

    def send(self, command):
        self.stdin.write(command + "\n")
        self.stdin.flush()
        logger.debug("<< %s" % command)

    def setoption(self, options):
        for option, value in options.items():
            if option == "go_commands":
                continue

            if option not in self.supported_options:
                continue

            if self.protocol == "UCCI":
                self.send("setoption %s %s" % (option, str(value)))
            else:
                self.send("setoption name %s value %s" % (option, str(value)))

        stdout = self.isready()
        if stdout.find("No such") >= 0:
            logger.debug(">> %s" % stdout)

    def go(self, ponder=False,
           time=None, inc=None, opptime=None, oppinc=None,
           wtime=None, btime=None, winc=None, binc=None,
           depth=None, nodes=None, movetime=None, perft=None):

        builder = ["go"]

        if ponder:
            builder.append("ponder")

        if self.protocol == "UCCI":
            if time is not None:
                builder.append("time")
                builder.append(str(int(time)))

            if inc is not None:
                builder.append("increment")
                builder.append(str(int(inc)))

            if opptime is not None:
                builder.append("opptime")
                builder.append(str(int(opptime)))

            if oppinc is not None:
                builder.append("oppincrement")
                builder.append(str(int(oppinc)))
        else:
            if wtime is not None:
                builder.append("wtime")
                builder.append(str(int(wtime)))

            if btime is not None:
                builder.append("btime")
                builder.append(str(int(btime)))

            if winc is not None:
                builder.append("winc")
                builder.append(str(int(winc)))

            if binc is not None:
                builder.append("binc")
                builder.append(str(int(binc)))

            if movetime is not None:
                builder.append("movetime")
                builder.append(str(int(movetime)))

            if perft is not None:
                builder.append("perft")
                builder.append(str(int(perft)))
                movelist = []

        if depth is not None:
            builder.append("depth")
            builder.append(str(int(depth)))

        if nodes is not None:
            builder.append("nodes")
            builder.append(str(int(nodes)))

        self.send(" ".join(builder))

        while True:
            line = self.stdout.readline().strip()
            if line == "":
                continue
            parts = line.split()
            if parts[0] == "bestmove":
                if len(parts) == 4 and parts[2] == "ponder":
                    ponder = parts[3]
                else:
                    ponder = None
                logger.debug(">> %s" % line)
                return parts[1], ponder
            elif parts[0] == "info" and "pv" in parts:
                logger.debug(">> %s" % line)
            elif parts[0][-1] == ":":
                movelist.append(parts[0][:-1])
            elif parts[0] == "Nodes" and parts[1] == "searched:":
                return movelist
            else:
                print(parts)

    def isready(self):
        self.send("isready")
        while True:
            line = self.stdout.readline().strip()
            if line == "readyok":
                logger.debug(">> %s" % line)
                return line

    def init(self):
        self.send("usi" if self.protocol == "USI" else
                  "ucci" if self.protocol == "UCCI" else
                  "uci")
        while True:
            line = self.stdout.readline().strip()
            logger.debug(">> %s" % line)
            if line.startswith("id name"):
                self.name = line[7:]
            elif line.startswith("option"):
                op = "option " if self.protocol == "UCCI" else "option name "
                parts = line.split(op)
                option_name = parts[1].split(" type")[0]
                self.supported_options.append(option_name)
            elif line == "usiok" or line == "uciok" or line == "ucciok":
                return line

    def position(self, board):
        builder = ["position"]
        builder.append("sfen" if self.protocol == "USI" else "fen")
        builder.append(board.fen())

        if board.move_stack:
            builder.append("moves")
            builder.extend(board.move_stack)

        self.send(" ".join(builder))
        self.isready()

    def newgame(self):
        self.send("usinewgame" if self.protocol == "USI" else
                  "uccinewgame" if self.protocol == "UCCI" else
                  "ucinewgame")
        self.isready()


class GeneralEngine:
    def __init__(self, board, commands, options=None, silence_stderr=False):
        variant = board.uci_variant
        if variant == "shogi":
            self.protocol = "USI"
        elif variant == "xiangqi":
            self.protocol = "UCCI"
        else:
            self.protocol = "UCI"

        commands = commands[0] if len(commands) == 1 else commands
        self.go_commands = options.get("go_commands", {})
        self.threads = options.get("Threads", 1)

        self.engine = PopenEngine(commands, options, protocol=self.protocol)
        self.engine.init()

        options["UCI_Variant"] = variant
        self.engine.setoption(options)

        self.engine.newgame()
        self.engine.position(board)

    def set_time_control(self, game):
        pass

    def get_stats(self):
        # TODO
        pass

    def first_search(self, board, movetime):
        self.engine.position(board)
        if self.protocol == "UCCI":
            best_move, _ = self.engine.go(depth=10)
        else:
            best_move, _ = self.engine.go(movetime=movetime)
        return best_move

    def search(self, board, wtime, btime, winc, binc):
        self.engine.position(board)
        cmds = self.go_commands

        if self.protocol == "UCCI":
            if board.color == WHITE:
                time = wtime
                inc = winc
                opptime = btime
                oppinc = binc
            else:
                time = btime
                inc = binc
                opptime = wtime
                oppinc = winc

            best_move, _ = self.engine.go(
                time=time,
                inc=inc,
                opptime=opptime,
                oppinc=oppinc,
                depth=cmds.get("depth"),
                nodes=cmds.get("nodes"),
            )
        else:
            best_move, _ = self.engine.go(
                wtime=wtime,
                btime=btime,
                winc=winc,
                binc=binc,
                depth=cmds.get("depth"),
                nodes=cmds.get("nodes"),
                movetime=cmds.get("movetime")
            )
        return best_move

    def name(self):
        return self.engine.name

    def quit(self):
        self.engine.terminate()

    def set_skill_level(self, lvl):
        level = LVL_SKILL[lvl - 1]
        movetime = int(round(LVL_MOVETIMES[lvl - 1] / (
            self.threads * 0.9 ** (self.threads - 1))))
        depth = LVL_DEPTHS[lvl - 1]

        self.engine.setoption({"Skill Level": level})
        self.go_commands = {"movetime": movetime, "depth": depth}
