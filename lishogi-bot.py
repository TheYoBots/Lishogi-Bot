import argparse
import shogi
import engine_wrapper
import model
import json
import lishogi
import logging
import logging.handlers
import multiprocessing
import signal
import time
import backoff
import sys
import threading
import random
import traceback
from config import load_config
from conversation import Conversation, ChatLine
from requests.exceptions import ChunkedEncodingError, ConnectionError, HTTPError, ReadTimeout
from rich.logging import RichHandler
import copy
from collections import defaultdict
from http.client import RemoteDisconnected

logger = logging.getLogger(__name__)

__version__ = "1.1.1"

terminated = False


def signal_handler(signal, frame):
    global terminated
    logger.debug("Recieved SIGINT. Terminating client.")
    terminated = True


signal.signal(signal.SIGINT, signal_handler)


def is_final(exception):
    return isinstance(exception, HTTPError) and exception.response.status_code < 500


def upgrade_account(li):
    if li.upgrade_to_bot_account() is None:
        return False

    logger.info("Succesfully upgraded to Bot Account!")
    return True


def watch_control_stream(control_queue, li):
    while not terminated:
        try:
            response = li.get_event_stream()
            lines = response.iter_lines()
            for line in lines:
                if line:
                    event = json.loads(line.decode("utf-8"))
                    control_queue.put_nowait(event)
                else:
                    control_queue.put_nowait({"type": "ping"})
        except:
            pass


def do_correspondence_ping(control_queue, period):
    while not terminated:
        time.sleep(period)
        control_queue.put_nowait({"type": "correspondence_ping"})


def logging_configurer(level, filename):
    console_handler = RichHandler()
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    all_handlers = [console_handler]

    if filename:
        file_handler = logging.FileHandler(filename, delay=True)
        FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"
        file_formatter = logging.Formatter(FORMAT)
        file_handler.setFormatter(file_formatter)
        all_handlers.append(file_handler)

    logging.basicConfig(level=level,
                        handlers=all_handlers,
                        force=True)


def logging_listener_proc(queue, configurer, level, log_filename):
    configurer(level, log_filename)
    logger = logging.getLogger()
    while not terminated:
        try:
            logger.handle(queue.get())
        except Exception:
            pass


def game_logging_configurer(queue, level):
    if sys.platform == "win32":
        h = logging.handlers.QueueHandler(queue)
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(h)
        root.setLevel(level)


def game_error_handler(error):
    logger.error("".join(traceback.format_exception(error)))


