import logging

logger = logging.getLogger(__name__)


class Conversation:
    def __init__(self, game, engine, xhr, version, challenge_queue):
        self.game = game
        self.engine = engine
        self.xhr = xhr
        self.version = version
        self.challenge_queue = challenge_queue

    command_prefix = "!"

    def react(self, line):
        logger.info(f'*** {self.game.url()} [{line.room}] {line.username}: {line.text.encode("utf-8")}')
        if line.text.startswith(self.command_prefix):
            self.command(line, line.text[1:].lower())

    def command(self, line, cmd):
        if cmd == "commands" or cmd == "help":
            self.send_reply(line, "Supported commands: !wait (only applicable at the start of the game), !name, !howto, !eval, !queue")
        elif cmd == "wait" and self.game['state']['status'] == 'started':
            self.game.ping(60, 120, 120)
            self.send_reply(line, "Waiting 60 seconds...")
        elif cmd == "name":
            name = self.game.me['name']
            self.send_reply(line, f"{name} running {self.engine.name()} (Lishogi-Bot v{self.version})")
        elif cmd == "howto":
            self.send_reply(line, "How to run: https://github.com/TheYoBots/Lishogi-Bot")
        elif cmd == "eval" and line.room == "spectator":
            stats = self.engine.get_stats()
            self.send_reply(line, ", ".join(stats))
        elif cmd == "eval":
            self.send_reply(line, "I don't tell that to my opponent, sorry.")
        elif cmd == "queue":
            if self.challenge_queue:
                challengers = ", ".join([f"@{challenger['challenger']['name']}" for challenger in reversed(self.challenge_queue)])
                self.send_reply(line, f"Challenge queue: {challengers}")
            else:
                self.send_reply(line, "No challenges queued.")

    def send_reply(self, line, reply):
        self.xhr.chat(self.game['id'], line.room, reply)

    def send_message(self, room, message):
        if message:
            self.send_reply(ChatLine({"room": room}), message)


class ChatLine:
    def __init__(self, json):
        self.room = json.get("room")
        self.username = json.get("username")
        self.text = json.get("text")
