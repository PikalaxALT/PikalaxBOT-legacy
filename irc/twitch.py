from .common import *
cooldown = {}
custom_cooldowns = {"#adventuresofchat": 60}
# PBR = None
my_tags = {}

chatot_dungeon = "#_chatotdungeon_1481039460679"

twitch_caps = ("twitch.tv/membership", "twitch.tv/tags", "twitch.tv/commands")
chan_list = ("#twitchplayspokemon", "#adventuresofchat", "#pikalaxalt", "#twitchspeaks", chatot_dungeon, "#pigdevil2010", "#tpp", "#keizaron")
ignore_list = ("twitchplaysleaderboard", "wow_deku_onehand", "wallbot303", "kmsbot", "23forces", "facts_bot", "alicecatson", "resreveregassem", "friendlyjoltik", "frunky5", "groudonger")

# Bank = namedtuple("Bank", ["pokeyen", "tokens"])
# MIN_BET = 100 # minimum bet for PBR 2.0
# MOVES = ('a','b','c','d','-','1','2','3')

commands = {
"riot": BotCommand(on_riot, ["#twitchplayspokemon", "#projectrevotpp"]),
"emote": BotCommand(on_emote, ["#twitchplayspokemon", "#projectrevotpp"]),
"spellrand": BotCommand(on_spellrand, ["#twitchplayspokemon", "#projectrevotpp"]),
"dongers": BotCommand(on_dongers, ["#twitchplayspokemon", "#projectrevotpp"]),
"klappa": BotCommand(on_klappa, ["#twitchplayspokemon", "#projectrevotpp"]),
"prchase": BotCommand(on_prchase, ["#twitchplayspokemon", "#projectrevotpp"]),
"song": BotCommand(on_song, ["#twitchplayspokemon", "#projectrevotpp"]),
"rip": BotCommand(on_rip, ["#twitchplayspokemon", "#projectrevotpp"]),
"dongstortion": BotCommand(on_dongstortion, ["#twitchplayspokemon", "#projectrevotpp"]),
"archeops": BotCommand(on_archeops, ["#twitchplayspokemon", "#projectrevotpp"]),
"fuck": BotCommand(on_fuck, ["#twitchplayspokemon", "#projectrevotpp"]),
"nebby": BotCommand(on_nebby, ["#twitchplayspokemon", "#projectrevotpp"]),
"bag": BotCommand(on_bag, ["#twitchplayspokemon", "#projectrevotpp"]),
"addbag": BotCommand(on_addbag, ["#twitchplayspokemon", "#projectrevotpp"]),
}

_pbr_msgs = ("Team (Red|Blue) won the match!",
             "Match resulted in a draw.",
             # "A new match is about to begin!",
             "The battle between .+?, .+?, .+? and .+?, .+?, .+? has just begun!",
             "The [Pp]ok[\xe9e]mon for the next match are .+?, .+?, .+? and .+?, .+?, .+?!",
             )
PBR_MSGS = re.compile("(?P<botmsg>" + "|".join(_pbr_msgs) + ")$")

_badge_get = "^you've won a #(?P<dexno>\d+) (?P<name>\w+) badge!$"
BADGE_GET = re.compile(_badge_get)

def tpp_trigger(message, source, target, tags, connection):
    M = PBR_MSGS.match(message)
    if M and connection.partner.connected:
        return try_send_message(connection.partner, "#poketext", "TPP: " + M.group("botmsg"))

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
    if source.nick == "tpp" and target == "#twitchplayspokemon":
        return tpp_trigger(message, source, target, tags, connection)
    M = re.match("((.*) )?riot$", message, re.I)
    if M and target not in ["#twitchplayspokemon", "#projectrevotpp"]:
        return on_riot(M.groups()[1], source, target, tags, connection)
    if connection.get_nickname().lower() in lower_message\
        and target not in ["#twitchplayspokemon", "#projectrevotpp"]:
        return on_highlight(message, source, target, tags, connection)
    M = sed_syntax.match(message)
    if M and target not in ["#twitchplayspokemon", "#projectrevotpp", chatot_dungeon]:
        return on_sed(M.groups(), source, target, tags, connection)
    return False

def on_pubmsg(c, e):
    # global PBR
    # if not PBR:
        # PBR = PBRBot(c)
    # e.source is speaker
    # e.target is channel
    # e.arguments is the messages
    # e.tags is metadata
    tags = {x['key']: x['value'] for x in e.tags}
    with open(os.path.join(c.logs_dir, e.target + ".log"), "a", encoding = "utf-8") as F:
        for msg in e.arguments:
            F.write(e.source + "\t" + msg + "\n")
            if e.target == "#twitchplayspokemon":
                streamMC.train_line(msg)
            elif e.target == "#tpp":
                botMC.train_line(msg)
            elif e.target == "#keizaron":
                keizaMC.train_line(msg)
    if e.source.nick in ignore_list:
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
                whisper(c, "pikalaxalt", line)

def on_whisper(c, e):
    # global PBR
    # if not PBR:
        # PBR = PBRBot(c)
    # e.source is speaker
    # e.arguments is the message
    # e.tags is metadata
    for message in e.arguments:
        try:
            if e.source.nick == "tpp":
                # process TPP's message
                # M = balance_req.match(message)
                # if M:
                    # PBR.update_balance(*M.groups())
                # else:
                M = BADGE_GET.match(message)
                if M:
                    try_send_message(c, chatot_dungeon, "PogChamp I just won a {} badge! PogChamp".format(M.group('name')))
            elif e.source.nick == "pikalaxalt":
                # this is owner-senpai
                if message.startswith("exec "):
                    c.send_raw(message[5:])
        except KeyboardInterrupt:
            raise
        except:
            tb = traceback.format_exc().split("\n")
            for line in tb:
                whisper(c, "pikalaxalt", "\u200b" + line)
                time.sleep(1)

def on_ctcp(c, e):
    if e.arguments[0] == "FINGER":
        whisper(c, e.source.nick, "( ͡° ͜ʖ ͡°)")

def whisper(c, target, message):
    c.send_raw("PRIVMSG #jtv :/w %s %s" % (target, message))

def on_endofmotd(c, e):
    c.cap("REQ", *twitch_caps)
    c.join(",".join(chan_list))
    print("Connected to Twitch chat!")

def on_userstate(c, e):
    global my_tags
    my_tags = {x["key"]: x["value"] for x in e.tags}