def start(li, user_profile, config, logging_level, log_filename, one_game=False):
    challenge_config = config["challenge"]
    max_games = challenge_config.get("concurrency", 1)
    logger.info(f"You're now connected to {config['url']} and awaiting challenges.")
    manager = multiprocessing.Manager()
    challenge_queue = manager.list()
    control_queue = manager.Queue()
    control_stream = multiprocessing.Process(target=watch_control_stream, args=[control_queue, li])
    control_stream.start()
    correspondence_cfg = config.get("correspondence") or {}
    correspondence_checkin_period = correspondence_cfg.get("checkin_period", 600)
    correspondence_pinger = multiprocessing.Process(target=do_correspondence_ping, args=[control_queue, correspondence_checkin_period])
    correspondence_pinger.start()
    correspondence_queue = manager.Queue()
    correspondence_queue.put("")
    startup_correspondence_games = [game["gameId"] for game in li.get_ongoing_games() if game["perf"] == "correspondence"]
    wait_for_correspondence_ping = False

    busy_processes = 0
    queued_processes = 0


    logging_queue = manager.Queue()
    logging_listener = multiprocessing.Process(target=logging_listener_proc, args=(logging_queue, logging_configurer, logging_level, log_filename))
    logging_listener.start()

    with multiprocessing.pool.Pool(max_games + 1) as pool:
        while not terminated:
            try:
                event = control_queue.get()
            except InterruptedError:
                continue

            if event.get("type") is None:
                logger.warning("Unable to handle response from lishogi.org:")
                logger.warning(event)
                if event.get("error") == "Missing scope":
                    logger.warning('Please check that the API access token for your bot has the scope "Play games with the bot API" (bot:play).')
                continue

            if event["type"] == "terminated":
                break
            elif event["type"] == "local_game_done":
                busy_processes -= 1
                logger.info(f"+++ Process Free. Total Queued: {queued_processes}. Total Used: {busy_processes}")
                if one_game:
                    break
            elif event["type"] == "challenge":
                chlng = model.Challenge(event["challenge"])
                if chlng.is_supported(challenge_config):
                    challenge_queue.append(chlng)
                    if challenge_config.get("sort_by", "best") == "best":
                        list_c = list(challenge_queue)
                        list_c.sort(key=lambda c: -c.score())
                        challenge_queue = list_c
                else:
                    try:
                        li.decline_challenge(chlng.id)
                        logger.info(f"Decline {chlng}")
                    except:
                        pass
            elif event["type"] == "gameStart":
                game_id = event["game"]["id"]
                if game_id in startup_correspondence_games:
                    logger.info(f'--- Enqueue {config["url"] + game_id}')
                    correspondence_queue.put(game_id)
                    startup_correspondence_games.remove(game_id)
                else:
                    if queued_processes > 0:
                        queued_processes -= 1
                    busy_processes += 1
                    logger.info(f"--- Process Used. Total Queued: {queued_processes}. Total Used: {busy_processes}")
                    pool.apply_async(play_game, [li, game_id, control_queue, user_profile, config, challenge_queue, correspondence_queue, logging_queue, game_logging_configurer, logging_level], error_callback=game_error_handler)

            is_correspondence_ping = event["type"] == "correspondence_ping"
            is_local_game_done = event["type"] == "local_game_done"
            if (is_correspondence_ping or (is_local_game_done and not wait_for_correspondence_ping)) and not challenge_queue:
                if is_correspondence_ping and wait_for_correspondence_ping:
                    correspondence_queue.put("")

                wait_for_correspondence_ping = False
                while (busy_processes + queued_processes) < max_games:
                    game_id = correspondence_queue.get()
                    # stop checking in on games if we have checked in on all games since the last correspondence_ping
                    if not game_id:
                        if is_correspondence_ping and not correspondence_queue.empty():
                            correspondence_queue.put("")
                        else:
                            wait_for_correspondence_ping = True
                            break
                    else:
                        busy_processes += 1
                        logger.info(f"--- Process Used. Total Queued: {queued_processes}. Total Used: {busy_processes}")
                        pool.apply_async(play_game, [li, game_id, control_queue, user_profile, config, challenge_queue, correspondence_queue, logging_queue, game_logging_configurer, logging_level], error_callback=game_error_handler)

            while (queued_processes + busy_processes) < max_games and challenge_queue:  # keep processing the queue until empty or max_games is reached
                chlng = challenge_queue.pop(0)
                try:
                    logger.info(f"Accept {chlng}")
                    queued_processes += 1
                    li.accept_challenge(chlng.id)
                    logger.info(f"--- Process Queue. Total Queued: {queued_processes}. Total Used: {busy_processes}")
                except (HTTPError, ReadTimeout) as exception:
                    if isinstance(exception, HTTPError) and exception.response.status_code == 404:  # ignore missing challenge
                        logger.info(f"Skip missing {chlng}")
                    queued_processes -= 1

            control_queue.task_done()

    logger.info("Terminated")
    control_stream.terminate()
    control_stream.join()
    correspondence_pinger.terminate()
    correspondence_pinger.join()
    logging_listener.terminate()
    logging_listener.join()


ponder_results = {}


