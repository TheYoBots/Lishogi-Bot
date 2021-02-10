# Lishogi Bot

[![Build Status](https://github.com/TheYoBots/Lishogi-Bot/workflows/Python%20application/badge.svg)](https://github.com/TheYoBots/Lishogi-Bot/actions)
[![Lishogi Bot](https://img.shields.io/badge/YoBot_v2-%40Lishogi_Bot-blue.svg)](https://lishogi.org/@/YoBot_v2)
[![Play Bot](https://img.shields.io/badge/Play_Bot-%40Lishogi-blue.svg)](https://lishogi.org/?user=YoBot_v2#friend)
[![Lishogi Team](https://img.shields.io/badge/Lishogi_Team-%40Team-blue.svg)](https://lishogi.org/team/yobot_v2-shogi)

A bridge between [Lichess API](https://lichess.org/api#tag/Chess-Bot) and Lishogi USI Bots. In case you don't know English, view the [Japanese Translation here (日本語翻訳)](https://github.com/TheYoBots/Lishogi-Bot/wiki/Japanese-Translation).

Current lishogi bot run using this repository is [YoBot_v2](https://lishogi.org/@/YoBot_v2) and team is [YoBot_v2 Shogi](https://lishogi.org/team/yobot_v2-shogi).

## How to Install

### Mac/Linux:
- **NOTE:** Only Python 3 is supported!
- Download the repo into Lishogi-Bot directory.
- Upgrade pip to prevent any flaws in further commands. To do so execute `pip install --upgrade pip`.
- Navigate to the directory in cmd/Terminal: `cd Lishogi-Bot`.
- Install virtualenv: `pip install virtualenv`.
- Setup virtualenv:

`virtualenv .venv -p python3` (if this fails you probably need to add Python3 to your PATH)
```
source .venv/bin/activate
pip install -r requirements.txt
```
- Edit the `config.yml` file to your liking by changing the supported [variants](https://github.com/TheYoBots/Lishogi-Bot/blob/c746023ce8bc95ab7c0f3810921675a8b96610e8/config.yml#L33), [timings](https://github.com/TheYoBots/Lishogi-Bot/blob/c746023ce8bc95ab7c0f3810921675a8b96610e8/config.yml#L36), [challenge modes](https://github.com/TheYoBots/Lishogi-Bot/blob/c746023ce8bc95ab7c0f3810921675a8b96610e8/config.yml#L43) and [incoming challenges](https://github.com/TheYoBots/Lishogi-Bot/blob/c746023ce8bc95ab7c0f3810921675a8b96610e8/config.yml#L26), so that it plays shogi.

### Windows:
- **NOTE:** Only Python 3 is supported!
- If you don't have Python, you may download it [here](https://www.python.org/downloads/). When installing it, enable `add Python to PATH`, then go to custom installation (this may be not necessary, but on some computers it won't work otherwise) and enable all options (especially `install for all users`), except the last . It's better to install Python in a path without spaces, like `C:\Python\`.
- To type commands it's better to use PowerShell. Go to Start menu and type `PowerShell`.
- Then you may need to upgrade pip. Execute `python -m pip install --upgrade pip` in PowerShell.
- Download the repo into lishogi-bot directory.
- Navigate to the directory in PowerShell: `cd [folder's adress]` (like `cd C:\shogi\lishogi-bot`).
- Install virtualenv: `pip install virtualenv`.
- Setup virtualenv:

`virtualenv .venv -p python` (if this fails you probably need to add Python to your PATH)

`./.venv/Scripts/activate` (`.\.venv\Scripts\activate` should work in cmd in administator mode) (This may not work on Windows, and in this case you need to execute "Set-ExecutionPolicy RemoteSigned" first and choose "Y" there (you may need to run Powershell as administrator). After you executed the script, change execution policy back with "Set-ExecutionPolicy Restricted" and pressing "Y")

`pip install -r requirements.txt`
- Edit the `config.yml` file to your liking by changing the supported [variants](https://github.com/TheYoBots/Lishogi-Bot/blob/c746023ce8bc95ab7c0f3810921675a8b96610e8/config.yml#L33), [timings](https://github.com/TheYoBots/Lishogi-Bot/blob/c746023ce8bc95ab7c0f3810921675a8b96610e8/config.yml#L36), [challenge modes](https://github.com/TheYoBots/Lishogi-Bot/blob/c746023ce8bc95ab7c0f3810921675a8b96610e8/config.yml#L43) and [incoming challenges](https://github.com/TheYoBots/Lishogi-Bot/blob/c746023ce8bc95ab7c0f3810921675a8b96610e8/config.yml#L26), so that it plays shogi.

## Lishogi OAuth
- Create an account for your bot on [Lishogi.org](https://lishogi.org/signup).
- **NOTE:** If you have previously played games on an existing account, you will not be able to use it as a bot account.
- Once your account has been created and you are logged in, [create a personal OAuth2 token](https://lishogi.org/account/oauth/token/create) with the "Play as a bot" selected and add a description.
- A `token` e.g. `xxxxxxxxxxxxxxxx` will be displayed. Store this in `config.yml` as the `token` field.
- **NOTE:** You won't see this token again on Lishogi, so save it or store it somewhere.

## Setup Engine
- Place your engine(s) in the `engine.dir` directory
- In your `config.yml` file, enter the binary name as the `engine.name` field.
- Using this process any engine can be added to the bot.
- **Note: The engine you add has to be running under the USI protocol, then only it will work**


## Lishogi Upgrade to Bot Account
**WARNING** This is irreversible. Read more about [upgrading to bot account](https://lichess.org/api#operation/botAccountUpgrade).
- run `python lishogi-bot.py -u`
- for more verbrose logs run `python lishogi-bot.py -v`

# Acknowledgements
Thanks to the Lichess Team for creating a [repository](https://github.com/ShailChoksi/lichess-bot) that could be easily accessed and modified to help converting it to a format that supports Lishogi and for running an [API](https://lichess.org/api) which is used by lishogi. Thanks to the [Tasuku SUENAGA a.k.a. gunyarakun](https://github.com/gunyarakun) and his [python-shogi](https://github.com/gunyarakun) code which allows engine communication seamlessly. Thanks to [allthatglittersisgold](https://github.com/allthatglittersisgold) for creating a Windows executable for `lishogi-bot.py` and Thanks to  [WandererXII](https://github.com/WandererXII) for all his effort and help.
