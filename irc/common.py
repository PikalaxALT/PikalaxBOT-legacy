import numpy as np
import subprocess, os, re, time, traceback
import requests, json, pickle, logging, sys
from threading import Timer
from collections import namedtuple
from irc import bot, client
client.ServerConnection.buffer_class.encoding = 'utf8'
from foaas import Fuck, FuckingResponse
fuck = Fuck(secure = True)
from ..utils.commands import RWMC, build_nebby, sample_bag, add_bag, reset_bag

emotelist = []
emote_regex = re.compile("")

_sed_syntax = "^s([,/])(?P<pattern>.*)\\1(?P<replacement>.*)\\1(?P<flags>.*)$"
sed_syntax = re.compile(_sed_syntax)
BotCommand = namedtuple("BotCommand", ["callback", "banned_channels"])

tpp_cmds = r"^((a|b|start|select|left|right|up|down|x|y|r|l|home|\d+,\d+|anarchy|democracy|blow|mic)[\d\+]?)+$"
commands_regex = re.compile(tpp_cmds, re.I)
client_id = 'jw8r8cngubpkudi6038smyplvlz336r'

from .memesongs import *

def try_send_message(c, t, m):
    try:
        c.privmsg(t, m)
    except client.MessageTooLong:
        c.privmsg(t, "Message too long.")
    else:
        return True

def load_emotes():
    global emotelist, emote_regex
    while True:
        try:
            response = requests.request('GET', 'https://api.twitch.tv/kraken/chat/twitchplayspokemon/emoticons', headers = {'Client-ID': client_id})
            if response.status_code != 200:
                raise requests.HTTPError
        except:
            emotes_tries += 1
            if emotes_tries >= 3:
                print("Failed to compile emotes list")
                emotelist = [str(x['regex']) for x in json.load(open('emotes.json', 'r'))['emoticons'] if '\\' not in x['regex']]
                print("Loaded {} emotes from backup".format(len(emotelist)))
                break
        else:
            emotelist = [x['regex'] for x in response.json()['emoticons'] if '\\' not in x['regex']]
            print("Loaded {} emotes".format(len(emotelist)))
            with open('emotes.json', 'w+') as F:
                F.write(response.content.decode())
            break
    emote_regex = re.compile(r"\b(" + "|".join(emotelist) + r")\b")
    sys.stdout.flush()

def on_klappa(message, source, target, tags, connection):
    emote = np.random.choice(['Kappa', 'Keepo', 'KappaPride', 'KappaRoss', 'KappaClaus', 'KappaWealth'])
    return try_send_message(connection, target, '{} 👏'.format(emote))

def on_highlight(message, source, target, tags, connection):
    try:
        name = tags["display-name"]
    except KeyError:
        name = source.nick
    if target == "#keizaron":
        chain = keizaMC.build_chain()
    else:
        chain = streamMC.build_chain()
    return try_send_message(connection, target, name + ": " + chain)

def on_prchase(message, source, target, tags, connection):
    try:
        name = tags["display-name"]
    except KeyError:
        name = source.nick
    chain = botMC.build_chain()
    return try_send_message(connection, target, name + ": " + chain)

def on_riot(message, source, target, tags, connection):
    if not message:
        return try_send_message(connection, target, "ヽ༼ຈل͜ຈ༽ﾉ RIOT ヽ༼ຈل͜ຈ༽ﾉ")
    else:
        message = message.upper()
        if "DANCE" in message:
            return try_send_message(connection, target, "♫ ┌༼ຈل͜ຈ༽┘ ♪ {} RIOT ♪ └༼ຈل͜ຈ༽┐♫".format(message))
        else:
            return try_send_message(connection, target, "ヽ༼ຈل͜ຈ༽ﾉ {} RIOT ヽ༼ຈل͜ຈ༽ﾉ".format(message))

def on_dongers(message, source, target, tags, connection):
    if not message:
        return False
    message = message.upper()
    return try_send_message(connection, target, "ヽ༼ຈل͜ຈ༽ﾉ {} ヽ༼ຈل͜ຈ༽ﾉ".format(message))

def on_emote(message, source, target, tags, connection):
    return try_send_message(connection, target, np.random.choice(emotelist))

def on_spellrand(message, source, target, tags, connection):
    emote = np.random.choice(emotelist)
    msg = emote + " " + (" " + emote + " ").join(list(emote.upper())) + " " +  emote
    return try_send_message(connection, target, msg)

