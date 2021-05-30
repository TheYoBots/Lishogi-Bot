# Lishogi Bot

[![Lishogi Bot Tests](https://github.com/TheYoBots/Lishogi-Bot/actions/workflows/lishogi-bot-tests.yml/badge.svg)](https://github.com/TheYoBots/Lishogi-Bot/actions/workflows/lishogi-bot-tests.yml)
[![Python Tests](https://github.com/TheYoBots/Lishogi-Bot/actions/workflows/python-tests.yml/badge.svg)](https://github.com/TheYoBots/Lishogi-Bot/actions/workflows/python-tests.yml)
[![Lishogi Bots](https://img.shields.io/badge/Lishogi_Bots-%40Bot-blue.svg)](https://lishogi.org/player/bots)

A bridge between [Lichess API](https://lichess.org/api#tag/Bot) and Lishogi USI Bots. In case you don't know English, view the [Japanese Translation here (日本語翻訳)](https://github.com/TheYoBots/Lishogi-Bot/wiki/Japanese-Translation).

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
virtualenv .venv -p python3  # if this fails you probably need to add Python3 to your PATH.
source ./venv/bin/activate
python3 -m pip install -r requirements.txt
```
- Copy `config.yml.default` to `config.yml`.
- Edit the `config.yml` file to your liking by changing the supported [variants](https://github.com/TheYoBots/Lishogi-Bot/blob/master/config.yml.default#L42-L44), [timings](https://github.com/TheYoBots/Lishogi-Bot/blob/master/config.yml.default#L45-L51), [challenge modes](https://github.com/TheYoBots/Lishogi-Bot/blob/master/config.yml.default#L52-L54) and [incoming challenges](https://github.com/TheYoBots/Lishogi-Bot/blob/master/config.yml.default#L31-L41), so that it plays shogi the way you want it to.

### Windows:

- **NOTE: Only Python 3.7 or later is supported!**
- If you don't have Python, you may download it [here](https://www.python.org/downloads/). When installing it, enable `add Python to PATH`, then go to custom installation (this may be not necessary, but on some computers it won't work otherwise) and enable all options (especially `install for all users`), except the last . It's better to install Python in a path without spaces, like `C:\Python\`.
- To type commands it's better to use PowerShell. Go to Start menu and type `PowerShell`.
- Then you may need to upgrade pip. Execute `python -m pip install --upgrade pip` in PowerShell.
- Download the repo into lishogi-bot directory.
- Navigate to the directory in PowerShell: `cd [folder's adress]` (like `cd C:\shogi\lishogi-bot`).
- Install virtualenv: `pip install virtualenv`.
- Setup virtualenv:

```python
python -m venv .venv  # if this fails you probably need to add Python to your PATH.
./.venv/Scripts/Activate.ps1  # .\.venv\Scripts\activate.bat should work in cmd in administator mode. This may not work on Windows, and in this case you need to execute "Set-ExecutionPolicy RemoteSigned" first and choose "Y" there (you may need to run Powershell as administrator). After you executed the script, change execution policy back with "Set-ExecutionPolicy Restricted" and pressing "Y").
pip install -r requirements.txt
```
- Copy `config.yml.default` to `config.yml`.
- Edit the `config.yml` file to your liking by changing the supported [variants](https://github.com/TheYoBots/Lishogi-Bot/blob/master/config.yml.default#L42-L44), [timings](https://github.com/TheYoBots/Lishogi-Bot/blob/master/config.yml.default#L45-L51), [challenge modes](https://github.com/TheYoBots/Lishogi-Bot/blob/master/config.yml.default#L52-L54) and [incoming challenges](https://github.com/TheYoBots/Lishogi-Bot/blob/master/config.yml.default#L31-L41), so that it plays shogi the way you want it to.

## Lishogi OAuth

- Create an account for your bot on [Lishogi.org](https://lishogi.org/signup).
- **NOTE: If you have previously played games on an existing account, you will not be able to use it as a bot account.**
- Once your account has been created and you are logged in, [create a personal OAuth2 token with the "Play games with the bot API" ('play:bot' scopes), "Read incoming challenges" ('challenge:read' scopes) and "Create, accept, decline challenges" ('challenge:write' scopes)](https://lishogi.org/account/oauth/token/create?scopes[]=bot:play&scopes[]=challenge:read&scopes[]=challenge:write&description=Lishogi+Bot+Token) selected and a description added.
- A `token` e.g. `xxxxxxxxxxxxxxxx` will be displayed. Store this in `config.yml` as the `token` field.
- **NOTE: You won't see this token again on Lishogi, so save it or store it somewhere.**

## Setup Engine

- Place your engine(s) in the `engine.dir` directory
- In your `config.yml` file, enter the binary name as the `engine.name` field.
- Using this process any engine can be added to the bot.
- **Note: The engine you add has to be running under the USI protocol, then only it will work**

## Lishogi Upgrade to Bot Account

**WARNING: This is irreversible. Read more about [upgrading to bot account](https://lichess.org/api#operation/botAccountUpgrade).**
- run `python lishogi-bot.py -u`
- for more verbrose logs run `python lishogi-bot.py -v`

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

# Acknowledgements

Thanks to the Lichess Team for creating a [repository](https://github.com/ShailChoksi/lichess-bot) that could be easily accessed and modified to help converting it to a format that supports Lishogi and for running an [API](https://lichess.org/api) which is used by lishogi. Thanks to the [Tasuku SUENAGA a.k.a. gunyarakun](https://github.com/gunyarakun) and his [python-shogi](https://github.com/gunyarakun) code which allows engine communication seamlessly. Thanks to  [WandererXII](https://github.com/WandererXII) for all his effort and help.
