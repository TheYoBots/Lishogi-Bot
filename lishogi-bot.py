import argparse
import shogi
import engine_wrapper
import model
import json
import lishogi
import logging
import logging.handlers
import multiprocessing
import logging_pool
import signal
import time
import backoff
import sys
import threading
from config import load_config
from conversation import Conversation, ChatLine
from functools import partial
from requests.exceptions import ChunkedEncodingError, ConnectionError, HTTPError, ReadTimeout
from urllib3.exceptions import ProtocolError
from ColorLogger import enable_color_logging
from util import *
import copy

logger = logging.getLogger(__name__)

from http.client import RemoteDisconnected

__version__ = "1.1.0"

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
                    event = json.loads(line.decode('utf-8'))
                    control_queue.put_nowait(event)
                else:
                    control_queue.put_nowait({"type": "ping"})
        except:
            pass


def do_correspondence_ping(control_queue, period):
    while not terminated:
        time.sleep(period)
        control_queue.put_nowait({"type": "correspondence_ping"})
        
def listener_configurer(level, filename):
    logging.basicConfig(level=level, filename=filename,
                        format="%(asctime)-15s: %(message)s")
    enable_color_logging(level)


def logging_listener_proc(queue, configurer, level, log_filename):
    configurer(level, log_filename)
    logger = logging.getLogger()
    while not terminated:
        try:
            logger.handle(queue.get())
        except Exception:
            pass


def game_logging_configurer(queue, level):
    if sys.platform == 'win32':
        h = logging.handlers.QueueHandler(queue)
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(h)
        root.setLevel(level)


def start(li, user_profile, engine_factory, config, logging_level, log_filename, one_game=False):
    challenge_config = config["challenge"]
    max_games = challenge_config.get("concurrency", 1)
    logger.info("You're now connected to {} and awaiting challenges.".format(config["url"]))
    manager = multiprocessing.Manager()
    challenge_queue = manager.list()
    control_queue = manager.Queue()
    control_stream = multiprocessing.Process(target=watch_control_stream, args=[control_queue, li])
    control_stream.start()
    correspondence_cfg = config.get("correspondence", {}) or {}
    correspondence_checkin_period = correspondence_cfg.get("checkin_period", 600)
    correspondence_pinger = multiprocessing.Process(target=do_correspondence_ping, args=[control_queue, correspondence_checkin_period])
    correspondence_pinger.start()
    correspondence_queue = manager.Queue()
    correspondence_queue.put("")
    wait_for_correspondence_ping = False
    busy_processes = 0
    queued_processes = 0


    logging_queue = manager.Queue()
    logging_listener = multiprocessing.Process(target=logging_listener_proc, args=(logging_queue, listener_configurer, logging_level, log_filename))
    logging_listener.start()


    with logging_pool.LoggingPool(max_games + 1) as pool:
        while not terminated:
            try:
                event = control_queue.get()
            except InterruptedError:
                continue
            if event["type"] == "terminated":
                break
            elif event["type"] == "local_game_done":
                busy_processes -= 1
                logger.info("+++ Process Free. Total Queued: {}. Total Used: {}".format(queued_processes, busy_processes))
                if one_game:
                    break
            elif event["type"] == "challenge":
                chlng = model.Challenge(event["challenge"])
                if chlng.is_supported(challenge_config):
                    challenge_queue.append(chlng)
                    if (challenge_config.get("sort_by", "best") == "best"):
                        list_c = list(challenge_queue)
                        list_c.sort(key=lambda c: -c.score())
                        challenge_queue = list_c
                else:
                    try:
                        li.decline_challenge(chlng.id)
                        logger.info("Decline {}".format(chlng))
                    except:
                        pass
            elif event["type"] == "gameStart":
                if queued_processes <= 0:
                    logger.debug("Something went wrong. Game is starting and we don't have a queued process")
                else:
                    queued_processes -= 1
                busy_processes += 1
                logger.info("--- Process Used. Total Queued: {}. Total Used: {}".format(queued_processes, busy_processes))
                game_id = event["game"]["id"]
                pool.apply_async(play_game, [li, game_id, control_queue, engine_factory, user_profile, config, challenge_queue, correspondence_queue, logging_queue, game_logging_configurer, logging_level])

            if event["type"] == "correspondence_ping" or (event["type"] == "local_game_done" and not wait_for_correspondence_ping):
                if event["type"] == "correspondence_ping" and wait_for_correspondence_ping:
                    correspondence_queue.put("")

                wait_for_correspondence_ping = False
                while (busy_processes + queued_processes) < max_games:
                    game_id = correspondence_queue.get()
                    # stop checking in on games if we have checked in on all games since the last correspondence_ping
                    if not game_id:
                        wait_for_correspondence_ping = True
                        break
                    else:
                        busy_processes += 1
                        logger.info("--- Process Used. Total Queued: {}. Total Used: {}".format(queued_processes, busy_processes))
                        pool.apply_async(play_game, [li, game_id, control_queue, engine_factory, user_profile, config, challenge_queue, correspondence_queue, logging_queue, game_logging_configurer, logging_level])

            while ((queued_processes + busy_processes) < max_games and challenge_queue):  # keep processing the queue until empty or max_games is reached
                chlng = challenge_queue.pop(0)
                try:
                    logger.info("Accept {}".format(chlng))
                    queued_processes += 1
                    li.accept_challenge(chlng.id)
                    logger.info("--- Process Queue. Total Queued: {}. Total Used: {}".format(queued_processes, busy_processes))
                except (HTTPError, ReadTimeout) as exception:
                    if isinstance(exception, HTTPError) and exception.response.status_code == 404:  # ignore missing challenge
                        logger.info("Skip missing {}".format(chlng))
                    queued_processes -= 1

            control_queue.task_done()
                    
    logger.info("Terminated")
    control_stream.terminate()
    control_stream.join()
    correspondence_pinger.terminate()
    correspondence_pinger.join()
    logging_listener.terminate()
    logging_listener.join()


