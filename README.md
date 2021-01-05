# Lishogi-Bot
A bridge between [Lichess API](https://lichess.org/api#tag/Chess-Bot) and Lishogi Bots.

## Lishogi OAuth
- Create an account for your bot on [Lishogi.org](https://lishogi.org/signup).
- NOTE: If you have previously played games on an existing account, you will not be able to use it as a bot account.
- Once your account has been created and you are logged in, [create a personal OAuth2 token](https://lishogi.org/account/oauth/token/create) with the "Play as a bot" selected and add a description.
- A `token` e.g. `Xb0ddNrLabc0lGK2` will be displayed. Store this in `.yml` as the `token` field.
- NOTE: You won't see this token again on Lishogi.


## Setup Engine
- Place your engine(s) in the `engine.dir` directory
- In your `.yml` file, enter the binary name as the `engine.name` field.


## Lishogi Upgrade to Bot Account
**WARNING** This is irreversible. [Read more about upgrading to bot account](https://lichess.org/api#operation/botAccountUpgrade).
- run `python lichess-bot.py -u`

## To Quit Python after Upgrading to Bot Account
- Press `CTRL+C`.
- It may take some time to quit.

# Acknowledgements
Thanks to the Lichess Team for creating a [repository](https://github.com/ShailChoksi/lichess-bot) that could be easily accessed and modified to help converting it to a format that supports Lishogi.

Thanks to the Lichess team, especially T. Alexander Lystad and Thibault Duplessis for working with the LeelaChessZero team to get this API up. Thanks to the Niklas Fiekas and his [python-chess](https://github.com/niklasf/python-chess) code which allows engine communication seamlessly.