@backoff.on_exception(backoff.expo, BaseException, max_time=600, giveup=is_final)
def play_game(li, game_id, control_queue, user_profile, config, challenge_queue, correspondence_queue, logging_queue, game_logging_configurer, logging_level):
    game_logging_configurer(logging_queue, logging_level)
    logger = logging.getLogger(__name__)

    response = li.get_game_stream(game_id)
    lines = response.iter_lines()

    # Initial response of stream will be the full game info. Store it
    initial_state = json.loads(next(lines).decode("utf-8"))
    game = model.Game(initial_state, user_profile["username"], li.baseUrl, config.get("abort_time", 20))

    engine = engine_wrapper.create_engine(config)
    engine.get_opponent_info(game)
    conversation = Conversation(game, engine, li, __version__, challenge_queue)

    logger.info(f"+++ {game}")

    is_correspondence = game.perf_name == "Correspondence"
    correspondence_cfg = config.get("correspondence") or {}
    correspondence_move_time = correspondence_cfg.get("move_time", 60) * 1000

    engine_cfg = config["engine"]
    ponder_cfg = correspondence_cfg if is_correspondence else engine_cfg
    can_ponder = ponder_cfg.get("ponder", False)
    move_overhead = config.get("move_overhead", 1000)
    delay_seconds = config.get("rate_limiting_delay", 0)/1000
    online_moves_cfg = engine_cfg.get("online_moves", {})

    ponder_thread = None
    ponder_usi = None

    logger.debug(f"Game state: {game.state}")

    greeting_cfg = config.get("greeting") or {}
    keyword_map = defaultdict(str, me=game.me.name, opponent=game.opponent.name)
    get_greeting = lambda greeting: str(greeting_cfg.get(greeting) or "").format_map(keyword_map)
    hello = get_greeting("hello")
    goodbye = get_greeting("goodbye")

    first_move = True
    correspondence_disconnect_time = 0

    while not terminated:
        move_attempted = False
        try:
            if first_move:
                upd = game.state
                first_move = False
            else:
                binary_chunk = next(lines)
                upd = json.loads(binary_chunk.decode("utf-8")) if binary_chunk else None

            logger.debug(f"Update: {upd}")
            u_type = upd["type"] if upd else "ping"
            if u_type == "chatLine":
                conversation.react(ChatLine(upd), game)
            elif u_type == "gameState":
                game.state = upd
                board = setup_board(game)
                if not is_game_over(game) and is_engine_move(game, board):
                    if len(board.move_stack) < 2:
                        conversation.send_message("player", hello)
                    start_time = time.perf_counter_ns()
                    fake_thinking(config, board, game)
                    print_move_number(board)
                    correspondence_disconnect_time = correspondence_cfg.get("disconnect_time", 300)

                    if len(board.move_stack) < 2:
                        best_move, ponder_move = choose_first_move(engine, board, game)
                    elif is_correspondence:
                        best_move, ponder_move = choose_move_time(engine, board, game, correspondence_move_time)
                    else:
                        best_move, ponder_move = get_pondering_result(engine, game, board.move_stack, ponder_thread, ponder_usi)
                        move_attempted = True
                        if best_move is None:
                            best_move, ponder_move = play_midgame_move(engine, board, upd["btime"], upd["wtime"], move_overhead, start_time, logger, game)
                        if best_move is None:
                            best_move, ponder_move = get_online_move(li, board, game, online_moves_cfg)
                    li.make_move(game.id, best_move)
                    ponder_thread, ponder_usi = start_pondering(engine, board, best_move, ponder_move, upd["btime"], upd["wtime"], game, logger, move_overhead, start_time, can_ponder)
                    time.sleep(delay_seconds)
                elif is_game_over(game):
                    engine.report_game_result(game, board)
                    tell_user_game_result(game, board)
                    conversation.send_message("player", goodbye)
                elif len(board.move_stack) == 0:
                    correspondence_disconnect_time = correspondence_cfg.get("disconnect_time", 300)

                bw = "b" if board.turn == shogi.BLACK else "w"
                game.ping(config.get("abort_time", 30), (upd[f"{bw}time"] + upd[f"{bw}inc"] + upd["byo"]) / 1000 + 60, correspondence_disconnect_time)
            elif u_type == "ping":
                if is_correspondence and not is_engine_move(game, board) and game.should_disconnect_now():
                    break
                elif game.should_abort_now():
                    logger.info(f"Aborting {game.url()} by lack of activity")
                    li.abort(game.id)
                    break
                elif game.should_terminate_now():
                    logger.info(f"Terminating {game.url()} by lack of activity")
                    if game.is_abortable():
                        li.abort(game.id)
                    break
        except (HTTPError, ReadTimeout, RemoteDisconnected, ChunkedEncodingError, ConnectionError):
            if move_attempted:
                continue
            if game.id not in (ongoing_game["gameId"] for ongoing_game in li.get_ongoing_games()):
                break
        except StopIteration:
            break

    engine.stop()
    engine.quit()

    if ponder_thread is not None:
        ponder_thread.join()

    engine.kill_process()

    if is_correspondence and not is_game_over(game):
        logger.info(f"--- Disconnecting from {game.url()}")
        correspondence_queue.put(game_id)
    else:
        logger.info(f"--- {game.url()} Game over")

    control_queue.put_nowait({"type": "local_game_done"})


def play_midgame_move(engine, board, btime, wtime, move_overhead, start_time, logger, game):
    btime, wtime = adjust_game_time(btime, wtime, board, move_overhead, start_time)
    logger.info(f"Searching for btime {btime} wtime {wtime}")
    best_move, ponder_move = engine.search_with_ponder(game, board, btime, wtime, game.state["binc"], game.state["winc"], game.state["byo"])
    return best_move, ponder_move


