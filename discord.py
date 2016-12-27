# -*- coding: utf-8 -*-

import sys
assert sys.version_info >= (3, 5), """This script requires Python 3.5 or higher.
It is not compatible with any version of Python 2."""

import platform
assert platform.system != "Windows", "This script is not compatible with Windows."

from .utils.commands import RWMC, build_nebby, add_bag, sample_bag
from .utils.games import Anagram, Hangman
from .irc.memesongs import *
import shlex, discord, re, subprocess, json, urllib3, time, traceback, asyncio, wave, codecs, requests, pickle, logging
http = urllib3.PoolManager()
import numpy as np
from urllib3.exceptions import InsecureRequestWarning
logging.basicConfig(level=logging.INFO)
from websockets.exceptions import ConnectionClosed

urllib3.disable_warnings(InsecureRequestWarning)

VC = None
player = None
ytqueue = []
client = discord.Client()
bot_channel = None
doot_channel = None
default_tts_params = {"a": "100", "s": "175", "g": "1", "p": "50", "v": "en"}

settingsfile = "/home/pi/.config/discord/bot/settings.pickle"
def write_settings():
    pickle.dump((prefix, tts_params, disabled_commands, client_game), open(settingsfile, 'wb'))
try:
    prefix, tts_params, disabled_commands, client_game = pickle.load(open(settingsfile, 'rb'))
except:
    prefix = "!"
    tts_params = default_tts_params.copy()
    disabled_commands = []
    client_game = "OLDEN"
    write_settings()

my_name = "PikalaxBOT"
voice_disabled = False
my_owner = None
myself = None

stat_names = ['hp', 'attack', 'defense', 'special-attack', 'special-defense', 'speed']
stat_names_o = ["HP:   ", "Atk:  ", "Def:  ", "SpAtk:", "SpDef:", "Speed:"]

cooldown = 10
last_message = {}
rate = 0.0001

