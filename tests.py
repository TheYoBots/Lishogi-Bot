import pytest
import pytest_timeout
import requests
import time
import yaml
import importlib
lishogi_bot = importlib.import_module("lishogi-bot")


def test_nothing():
    assert True


def download_fsf():
    response = requests.get('https://github.com/ianfab/Fairy-Stockfish/releases/download/fairy_sf_13_1/fairy-stockfish-largeboard_x86-64.exe', allow_redirects=True)
    with open('fsf.exe', 'wb') as file:
        file.write(response.content)


def run_bot(CONFIG, logging_level):
    lishogi_bot.logger.info(lishogi_bot.intro())
    li = lishogi_bot.lishogi.Lishogi(CONFIG["token"], CONFIG["url"], lishogi_bot.__version__)

    user_profile = li.get_profile()
    username = user_profile["username"]
    is_bot = user_profile.get("title") == "BOT"
    lishogi_bot.logger.info("Welcome {}!".format(username))

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
            response = response.text
            response = response.lower()
            response = response.split('\n')
            result = list(filter(lambda line: 'result' in line, response))
            result = result[0][9:-2]
            color = list(filter(lambda line: 'sente' in line, response))
            color = 'w' if username.lower() in color[0] else 'b'
            win = result == '1-0' and color == 'w' or result == '0-1' and color == 'b'
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
    download_fsf()
    lishogi_bot.logger.info("Downloaded Fairy Stockfish")
    with open("./config.yml.default") as file:
        CONFIG = yaml.safe_load(file)
    CONFIG['token'] = 'Ao7zQxDqoBhE7tpG'
    CONFIG['engine']['dir'] = './'
    CONFIG['engine']['name'] = 'fsf.exe'
    run_bot(CONFIG, logging_level)


if __name__ == '__main__':
    test_bot()