def adjust_game_time(btime, wtime, board, move_overhead, start_time, binc=0, winc=0, byo=0):
    if board.turn == shogi.BLACK:
        btime = max(0, btime - move_overhead - int((time.perf_counter_ns() - start_time) / 1000000)) + binc + byo
    else:
        wtime = max(0, wtime - move_overhead - int((time.perf_counter_ns() - start_time) / 1000000)) + winc + byo
    return btime, wtime


def start_pondering(engine, board, best_move, ponder_move, btime, wtime, game, logger, move_overhead, start_time, can_ponder):
    if not can_ponder or ponder_move is None:
        return None, None
    ponder_board = copy.deepcopy(board)
    if game.variant_name == "Standard":
        ponder_board.push(shogi.Move.from_usi(best_move))
        ponder_board.push(shogi.Move.from_usi(ponder_move))
    else:
        ponder_board.push(shogi.Move.null())
        ponder_board.push(shogi.Move.null())
    ponder_usi = ponder_move

    btime, wtime = adjust_game_time(btime, wtime, board, move_overhead, start_time, game.state["winc"], game.state["binc"], game.state["byo"])
    logger.info(f"Pondering {ponder_move} for btime {btime} wtime {wtime}")

    def ponder_thread_func(game, engine, board, btime, wtime, binc, winc, byo):
        global ponder_results
        best_move, ponder_move = engine.search_with_ponder(game, board, btime, wtime, binc, winc, byo, True)
        ponder_results[game.id] = (best_move, ponder_move)

    ponder_thread = threading.Thread(target=ponder_thread_func, args=(game, engine, ponder_board, btime, wtime, game.state["binc"], game.state["winc"], game.state["byo"]))
    ponder_thread.start()
    return ponder_thread, ponder_usi


def get_pondering_result(engine, game, moves, ponder_thread, ponder_usi):
    if ponder_thread is None:
        return None, None

    if ponder_usi == moves[-1].usi():
        engine.ponderhit()
        ponder_thread.join()
        return ponder_results[game.id]
    else:
        engine.stop()
        ponder_thread.join()
        return None, None


def get_lishogi_cloud_move(li, board, game, lishogi_cloud_cfg):
    bw = "b" if board.turn == shogi.BLACK else "w"
    if not lishogi_cloud_cfg.get("enabled", False) or game.state[f"{bw}time"] < lishogi_cloud_cfg.get("min_time", 20) * 1000:
        return None

    move = None

    quality = lishogi_cloud_cfg.get("move_quality", "best")
    multipv = 1 if quality == "best" else 5
    variant = game.variant_name.lower()

    try:
        data = li.api_get("https://lishogi.org/api/cloud-eval", params={"sfen": board.sfen(), "multiPv": multipv, "variant": variant}, raise_for_status=False)
        if "error" not in data:
            if quality == "best":
                depth = data["depth"]
                knodes = data["knodes"]
                if depth >= lishogi_cloud_cfg.get("min_depth", 20) and knodes >= lishogi_cloud_cfg.get("min_knodes", 0):
                    pv = data["pvs"][0]
                    move = pv["moves"].split()[0]
                    score = pv["cp"]
                    logger.info(f"Got move {move} from lishogi cloud analysis (depth: {depth}, score: {score}, knodes: {knodes})")
            else:
                depth = data["depth"]
                knodes = data["knodes"]
                if depth >= lishogi_cloud_cfg.get("min_depth", 20) and knodes >= lishogi_cloud_cfg.get("min_knodes", 0):
                    best_eval = data["pvs"][0]["cp"]
                    pvs = data["pvs"]
                    max_difference = lishogi_cloud_cfg.get("max_score_difference", 50)
                    if bw == "b":
                        pvs = list(filter(lambda pv: pv["cp"] >= best_eval - max_difference, pvs))
                    else:
                        pvs = list(filter(lambda pv: pv["cp"] <= best_eval + max_difference, pvs))
                    pv = random.choice(pvs)
                    move = pv["moves"].split()[0]
                    score = pv["cp"]
                    logger.info(f"Got move {move} from lishogi cloud analysis (depth: {depth}, score: {score}, knodes: {knodes})")
    except Exception:
        pass

    return move


def get_online_move(li, board, best_move, game, online_moves_cfg):
    lishogi_cloud_cfg = online_moves_cfg.get("lishogi_cloud_analysis", {})
    if best_move is None:
        best_move, ponder_move = get_lishogi_cloud_move(li, board, game, lishogi_cloud_cfg)
    if best_move:
        return shogi.Move.from_usi(best_move, ponder_move)
    return shogi.Move.from_usi(best_move, ponder_move)