@backoff.on_exception(backoff.expo, BaseException, max_time=600, giveup=is_final)
def play_game(li, game_id, control_queue, engine_factory, user_profile, config, challenge_queue, correspondence_queue, logging_queue, logging_configurer, logging_level):
    logging_configurer(logging_queue, logging_level)
    logger = logging.getLogger(__name__)

    response = li.get_game_stream(game_id)
    lines = response.iter_lines()

    # Initial response of stream will be the full game info. Store it
    initial_state = json.loads(next(lines).decode('utf-8'))
    game = model.Game(initial_state, user_profile["username"], li.baseUrl, config.get("abort_time", 20))
    board = setup_board(game)
    engine = engine_factory(board)
    engine.get_opponent_info(game)
    conversation = Conversation(game, engine, li, __version__, challenge_queue)

    logger.info("+++ {}".format(game))

    is_correspondence = game.perf_name == "Correspondence"
    correspondence_cfg = config.get("correspondence", {}) or {}
    correspondence_move_time = correspondence_cfg.get("move_time", 60) * 1000

    engine_cfg = config["engine"]
    is_usi = engine_cfg["protocol"] == "usi"
    is_usi_ponder = is_usi and engine_cfg.get("ponder", False)
    move_overhead = config.get("move_overhead", 1000)
    delay_seconds = config.get("rate_limiting_delay", 0)/1000
    polyglot_cfg = engine_cfg.get("polyglot", {})
    book_cfg = polyglot_cfg.get("book", {})

    ponder_thread = None
    deferredFirstMove = False

    ponder_usi = None
    
    def ponder_thread_func(game, engine, board, btime, wtime, binc, winc, byo):
        global ponder_results        
        best_move, ponder_move = engine.search_with_ponder(game, board, btime, wtime, binc, winc, byo, True)
        ponder_results[game.id] = ( best_move, ponder_move )

    logger.debug("Game state: {}".format(game.state))

    if len(board.move_stack) < 2:
        while not terminated:
            try:
                if not play_first_move(game, engine, board, li):
                    deferredFirstMove = True
                break
            except (HTTPError) as exception:
                if exception.response.status_code == 400:  # fallthrough
                    break
    else:
        moves = game.state["moves"].split()
        if not is_game_over(game) and is_engine_move(game, moves):
            best_move = None
            ponder_move = None
            btime = game.state["btime"]
            wtime = game.state["wtime"]
            start_time = time.perf_counter_ns()
            
            if board.turn == shogi.BLACK:
                btime = max(0, btime - move_overhead - int((time.perf_counter_ns() - start_time) / 1000000))
            else:
                wtime = max(0, wtime - move_overhead - int((time.perf_counter_ns() - start_time) / 1000000))
            logger.info("Searching for btime {} wtime {}".format(btime, wtime))
            best_move, ponder_move = engine.search_with_ponder(game, board, btime, wtime, game.state["binc"], game.state["winc"], game.state["byo"])
            engine.print_stats()

            if is_usi_ponder and not ( ponder_move is None ):
                ponder_board = copy.deepcopy(board)
                ponder_board.push(shogi.Move.from_usi(best_move))
                ponder_board.push(shogi.Move.from_usi(ponder_move))
                ponder_usi = ponder_move
                
                if board.turn == shogi.BLACK:
                    btime = max(0, btime - move_overhead - int((time.perf_counter_ns() - start_time) / 1000000) + game.state["binc"])
                else:
                    wtime = max(0, wtime - move_overhead - int((time.perf_counter_ns() - start_time) / 1000000) + game.state["winc"])
                logger.info("Pondering for btime {} wtime {}".format(btime, wtime))
                ponder_thread = threading.Thread(target=ponder_thread_func, args=(game, engine, ponder_board, btime, wtime, game.state["binc"], game.state["winc"], game.state["byo"]))
                ponder_thread.start()
            li.make_move(game.id, best_move)
            time.sleep(delay_seconds)
        elif is_game_over(game):
            engine.report_game_result(game, board)
        elif len(board.move_stack) == 0:
            correspondence_disconnect_time = correspondence_cfg.get("disconnect_time", 300)

    correspondence_disconnect_time = 0
    while not terminated:
        try:
            binary_chunk = next(lines)
        
            upd = json.loads(binary_chunk.decode('utf-8')) if binary_chunk else None
            logger.debug("Update: {}".format(upd))
            u_type = upd["type"] if upd else "ping"
            if u_type == "chatLine":
                conversation.react(ChatLine(upd), game)
            elif u_type == "gameState":
                game.state = upd
                moves = upd["moves"].split()
                if len(moves) > 0 and len(moves) != len(board.move_stack):
                    board = update_board(board, moves[-1])
                if not is_game_over(game) and is_engine_move(game, moves):
                    start_time = time.perf_counter_ns()
                    fake_thinking(config, board, game)
                    print_move_number(board)
                    correspondence_disconnect_time = correspondence_cfg.get("disconnect_time", 300)

                    best_move = None
                    ponder_move = None

                    btime = upd["btime"]
                    wtime = upd["wtime"]
                    start_time = time.perf_counter_ns()

                    if not deferredFirstMove:
                        if best_move == None:
                            if board.turn == shogi.BLACK:
                                btime = max(0, btime - move_overhead - int((time.perf_counter_ns() - start_time) / 1000000))
                            else:
                                wtime = max(0, wtime - move_overhead - int((time.perf_counter_ns() - start_time) / 1000000))
                            logger.info("Searching for btime {} wtime {}".format(btime, wtime))
                            best_move, ponder_move = engine.search_with_ponder(game, board, btime, wtime, upd["binc"], upd["winc"], upd["byo"])
                            engine.print_stats()

                        if is_usi_ponder and not ( ponder_move is None ):
                            ponder_board = copy.deepcopy(board)
                            ponder_board.push(shogi.Move.from_usi(best_move))
                            ponder_board.push(shogi.Move.from_usi(ponder_move))
                            ponder_usi = ponder_move
                            if board.turn == shogi.BLACK:
                                btime = max(0, btime - move_overhead - int((time.perf_counter_ns() - start_time) / 1000000) + upd["binc"])
                            else:
                                wtime = max(0, wtime - move_overhead - int((time.perf_counter_ns() - start_time) / 1000000) + upd["winc"])
                            logger.info("Pondering for btime {} wtime {}".format(btime, wtime))
                            ponder_thread = threading.Thread(target=ponder_thread_func, args=(game, engine, ponder_board, btime, wtime, upd["binc"], upd["winc"], upd["byo"]))
                            ponder_thread.start()
                        li.make_move(game.id, best_move)
                    else:
                        play_first_move(game, engine, board, li)
                        deferredFirstMove = False
                wb = 'w' if board.turn == shogi.BLACK else 'b'
                game.ping(config.get("abort_time", 30), (upd[f"{wb}time"] + upd[f"{wb}inc"]) / 1000 + 60, correspondence_disconnect_time)
            elif u_type == "ping":
                if is_correspondence and not is_engine_move(game, board) and game.should_disconnect_now():
                    break
                elif game.should_abort_now():
                    logger.info("Aborting {} by lack of activity".format(game.url()))
                    li.abort(game.id)
                    break
                elif game.should_terminate_now():
                    logger.info("Terminating {} by lack of activity".format(game.url()))
                    if game.is_abortable():
                        li.abort(game.id)
                    break
        except (HTTPError, ReadTimeout, RemoteDisconnected, ChunkedEncodingError, ConnectionError, ProtocolError):
            if game.id not in (ongoing_game["gameId"] for ongoing_game in li.get_ongoing_games()):
                break
        except StopIteration:
            break

    engine.stop()
    if not ( ponder_thread is None ):
        ponder_thread.join()

    if is_correspondence and not is_game_over(game):
        logger.info("--- Disconnecting from {}".format(game.url()))
        correspondence_queue.put(game_id)
    else:
        logger.info("--- {} Game over".format(game.url()))

    control_queue.put_nowait({"type": "local_game_done"})


