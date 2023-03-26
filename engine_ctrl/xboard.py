import shogi
import threading
import subprocess
import os
import signal
import logging

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, command, cwd=None):
        self.info = {}
        self.id = {}
        cwd = cwd or os.path.realpath(os.path.expanduser("."))
        self.proccess = self.open_process(command, cwd)
        self.go_commands = None

    def set_go_commands(self, go_comm):
        self.go_commands = go_comm
        logger.info(self.go_commands)

    def open_process(self, command, cwd=None, shell=True, _popen_lock=threading.Lock()):
        kwargs = {
            "shell": shell,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "stdin": subprocess.PIPE,
            "bufsize": 1,  # Line buffered
            "universal_newlines": True,
        }

        if cwd is not None:
            kwargs["cwd"] = cwd

        # Prevent signal propagation from parent process
        try:
            # Windows
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        except AttributeError:
            # Unix
            kwargs["preexec_fn"] = os.setpgrp

        with _popen_lock:  # Work around Python 2 Popen race condition
            return subprocess.Popen(command, **kwargs)

    def kill_process(self):
        try:
            # Windows
            self.proccess.send_signal(signal.CTRL_BREAK_EVENT)
        except AttributeError:
            # Unix
            os.killpg(self.proccess.pid, signal.SIGKILL)

    def send(self, line):
        logger.debug(f"<< {line}")
        assert self.proccess.stdin is not None
        self.proccess.stdin.write(line + "\n")
        self.proccess.stdin.flush()

    def recv(self):
        while True:
            assert self.proccess.stdout is not None
            line = self.proccess.stdout.readline()
            if line == "":
                raise EOFError()

            line = line.rstrip()

            logger.debug(f">> {line}")

            if line:
                return line

    def recv_xboard(self):
        command_and_args = self.recv().split(None, 1)
        if len(command_and_args) == 1:
            return command_and_args[0], ""
        elif len(command_and_args) == 2:
            return command_and_args

    def xboard(self):
        self.send("xboard")
        self.send("protover 2")

        engine_info = {}

        while True:
            command, arg = self.recv_xboard()

            if command == "feature":
                if arg == "done=1":
                    return engine_info
                #elif command == "id":
                #    name_and_value = arg.split(None, 1)
                #    if len(name_and_value) == 2:
                #        engine_info[name_and_value[0]] = name_and_value[1]
                pass
            else:
                logger.warning("Unexpected engine response to protover 2: %s %s" % (command, arg))
            self.id = engine_info

    def ping(self):
        self.send("ping")
        while True:
            command, arg = self.recv_xboard()
            if command == "pong":
                break
            else:
                logger.warning("Unexpected engine response to ping: %s %s" % (command, arg))

    def setoption(self, name, value):
        name = name.lower()
        if name == "hash":
            name = "memory"
        elif name == "threads":
            name = "cores"
        elif name == "usi_variant":
            name = "new\nvariant"
            value = value.lower()
            if value == "chushogi":
                value = "chu"

        if value is True:
            value = "true"
        elif value is False:
            value = "false"
        elif value is None:
            value = "none"

        self.send("%s %s" % (name, value))

    def go(self, position, moves, turn, movetime=None, btime=None, wtime=None, binc=None, winc=None, byo=None, depth=None, nodes=None, ponder=False):
        self.setboard(position, moves)
        time = btime if turn == shogi.BLACK else wtime
        otim = btime if turn == shogi.WHITE else wtime

        builder = []
        if ponder:
            builder.append("hard")
        else:
            builder.append("easy")
        if movetime is not None:
            builder.append("st %d" % movetime)
        #if nodes is not None:
        #    builder.append("nodes")
        #    builder.append(str(nodes))
        if depth is not None:
            builder.append("sd %d" % depth)
        # In Shogi and USI, black is the player to move first
        if time is not None:
            builder.append("time %d" % time)
        if otim is not None:
            builder.append("otim %d" % otim)
        #if binc is not None:
        #    builder.append("binc %d" % inc)
        #if winc is not None:
        #    builder.append("winc %d" % inc)
        #if byo is not None:
        #    builder.append("byoyomi %d" % byo)
        builder.append("go")

        self.send("\n".join(builder))
        logger.info("\n".join(builder))

        info = {}
        info["move"] = None
        info["pondermove"] = None

        while True:
            command, arg = self.recv_xboard()

            if command == "move":
                arg_split = arg.split()
                bestmove = arg_split[0]
                if bestmove and bestmove != "@@@@":
                    info["bestmove"] = bestmove
                if len(arg_split) == 3:
                    if arg_split[1] == "ponder":
                        ponder_move = arg_split[2]
                        if ponder_move and ponder_move != "@@@@":
                            info["pondermove"] = ponder_move
                return (info["bestmove"], info["pondermove"])

            elif command == "info":
                arg = arg or ""

                # Parse all other parameters
                score_kind, score_value, lowerbound, upperbound = None, None, False, False
                current_parameter = None
                for token in arg.split(" "):
                    if current_parameter == "string":
                        # Everything until the end of line is a string
                        if "string" in info:
                            info["string"] += " " + token
                        else:
                            info["string"] = token
                    elif token == "score":
                        current_parameter = "score"
                    elif token == "pv":
                        current_parameter = "pv"
                        if info.get("multipv", 1) == 1:
                            info.pop("pv", None)
                    elif token in ["depth", "seldepth", "time", "nodes", "multipv",
                                "currmove", "currmovenumber",
                                "hashfull", "nps", "tbhits", "cpuload",
                                "refutation", "currline", "string"]:
                        current_parameter = token
                        info.pop(current_parameter, None)
                    elif current_parameter in ["depth", "seldepth", "time",
                                            "nodes", "currmovenumber",
                                            "hashfull", "nps", "tbhits",
                                            "cpuload", "multipv"]:
                        # Integer parameters
                        info[current_parameter] = int(token)
                    elif current_parameter == "score":
                        # Score
                        if token in ["cp", "mate"]:
                            score_kind = token
                            score_value = None
                        elif token == "lowerbound":
                            lowerbound = True
                        elif token == "upperbound":
                            upperbound = True
                        else:
                            score_value = int(token)
                    elif current_parameter != "pv" or info.get("multipv", 1) == 1:
                        # Strings
                        if current_parameter in info:
                            info[current_parameter] += " " + token
                        else:
                            info[current_parameter] = token

                # Set score. Prefer scores that are not just a bound
                if score_kind and score_value is not None and (not (lowerbound or upperbound) or "score" not in info or info["score"].get("lowerbound") or info["score"].get("upperbound")):
                    info["score"] = {score_kind: score_value}
                    if lowerbound:
                        info["score"]["lowerbound"] = lowerbound
                    if upperbound:
                        info["score"]["upperbound"] = upperbound
                self.info = info
            else:
                logger.warning("Unexpected engine response to go: %s %s" % (command, arg))

    def setboard(self, position, moves):
        #self.send("setboard %s moves %s" % (position, moves))
        #logger.debug("setboard %s moves %s" % (position, moves))
        return

    def stop(self):
        self.send("stop")

    def ponderhit(self):
        self.send("ponderhit")
        logger.info("ponderhit")

    def quit(self):
        self.send("quit")