def choose_move_time(engine, board, game, search_time):
    logger.info(f"Searching for time {search_time}")
    return engine.search_for(board, game, search_time)


def choose_first_move(engine, board, game):
    # need to hardcode first movetime since Lishogi has 30 sec limit.
    return choose_move_time(engine, board, game, 1000)


def fake_thinking(config, board, game):
    if config.get("fake_think_time") and len(board.move_stack) > 9:
        delay = min(game.clock_initial, game.my_remaining_seconds()) * 0.015
        accel = 1 - max(0, min(100, len(board.move_stack) - 20)) / 150
        sleep = min(5, delay * accel)
        time.sleep(sleep)


def print_move_number(board):
    logger.info("")
    logger.info(f"move: {len(board.move_stack) // 1 + 1}")


def setup_board(game):
    if game.variant_name == "Standard":
        if game.initial_sfen != "startpos":
            board = shogi.Board(game.initial_sfen)
        else:
            board = shogi.Board() # Standard

        for move in game.state["moves"].split():
            usi_move = shogi.Move.from_usi(move)
            if board.is_legal(usi_move):
                board.push(usi_move)
            else:
                logger.debug(f"Ignoring illegal move {move} on board {board.sfen()}")
    else:
        board = shogi.Board()
        for move in game.state["moves"].split():
            board.push(shogi.Move.null())

    return board


def is_engine_move(game, board):
    return game.is_sente == (board.turn == shogi.BLACK)


def is_game_over(game):
    return game.state["status"] != "started"


def tell_user_game_result(game, board):
    winner = game.state.get("winner")
    termination = game.state.get("status")

    winning_name = game.sente.name if winner == "sente" else game.gote.name
    losing_name = game.sente.name if winner == "gote" else game.gote.name

    if winner is not None:
        logger.info(f"{winning_name} won!")
    elif termination == engine_wrapper.Termination.DRAW:
        logger.info("Game ended in draw.")
    else:
        logger.info("Game adjourned.")

    if termination == engine_wrapper.Termination.MATE:
        logger.info("Game won by checkmate.")
    elif termination == engine_wrapper.Termination.TIMEOUT:
        logger.info(f"{losing_name} forfeited on time.")
    elif termination == engine_wrapper.Termination.RESIGN:
        logger.info(f"{losing_name} resigned.")
    elif termination == engine_wrapper.Termination.ABORT:
        logger.info("Game aborted.")
    elif termination == engine_wrapper.Termination.DRAW:
        if board.is_fifty_moves():
            logger.info("Game drawn by 50-move rule.")
        elif board.is_repetition():
            logger.info("Game drawn by threefold repetition.")
        else:
            logger.info("Game drawn by agreement.")
    elif termination:
        logger.info(f"Game ended by {termination}")


def intro():
    return r"""
    .   _/\_
    .  //o o\\
    .  ||    ||  Lishogi-Bot %s
    .  ||    ||
    .  ||____||  Play on Lishogi with a bot
    """ % __version__


def start_lishogi_bot():
    parser = argparse.ArgumentParser(description="Play on Lishogi with a bot")
    parser.add_argument("-u", action="store_true", help="Upgrade your account to a bot account.")
    parser.add_argument("-v", action="store_true", help="Make output more verbose. Include all communication with lishogi.org.")
    parser.add_argument("--config", help="Specify a configuration file (defaults to ./config.yml)")
    parser.add_argument("-l", "--logfile", help="Record all console output to a log file.", default=None)
    args = parser.parse_args()

    logging_level = logging.DEBUG if args.v else logging.INFO
    logging_configurer(logging_level, args.logfile)
    logger.info(intro(), extra={"highlighter": None})
    CONFIG = load_config(args.config or "./config.yml")
    li = lishogi.Lishogi(CONFIG["token"], CONFIG["url"], __version__, logging_level)

    user_profile = li.get_profile()
    username = user_profile["username"]
    is_bot = user_profile.get("title") == "BOT"
    logger.info(f"Welcome {username}!")

    if args.u and not is_bot:
        is_bot = upgrade_account(li)

    if is_bot:
        start(li, user_profile, CONFIG, logging_level, args.logfile)
    else:
        logger.error(f"{username} is not a bot account. Please upgrade it to a bot account!")


if __name__ == "__main__":
    try:
        start_lishogi_bot()
    except Exception as error:
        logger.error(error)
        logger.error(game_error_handler(error))
