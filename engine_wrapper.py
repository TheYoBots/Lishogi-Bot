import os
import shogi
import backoff
import subprocess
from util import *

import engine_ctrl

@backoff.on_exception(backoff.expo, BaseException, max_time=120)
def create_engine(config, board):
    cfg = config["engine"]
    engine_path = os.path.join(cfg["dir"], cfg["name"])
    engine_type = cfg.get("protocol")
    engine_options = cfg.get("engine_options")
    commands = [engine_path]
    if engine_options:
        for k, v in engine_options.items():
            commands.append("--{}={}".format(k, v))

    silence_stderr = cfg.get("silence_stderr", False)

    return USIEngine(board, commands, cfg.get("usi_options", {}) or {}, silence_stderr)


class EngineWrapper:

    def __init__(self, board, commands, options=None, silence_stderr=False):
        pass

    def set_time_control(self, game):
        pass

    def first_search(self, board, movetime):
        pass

    def search(self, board, wtime, btime, winc, binc):
        pass

    def print_stats(self):
        pass

    def get_opponent_info(self, game):
        pass

    def name(self):
        return self.engine.name

    def quit(self):
        self.engine.kill_process()

    def print_handler_stats(self, info, stats):
        for stat in stats:
            if stat in info:
                print("    {}: {}".format(stat, info[stat]))

    def get_handler_stats(self, info, stats):
        stats_str = []
        for stat in stats:
            if stat in info:
                stats_str.append("{}: {}".format(stat, info[stat]))

        return stats_str


class USIEngine(EngineWrapper):

    def __init__(self, board, commands, options, silence_stderr=False):
        commands = commands[0] if len(commands) == 1 else commands
        self.go_commands = options.get("go_commands", {})
        print("GO, OPTIONS:", options)

        self.engine = engine_ctrl.Engine(commands)
        self.engine.usi()

        if options:
            for name, value in options["options"].items():
                self.engine.setoption(name, value)

    def first_search(self, board, movetime):
        best_move, _ = self.engine.go(board.sfen(), "", movetime=movetime)
        return best_move

    def search_with_ponder(self, board, wtime, btime, winc, binc, ponder=False):
        moves = [m.usi() for m in list(board.move_stack)]
        best_move, ponder_move = self.engine.go(
            board.sfen(),
            moves,
            wtime=wtime,
            btime=btime,
            winc=winc,
            binc=binc,
            #ponder=ponder
        )
        return (best_move, ponder_move)

    def search(self, board, wtime, btime, winc, binc):
        cmds = self.go_commands
        moves = [m.usi() for m in list(board.move_stack)]
        best_move, _ = self.engine.go(
            board.sfen(),
            moves,
            wtime=wtime,
            btime=btime,
            winc=winc,
            binc=binc,
            depth=cmds.get("depth"),
            nodes=cmds.get("nodes"),
            movetime=cmds.get("movetime")
        )
        return best_move


    def stop(self):
        self.engine.kill_process()

    def print_stats(self):
        pass

    def get_stats(self):
        pass

    def get_opponent_info(self, game):
        name = game.opponent.name
        if name:
            rating = game.opponent.rating if game.opponent.rating is not None else "none"
            title = game.opponent.title if game.opponent.title else "none"
            player_type = "computer" if title == "BOT" else "human"