def on_sed(groups, source, target, tags, connection):
    try:
        sep, pattern, replacement, flags = groups
        filename = os.path.join(connection.logs_dir, target + ".log")
        cut_file = subprocess.Popen(["cut", "-d", "\t", "-f", "2-", filename], stdout = subprocess.PIPE)
        find_pattern = subprocess.Popen(["grep", "-nE", pattern], stdin = cut_file.stdout, stdout = subprocess.PIPE)
        get_last_line = find_pattern.stdout.readlines()[-2].decode()
        spl_read = get_last_line.split(":", 2)
        line_no = spl_read[0]
        echo_line = subprocess.Popen(["echo", spl_read[1]], stdout = subprocess.PIPE)
        replace = subprocess.Popen(["sed", "-r", "s{0}{1}{0}{2}{0}{3}".format(*groups)], stdin = echo_line.stdout, stdout = subprocess.PIPE)
        userhosts = subprocess.Popen(["cut", "-d", "\t", "-f", "1", filename], stdout = subprocess.PIPE)
        head = subprocess.Popen(["head", "-n", line_no], stdin = userhosts.stdout, stdout = subprocess.PIPE)
        author = client.NickMask(head.stdout.readlines()[-1].decode().rstrip())
        return try_send_message(connection, target, source.nick + ": " + author.nick + " actually meant: " + replace.stdout.read().decode().rstrip())
    except client.MessageTooLong:
        return try_send_message(connection, target, source.nick + ": Message too long.")
    except:
        return try_send_message(connection, target, source.nick + ": An unknown error occurred.")

def on_song(message, source, target, tags, connection):
    words = message.split()
    if len(words) > 0:
        if words[0] == "trashy":
            song = trashy_song
        elif words[0] == "modbot":
            song = modbot_song
        elif words[0] == "starmie":
            song = starmie_song
        elif words[0] == "riot":
            song = riot_song
        elif words[0] == "ledge":
            song = ledge_song
        elif words[0] == "leechking":
            song = leechking_song
        elif words[0] == "counting":
            global songcount
            songcount += 1
            song = counting_song.format(songcount)
        else:
            song = re.sub("Donger", words[0], donger_song)
    else:
        song = donger_song
    return try_send_message(connection, target, song)

def on_rip(message, source, target, tags, connection):
    if message:
        return try_send_message(connection, target, "RIP {}. Press F to pay your respects.".format(message))
    else:
        return try_send_message(connection, target, "RIP")

def on_dongstortion(message, source, target, tags, connection):
    storted = "".join(np.random.permutation(["ヽ","༼","ຈ","ل","͜","ຈ","༽","ﾉ"]))
    return try_send_message(connection, target, "ヽ༼ຈل͜ຈ༽ﾉ Something strange... DONGSTORTION! {}".format(storted))

def on_archeops(message, source, target, tags, connection):
    words = message.split()
    while len(words) < 2:
        words += [""]
    R = requests.request("POST", "http://watchout4snakes.com/wo4snakes/Random/RandomParagraph", data = {"Subject1": words[0], "Subject2": words[1]})
    return try_send_message(connection, target, R.content.decode())

def on_fuck(message, source, target, tags, connection):
    words = message.split()
    if len(words) == 0:
        words.append("random")
        words.append("yourself")
    if words[0] == "random":
        words[0] = np.random.choice(list(fuck.actions.keys()))
    elif words[0] not in fuck.actions:
        return try_send_message(connection, target, source.nick + ": That shit\u200b isn't within my capabilities.")
    params = {}
    try:
        action = fuck.actions[words.pop(0)]
        for param in re.findall("{(\w+?)}", action):
            if param == "from":
                params[param] = connection.get_nickname()
            elif param == "name":
                params[param] = source.nick
            elif len(words) == 0:
                params[param] = "yourself"
            else:
                params[param] = words.pop(0)
    except IndexError:
        return try_send_message(connection, target, source.nick + ": I need more parameters to do this shit!")
    url = fuck.build_url(action, **params)
    response = FuckingResponse(url).text
    return try_send_message(connection, target, response)

def on_nebby(message, source, target, tags, connection):
    output = build_nebby()
    return try_send_message(connection, target, output) or try_send_message(connection, target, 'Pew!')

def on_bag(message, source, target, tags, connection):
    return try_send_message(connection, target, '\x01ACTION {}\x01'.format(sample_bag()))

def on_addbag(message, source, target, tags, connection):
    if add_bag(message):
        return try_send_message(connection, target, 'Message was put in the bag!')
    else:
        return try_send_message(connection, target, 'Could not put message in bag!')

load_emotes()
streamMC = RWMC(filename = "/home/pi/irclogs/twitch/#twitchplayspokemon.log", emote_regex = emote_regex, commands_regex = commands_regex)
keizaMC = RWMC(filename = "/home/pi/irclogs/twitch/#keizaron.log", emote_regex = emote_regex)
botMC = RWMC(filename = "/home/pi/irclogs/twitch/#tpp.log", emote_regex = emote_regex, commands_regex = commands_regex)
