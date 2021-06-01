import os
import shogi
import backoff
import subprocess
from util import *
import logging

logger = logging.getLogger(__name__)

import engine_ctrl


@backoff.on_exception(backoff.expo, BaseException, max_time=120)
def create_engine(config, board):
    cfg = config["engine"]
    engine_path = os.path.realpath(os.path.join(cfg["dir"], cfg["name"]))
    engine_type = cfg.get("protocol")
    engine_options = cfg.get("engine_options")
    commands = [engine_path]
    if engine_options:
        for k, v in engine_options.items():
            commands.append("--{}={}".format(k, v))

    silence_stderr = cfg.get("silence_stderr", False)

    return USIEngine(board, commands, cfg.get("usi_options", {}), cfg.get("go_commands", {}), silence_stderr)


class EngineWrapper:
    def __init__(self, board, commands, options=None, silence_stderr=False):
        pass

    def search_for(self, board, movetime):
        pass

    def first_search(self, board, movetime):
        pass

    def search(self, game, board, btime, wtime, binc, winc):
        pass

    def print_stats(self):
        pass

    def get_opponent_info(self, game):
        pass

    def name(self):
        return self.engine.name

    def report_game_result(self, game, board):
        pass

    def quit(self):
        self.engine.kill_process()

    def print_handler_stats(self):
        pass

    def get_handler_stats(self):
        pass


class USIEngine(EngineWrapper):
    def __init__(self, board, commands, options, go_commands={}, silence_stderr=False):
        commands = commands[0] if len(commands) == 1 else commands        
        self.go_commands = go_commands

        self.engine = engine_ctrl.Engine(commands)
        self.engine.usi()

        if options:
            for name, value in options.items():
                self.engine.setoption(name, value)
        self.engine.isready()

    def first_search(self, board, movetime):
        best_move, _ = self.engine.go(board.sfen(), "", movetime=movetime)
        return best_move

    def search_with_ponder(self, game, board, btime, wtime, binc, winc, byo, ponder=False):
        moves = [m.usi() for m in list(board.move_stack)]
        cmds = self.go_commands        
        if len(cmds) > 0:
               best_move, ponder_move = self.engine.go(
                   game.initial_fen,
                   moves,
                   nodes=cmds.get("nodes"),
                   depth=cmds.get("depth"),
                   movetime=cmds.get("movetime"),
                   ponder=ponder
               )
        else:
               best_move, ponder_move = self.engine.go(
                   game.initial_fen,
                   moves,
                   btime=btime,
                   wtime=wtime,
                   binc=binc,
                   winc=winc,
                   byo=byo,
                   ponder=ponder
               )
        return (best_move, ponder_move)

    def search(self, game, board, btime, wtime, binc, winc):
        cmds = self.go_commands
        moves = [m.usi() for m in list(board.move_stack)]
        best_move, _ = self.engine.go(
            game.initial_fen,
            moves,
            btime=btime,
            wtime=wtime,
            binc=binc,
            winc=winc,
            depth=cmds.get("depth"),
            nodes=cmds.get("nodes"),
            movetime=cmds.get("movetime")
        )
        return best_move

    def stop(self):
        self.engine.kill_process()

    def print_stats(self, stats=None):
        if stats is None:
            stats = ['score', 'depth', 'nodes', 'nps']
        info = self.engine.info
        for stat in stats:
            if stat in info:
                logger.info("{}: {}".format(stat, info[stat]))

    def get_stats(self, stats=None):
        if stats is None:
            stats = ['score', 'depth', 'nodes', 'nps']
        info = self.engine.info
        stats_str = []
        for stat in stats:
            if stat in info:
                stats_str.append("{}: {}".format(stat, info[stat]))
        return stats_str

    def get_opponent_info(self, game):
        name = game.opponent.name
        if name:
            rating = game.opponent.rating if game.opponent.rating is not None else "none"
            title = game.opponent.title if game.opponent.title else "none"
            player_type = "computer" if title == "BOT" else "human"
    
    def report_game_result(self, game, board):
        self.engine.protocol._position(board)
