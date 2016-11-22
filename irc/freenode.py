#!/usr/local/bin/python3
# coding=utf-8

from .common import *
from ..utils.games import Hangman, Anagram
hangman = Hangman()
anagram = Anagram()

custom_cooldowns = {}

freenode_caps = ("account-notify", "extended-join", "identify-msg", "multi-prefix", "sasl")
chan_list = ("#tppleague", "#twitchplayspokemon", "#poketext", "#twitchplayspokemon-secret", "#AdventuresOfChat")
ignore_list = ("dootbot", "doofbot", "yaybot", "q20pokemonbot")
my_owner = "unaffiliated/pikalaxalt"

def on_wtf(message, source, target, tags, connection):
    if target != "#tppleague":
        return False
    return try_send_message(connection, target, "\"wtf\" - Liria_10 since the beginning of time")

def on_ripchat(message, source, target, tags, connection):
    if target != "#tppleague":
        return False
    connection.action(target, "used a Max Revive on the chat!")
    return True

def on_hangman(message, source, target, tags, connection):
    args = message.lower().split()
    if len(args) == 0:
        try_send_message(connection, target, "Error: Insufficient parameters for !hangman")
        return False
    if args[0] == "start":
        if anagram.active:
            try_send_message(connection, target, "Error: Cannot run Hangman while Anagram is running")
            return False
        if hangman.active:
            try_send_message(connection, target, "Error: Hangman is already running")
            return False
        hangman.start(target)
        try_send_message(connection, target, "Hangman has started!")
        try_send_message(connection, target, " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
    elif hangman.channel != target:
        try_send_message(connection, target, "Error: Hangman is running, but in " + hangman.channel)
    elif args[0] == "stop":
        if not hangman.active:
            try_send_message(connection, target, "Error: Hangman is not running")
        elif source.host != my_owner:
            try_send_message(connection, target, "Error: Insufficient permissions")
        else:
            hangman.stop()
            try_send_message(connection, target, "Hangman terminated")
    elif args[0] == "guess":
        if len(args) < 2:
            try_send_message(connection, target, "Error: Insufficient parameters for !hangman")
            return False
        if not hangman.active:
            try_send_message(connection, target, "Error: Hangman is not running")
            return False
        outcome = hangman.check_guess(args[1])
        if outcome == 2:
            try_send_message(connection, target, source.nick + " solved the puzzle! Well done, " + source.nick + "!")
            try_send_message(connection, target, "The correct answer was: " + hangman.solution)
            hangman.stop()
        elif outcome == 1:
            try_send_message(connection, target, " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
        else:
            if hangman.guesses:
                try_send_message(connection, target, " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
            else:
                try_send_message(connection, target, "You've run out of guesses! The correct answer is: " + hangman.solution)
                hangman.stop()
    elif args[0] == "show":
        if not hangman.active:
            try_send_message(connection, target, "Error: Hangman is not running")
            return False
        try_send_message(connection, target, " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
    else:
        try_send_message(connection, target, "Error: Method " + args[0] + " not supported")

def on_anagram(message, source, target, tags, connection):
    args = message.lower().split()
    if len(args) == 0:
        try_send_message(connection, target, "Error: Insufficient parameters for !anagram")
        return False
    if args[0] == "start":
        if hangman.active:
            try_send_message(connection, target, "Error: Cannot run Anagram while Hangman is running")
            return False
        if anagram.active:
            try_send_message(connection, target, "Error: Anagram is already running")
            return False
        anagram.start(target)
        try_send_message(connection, target, "Anagram has started!")
        try_send_message(connection, target, anagram.prompt + " | Incorrect: " + ", ".join(anagram.incorrect) + " | Guesses remaining: " + str(anagram.guesses))
    elif anagram.channel != target:
        try_send_message(connection, target, "Error: Anagram is running, but in " + anagram.channel)
    elif args[0] == "stop":
        if not anagram.active:
            try_send_message(connection, target, "Error: Anagram is not running")
        elif source.host != my_owner:
            try_send_message(connection, target, "Error: Insufficient permissions")
        else:
            anagram.stop()
            try_send_message(connection, target, "Anagram terminated")
    elif args[0] == "solve":
        if len(args) < 2:
            try_send_message(connection, target, "Error: Insufficient parameters for !anagram")
            return False
        if not anagram.active:
            try_send_message(connection, target, "Error: Anagram is not running")
            return False
        try_send_message(connection, target, source.nick + " has guessed " + args[1].upper() + ".")
        if anagram.check_guess(args[1]):
            try_send_message(connection, target, "That's absolutely correct! Well done, " + source.nick + "!")
            anagram.stop()
        else:
            try_send_message(connection, target, "Nope, that wasn't it.")
            if anagram.guesses:
                try_send_message(connection, target, anagram.prompt + " | Incorrect: " + ", ".join(anagram.incorrect) + " | Guesses remaining: " + str(anagram.guesses))
            else:
                try_send_message(connection, target, "You've run out of guesses! The correct answer is: " + anagram.solution)
                anagram.stop()
    elif args[0] == "show":
        if not anagram.active:
            try_send_message(connection, target, "Error: Anagram is not running")
            return False
        try_send_message(connection, target, anagram.prompt + " | Incorrect: " + ", ".join(anagram.incorrect) + " | Guesses remaining: " + str(anagram.guesses))
    else:
        try_send_message(connection, target, "Error: Method " + args[0] + " not supported")

commands = {
"riot": BotCommand(on_riot, ["#twitchplayspokemon", "#poketext"]),
"emote": BotCommand(on_emote, ["#twitchplayspokemon", "#poketext"]),
"spellrand": BotCommand(on_spellrand, ["#twitchplayspokemon", "#poketext"]),
"dongers": BotCommand(on_dongers, ["#twitchplayspokemon", "#poketext"]),
"hangman": BotCommand(on_hangman, ["#twitchplayspokemon", "#poketext"]),
"anagram": BotCommand(on_anagram, ["#twitchplayspokemon", "#poketext"]),
"klappa": BotCommand(on_klappa, ["#twitchplayspokemon", "#poketext"]),
"prchase": BotCommand(on_prchase, ["#twitchplayspokemon", "#poketext"]),
"wtf": BotCommand(on_wtf, []),
"ripchat": BotCommand(on_ripchat, []),
"song": BotCommand(on_song, ["#twitchplayspokemon", "#poketext"]),
"rip": BotCommand(on_rip, ["#twitchplayspokemon", "#poketext"]),
"dongstortion": BotCommand(on_dongstortion, ["#twitchplayspokemon", "#poketext"]),
"archeops": BotCommand(on_archeops, ["#twitchplayspokemon", "#poketext"]),
"fuck": BotCommand(on_fuck, ["#twitchplayspokemon", "#poketext", "#tppleague"]),
}

cooldown = {}

def do_command(message, source, target, tags, connection):
    try:
        command, args = tuple(message.split(' ', 1))
        command = command[1:].lower()
    except ValueError:
        command = message[1:].lower()
        args = ""
    except:
        return False
    cur_command = commands.get(command)
    if cur_command is None:
        return False
    if target in cur_command.banned_channels:
        return False
    return commands[command].callback(args, source, target, tags, connection)

def do_buzzword(message, source, target, tags, connection):
    lower_message = message.lower()
    M = re.match("((.*) )?riot$", message, re.I)
    if M and target not in ["#twitchplayspokemon", "#poketext"]:
        return on_riot(M.groups()[1], source, target, tags, connection)
    if connection.get_nickname().lower() in lower_message\
        and target not in ["#twitchplayspokemon", "#poketext", "#tppleague"]:
        return on_highlight(message, source, target, tags, connection)
    M = sed_syntax.match(message)
    if M and target not in ["#twitchplayspokemon", "#poketext", "#tppleague"]:
        return on_sed(M.groups(), source, target, tags, connection)
    return False

def on_pubmsg(c, e):
    # e.source is speaker
    # e.target is channel
    # e.arguments is the messages
    # e.tags is metadata
    tags = {x['key']: x['value'] for x in e.tags}
    with open(os.path.join(c.logs_dir, e.target + ".log"), "a", encoding = "utf-8") as F:
        for msg in e.arguments:
            F.write(e.source + "\t" + msg[1:] + "\n")
    if e.source.nick.lower() in ignore_list:
        return
    now = time.time()
    if (e.source, e.target) in cooldown:
        if e.target in custom_cooldowns:
            _cooldown = custom_cooldowns[e.target]
        else:
            _cooldown = 10
        if now < cooldown[(e.source, e.target)] + _cooldown:
            return
    for message in e.arguments:
        R = False
        message = message[1:]
        try:
            if message.startswith("!"):
                R = do_command(message, e.source, e.target, tags, c)
            else:
                R = do_buzzword(message, e.source, e.target, tags, c)
            if R:
                cooldown[(e.source, e.target)] = now
        except KeyboardInterrupt as e:
            c._error = e
            raise
        except:
            tb = traceback.format_exc().split('\n')
            for line in tb:
                try_send_message(c, "pikalaxalt", line)
                time.sleep(1)

def on_privmsg(c, e):
    for message in e.arguments:
        try:
            if e.source.host == my_owner:
                # this is owner-senpai
                message = message[1:]
                if message.startswith("exec "):
                    c.send_raw(message[5:])
        except KeyboardInterrupt:
            raise
        except:
            tb = traceback.format_exc().split('\n')
            for line in tb:
                try_send_message(c, "pikalaxalt", line)
                time.sleep(1)
    pass

def on_join(c, e):
    if e.target in ["#poketext", "#twitchplayspokemon"]:
        return
    try_send_message(c, e.target, "HeyGuys hi " + e.source.nick)

def on_part(c, e):
    if e.target in ["#poketext", "#twitchplayspokemon", None]:
        return
    try_send_message(c, e.target, "RIP " + e.source.nick)

def on_quit(c, e):
    pass

def on_ctcp(c, e):
    pass

def on_endofmotd(c, e):
    c.cap("REQ", *freenode_caps)
    c.join(",".join(chan_list))
    print("Connected to Freenode chat!")

