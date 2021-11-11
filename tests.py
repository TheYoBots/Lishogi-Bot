import pytest
import pytest_timeout
import requests
import time
import zipfile
import yaml
import shogi
import shogi.KIF as kif
from shutil import copyfile
import importlib
lishogi_bot = importlib.import_module("lishogi-bot")

TOKEN = 'Ao7zQxDqoBhE7tpG'


def test_nothing():
    assert True


def download_yaneuraou():
    response = requests.get('https://github.com/WandererXII/shoginet/raw/main/YaneuraOu-by-gcc', allow_redirects=True)
    with open('yaneuraou.exe', 'wb') as file:
        file.write(response.content)


def download_nnue():
    response = requests.get('https://github.com/WandererXII/shoginet/raw/main/eval/nn.bin', allow_redirects=True)
    with open('shogi.zip', 'wb') as file:
        file.write(response.content)
    with zipfile.ZipFile('shogi.zip', 'r') as zip_ref:
        zip_ref.extractall('.')
    copyfile('./eval/nn.bin', 'nn.bin')


def run_bot(CONFIG, logging_level):
    lishogi_bot.logger.info(lishogi_bot.intro())
    li = lishogi_bot.lishogi.Lishogi(CONFIG["token"], CONFIG["url"], lishogi_bot.__version__)

    user_profile = li.get_profile()
    username = user_profile["username"]
    is_bot = user_profile.get("title") == "BOT"
    lishogi_bot.logger.info("Welcome BOT {}!".format(username))

    if not is_bot:
        is_bot = lishogi_bot.upgrade_account(li)

    if is_bot:
        engine_factory = lishogi_bot.partial(lishogi_bot.engine_wrapper.create_engine, CONFIG)
        games = li.get_ongoing_games()
        game_ids = list(map(lambda game: game['gameId'], games))
        for game in game_ids:
            try:
                li.abort(game)
            except:
                pass
            time.sleep(2)
        while li.get_ongoing_games():
            time.sleep(60)
        game_id = li.challenge_ai()['id']
        time.sleep(2)
        games = li.get_ongoing_games()
        game_ids = list(map(lambda game: game['gameId'], games))
        for game in game_ids:
            if game != game_id:
                try:
                    li.abort(game)
                except:
                    pass
                time.sleep(2)

        @pytest.mark.timeout(300)
        def run_test():
            lishogi_bot.start(li, user_profile, engine_factory, CONFIG, logging_level, None, one_game=True)
            response = requests.get('https://lishogi.org/game/export/{}'.format(game_id))
            response = response.content.decode()
            parser = kif.Parser()
            summary = parser.parse_str(response)[0]
            starting = 'lishogi' in summary['names'][1]
            board = shogi.Board()
            for move in summary['moves']:
                board.push_usi(move)
            win = board.turn == (shogi.WHITE if starting else shogi.BLACK) and board.is_game_over()
            assert win

        run_test()
    else:
        lishogi_bot.logger.error("{} is not a bot account. Please upgrade it to a bot account!".format(user_profile["username"]))
    games = li.get_ongoing_games()
    game_ids = list(map(lambda game: game['gameId'], games))
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
    download_nnue()
    lishogi_bot.logger.info("Downloaded NNUE")
    download_yaneuraou()
    lishogi_bot.logger.info("Downloaded yaneuraou")
    with open("./config.yml.default") as file:
        CONFIG = yaml.safe_load(file)
    CONFIG['token'] = TOKEN
    CONFIG['engine']['dir'] = './'
    CONFIG['engine']['name'] = 'yaneuraou.exe'
    CONFIG['engine']['usi_options']['EvalDir'] = 'D:\a\Lishogi-Bot\Lishogi-Bot\Eval'
    run_bot(CONFIG, logging_level)


if __name__ == '__main__':
    test_bot()