def choose_move_time(engine, board, search_time, ponder):
    logger.info("Searching for time {}".format(search_time))
    return engine.search_for(board, search_time, ponder)

def play_first_move(game, engine, board, li):
    moves = game.state["moves"].split()
    if is_engine_move(game, moves):
        # need to hardcode first movetime since Lishogi has 30 sec limit.
        best_move = engine.first_search(board, 1000)
        engine.print_stats()
        li.make_move(game.id, best_move)
        return True
    return False


def play_first_book_move(game, engine, board, li, config):
    pass


def get_book_move(board, config):
    pass


def fake_thinking(config, board, game):
    if config.get("fake_think_time") and len(board.move_stack) > 9:
        delay = min(game.clock_initial, game.my_remaining_seconds()) * 0.015
        accel = 1 - max(0, min(100, len(board.move_stack) - 20)) / 150
        sleep = min(5, delay * accel)
        time.sleep(sleep)


def print_move_number(board):
    logger.info("")
    logger.info("move: {}".format(len(board.move_stack) // 1 + 1))


def setup_board(game):
    if game.variant_name == "From Position":
        board = shogi.Board(game.initial_fen)
    else:
        board = shogi.Board() # Standard
    moves = game.state["moves"].split()
    for move in moves:
        board = update_board(board, move)

    return board


def is_sente_to_move(game, moves):
    return len(moves) % 2 == (0 if game.sente_starts else 1)


def is_engine_move(game, moves):
    return game.is_sente == is_sente_to_move(game, moves)


def is_game_over(game):
    return game.state["status"] != "started"


def update_board(board, move):
    usi_move = shogi.Move.from_usi(makeusi(move))
    if board.is_legal(usi_move):
        board.push(usi_move)
    else:
        logger.debug("Ignoring illegal move {} on board {}".format(makeusi(move), board.sfen()))
    return board


def intro():
    return r"""
    .   _/\_
    .  //o o\\
    .  ||    ||  lishogi-bot %s
    .  ||    ||
    .  ||____||  Play on Lishogi with a bot
    """ % __version__


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Play on Lishogi with a bot')
    parser.add_argument('-u', action='store_true', help='Add this flag to upgrade your account to a bot account.')
    parser.add_argument('-v', action='store_true', help='Verbose output. Changes log level from INFO to DEBUG.')
    parser.add_argument('--config', help='Specify a configuration file (defaults to ./config.yml)')
    parser.add_argument('-l', '--logfile', help="Log file to append logs to.", default=None)
    args = parser.parse_args()

    logging_level = logging.DEBUG if args.v else logging.INFO
    logging.basicConfig(level=logging_level, filename=args.logfile,
                        format="%(asctime)-15s: %(message)s")
    enable_color_logging(debug_lvl=logging_level)
    logger.info(intro())
    CONFIG = load_config(args.config or "./config.yml")
    li = lishogi.Lishogi(CONFIG["token"], CONFIG["url"], __version__)

    user_profile = li.get_profile()
    username = user_profile["username"]
    is_bot = user_profile.get("title") == "BOT"
    logger.info("Welcome {}!".format(username))

    if args.u and not is_bot:
        is_bot = upgrade_account(li)

    if is_bot:
        engine_factory = partial(engine_wrapper.create_engine, CONFIG)
        start(li, user_profile, engine_factory, CONFIG, logging_level, args.logfile)
    else:
        logger.error("{} is not a bot account. Please upgrade it to a bot account!".format(user_profile["username"]))