time_to_hms = lambda num_secs: "%dh%dm%ds" % (num_secs // 3600, (num_secs // 60) % 60, num_secs % 60)

def pairs(object):
    if len(object) % 2:
        raise ValueError("object length must be a multiple of 2")
    ret = []
    for i in range(len(object) // 2):
        ret.append((object[2 * i], object[2 * i + 1]))
    return ret

def try_int(x):
    try:
        x = int(x)
    except:
        return False
    return True

def format_proper_noun(instr):
    return re.sub("(\w+)", lambda x: x.groups()[0][0].upper() + x.groups()[0][1:], instr)

def init_functions():
    global cmd_dict, buzz_dict
    cmd_dict = {
    prefix + "riot": (riot_cb, False, prefix + "riot <text> --> Riot about <text>!\n!riot <text with the word dance> --> Dance riot!", True),
    prefix + "emote": (emote_cb, False, prefix + "emote --> Random emote", True),
    prefix + "spellrand": (spellrand_cb, False, prefix + "spellrand --> Random emote, but decorates it with its spelling (all caps)", True),
    prefix + "dongers": (dongers_cb, False, prefix + "dongers <text> --> Wraps text in Dongers\n!dongers dance <text> --> Wraps text in dancing Dongers.", True),
    prefix + "pikacoin": (coin_cb, False, prefix + "pikacoin <1-20> --> Flips that many coins.\n!pikacoin until <heads, tails> --> Flips coins until specified side comes up.", True),
    prefix + "anagram": (anagram_cb, True, prefix + "anagram start --> Starts a game of Anagram.\n!anagram show --> Shows the current puzzle.\n!anagram solve <guess> --> Solves the puzzle.", True),
    prefix + "hangman": (hangman_cb, True, prefix + "hangman start --> Starts a game of Hangman.\n!hangman show --> Shows the current puzzle.\n!hangman guess <guess> --> Guess a letter or the solution.", True),
    prefix + "pokeapi": (pokeapi_cb, False, prefix + "pokeapi <category> <name or id> --> Searches http://pokeapi.co for the given query.", True),
    prefix + "ttsparams": (voice_params_cb, False, prefix + "ttsparams (param, value) --> Change the parameters accepted by espeak.  Currently supported: 'a', 's', 'p', 'g', 'v'", True),
    prefix + "speak": (voice_cb, True, prefix + "speak <text> --> Use espeak to synthesize the given text.", False),
    prefix + "pikahelp": (pikahelp_cb, True, prefix + "pikahelp --> Displays this message.  Only this message.", False),
    prefix + "ytplay": (youtube_cb, False, prefix + "ytplay <video hash> --> Plays the video with specified hash from YouTube", True),
    prefix + "pikashutup": (stop_player_cb, True, prefix + "pikashutup --> Stop any audio that's currently playing", False),
    prefix + "ytnext": (next_video_cb, True, prefix + "ytnext --> Play the next video in the queue.", True),
    prefix + "ytqueue": (check_ytqueue_cb, False, prefix + "ytqueue --> Show the queued videos.", True),
    prefix + "olden": (olden_cb, False, prefix + "olden --> WutFace", True),
    prefix + "rip": (rip_cb, False, prefix + "rip <stuff> --> Pays respects to <stuff>.", True),
    prefix + "prchase": (prchase_cb, False, prefix + "prchase --> The battle is getting intense! PRChase", True),
    prefix + "archeops": (archeops_cb, False, prefix + "archeops [word1 [word2]] --> Random paragraph from WatchOut4Snakes.com MingLee", True),
    prefix + "song": (song_cb, False, prefix + "song [word] --> Copypasta based on the Donger Song", True),
    prefix + "pikaowner": (pikaowner_cb, True, prefix + "pikaowner --> Restricted use", True),
    prefix + "shutdown": (shutdown_cb, False, prefix + "shutdown --> Restricted use", True),
    prefix + "nebby": (nebby_cb, False, prefix + "nebby --> Random Cosmog noise", True),
    # prefix + "bag": (bag_cb, False, prefix + "bag --> Cosmog interacts with the bag", True),
    # prefix + "addbag": (addbag_cb, False, prefix + "addbag [message] --> Add a Cosmog-bag interaction", True),
    }

    buzz_dict = {
    "riot": (riot_bw, False, "Say \"riot\" anywhere in the text to riot! Add the word \"dance\" for added fun!", False),
    myself.name.lower(): (rwmc_bw, False, "Say my name, and I'll try to respond in a semi-coherent fashion, by stringing together sentences from Twitch Plays Pokemon chat on Discord.", True)
    }

async def get_pokeapi(category, name):
    url = "http://pokeapi.co/api/v2/%s/%s/" % (category, name)
    resp = http.request('GET', url)
    if resp.status == 200:
        return json.loads(resp.data.decode())
    await client.send_message(message.channel, "Server error: %d" % resp.status)

def process_api_pokemon(json_obj):
    output  = "Name: " + format_proper_noun(json_obj['name']) + " (#{:03})".format(json_obj['id']) + "\n"

    output += "Types: "
    types = [None] * 2 # Assume every Pokemon can have at most 2 types
    for x in json_obj['types']:
        types[x['slot'] - 1] = format_proper_noun(x['type']['name'])
    output += types[0]
    if types[1]:
        output += ", " + types[1]
    output += "\n"

    output += "Abilities: \n"
    abilities = [None] * 3 # Assume every Pokemon can have at most 3 abilities
    for x in json_obj['abilities']:
        abilities[x['slot'] - 1] = (format_proper_noun(x['ability']['name']), x['is_hidden'])
    for x in abilities:
        if x:
            name, hidden = x
            if hidden:
                output += '\t' + name + ' (hidden)\n'
            else:
                output += '\t' + name + '\n'

    output += "Base Stats:\n"
    stats = [None] * 6
    for x in json_obj['stats']:
        stats[stat_names.index(x['stat']['name'])] = (x['base_stat'], x['effort'])
    for i, x in enumerate(stats):
        output += "\t" + stat_names_o[i] + " {:>3}\n".format(x[0])
    return output

def process_pokeapi(category, json_obj):
    if category == "pokemon":
        output = process_api_pokemon(json_obj)
    else:
        # output = str(json_obj) # temporary, just to get the structure set up
        output = "Method \"" + category + "\" is not yet supported."
    return output

async def pokeapi_cb(message):
    args = message.content.split()
    if len(args) < 3:
        await client.send_message(message.channel, "Not enough arguments")
        return
    try:
        output = await get_pokeapi(args[1], args[2])
    except:
        await client.send_message(message.channel, "The server returned an error. BrokeBack\n```%s```" % traceback.format_exc())
    else:
        if output:
            processed = process_pokeapi(args[1], output)
            await client.send_message(message.channel, "```%s```" % processed)

def update_cooldown(message, flag):
    if flag:
        return 1
    global last_message
    now = time.time()
    key = (message.server.name, message.channel.name, message.author.name)
    if key in last_message:
        if last_message[key] + cooldown > now:
            return 0
    last_message[key] = now
    return 1

async def riot_cb(message):
    riot_msg = message.content
    if len(riot_msg) > len(prefix + "riot "):
        riot_msg = riot_msg[len(prefix + "riot "):]
        if "DANCE" in riot_msg:
            await client.send_message(message.channel, "♫ ┌༼ຈل͜ຈ༽┘ ♪ {} RIOT ♪ └༼ຈل͜ຈ༽┐♫ ".format(riot_msg))
        else:
            await client.send_message(message.channel, "ヽ༼ຈل͜ຈ༽ﾉ {} RIOT ヽ༼ຈل͜ຈ༽ﾉ".format(riot_msg))
    else:
        await client.send_message(message.channel, "ヽ༼ຈل͜ຈ༽ﾉ RIOT ヽ༼ຈل͜ຈ༽ﾉ")

async def dongers_cb(message):
    riot_msg = message.content
    if len(riot_msg) > len(prefix + "dongers "):
        riot_msg = riot_msg[len(prefix + "dongers "):]
        if riot_msg.startswith("DANCE "):
            await client.send_message(message.channel, "♫ ┌༼ຈل͜ຈ༽┘ ♪ {} ♪ └༼ຈل͜ຈ༽┐♫ ".format(riot_msg[6:]))
        else:
            await client.send_message(message.channel, "ヽ༼ຈل͜ຈ༽ﾉ {} ヽ༼ຈل͜ຈ༽ﾉ".format(riot_msg))
    

async def riot_bw(message):
    if message.content.split()[-1].lower() == "riot":
        await client.send_typing(message.channel)
        content = message.content
        if "DANCE" in content:
            await client.send_message(message.channel, "♫ ┌༼ຈل͜ຈ༽┘ ♪ {} ♪ └༼ຈل͜ຈ༽┐♫ ".format(content))
        else:
            await client.send_message(message.channel, "ヽ༼ຈل͜ຈ༽ﾉ {} ヽ༼ຈل͜ຈ༽ﾉ".format(content))

async def emote_cb(message):
    await client.send_message(message.channel, str(np.random.choice(message.server.emojis)))

async def spellrand_cb(message):
    cur_emote = np.random.choice(message.server.emojis)
    cur_emote_str = str(cur_emote)
    spelled_emote = cur_emote_str + " " + (" " + cur_emote_str + " ").join(list(cur_emote.name.upper())) + " " + cur_emote_str
    await client.send_message(message.channel, spelled_emote)

async def rwmc_bw(message):
    if message.server.id == "88066218971385856":
        return await build_rwmc(message, psrMC)
    return await build_rwmc(message, streamMC)

async def prchase_cb(message):
    return await build_rwmc(message, botMC)

async def nebby_cb(message):
    output = build_nebby()
    await client.send_message(message.channel, output)

async def build_rwmc(message, chainer):
    chain = chainer.build_chain()
    await client.send_message(message.channel, message.author.mention + ": " + chain)
    return True

async def olden_cb(message):
    return await client.send_file(message.channel, "/home/pi/NGLKKBO.png")

async def coin_cb(message):
    coin_results = ["HEADS", "TAILS"]
    msg = message.content.split()
    if len(msg) == 1:
        await client.send_message(message.channel, message.author.mention + " flipped a coin.  It landed on " + np.random.choice(coin_results) + prefix + "")
    elif try_int(msg[1]):
        if int(msg[1]) > 20:
            await client.send_message(message.channel, message.author.mention + " wants to flip " + msg[1] + " coins, but that would take too long.")
        elif int(msg[1]) < 0:
            await client.send_message(message.channel, message.author.mention + " wants to flip " + msg[1] + " coins, but that would break physics.")
        elif int(msg[1]) == 0:
            await client.send_message(message.channel, message.author.mention + " wants to flip " + msg[1] + " coins, but that would be utterly pointless.")
        else:
            await client.send_message(message.channel, message.author.mention + " started flipping coins!")
            results = np.random.choice(coin_results, int(msg[1]), replace = True)
            num_heads = (results == coin_results[0]).sum()
            num_tails = int(msg[1]) - num_heads
            await client.send_message(message.channel, ", ".join(results))
            await client.send_message(message.channel, "Results: " + str(num_heads) + " " + coin_results[0] + ", " + str(num_tails) + " " + coin_results[1])
    elif message.content.lower() == prefix + "pikacoin until tails":
        await client.send_message(message.channel, message.author.mention + " started flipping coins!")
        results = []
        while True:
            flipped = np.random.choice(coin_results)
            results.append(flipped)
            if flipped == coin_results[1]:
                break
            if len(results) == 20:
                await client.send_message(message.channel, "The first 20 flips were all " + coin_results[0] + ". Lucky!")
                return
        await client.send_message(message.channel, ", ".join(results))
        await client.send_message(message.channel, "Results: " + str(len(results)-1) + " " + coin_results[0] + ", 1 " + coin_results[1])
    elif message.content.lower() == prefix + "pikacoin until heads":
        await client.send_message(message.channel, message.author.mention + " started flipping coins!")
        results = []
        while True:
            flipped = np.random.choice(coin_results)
            results.append(flipped)
            if flipped == coin_results[0]:
                break
            if len(results) == 20:
                await client.send_message(message.channel, "The first 20 flips were all " + coin_results[1] + ". Lucky!")
                return
        await client.send_message(message.channel, ", ".join(results))
        await client.send_message(message.channel, "Results: 1 " + coin_results[0] +", " + str(len(results)-1) + " " + coin_results[1])
    else:
        await client.send_message(message.channel, message.author.mention + " flipped a coin.  It landed on " + np.random.choice(coin_results) + prefix + "")

async def check_ytqueue_cb(message):
    global ytqueue
    if len(ytqueue) == 0:
        await client.send_message(message.channel, "Nothing in the queue")
    else:
        output = "%d videos in queue:\n" % len(ytqueue)
        for ind, player in enumerate(ytqueue):
            output += "%d: `%s by %s (%s)`%s\n" % (ind, player.title, player.uploader, time_to_hms(player.duration), " (currently playing)" if not ind else "")
        await client.send_message(message.channel, output)

def strip_unicode(content):
    new_content = [ord(x) for x in content]
    for i,x in enumerate(new_content):
        if (x not in range(0x20, 0x80)) and (x not in range(0xa0, 0x100)):
            new_content[i] = 0x20
    return "".join([chr(x) for x in new_content])

async def voice_cb(message):
    global player, ytqueue
    if ytqueue:
        return
    if player:
        if player.is_playing():
            return
    to_say = strip_unicode(message.clean_content[len(prefix + "speak "):])
    to_say = re.sub(r'<:(\S+?):\d+>', r'\1', to_say)
    # await client.send_message(message.channel, to_say)
    if client.is_voice_connected(message.server):
        # await client.send_message(message.channel, "Now saying: " + to_say)
        cur_params = []
        for k, v in tts_params.items():
            cur_params += ["-" + k, v]
        O = subprocess.run(['espeak', '-k', '20'] + cur_params + [to_say, '-w', 'temp.wav'])
        player = VC.create_ffmpeg_player("temp.wav", before_options = "-hide_banner -loglevel panic")
        player.start()
    else:
        await client.send_message(message.channel, "Voice client is not connected.")

async def next_video_cb(message):
    global ytqueue
    if len(ytqueue) == 0:
        await client.send_message(message.channel, "Nothing to skip.")
        return
    ytqueue[0].stop()
    if len(ytqueue) == 0:
        await client.send_message(message.channel, "Skipped video. Reached end of queue")
    else:
        await client.send_message(message.channel, "Skipped video. Now playing: `%s by %s (%s)`" % (ytqueue[0].title, ytqueue[0].uploader, time_to_hms(ytqueue[0].duration)))

def next_video():
    global ytqueue
    ytqueue.pop(0)
    time.sleep(1)
    if len(ytqueue) > 0:
        ytqueue[0].start()

async def youtube_cb(message):
    global player, ytqueue
    if len(message.content.split()) == 1:
        await client.send_message(message.channel, "Whoops! You didn't specify a video ID!")
        return
    if player:
        if player.is_playing():
            return

    if client.is_voice_connected(message.server):
        vidhash = message.content.split()[1]
        url = "http://youtu.be/" + vidhash
        for attempt in range(3):
            try:
                ytqueue.append(await VC.create_ytdl_player(url, after = next_video, ytdl_options = {"quiet": True}))
                ytqueue[-1].message = message
            except:
                pass
            else:
                break
        else:
            await client.send_message(message.channel, "Whoops! I couldn't get that video for you.  Try another?")
            return
        if len(ytqueue) == 1:
            await client.send_message(message.channel, "Now playing: `%s by %s (%s)`" % (ytqueue[-1].title, ytqueue[-1].uploader, time_to_hms(ytqueue[-1].duration)))
            ytqueue[-1].start()
        else:
            await client.send_message(message.channel, "Queued: `%s by %s (%s)`" % (ytqueue[-1].title, ytqueue[-1].uploader, time_to_hms(ytqueue[-1].duration)))
    else:
        await client.send_message(message.channel, "Voice client is not connected.")

def try_stop_player(player_ob):
    if not player_ob:
        return
    while player_ob.is_playing():
        try:
            player_ob.stop()
        except:
            pass

async def stop_player_cb(message):
    global player, ytqueue
    try_stop_player(player)
    if len(ytqueue) > 0:
        ytplayer = ytqueue[0]
        ytqueue = []
        try_stop_player(ytplayer)

async def song_cb(message):
    words = message.clean_content.split()
    if len(words) > 1:
        if words[1] == "trashy":
            song = trashy_song
        elif words[1] == "modbot":
            song = modbot_song
        elif words[1] == "starmie":
            song = starmie_song
        elif words[1] == "riot":
            song = riot_song
        elif words[1] == "ledge":
            song = ledge_song
        elif words[1] == "leechking":
            song = leechking_song
        elif words[1] == "counting":
            global songcount
            songcount += 1
            song = counting_song.format(songcount)
        else:
            song = re.sub("Donger", words[1], donger_song)
    else:
        song = donger_song
    await client.send_message(message.channel, song)
    

anagram = Anagram()
hangman = Hangman()

async def anagram_cb(message):
    args = message.content.lower().split()
    if len(args) == 1:
        await client.send_message(message.channel, "Error: Insufficient parameters for !anagram")
        return
    if args[1] == "start":
        if hangman.active:
            await client.send_message(message.channel, "Error: Cannot run Anagram while Hangman is running")
            return
        if anagram.active:
            await client.send_message(message.channel, "Error: Anagram is already running")
            return
        anagram.start(message.channel)
        await client.send_message(message.channel, "Anagram has started!")
        await client.send_message(message.channel, anagram.prompt + " | Incorrect: " + ", ".join(anagram.incorrect) + " | Guesses remaining: " + str(anagram.guesses))
    elif (anagram.channel is not None) and (anagram.channel != message.channel):
        await client.send_message(message.channel, "Error: Anagram is running, but in " + anagram.channel.mention)
    elif args[1] == "stop":
        if not anagram.active:
            await client.send_message(message.channel, "Error: Anagram is not running")
        elif message.author != my_owner:
            await client.send_message(message.channel, "Error: Insufficient permissions")
        else:
            anagram.stop()
            await client.send_message(message.channel, "Anagram terminated")
    elif args[1] == "solve":
        if len(args) < 3:
            await client.send_message(message.channel, "Error: Insufficient parameters for !anagram")
            return
        if not anagram.active:
            await client.send_message(message.channel, "Error: Anagram is not running")
            return
        await client.send_message(message.channel, message.author.mention + " has guessed " + args[2].upper() + ".")
        if anagram.check_guess(args[2]):
            await client.send_message(message.channel, "That's absolutely correct! Well done, " + message.author.mention + "!")
            anagram.stop()
        else:
            await client.send_message(message.channel, "Nope, that wasn't it.")
            if anagram.guesses:
                await client.send_message(message.channel, anagram.prompt + " | Incorrect: " + ", ".join(anagram.incorrect) + " | Guesses remaining: " + str(anagram.guesses))
            else:
                await client.send_message(message.channel, "You've run out of guesses! The correct answer is: " + anagram.solution)
                anagram.stop()
    elif args[1] == "show":
        if not anagram.active:
            await client.send_message(message.channel, "Error: Anagram is not running")
            return
        await client.send_message(message.channel, anagram.prompt + " | Incorrect: " + ", ".join(anagram.incorrect) + " | Guesses remaining: " + str(anagram.guesses))
    else:
        await client.send_message(message.channel, "Error: Method " + args[1] + " not supported")

async def hangman_cb(message):
    args = message.content.lower().split()
    if len(args) == 1:
        return await client.send_message(message.channel, "Error: Insufficient parameters for !hangman")
    if args[1] == "start":
        if anagram.active:
            return await client.send_message(message.channel, "Error: Cannot run Hangman while Anagram is running")
        if hangman.active:
            return await client.send_message(message.channel, "Error: Hangman is already running")
        hangman.start(message.channel)
        await client.send_message(message.channel, "Hangman has started!")
        await client.send_message(message.channel, " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
    elif (hangman.channel is not None) and (hangman.channel != message.channel):
        await client.send_message(message.channel, "Error: Hangman is running, but in " + hangman.channel.mention)
    elif args[1] == "stop":
        if not hangman.active:
            await client.send_message(message.channel, "Error: Hangman is not running")
        elif message.author != my_owner:
            await client.send_message(message.channel, "Error: Insufficient permissions")
        else:
            hangman.stop()
            await client.send_message(message.channel, "Hangman terminated")
    elif args[1] == "guess":
        if len(args) < 3:
            return await client.send_message(message.channel, "Error: Insufficient parameters for !hangman")
        if not hangman.active:
            return await client.send_message(message.channel, "Error: Hangman is not running")
        outcome = hangman.check_guess(args[2])
        if outcome == 2:
            await client.send_message(message.channel, message.author.mention + " solved the puzzle! Well done, " + message.author.mention + "!")
            await client.send_message(message.channel, "The correct answer was: " + hangman.solution)
            hangman.stop()
        elif outcome == 1:
            await client.send_message(message.channel, " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
        else:
            if hangman.guesses:
                await client.send_message(message.channel, " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
            else:
                await client.send_message(message.channel, "You've run out of guesses! The correct answer is: " + hangman.solution)
                hangman.stop()
    elif args[1] == "show":
        if not hangman.active:
            return await client.send_message(message.channel, "Error: Hangman is not running")
        await client.send_message(message.channel, " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
    else:
        await client.send_message(message.channel, "Error: Method " + args[1] + " not supported")

async def pikahelp_cb(message):
    await client.send_message(message.author, "```" + "\n".join([x[2] for x in cmd_dict.values()]) + "```")
    await client.send_message(message.author, "```" + "\n".join([x[2] for x in buzz_dict.values()]) + "```")

async def set_game_cb(message, game_name):
    global client_game
    client_game = game_name
    await client.change_presence(game = discord.Game(name = client_game))
    write_settings()

async def set_prefix_cb(message, new_prefix):
    global prefix
    assert " " not in new_prefix, "Cannot have a prefix with a space in it"
    assert len(prefix) <= 4, "Prefix too long (max length: 4)"
    prefix = new_prefix
    init_functions()

async def disable_cmd_cb(message, command):
    global disabled_commands
    command = command.lower()
    if command == prefix + "pikaowner":
        raise RuntimeError("unable to disable mod command")
    if (command not in cmd_dict) and (command not in buzz_dict):
        raise RuntimeError("not actually a command")
    if command in disabled_commands:
        raise RuntimeError("command already disabled")
    disabled_commands.append(command)

async def enable_cmd_cb(message, command):
    global disabled_commands
    command = command.lower()
    if command == prefix + "pikaowner":
        raise RuntimeError("unable to disable mod command")
    if (command not in cmd_dict) and (command not in buzz_dict):
        raise RuntimeError("not actually a command")
    if command not in disabled_commands:
        raise RuntimeError("command not disabled")
    disabled_commands.remove(command)

async def change_voice_channel_cb(message, command):
    global VC
    VoiceChannel = discord.utils.get(client.get_all_channels(), server__name = message.server.name, name = command, type = discord.ChannelType.voice)
    if VoiceChannel:
        await stop_player_cb(None)
        await VC.disconnect()
        VC = await client.join_voice_channel(VoiceChannel)
    else:
        raise RuntimeError("channel does not exist")

set_params = {
"game": set_game_cb,
"prefix": set_prefix_cb,
"disable": disable_cmd_cb,
"enable": enable_cmd_cb,
"voicechan": change_voice_channel_cb
}

async def pikaowner_cb(message):
    if message.author != my_owner:
        await client.send_message(message.channel, "You are not allowed to change my properties.")
        return
    try:
       args = pairs(shlex.split(message.content)[1:])
    except ValueError:
        await client.send_message(message.channel, "Arguments must be in pairs")
    except:
        await client.send_message(message.channel, "An unhandled exception has occurred. Details below.")
        raise
    else:
        # check loop
        for key, value in args:
            if key not in set_params.keys():
                await client.send_message(message.channel, "Error: Key `" + key + "` not found")
                return
        for key, value in args:
            try:
                await set_params[key](message, value)
                await client.send_message(message.channel, "Set {} to `{}`".format(key, value))
            except:
                await client.send_message(message.channel, "Error:\n```" + traceback.format_exc() + "```")
        write_settings()

async def rip_cb(message):
    words = message.content.split()
    if len(words) > 1:
        await client.send_message(message.channel, "RIP {}. Press F to pay your respects.".format(" ".join(words[1:])))
    else:
        await client.send_message(message.channel, "RIP")

async def bag_cb(message):
    await client.send_message(message.channel, '_{}_'.format(sample_bag()))

async def addbag_cb(message):
    if add_bag(message.clean_content.split(' ', 1)[1]):
        await client.send_message(message.channel, 'Message was put in the bag!')
    else:
        await client.send_message(message.channel, 'Could not put message in bag!')

async def voice_params_cb(message):
    global tts_params
    tts_params_backup = tts_params.copy()
    args = message.content.lower().split()
    if len(args) < 3:
        await client.send_message(message.channel, "Not enough parameters")
    elif len(args[1:]) % 2:
        await client.send_message(message.channel, "Arguments must be in pairs")
    elif not all([args[1 + 2*i] in tts_params.keys() for i in range(len(args[1:]) // 2)]):
        await client.send_message(message.channel, "Invalid argument detected")
    else:
        for param, value in pairs(args[1:]):
            tts_params[param] = value
            await client.send_message(message.channel, "Set param \"{}\" to: {}".format(param, value))
        cur_params = []
        for k, v in tts_params.items():
            cur_params += ["-" + k, v]
        O = subprocess.run(['espeak', '-k', '20'] + cur_params + ["test", '-w', 'garbage.wav'])
        if O.returncode:
            await client.send_message(message.channel, "Invalid paramters for espeak, reverting...")
            tts_params = tts_params_backup.copy()
    write_settings()

async def archeops_cb(message):
    words = message.clean_content.split()
    while len(words) < 3:
        words += [""]
    R = requests.request("POST", "http://watchout4snakes.com/wo4snakes/Random/RandomParagraph", data = {"Subject1": words[1], "Subject2": words[2]})
    await client.send_message(message.channel, R.content.decode())

async def shutdown_cb(message):
    if message.author == my_owner:
        raise KeyboardInterrupt
    else:
        await client.send_message(message.channel, message.author.mention + ": Operation not permitted TriHard")
    
cmd_dict = {}
buzz_dict = {}

previous_traceback = ""

def is_allowed(message):
    if message.author == myself:
        return False
    elif message.server.id in ["148079346685313034", "162752501131640832"]:
        return True
    elif message.server.id == "88066218971385856":
        return message.channel.id == "110897075159302144"
    elif message.server.id == "110373943822540800":
        return message.channel.id not in ["110374153562886144", "110373943822540800"]
    else:
        return True

@client.event
async def on_ready():
    global bot_channel, my_owner, myself, botMC, streamMC, psrMC
    # with open("/home/pi/NGLKKBO.png", "rb") as F:
    #     await client.edit_profile(avatar = F.read())
    bot_channel = discord.utils.get(client.get_all_channels(), id="151257324869255168")
    sent_msg = await client.send_message(bot_channel, "Booting...")
    await client.change_presence(game = discord.Game(name = client_game))
    if voice_disabled:
        print("Voice comms disabled")
    elif discord.opus.is_loaded():
        global VC
        VC = await client.join_voice_channel(discord.utils.get(client.get_all_channels(), id="148080149995192320")) # main channel in tpp server
    else:
        sys.stdout.write("Opus is not loaded, so voice will not be available.\n")
        sys.stdout.flush()
    sys.stdout.write("Loading client data, kill this if it takes too long\n")
    sys.stdout.flush()
    my_owner = discord.utils.get(client.get_all_members(), id="148462033770119168")
    myself = client.user
    try:
        n_attempts = 0
        doot_channel = discord.utils.get(client.get_all_channels(), id="148080089488162817")
        botMC = RWMC(filename = "/home/pi/irclogs/twitch/#tpp.log")
        streamMC = RWMC()
        async for x in client.logs_from(doot_channel, limit = 5000):
            streamMC.train_line(x.clean_content)
        psrMC = RWMC()
        PSR_server = client.get_server("88066218971385856")
        for channel in PSR_server.channels:
            try:
                async for x in client.logs_from(channel, limit = 500):
                    psrMC.train_line(x.clean_content)
            except discord.errors.Forbidden:
                continue
        # await client.send_message(my_owner, "{}".format(len(streamMC)))
        sys.stdout.write("Client data loaded!\n")
        sys.stdout.flush()
        init_functions()
        await client.edit_message(sent_msg, "PikalaxBOT is now online")
        # await client.send_message(bot_channel, "Markov chains are temporarily disabled due to an unresolved bug. Sorry :\\")
    except:
        last_traceback = traceback.format_exc()
        await client.edit_message(sent_msg, "Setup error: ```Python\n" + last_traceback + "```")

@client.event
async def on_message(message):
    if message.channel == doot_channel:
        streamMC.train_line(message.clean_content)
    elif message.server.id == "88066218971385856":
        psrMC.train_line(message.clean_content)
    if is_allowed(message):
        word = message.content.split()
        if len(word) == 0:
            return
        try:
            cur_cmd = ""
            cmd = word[0].lower()
            if (cmd in cmd_dict) and (cmd not in disabled_commands):
                if update_cooldown(message, cmd_dict[cmd][1]):
                    cur_cmd = cmd
                    if cmd_dict[cmd][3]:
                        await client.send_typing(message.channel)
                    await cmd_dict[cmd][0](message)
            else:
                for x in buzz_dict:
                    if (x in message.content.lower()) and (x not in disabled_commands):
                        if update_cooldown(message, buzz_dict[x][1]):
                            cur_cmd = x
                            if buzz_dict[x][3]:
                                await client.send_typing(message.channel)
                            await buzz_dict[x][0](message)
                            break
                if (np.random.random() < rate or myself in message.mentions) and update_cooldown(message, False) and (myself.name.lower() not in disabled_commands) and (not cur_cmd):
                    await client.send_typing(message.channel)
                    await rwmc_bw(message)
                    cur_cmd = "rwmc"
        except KeyboardInterrupt:
            await client.send_message(discord.bot_channel, "Shutting down...")
            await client.logout()
            await client.close()
        except discord.errors.Forbidden:
            await client.send_message(my_owner, "Received Error 403 when responding to {} in {} on server {}".format(cur_cmd, message.channel.name, message.server.name))
            await client.send_message(message.channel, "Insufficient permissions danNo")
        except ConnectionClosed:
            raise
        except:
            global previous_traceback
            last_traceback = traceback.format_exc()
            if last_traceback != previous_traceback:
                await client.send_message(message.channel, "Something went wrong on my end :BibleThump:")
                try:
                    await client.send_message(message.channel, "```Python\n" + last_traceback + "```")
                except:
                    tb_filename = "tracebacks/{:d}.txt".format(time.time())
                    open(tb_filename, "w+").write(last_traceback)
                    await client.send_file(message.channel, tb_filename)
                finally:
                    print(last_traceback)
                    previous_traceback = last_traceback
