import threading
import subprocess
import os
import signal

from util import *


class Engine:
    def __init__(self, command):
        self.proccess = self.open_process(command)
        self.go_commands = None

    def set_go_commands(self, go_comm):
        self.go_commands = go_comm
        print(self.go_commands)
     
    def open_process(self, command, shell=True, _popen_lock=threading.Lock()):
        kwargs = {
            "shell": shell,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "stdin": subprocess.PIPE,
            "bufsize": 1,  # Line buffered
            "universal_newlines": True,
        }
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
        self.proccess.stdin.write(line + "\n")
        self.proccess.stdin.flush()

    def recv(self):
        while True:
            line = self.proccess.stdout.readline()
            if line == "":
                raise EOFError()

            line = line.rstrip()

            if line:
                return line

    def recv_usi(self):
        command_and_args = self.recv().split(None, 1)
        if len(command_and_args) == 1:
            return command_and_args[0], ""
        elif len(command_and_args) == 2:
            return command_and_args

    def usi(self):
        self.send("usi")

        engine_info = {}

        while True:
            command, arg = self.recv_usi()

            if command == "usiok":
                return engine_info
            elif command == "id":
                name_and_value = arg.split(None, 1)
                if len(name_and_value) == 2:
                    engine_info[name_and_value[0]] = name_and_value[1]
            elif command == "option" or command.startswith("Fairy-Stockfish"):
                pass
            else:
                print("Unexpected engine response to usi: %s %s" % (command, arg))

    def isready(self):
        self.send("isready")
        while True:
            command, arg = self.recv_usi()
            if command == "readyok":
                break
            elif command == "info" and arg.startswith("string Error! "):
                print("Unexpected engine response to isready: %s %s" % (command, arg))
            elif command == "info" and arg.startswith("string "):
                pass
            else:
                print("Unexpected engine response to isready: %s %s" % (command, arg))

    def setoption(self, name, value):
        if value is True:
            value = "true"
        elif value is False:
            value = "false"
        elif value is None:
            value = "none"

        self.send("setoption name %s value %s" % (name, value))

    def go(self, position, moves, movetime=None, wtime=None, btime=None, winc=None, binc=None, byo=None, depth=None, nodes=None):
        self.send("position sfen %s moves %s" % (position, " ".join(moves)))
        print("position sfen %s moves %s" % (position, " ".join(moves)))

        builder = []
        builder.append("go")
        if movetime is not None:
            builder.append("movetime")
            builder.append(str(movetime))
        else:
            builder.append("movetime")
            builder.append("1500")
        if depth is not None:
            builder.append("depth")
            builder.append(str(depth))
        if nodes is not None:
            builder.append("nodes")
            builder.append(str(nodes))
        if wtime is not None:
            builder.append("wtime")
            builder.append(str(wtime * 10))
        if btime is not None:
            builder.append("btime")
            builder.append(str(btime * 10))
        if byo is not None:
            builder.append("byoyomi")
            builder.append(str(byo * 1000))
        if winc is not None:
            builder.append("winc")
            builder.append(str(winc * 1000))
        if binc is not None:
            builder.append("binc")
            builder.append(str(binc * 1000))

        self.send(" ".join(builder))
        print(" ".join(builder))

        info = {}
        info["bestmove"] = None

        while True:
            command, arg = self.recv_usi()

            if command == "bestmove":
                bestmove = arg.split()[0]
                if bestmove and bestmove != "(none)":
                    info["bestmove"] = bestmove
                return (info["bestmove"], None)

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
            else:
                print("Unexpected engine response to go: %s %s" % (command, arg))
