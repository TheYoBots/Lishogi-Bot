# Lishogi Bot
A bridge between [Lichess API](https://lichess.org/api#tag/Chess-Bot) and Lishogi Bots. In case you don't know English, view the [Japanese Translation here (日本語翻訳)](https://github.com/TheYoBots/Lishogi-Bot/wiki/Japanese-Translation).

## How to Install

### Mac/Linux:
- **NOTE:** Only Python 3 is supported!
- Download the repo into lishogi-bot directory.
- Navigate to the directory in cmd/Terminal: `cd lishogi-bot`.
- Install virtualenv: `pip install virtualenv`.
- Setup virtualenv:

`virtualenv .venv -p python3` (if this fails you probably need to add Python3 to your PATH)
```
source .venv/bin/activate
pip install -r requirements.txt
```
- Copy `config.yml.default` to `config.yml`.
- Edit the `.yml` files to your liking, so that it plays shogi.

### Windows:
- **NOTE:** Only Python 3 is supported!
- If you don't have Python, you may download it here: (https://www.python.org/downloads/). When installing it, enable "add Python to PATH", then go to custom installation (this may be not necessary, but on some computers it won't work otherwise) and enable all options (especially "install for all users"), except the last . It's better to install Python in a path without spaces, like "C:\Python\".
- To type commands it's better to use PowerShell. Go to Start menu and type "PowerShell" (you may use cmd too, but sometimes it may not work).
- Then you may need to upgrade pip. Execute `python -m pip install --upgrade pip` in PowerShell.
- Download the repo into lishogi-bot directory.
- Navigate to the directory in PowerShell: `cd [folder's adress]` (like "cd C:\shogi\lishogi-bot").
- Install virtualenv: `pip install virtualenv`.
- Setup virtualenv:

`virtualenv .venv -p python` (if this fails you probably need to add Python to your PATH)

`./.venv/Scripts/activate` (`.\.venv\Scripts\activate` should work in cmd in administator mode) (This may not work on Windows, and in this case you need to execute "Set-ExecutionPolicy RemoteSigned" first and choose "Y" there [you may need to run Powershell as administrator]. After you executed the script, change execution policy back with "Set-ExecutionPolicy Restricted" and pressing "Y")

`pip install -r requirements.txt`
- Copy `config.yml.default` to `config.yml`
- Edit the `.yml` files to your liking, so that it plays shogi.

## Lishogi OAuth
- Create an account for your bot on [Lishogi.org](https://lishogi.org/signup).
- NOTE: If you have previously played games on an existing account, you will not be able to use it as a bot account.
- Once your account has been created and you are logged in, [create a personal OAuth2 token](https://lishogi.org/account/oauth/token/create) with the "Play as a bot" selected and add a description.
- A `token` e.g. `Xb0ddNrLabc0lGK2` will be displayed. Store this in `.yml` as the `token` field.
- NOTE: You won't see this token again on Lishogi.


## Setup Engine
- Place your engine(s) in the `engine.dir` directory
- In your `.yml` file, enter the binary name as the `engine.name` field.
- Using this process any engine can be added to the bot.


## Lishogi Upgrade to Bot Account
**WARNING** This is irreversible. Read more about [upgrading to bot account](https://lichess.org/api#operation/botAccountUpgrade).
- run `python lichess-bot.py -u`

## To Quit Python after Upgrading to Bot Account
- Press `CTRL+C`.
- It may take some time to quit.

# Supported Chess Variants
- [Standard Chess](https://www.pychess.org/variant/chess)
- [Crazyhouse](https://lichess.org/variant/crazyhouse)
- [Chess960](https://lichess.org/variant/chess960)
- [King of the Hill](https://lichess.org/variant/kingOfTheHill)
- [Three-Check](https://lichess.org/variant/threeCheck)
- [AntiChess](https://lichess.org/variant/antichess)
- [Atomic](https://lichess.org/variant/atomic)
- [Horde](https://lichess.org/variant/horde)
- [Racing Kings](https://lichess.org/variant/racingKings)
- [Shogi](https://www.pychess.org/variant/shogi)
- [Xiangqi](https://www.pychess.org/variant/xiangqi)
- [Makruk](https://www.pychess.org/variant/makruk)
- [Sittuyin](https://www.pychess.org/variant/sittuyin)
- [Placement](https://www.pychess.org/variant/placement)
- [Capablanca](https://www.pychess.org/variant/capablanca)
- [Capahouse](https://www.pychess.org/variant/capahouse)
- [SHouse](https://www.pychess.org/variant/shouse)
- [Seirawan](https://www.pychess.org/variant/seirawan)
- **Note:** Other Variants can also be added, but on [Lishogi.org](https://lishogi.org/), the bot will only play [Shogi](https://www.pychess.org/variant/shogi). Changes can be made for the Bot to play on other websites with the above Variants and more can be added.

# Acknowledgements
Thanks to the Lichess Team for creating a [repository](https://github.com/ShailChoksi/lichess-bot) that could be easily accessed and modified to help converting it to a format that supports Lishogi.

Thanks to the Lichess team, especially T. Alexander Lystad and Thibault Duplessis for working with the LeelaChessZero team to get this API up. Thanks to the Niklas Fiekas and his [python-chess](https://github.com/niklasf/python-chess) code which allows engine communication seamlessly.
