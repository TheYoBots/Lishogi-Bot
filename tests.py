import os
import pytest
import pytest_timeout
import requests
import time
import zipfile
import yaml
import shogi
import shogi.KIF as kif
import shutil
import importlib
lishogi_bot = importlib.import_module("lishogi-bot")

TOKEN = os.environ['BOT_TOKEN']


def test_nothing():
    assert True


def download_yo():
    response = requests.get("https://github.com/mizar/YaneuraOu/releases/download/v7.0.0/Suisho5-YaneuraOu-v7.0.0-windows.zip", allow_redirects=True)
    with open("yo.zip", "wb") as file:
        file.write(response.content)
    with zipfile.ZipFile("yo.zip", "r") as zip_ref:
        zip_ref.extractall(".")
    shutil.copyfile(f"YaneuraOu_NNUE-tournament-clang++-sse42.exe", f"yo.exe")


def run_bot(CONFIG, logging_level):
    lishogi_bot.logger.info(lishogi_bot.intro())
    li = lishogi_bot.lishogi.Lishogi(CONFIG["token"], CONFIG["url"], lishogi_bot.__version__, logging_level)

    user_profile = li.get_profile()
    username = user_profile["username"]
    is_bot = user_profile.get("title") == "BOT"
    lishogi_bot.logger.info(f"Welcome BOT {username}!")

    if not is_bot:
        is_bot = lishogi_bot.upgrade_account(li)

    if is_bot:
        games = li.get_ongoing_games()
        game_ids = list(map(lambda game: game["gameId"], games))
        for game in game_ids:
            try:
                li.abort(game)
            except:
                pass
            time.sleep(2)
        while li.get_ongoing_games():
            time.sleep(60)
        game_id = li.challenge_ai()["id"]
        time.sleep(2)
        games = li.get_ongoing_games()
        game_ids = list(map(lambda game: game["gameId"], games))
        for game in game_ids:
            if game != game_id:
                try:
                    li.abort(game)
                except:
                    pass
                time.sleep(2)

        @pytest.mark.timeout(300)
        def run_test():
            lishogi_bot.start(li, user_profile, CONFIG, logging_level, None, one_game=True)
            response = requests.get(f"https://lishogi.org/game/export/{game_id}")
            response = response.content.decode()
            parser = kif.Parser()
            summary = parser.parse_str(response)[0]
            starting = "lishogi" in summary["names"][1]
            board = shogi.Board()
            for move in summary["moves"]:
                board.push_usi(move)
            win = board.turn == (shogi.WHITE if starting else shogi.BLACK) and board.is_game_over()
            assert win

        run_test()
    else:
        lishogi_bot.logger.error(f"{username} is not a bot account. Please upgrade it to a bot account!")
    games = li.get_ongoing_games()
    game_ids = list(map(lambda game: game["gameId"], games))
    for game in game_ids:
        try:
            li.abort(game)
        except:
            pass
        time.sleep(2)


def test_bot():
    logging_level = lishogi_bot.logging.INFO  # lishogi_bot.logging_level.DEBUG
    lishogi_bot.logging.basicConfig(level=logging_level, filename=None, format="%(asctime)-15s: %(message)s")
    lishogi_bot.enable_color_logging(debug_lvl=logging_level)
    download_yo()
    lishogi_bot.logger.info("Downloaded YaneuraOu for NNUE")
    with open("./config.yml.default") as file:
        CONFIG = yaml.safe_load(file)
    CONFIG["token"] = TOKEN
    CONFIG["engine"]["dir"] = "./"
    CONFIG["engine"]["name"] = "yo.exe"
    CONFIG["engine"]["usi_options"]["BookFile"] = "no_book"
    CONFIG["engine"]["usi_options"]["NetworkDelay"] = 500
    run_bot(CONFIG, logging_level)


if __name__ == "__main__":
    test_bot()