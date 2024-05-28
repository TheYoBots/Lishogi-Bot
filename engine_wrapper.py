import os
import backoff
import logging
from enum import Enum

logger = logging.getLogger(__name__)

from engine_ctrl import usi


@backoff.on_exception(backoff.expo, BaseException, max_time=120)
def create_engine(config):
    cfg = config["engine"]
    engine_path = os.path.realpath(os.path.join(cfg["dir"], cfg["name"]))
    engine_working_dir = cfg.get("working_dir") or os.getcwd()
    engine_type = cfg.get("protocol")
    engine_options = cfg.get("engine_options")
    usi_options = cfg.get("usi_options") or {}
    commands = [engine_path]
    if engine_options:
        for k, v in engine_options.items():
            commands.append(f"--{k}={v}")
    go_commands = cfg.get("go_commands") or {}

    silence_stderr = cfg.get("silence_stderr", False)

    if engine_type == "homemade":
        Engine = getHomemadeEngine(cfg["name"])
    elif engine_type == "usi":
        Engine = USIEngine
    else:
        raise ValueError(
            f"Invalid engine type: {engine_type}. Expected usi or homemade.")

    logger.debug(f"Starting engine: {' '.join(commands)}")
    return Engine(commands, usi_options, go_commands, silence_stderr, cwd=engine_working_dir)


class Termination(str, Enum):
    MATE = "mate"
    TIMEOUT = "outoftime"
    RESIGN = "resign"
    ABORT = "aborted"
    DRAW = "draw"
    STALEMATE = "stalemate"
    TRYRULE = "tryRule"
    IMPASSE = "impasse27"
    PERPETUALCHECK = "perpetualCheck"


class EngineWrapper:
    def __init__(self, go_commands):
        self.go_commands = go_commands
        pass

    def search_for(self, board, game, movetime):
        if game.variant_name == "Kyoto shogi":
            moves = game.state["fairyMoves"].split()
        else:
            moves = "" if game.variant_name == "Standard" else game.state["moves"].split()
        sfen = board.sfen() if game.variant_name == "Standard" else game.initial_sfen
        self.engine.set_variant_options(game.variant_name.lower())
        return self.search(sfen, moves, movetime=movetime)
    
    def search_with_ponder(self, game, board, btime, wtime, binc, winc, byo, ponder=False):
        if game.variant_name == "Kyoto shogi":
            moves = game.state["fairyMoves"].split()
        else:
            moves = [m.usi() for m in list(board.move_stack)] if game.variant_name == "Standard" else game.state["moves"].split()
        sfen = game.initial_sfen
        cmds = self.go_commands
        movetime = cmds.get("movetime")
        if movetime is not None:
            movetime = float(movetime)
        best_move, ponder_move = self.search(sfen,
                                             moves,
                                             btime=btime,
                                             wtime=wtime,
                                             binc=binc,
                                             winc=winc,
                                             byo=byo,
                                             nodes=cmds.get("nodes"),
                                             depth=cmds.get("depth"),
                                             movetime=movetime,
                                             ponder=ponder)
        return best_move, ponder_move
    
    def search(self, sfen, moves, btime=None, wtime=None, binc=None, winc=None, byo=None, nodes=None, depth=None, movetime=None, ponder=False):
        best_move, ponder_move = self.engine.go(sfen,
                                                moves,
                                                btime=btime,
                                                wtime=wtime,
                                                binc=binc,
                                                winc=winc,
                                                byo=byo,
                                                nodes=nodes,
                                                depth=depth,
                                                movetime=movetime,
                                                ponder=ponder)
        self.print_stats()
        return best_move, ponder_move

    def print_stats(self, stats=None):
        for line in self.get_stats(stats=stats):
            logger.info(f"{line}")

    def get_stats(self, stats=None):
        if stats is None:
            stats = ["score", "depth", "nodes", "nps"]
        info = self.engine.info
        return [f"{stat}: {info[stat]}" for stat in stats if stat in info]

    def get_opponent_info(self, game):
        pass

    def name(self):
        return self.engine.id["name"]

    def report_game_result(self, game, moves):
        pass

    def ponderhit(self):
        pass

    def stop(self):
        pass

    def quit(self):
        pass

    def kill_process(self):
        pass


class USIEngine(EngineWrapper):
    def __init__(self, commands, options, go_commands, silence_stderr=False, cwd=None):
        commands = commands[0] if len(commands) == 1 else commands
        super(USIEngine, self).__init__(go_commands)

        self.engine = usi.Engine(commands, cwd=cwd)
        self.engine.usi()

        if options:
            for name, value in options.items():
                self.engine.setoption(name, value)
        self.engine.isready()

    def ponderhit(self):
        self.engine.ponderhit()

    def stop(self):
        self.engine.stop()

    def quit(self):
        self.engine.quit()

    def kill_process(self):
        self.engine.kill_process()

    def get_opponent_info(self, game):
        name = game.opponent.name
        if name:
            rating = game.opponent.rating if game.opponent.rating is not None else "none"
            title = game.opponent.title if game.opponent.title else "none"
            player_type = "computer" if title == "BOT" else "human"

    def report_game_result(self, game, moves):
        self.engine.position(game.initial_sfen, moves)


def getHomemadeEngine(name):
    import strategies
    return eval(f"strategies.{name}")
