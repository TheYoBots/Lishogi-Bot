# Lishogi Bot
[![Lishogi Bot Build](https://github.com/TheYoBots/Lishogi-Bot/actions/workflows/lishogi-bot-build.yml/badge.svg)](https://github.com/TheYoBots/Lishogi-Bot/actions/workflows/lishogi-bot-build.yml)
[![Python Build](https://github.com/TheYoBots/Lishogi-Bot/actions/workflows/python-build.yml/badge.svg)](https://github.com/TheYoBots/Lishogi-Bot/actions/workflows/python-build.yml)
[![Lishogi Bots](https://img.shields.io/badge/Lishogi_Bots-%40Bot-blue.svg)](https://lishogi.org/player/bots)

A bridge between [Lishogi's Bot API](https://lichess.org/api#tag/Bot) and Lishogi USI Bots. In case you don't know English, view the [Japanese Translation here (日本語翻訳)](https://github.com/TheYoBots/Lishogi-Bot/wiki/Japanese-Translation).

## How to Install
### Mac/Linux:
- **NOTE: Only Python 3.7 or later is supported!**
- Download the repo into Lishogi-Bot directory.
- Navigate to the directory in cmd/Terminal: `cd Lishogi-Bot`.
- Install pip: `apt install python3-pip`.
- Install virtualenv: `pip install virtualenv`.
- Setup virtualenv: `apt install python3-venv`.
```python
python3 -m venv venv  # if this fails you probably need to add Python3 to your PATH.
virtualenv venv -p python3  # if this fails you probably need to add Python3 to your PATH.
source ./venv/bin/activate
python3 -m pip install -r requirements.txt
```
- Copy `config.yml.default` to `config.yml`.
- Edit the `config.yml` file to your liking by changing the supported [variants](/config.yml.default#L45-L47), [timings](/config.yml.default#L48-L54), [challenge modes](/config.yml.default#L55-L57) and [incoming challenges](/config.yml.default#L34-L44), so that it plays shogi the way you want it to.

### Windows:
- **NOTE: Only Python 3.7 or later is supported!**
- If you don't have Python, you may download it [here](https://www.python.org/downloads/). When installing it, enable `add Python to PATH`, then go to custom installation (this may be not necessary, but on some computers it won't work otherwise) and enable all options (especially `install for all users`), except the last . It's better to install Python in a path without spaces, like `C:\Python\`.
- To type commands it's better to use PowerShell. Go to Start menu and type `PowerShell` (you may use "cmd" too, but sometimes it may not work).
- Then you may need to upgrade pip. Execute `python -m pip install --upgrade pip` in PowerShell.
- Download the repo into lishogi-bot directory.
- Navigate to the directory in PowerShell: `cd [folder's adress]` (example, `cd C:\shogi\lishogi-bot`).
- Install virtualenv: `pip install virtualenv`.
- Setup virtualenv:
```python
python -m venv .venv  # if this fails you probably need to add Python to your PATH.
./.venv/Scripts/Activate.ps1  # `.\.venv\Scripts\activate.bat` should work in cmd in administator mode. This may not work on Windows, and in this case you need to execute "Set-ExecutionPolicy RemoteSigned" first and choose "Y" there (you may need to run Powershell as administrator). After you executed the script, change execution policy back with "Set-ExecutionPolicy Restricted" and pressing "Y".
pip install -r requirements.txt
```
- Copy `config.yml.default` to `config.yml`.
- Edit the `config.yml` file to your liking by changing the supported [variants](/config.yml.default#L45-L47), [timings](/config.yml.default#L48-L54), [challenge modes](/config.yml.default#L55-L57) and [incoming challenges](/config.yml.default#L34-L44), so that it plays shogi the way you want it to.

## Lishogi OAuth
- Create an account for your bot on [Lishogi.org](https://lishogi.org/signup).
- **NOTE: If you have previously played games on an existing account, you will not be able to use it as a bot account.**
- Once your account has been created and you are logged in, [create a personal OAuth2 token with the "Play games with the bot API" ('bot:play' scopes)](https://lishogi.org/account/oauth/token/create?scopes[]=bot:play&description=Lishogi+Bot+Token) selected and a description added.
- A `token` (e.g. `xxxxxxxxxxxxxxxx`) will be displayed. Store this in the `config.yml` file as the `token` field. You can also set the token in the environment variable `$LISHOGI_BOT_TOKEN`.
- **NOTE: You won't see this token again on Lishogi, so save it or store it somewhere.**

## Setup Engine
- Place your engine(s) in the `engine: dir` directory.
- In the `config.yml` file, enter the binary name as the `engine: name` field (In Windows you may need to type a name with `.exe`, like `YaneuraOu.exe`).
- Using this process any engine can be added to the bot.
- **Note: The engine you add has to be running under the USI protocol, only then it will work.**

## Creating a homemade bot
As an alternative to creating an entire chess engine and implementing one of the communiciation protocols (USI), a bot can also be created by writing a single class with a single method. The `search()` method in this new class takes the current board and the game clock as arguments and should return a move based on whatever criteria you desires.

Steps to create a homemade bot:
1. Do all the steps mentioned in [How to Install](#how-to-install).
2. In the `config.yml`, change the engine protocol to `homemade`.
3. Create a class in some file that extends the `MinimalEngine` class (in the `strategies.py` file).
    - Look at the `strategies.py` file to see some examples.
    - If you don't know what to implement, look at the `EngineWrapper` or `USIEngine` class.
        - You don't have to create your own engine, even though it's an `EngineWrapper` class. <br/>
The examples just implement `search`.
4. In the `config.yml`, change the name from `engine_name` to the name of your class.
    - In this case, you could change it to: <br/>
`name: "RandomMove"`

### Engine Configuration
Besides the above, there are many possible options within `config.yml` for configuring the engine for use with lishogi-bot.
- `protocol`: Specify which protocol your engine uses. `"usi"` for the [Universal Shogi Interface](http://hgm.nubati.net/usi.html) is the only supported protocol.
- `ponder`: Specify whether your bot will ponder, i.e., think while the bot's opponent is choosing a move.
- `engine_options`: Command line options to pass to the engine on startup. For example, the `config.yml.default` has the configuration
```yml
  engine_options:
    cpuct: 3.1
```
This would create the command-line option `--cpuct=3.1` to be used when starting the engine. Any number of options can be listed here, each getting their own command-line option.
- `usi_options`: A list of options to pass to a USI engine after startup. Different engines have different options, so treat the options in `config.yml.default` as templates and not suggestions. When USI engines start, they print a list of configurations that can modify their behavior. For example, YaneuraOu v6.50 prints the following when run at the command line:
```
id name YaneuraOu NNUE 6.50
id author by yaneurao
option name Threads type spin default 4 min 1 max 512
option name USI_Hash type spin default 16 min 1 max 33554432
option name USI_Ponder type check default false
option name Stochastic_Ponder type check default false
option name MultiPV type spin default 1 min 1 max 800
option name NetworkDelay type spin default 120 min 0 max 10000
option name NetworkDelay2 type spin default 1120 min 0 max 10000
option name MinimumThinkingTime type spin default 2000 min 1000 max 100000
option name SlowMover type spin default 100 min 1 max 1000
option name MaxMovesToDraw type spin default 0 min 0 max 100000
option name DepthLimit type spin default 0 min 0 max 2147483647
option name NodesLimit type spin default 0 min 0 max 9223372036854775807
option name EvalDir type string default eval
option name WriteDebugLog type check default false
option name GenerateAllLegalMoves type check default false
option name EnteringKingRule type combo default CSARule27 var NoEnteringKing var CSARule24 var CSARule24H var CSARule27 var CSARule27H var TryRule
option name ThreadIdOffset type spin default 0 min 0 max 7
option name LargePageEnable type check default true
option name USI_OwnBook type check default true
option name NarrowBook type check default false
option name BookMoves type spin default 16 min 0 max 10000
option name BookIgnoreRate type spin default 0 min 0 max 100
option name BookFile type combo default standard_book.db var no_book var standard_book.db var yaneura_book1.db var yaneura_book2.db var yaneura_book3.db var yaneura_book4.db var user_book1.db var user_book2.db var user_book3.db var book.bin
option name BookDir type string default book
option name BookEvalDiff type spin default 30 min 0 max 99999
option name BookEvalBlackLimit type spin default 0 min -99999 max 99999
option name BookEvalWhiteLimit type spin default -140 min -99999 max 99999
option name BookDepthLimit type spin default 16 min 0 max 99999
option name BookOnTheFly type check default false
option name ConsiderBookMoveCount type check default false
option name BookPvMoves type spin default 8 min 1 max 246
option name IgnoreBookPly type check default false
option name SkillLevel type spin default 20 min 0 max 20
option name DrawValueBlack type spin default -2 min -30000 max 30000
option name DrawValueWhite type spin default -2 min -30000 max 30000
option name PvInterval type spin default 300 min 0 max 100000
option name ResignValue type spin default 99999 min 0 max 99999
option name ConsiderationMode type check default false
option name OutputFailLHPV type check default true
usiok
```
Any of the names following `option name` can be listed in `usi_options` in order to configure the YaneuraOu engine.
```yml
  usi_options:
    NetworkDelay: 100
    Skill Level: 10
```
The exception to this are the options `Threads`, `USI_Ponder` and `MultiPv`. These will be handled by lishogi-bot after a game starts and should not be listed in the `config.yml` file. Also, if an option is listed under `usi_options` that is not in the list printed by the engine, it will cause an error when the engine starts because the engine won't understand the option. The word after `type` indicates the expected type of the options: `string` for a text string, `spin` for a numeric value, `check` for a boolean True/False value.

One last option is `go_commands`. Beneath this option, arguments to the USI `go` command can be passed. For example,
```yml
  go_commands:
    nodes: 1
    depth: 5
    movetime: 1000
```
will append `nodes 1 depth 5 movetime 1000` to the command to start thinking of a move: `go startpos e2e4 e7e5 ...`.

- `abort_time`: How many seconds to wait before aborting a game due to opponent inaction. This only applies during the first six moves of the game.
- `fake_think_time`: Artificially slow down the engine to simulate a person thinking about a move. The amount of thinking time decreases as the game goes on.
- `rate_limiting_delay`: For extremely fast games, the [lishogi.org](https://lishogi.org) servers may respond with an error if too many moves are played to quickly. This option avoids this problem by pausing for a specified number of milliseconds after submitting a move before making the next move.
- `move_overhead`: To prevent losing on time due to network lag, subtract this many milliseconds from the time to think on each move.

- `correspondence` These options control how the engine behaves during correspondence games.
  - `move_time`: How many seconds to think for each move.
  - `checkin_period`: How often (in seconds) to reconnect to games to check for new moves after disconnecting.
  - `disconnect_time`: How many seconds to wait after the bot makes a move for an opponent to make a move. If no move is made during the wait, disconnect from the game.
  - `ponder`: Whether the bot should ponder during the above waiting period.

- `challenge`: Control what kind of games for which the bot should accept challenges. All of the following options must be satisfied by a challenge to be accepted.
  - `concurrency`: The maximum number of games to play simultaneously.
  - `sort_by`: Whether to start games by the best rated/titled opponent `"best"` or by first-come-first-serve `"first"`.
  - `accept_bot`: Whether to accept challenges from other bots.
  - `only_bot`: Whether to only accept challenges from other bots.
  - `max_increment`: The maximum value of time increment.
  - `min_increment`: The minimum value of time increment.
  - `max_base`: The maximum base time for a game.
  - `min_base`: The minimum base time for a game.

- `variants`: An indented list of shogi variants that the bot can handle.
```yml
  variants:
    - standard
    - fromPosition
```

- `time_controls`: An indented list of acceptable time control types from `ultraBullet` to `correspondence`.
```yml
  time_controls:
    - ultraBullet
    - bullet
    - blitz
    - rapid
    - classical
    - correpondence
```
- `modes`: An indented list of acceptable game modes (`rated` and/or `casual`).
```yml
  modes:
    -rated
    -casual
```

## Lishogi Upgrade to Bot Account
**WARNING: This is irreversible. Read more about [upgrading to bot account](https://lichess.org/api#operation/botAccountUpgrade).**
- Run `python lishogi-bot.py -u`.

## To Run
After activating the virtual environment created in the installation steps (the `source` line for Linux and Macs or the `activate` script for Windows), run
```python
python lishogi-bot.py
```
The working directory for the engine execution will be the lishogi-bot directory. If your engine requires files located elsewhere, make sure they are specified by absolute path or copy the files to an appropriate location inside the lishogi-bot directory.

To output more information (including your engine's thinking output and debugging information), the `-v` option can be passed to lishogi-bot:
```python
python lishogi-bot.py -v
```

## To Quit
- Press `CTRL+C`.
- It may take some time to quit.

## Tips & Tricks
- You can specify a different config file with the `--config` argument.
- Here's an example systemd service definition:
```python
[Unit]
Description=Lishogi-Bot
After=network-online.target
Wants=network-online.target

[Service]
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3/home/User/Lishogi-Bot/Lishogi-Bot.py
WorkingDirectory=/home/User/lishogi-bot/
User=UserName
Group=GroupName
Restart=always

[Install]
WantedBy=multi-user.target
```

## Acknowledgements
Thanks to the Lichess Team for creating a [repository](https://github.com/ShailChoksi/lichess-bot) that could be easily accessed and modified to help converting it to a format that supports Lishogi. Thanks to [Tasuku SUENAGA a.k.a. gunyarakun](https://github.com/gunyarakun) and his [python-shogi](https://pypi.org/pypi/python-shogi/) code which allows engine communication seamlessly. Thanks to  [WandererXII](https://github.com/WandererXII) for all his effort and help.

## License
lishogi-bot is licensed under the AGPLv3 (or any later version at your option). Check out the [LICENSE file](/LICENSE) for the full text.
