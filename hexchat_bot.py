#!/usr/bin/python
# -*- coding: utf-8 -*-

import hexchat as hc
import numpy as np
import random, rwmc, re, time, requests, json, cPickle
from os import popen
from moves import movelist
from .hangman import Hangman
from .anagram import Anagram

owner_nick = "OLDEN"
owner_account = {
'freenode': "^.+@unaffiliated/pikalaxalt$",
'twitch': '^pikalaxalt!.+$'
}
botlist = ["pikalaxbot","slackbot","dootbot", "doofbot", "q20pokemonbot", "wow_deku_onehand", "wallbot303", "groudonger", "23forces", "facts_bot", "twitchplaysleaderboard", "alicecatson", "yaybot", "oldenbot"]

logs_dir = "/home/pi/.config/hexchat/logs"
dootabyll = False

last_donger = {}
timeouts = {
("freenode", "#twitchplayspokemon-secret"): 0,
("twitch", "#adventuresofchat"): 60
}
default_cooldown = 10

emotes_succeeded = False
emotes_tries = 0
messaging = False

userlists = {}

def try_int(x):
    try:
        x = int(x)
    except:
        return False
    else:
        return True

def on_blame(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    if re.match(speaker_nick, msg[1], re.I):
        hc.command("say {} blames themselves.".format(speaker_nick))
    else:
        hc.command("say {} blames {}.".format(speaker_nick, msg[1]))

def on_coin(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    if network == "freenode":
        coin_results = ["3HEADS", "4TAILS"]
    else:
        coin_results = ["HEADS", "TAILS"]
    if len(msg) == 1:
        hc.command("say " + speaker_nick + " flipped a coin.  It landed on " + random.choice(coin_results) + "!")
    elif try_int(msg[1]):
        if int(msg[1]) > 20:
            hc.command("say " + speaker_nick + " wants to flip " + msg[1] + " coins, but that would take too long.")
        elif int(msg[1]) < 0:
            hc.command("say " + speaker_nick + " wants to flip " + msg[1] + " coins, but that would break physics.")
        elif int(msg[1]) == 0:
            hc.command("say " + speaker_nick + " wants to flip " + msg[1] + " coins, but that would be utterly pointless.")
        else:
            hc.command("say " + speaker_nick + " started flipping coins!")
            results = [random.choice(coin_results) for i in xrange(int(msg[1]))]
            num_heads = results.count(coin_results[0])
            num_tails = int(msg[1]) - num_heads
            hc.command("say " + ", ".join(results))
            hc.command("say Results: " + str(num_heads) + " " + coin_results[0] + ", " + str(num_tails) + " " + coin_results[1])
    elif msg_eol[0].lower() == "!coin until tails":
        hc.command("say " + speaker_nick + " started flipping coins!")
        results = []
        while True:
            flipped = random.choice(coin_results)
            results.append(flipped)
            if flipped == coin_results[1]:
                break
            if len(results) == 20:
                hc.command("say The first 20 flips were all " + coin_results[0] + ". Lucky!")
                return
        hc.command("say " + ", ".join(results))
        hc.command("say Results: " + str(len(results)-1) + " " + coin_results[0] + ", 1 " + coin_results[1])
    elif msg_eol[0].lower() == "!coin until heads":
        hc.command("say " + speaker_nick + " started flipping coins!")
        results = []
        while True:
            flipped = random.choice(coin_results)
            results.append(flipped)
            if flipped == coin_results[0]:
                break
            if len(results) == 20:
                hc.command("say The first 20 flips were all " + coin_results[1] + ". Lucky!")
                return
        hc.command("say " + ", ".join(results))
        hc.command("say Results: 1 " + coin_results[0] +", " + str(len(results)-1) + " " + coin_results[1])
    else:
        hc.command("say " + speaker_nick + " flipped a coin.  It landed on " + random.choice(coin_results) + "!")

def on_noq20(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    if channel != "#tppleague":return
    if "q20pokemonbot" in [x.nick.lower() for x in hc.get_list("users")]:return
    hc.command("say RIP Q20PokemonBot")

def on_klappa(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    if network == 'Slack':
        emote = random.choice([':kappa:', ':keepo:', ':kappapride:', ':kappaross:', ':kappaclaus:'])
    else:
        emote = random.choice(['Kappa', 'Keepo', 'KappaPride', 'KappaRoss', 'KappaClaus'])
    hc.command('say {} 👏'.format(emote))

def on_sed(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    split_up = re.split(r'(?<!\\)' + msg_eol[0][1], msg_eol[0])
    if len(split_up) != 4:
        return
    if re.findall('I', split_up[3], re.I):
        flags = re.I
        split_up[3] = re.sub('I', '', split_up[3], flags = re.I)
    else:
        flags = 0
    if re.findall('g', split_up[3], re.I):
        f_global = True
        split_up[3] = re.sub('g', '', split_up[3], flags = re.I)
    else:
        f_global = False
    if split_up[3] == '':
        num = 0
    else:
        try:
            num = int(split_up[3])
        except:
            return
        if num < 0:
            return
    lines = popen('cat -v /home/pi/.config/hexchat/logs/' + network.lower() + '/' + channel.lower() + '.log | grep -E "^... .. ..:..:.. <\w+>" | tail -n500 | tac').read().split('\n')[:-1]
    if split_up[1] == '':
        for line in lines:    
            args = line.split('\t')
            if len(args) <= 1:
                continue
            matched_speaker = args[0].split('<')[1][:-1]
            if matched_speaker == hc.get_info('nick') and re.match("\w+: \w+ meant to say: .*$", args[1]):
                matched_speaker = re.findall("\w+: \w+ meant to say: ", args[1])[-1].split(" ")[1]
                args[1] = re.split("\w+: \w+ meant to say: ", args[1])[-1]
            if not re.findall("<\w+>", args[0]):
                continue
            if re.match(r'^s(\W).*\1.*\1.*', args[1], re.I):
                continue
            break
        output = split_up[2] + split_up[2].join(list(args[1])) + split_up[2]
    else:
        args = None
        for line in lines:
            args = line.split('\t')
            if len(args) <= 1:
                args = None
                continue
            matched_speaker = args[0].split('<')[1][:-1]
            if matched_speaker == hc.get_info('nick') and re.match("\w+: \w+ meant to say: .*$", args[1]):
                matched_speaker = re.findall("\w+: \w+ meant to say: ", args[1])[-1].split(" ")[1]
                args[1] = re.split("\w+: \w+ meant to say: ", args[1])[-1]
            if not re.findall("<\w+>", args[0]):
                args = None
                continue
            if re.match(r'^s(\W).*\1.*\1.*', args[1], re.I):
                args = None
                continue
            if re.findall(split_up[1], args[1], flags = flags):
                break
            args = None
        if args is None:
            hc.command("say {}: Regex not found in logs".format(speaker_nick))
            return
        first_match = args[1]
        output = popen('echo "{}" | sed -r "{}"'.format(first_match, msg_eol[0])).read()[:-1]
    output = re.sub('[{}]'.format(''.join([str(unichr(x)) for x in xrange(32)])),'',output)
    if len(output) > 200:
        hc.command("say {}: Output too long.".format(speaker_nick))
    else:
        hc.command("say {}: {} meant to say: {}".format(speaker_nick, matched_speaker, output))

def on_dongers(msg, msg_eol, userdata):
    if len(msg) > 1:
        if re.match(msg[1], "dance", re.I):
            content = msg_eol[2].upper()
            hc.command("say ♫ ┌༼ຈل͜ຈ༽┘ ♪ {} ♪ └༼ຈل͜ຈ༽┐♫ ".format(content))
        else:
            content = msg_eol[1].upper()
            hc.command("say ヽ༼ຈل͜ຈ༽ﾉ {} ヽ༼ຈل͜ຈ༽ﾉ".format(content))

def on_dingdong(msg, msg_eol, userdata):
    hc.command("say ♫ ┌༼ຈل͜ຈ༽┘ ♪ DING DONG DONGERS ♪ └༼ຈل͜ຈ༽┐♫ ")

def on_vowels(msg, msg_eol, userdata):
    hc.command("say ♫ ┌༼ຈل͜ຈ༽┘ ♪ O E A E A U I E O E A ♪ └༼ຈل͜ຈ༽┐♫ ")

def resample_doot(userdata):
    if random.random() < 0.01:
        dootabyll = True

while not emotes_succeeded:
    try:
        response = requests.request('GET', 'https://api.twitch.tv/kraken/chat/twitchplayspokemon/emoticons')
        if response.status_code != 200:
            raise requests.HTTPError
        emotelist = [x['regex'] for x in json.loads(response.content)['emoticons'] if '\\' not in x['regex']]
        hc.prnt("Loaded {} emotes".format(len(emotelist)))
        emotes_succeeded = True
    except:
        emotes_tries += 1
        if emotes_tries >= 10:
            hc.prnt("Failed to compile emotes list")
            popen('mv emotes.bak emotes.json').close()
            emotelist = [x['regex'] for x in json.load(open('emotes.json'))['emoticons'] if '\\' not in x['regex']]
            break

try:
    msg_inbox = cPickle.load(open("msg_inbox.pkl"))
except:
    msg_inbox = {}
    cPickle.dump(msg_inbox, open("msg_inbox.pkl", "w+"))

def on_later(msg, msg_eol, userdata):
    if msg[1] == "tell" and len(msg) >= 3:
        on_lt(msg[1:], msg_eol[1:], userdata)

def interpret_charcode(code):
    if "x" in code.group():
        I = int(code.group()[3:-1], 16)
    elif ";" in code.group():
        I = int(code.group()[2:-1], 10)
    else:
        I = int(code.group()[2:], 10)
    if (I < 0x20) or ((0x80 <= I) and (I < 0xa0)):
        return ""
    else:
        return unichr(I)

def parse_charcodes(string):
    return re.sub("&#(x[0-9a-f]+;|[0-9]+;?)", interpret_charcode, string)

def on_lt(msg, msg_eol, userdata):
    if len(msg) <= 2: return
    recipient = msg[1].lower()
    network, channel, speaker_nick = userdata
    if re.match(recipient, speaker_nick, re.I):
        hc.command("say ...")
    elif recipient in [x.nick.lower() for x in hc.get_list('users')]:
        hc.command("say Tell that person directly.")
    else:
        if (network, channel, recipient) in msg_inbox:
            msg_inbox[(network, channel, recipient)].append(speaker_nick + ": " + msg_eol[2])
        else:
            msg_inbox[(network, channel, recipient)] = [speaker_nick + ": " + msg_eol[2]]
        hc.command("say Message stored for {}. {} messages in queue.".format(recipient, len(msg_inbox[(network, channel, recipient)])))
    cPickle.dump(msg_inbox, open("msg_inbox.pkl", "w+"))

def pop_message(network, channel, username):
    username = username.lower()
    if (network, channel, username) in msg_inbox:
        hc.prnt(msg_inbox[(network, channel, username)])
        if len(msg_inbox[(network, channel, username)]) > 0:
            hc.command("say {}: You have {} messages.".format(username, len(msg_inbox[(network, channel, username)])))
            for x in msg_inbox[(network, channel, username)]:
                hc.command("say " + x)
        msg_inbox.pop((network, channel, username))
    cPickle.dump(msg_inbox, open("msg_inbox.pkl", "w+"))

def on_dongstortion(msg, msg_eol, userdata):
    D = list("ヽ༼ຈل͜ຈ༽ﾉ".decode('utf-8'))
    random.shuffle(D)
    hc.command("say ヽ༼ຈل͜ຈ༽ﾉ Something strange... DONGSTORTION!!! " + "".join(D).encode('utf-8'))

def on_song(msg, msg_eol, userdata):
    if len(msg) == 1:
        hc.command("say I like to raise my Donger I do it all the time ヽ༼ຈل͜ຈ༽ﾉ and every time its lowered┌༼ຈل͜ຈ༽┐ I cry and start to whine ┌༼@ل͜@༽┐But never need to worry ༼ ºل͟º༽ my Donger's staying strong ヽ༼ຈل͜ຈ༽ﾉA Donger saved is a Donger earned so sing the Donger song! ᕦ༼ຈل͜ຈ༽ᕤ")
    elif re.match(msg[1], "trashy", re.I):
        hc.command("say I am very disgusted with the trashy song. In spite of the katamari, and the jew, only trashy, I will outbid them all! For this I must mute myself. The bidder is the same too. Collect all the trashy, righteous mormon are all unpardonable! You don't listen me. The trashy singing is an eyesore.")
    else:
        hc.command("say I like to raise my {0} I do it all the time ヽ༼ຈل͜ຈ༽ﾉ and every time its lowered┌༼ຈل͜ຈ༽┐ I cry and start to whine ┌༼@ل͜@༽┐But never need to worry ༼ ºل͟º༽ my {0}'s staying strong ヽ༼ຈل͜ຈ༽ﾉA {0} saved is a {0} earned so sing the {0} song! ᕦ༼ຈل͜ຈ༽ᕤ".format(msg[1]))

def on_spellrand(msg, msg_eol, userdata):
    try:
        emote = random.choice(emotelist)
        if userdata[0] == "Slack":
            hc.command("say :" + emote.lower() + ": " + (" :" + emote.lower() + ": ").join(list(emote.upper())) + " :" + emote.lower() + ":")
        else:
            hc.command("say " + emote + " " + (" " + emote + " ").join(list(emote.upper())) + " " + emote)
    except NameError:
        hc.command("say Emotes could not be loaded at this time.")

def on_emote(msg, msg_eol, userdata):
    try:
        emote = random.choice(emotelist)
        if userdata[0] == "Slack":
            emote = ":" + emote.lower() + ":"
        hc.command("say " + emote)
    except NameError:
        hc.command("say Emotes could not be loaded at this time.")
        

def on_yolonome(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    move = random.choice(movelist)
    hc.command("say {} used Metronome! Waggling a finger allowed it to use {}!".format(speaker_nick, move))

def on_riot(msg, msg_eol, userdata):
    if len(msg) > 1:
        content = msg_eol[1].upper()
        if "DANCE" in content:
            hc.command("say ♫ ┌༼ຈل͜ຈ༽┘ ♪ {} RIOT ♪ └༼ຈل͜ຈ༽┐♫ ".format(content))
        else:
            hc.command("say ヽ༼ຈل͜ຈ༽ﾉ {} RIOT ヽ༼ຈل͜ຈ༽ﾉ".format(content))
    else:
        hc.command("say ヽ༼ຈل͜ຈ༽ﾉ RIOT ヽ༼ຈل͜ຈ༽ﾉ")

def on_riot_bw(msg, msg_eol, userdata):
    if re.match(msg[-1], "riot", re.I):
        content = msg_eol[0].upper()
        if "DANCE" in content:
            hc.command("say ♫ ┌༼ຈل͜ຈ༽┘ ♪ {} ♪ └༼ຈل͜ຈ༽┐♫ ".format(content))
        else:
            hc.command("say ヽ༼ຈل͜ຈ༽ﾉ {} ヽ༼ຈل͜ຈ༽ﾉ".format(content))

def on_ripchat(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    if channel == "#tppleague":
        hc.command("me uses a Max Revive on the chat.")

def on_fite_bw(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    if channel == "#tppleague":
        hc.command("say FITE FITE FITE")

def on_tpoke(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    if channel == "#tppleague":
        hc.command("me pokes {} with a trout on behalf of {}".format(msg[1], speaker_nick))

def on_highlight(msg, msg_eol, userdata):
    dootabyll = False
    network, channel, speaker_nick = userdata
    filename = logs_dir + "/" + network.lower() + "/" + channel.lower() + ".log"
    hc.command("say " + speaker_nick + ": " + rwmc.rwmc(popen("tail -n5000 " + filename), 40))

def on_wtf(msg, msg_eol, userdata):
    if hc.get_info("channel") == "#tppleague":
        hc.command("say \"wtf\" - Liria_10 since the beginning of time.")

def on_rip(msg, msg_eol, userdata):
    if len(msg) == 1:
        hc.command("say RIP")
    else:
        hc.command("say RIP " + msg_eol[1] + ". Press F to pay your respects.")

def on_concast(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    hc.command("say \"CONCAAAAAAAAAAAAAAAST!!!\" - {} {}".format(speaker_nick, time.localtime().tm_year))

# def on_summon(msg, msg_eol, userdata):
#     if len(msg) > 1:
#         

def on_gbaddr(msg, msg_eol, userdata):
    try:
        if ":" in msg[1]:
            args = msg[1].split(':')
            args[0] = int(args[0], 16)
            args[1] = int(args[1], 16)
            if args[0]:
                if args[0] > 0x7F:
                    hc.command("say Error: Bank exceeds ROM size")
                    return
                if args[1] < 0x4000 or args[1] >= 0x8000:
                    hc.command("say Error: Invalid ROMX address")
                    return
            else:
                if args[1] >= 0x4000:
                    hc.command("say Error: Invalid ROM0 address")
                    return
            hc.command("say {:>6X}".format(args[0] * 0x4000 + (args[1] % 0x4000)))
        else:
            arg = int(msg[1], 16)
            if arg >= 0x200000:
                hc.command("say Error: Address exceeds ROM size")
                return
            bank = arg / 0x4000
            addr = arg % 0x4000
            if bank:
                addr += 0x4000
            hc.command("say {:>2X}:{:04X}".format(bank, addr))
    except:
        hc.command("say An error has occurred.")

hangman = Hangman()
anagram = Anagram()

def on_hangman(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    if len(msg) == 1:
        return hc.command("say Error: Insufficient parameters for !hangman")
    if msg[1] == "start":
        if anagram.active:
            return hc.command("say Error: Cannot run Hangman while Anagram is running")
        if hangman.active:
            return hc.command("say Error: Hangman is already running")
        hangman.start((network, channel))
        hc.command("say Hangman has started!")
        hc.command("say " + " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
    elif hangman.channel != (network, channel):
        hc.command("say Error: Hangman is running, but in " + hangman.channel[0] + ":#" + hangman.channel[1])
    elif msg[1] == "stop":
        if not hangman.active:
            hc.command("say Error: Hangman is not running")
        elif speaker_nick != owner_nick:
            hc.command("say Error: Insufficient permissions")
        else:
            hangman.stop()
            hc.command("say Hangman terminated")
    elif msg[1] == "guess":
        if len(msg) < 3:
            return hc.command("say Error: Insufficient parameters for !hangman")
        if not hangman.active:
            return hc.command("say Error: Hangman is not running")
        outcome = hangman.check_guess(msg[2])
        if outcome == 2:
            hc.command("say " + speaker_nick + " solved the puzzle! Well done, " + speaker_nick + "!")
            hc.command("say The correct answer was: " + hangman.solution)
            hangman.stop()
        elif outcome == 1:
            hc.command("say " + " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
        else:
            if hangman.guesses:
                hc.command("say " + " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
            else:
                hc.command("say You've run out of guesses! The correct answer is: " + hangman.solution)
                hangman.stop()
    elif msg[1] == "show":
        if not hangman.active:
            return hc.command("say Error: Hangman is not running")
        hc.command("say " + " ".join(hangman.prompt) + " | Incorrect: " + ", ".join(hangman.incorrect) + " | Guesses remaining: " + str(hangman.guesses))
    else:
        hc.command("say Error: Method " + msg[1] + " not supported")

def on_anagram(msg, msg_eol, userdata):
    network, channel, speaker_nick = userdata
    if len(msg) == 1:
        hc.command("say Error: Insufficient parameters for !anagram")
        return
    if msg[1] == "start":
        if hangman.active:
            hc.command("say Error: Cannot run Anagram while Hangman is running")
            return
        if anagram.active:
            hc.command("say Error: Anagram is already running")
            return
        anagram.start((network, channel))
        hc.command("say Anagram has started!")
        hc.command("say " + anagram.prompt + " | Incorrect: " + ", ".join(anagram.incorrect) + " | Guesses remaining: " + str(anagram.guesses))
    elif anagram.channel != (network, channel):
        hc.command("say Error: Anagram is running, but in " + anagram.channel[0] + ":#" + anagram.channel[1])
    elif msg[1] == "stop":
        if not anagram.active:
            hc.command("say Error: Anagram is not running")
        elif speaker_nick != owner_nick:
            hc.command("say Error: Insufficient permissions")
        else:
            anagram.stop()
            hc.command("say Anagram terminated")
    elif msg[1] == "solve":
        if len(msg) < 3:
            hc.command("say Error: Insufficient parameters for !anagram")
            return
        if not anagram.active:
            hc.command("say Error: Anagram is not running")
            return
        hc.command("say " + speaker_nick + " has guessed " + msg[2].upper() + ".")
        if anagram.check_guess(msg[2]):
            hc.command("say That's absolutely correct! Well done, " + speaker_nick + "!")
            anagram.stop()
        else:
            hc.command("say Nope, that wasn't it.")
            if anagram.guesses:
                hc.command("say " + anagram.prompt + " | Incorrect: " + ", ".join(anagram.incorrect) + " | Guesses remaining: " + str(anagram.guesses))
            else:
                hc.command("say You've run out of guesses! The correct answer is: " + anagram.solution)
                anagram.stop()
    elif msg[1] == "show":
        if not anagram.active:
            hc.command("say Error: Anagram is not running")
            return
        hc.command("say " + anagram.prompt + " | Incorrect: " + ", ".join(anagram.incorrect) + " | Guesses remaining: " + str(anagram.guesses))
    else:
        hc.command("say Error: Method " + msg[1] + " not supported")

banlists = [
{"freenode": ["#tppleague", "#twitchplayspokemon", "#poketext"], "twitch": ["#twitchplayspokemon", '#_projectrevotpp_1453672491233']},
{"freenode": ["#poketext"], 'twitch': ['#_projectrevotpp_1453672491233']},
{"freenode": ["#tppleague", "#twitchplayspokemon", "#poketext"], "twitch": ["#twitchplayspokemon", "#_killermapper_1417986539782", '#_projectrevotpp_1453672491233']},
{'twitch': ['#_projectrevotpp_1453672491233']}
]

def check_banlist(network, channel, index):
    if network in banlists[index]:
        return channel in banlists[index][network]

command_dict = {
"!riot": (on_riot, 0),
"!spellrand": (on_spellrand, 0),
"!later": (on_later, 0),
"!lt": (on_lt, 0),
"!gbaddr": (on_gbaddr, 1),
"!wtf": (on_wtf, -1),
"!ripchat": (on_ripchat, -1),
"!dongstortion": (on_dongstortion, 1),
"!tpoke": (on_tpoke, -1),
"!rip": (on_rip, 1),
"!song": (on_song, 1),
"!yolonome": (on_yolonome, 0),
"!concast": (on_concast, 1),
"!dongers": (on_dongers, 1),
"!dingdong": (on_dingdong, 1),
"!vowels": (on_vowels, 1),
"!emote": (on_emote, 0),
"!coin": (on_coin, 1),
"!noq20": (on_noq20, -1),
"!blame": (on_blame, 1),
'!klappa': (on_klappa, -1),
'!hangman': (on_hangman, -1),
'!anagram': (on_anagram, -1),
}

buzzword_dict = {
"riot": (on_riot_bw, 0),
# hc.get_info('nick').lower(): (on_highlight, 0),
"fite": (on_fite_bw, -1),
r'^s(\W).*\1.*\1.*': (on_sed, 2)
}

infobot_filter = ["Voting has \w+ for the next input.*$", "Betting closes in .*$"]

def apply_cooldown(network, channel, speaker_mask):
    now = time.time()
    if (network, channel, speaker_mask) in last_donger:
        if (network, channel) in timeouts:
            cooldown = timeouts[(network, channel)]
        else:
            cooldown = default_cooldown
        if (now - last_donger[(network, channel, speaker_mask)]) < cooldown:
            return False
        else:
            last_donger[(network, channel, speaker_mask)] = now
            return True
    else:
        last_donger[(network, channel, speaker_mask)] = now
        return True

def on_privmsg(word, word_eol, userdata):
    server = hc.get_info("server")
    channel = hc.get_info("channel")
    network = hc.get_info("network")
    speaker_mask = word[0][1:]
    speaker_nick = speaker_mask.split('!')[0]
    pop_message(network, channel, speaker_nick.lower())

    # Freenode format is nick!uname@mask PRIVMSG #channel :+message
    # TMI format is nick!uname@twitch.tv PRIVMSG #channel :message

    if network in ["freenode", "slack"]:
        msg = word_eol[3][2:].split(' ')
    else:
        msg = word_eol[3][1:].split(' ')
    if len(msg) == 0:
        return hc.EAT_NONE
    while '' in msg:
        msg.remove('')
        if len(msg) == 0:
            return hc.EAT_NONE
#     msg = [parse_charcodes(x) for x in msg]
    msg_eol = [" ".join(msg[i:]) for i in xrange(len(msg))]
#     if (speaker_nick == "tppinfobot") and (channel == "#twitchplayspokemon") and (network == "twitch"):
#         if not any([re.match(x, msg_eol[0], re.I) for x in infobot_filter]):
#             for L in hc.get_list('channels'):
#                 if re.match(L.channel, '#poketext', re.I):
#                     L.context.command("say TPPInfoBot: " + msg_eol[0])
#     if (speaker_nick == "tppbankbot") and (channel == "#twitchplayspokemon") and (network == "twitch") and re.match("\w+ added \w+ tokens", msg_eol[0], re.I):
#         if not any([re.match(x, msg_eol[0], re.I) for x in infobot_filter]):
#             for L in hc.get_list('channels'):
#                 if re.match(L.channel, '#poketext', re.I):
#                     L.context.command("say TPPBankBot: " + msg_eol[0])
    if speaker_nick.lower() in botlist:
        return hc.EAT_NONE
    buzzes = [re.findall(x, msg_eol[0], re.I) for x in buzzword_dict]

    if network in owner_account:
#         hc.prnt("Checking for owner")
#         hc.prnt(owner_account[network])
#         hc.prnt(speaker_mask)
#         hc.prnt("yes" if re.match(owner_account[network], speaker_mask, re.I) else "no")
        if re.match(owner_account[network], speaker_mask, re.I) and (msg[0] == "exec") and not channel.startswith("#"):
            return hc.command('timer 1 ' + msg_eol[1])
    if msg[0][0] == "!":
        if msg[0].lower() in command_dict:
            if msg[0].lower() in ["!anagram", "!hangman"]:
                command_dict[msg[0].lower()][0](msg, msg_eol, (network, channel, speaker_nick))
            elif not check_banlist(network, channel, command_dict[msg[0].lower()][1]):
                if apply_cooldown(network, channel, speaker_mask):
                    command_dict[msg[0].lower()][0](msg, msg_eol, (network, channel, speaker_nick))
    elif any(buzzes):
        which_buzzword = buzzword_dict.values()[[len(x) > 0 for x in buzzes].index(1)]
        if not check_banlist(network, channel, which_buzzword[1]):
            if apply_cooldown(network, channel, speaker_mask):
                which_buzzword[0](msg, msg_eol, (network, channel, speaker_nick))
    elif (dootabyll or re.findall(hc.get_info('nick'), msg_eol[0], re.I)) and (not check_banlist(network, channel, 2)) and apply_cooldown(network, channel, speaker_mask):
        on_highlight(msg, msg_eol, (network, channel, speaker_nick))
    if network == 'freenode' and channel == '#twitchplayspokemon-secret' and speaker_nick != hc.get_info('nick'):
        L = hc.find_context(channel = '#_projectrevotpp_1453672491233')
        L.command("say " + speaker_nick + ": " + msg_eol[0])
    elif network == 'twitch' and channel == '#_projectrevotpp_1453672491233' and speaker_nick != hc.get_info('nick'):
        L = hc.find_context(channel = '#twitchplayspokemon-secret')
        L.command("say 4" + speaker_nick + ": " + msg_eol[0])
    return hc.EAT_NONE

def on_join(word, word_eol, userdata):
    server = hc.get_info("server")
    channel = hc.get_info("channel")
    network = hc.get_info("network")
    speaker_mask = word[0]
    speaker_nick = speaker_mask.split('!')[0][1:]
    if network in ["freenode","Slack"]:
        if not check_banlist(network, channel, 0):
            if re.match(speaker_nick, hc.get_info("nick"), re.I):
                return
            elif re.match(speaker_mask.split("@")[1], "unaffiliated/pikalaxalt"):
                hc.command("say ༼ つ ◕_◕ ༽つ MASTER ༼ つ ◕_◕ ༽つ")
            elif re.match(speaker_nick, "trainertimmy", re.I):
                hc.command("say Welcome to the Muters' Club, Timmy! OneHand")
            elif re.match(speaker_nick, "pigdevil2010", re.I):
                hc.command("say PIGUUUUUUUUUU SwiftRage")
            elif re.match(speaker_nick, "padz", re.I):
                hc.command("say working gfx.py, lz.py, and crowdmap when, padz? SoonerLater")
            elif re.match(speaker_nick, "chauzu", re.I):
                hc.command("say Also lying no tea Chauzu DansGame")
            elif re.match(speaker_nick, "abyll", re.I):
                hc.command("say Greetabyll")
            elif re.match(speaker_mask.split("@")[1], "unaffiliated/walle303"):
                hc.command("say Walle... TriHard")
            elif re.match(speaker_nick, 'TwitchPlaysPkmn', re.I):
                hc.command("say ༼ つ ◕_◕ ༽つ STREAMER ༼ つ ◕_◕ ༽つ")
            else:
                hc.command("say Welcome, {}!".format(speaker_nick))
    pop_message(network, channel, speaker_nick.lower())
    updateuserlists(None)

def on_nick(word, word_eol, userdata):
    server = hc.get_info("server")
    network = hc.get_info("network")
    speaker_mask = word[0]
    speaker_nick = speaker_mask.split('!')[0][1:]
    speaker_newnick = word[2][1:]
    for channel in hc.get_list('channels'):
        if (channel.network == network) and (channel.type == 2):
            pop_message(network, channel, speaker_newnick.lower())
    updateuserlists(None)

def print_msg_inbox(word, word_eol, userdata):
    for network, channel, recipient in msg_inbox:
        hc.prnt("Messages for " + recipient + " in " + network + "/" + channel + ":")
        for message in msg_inbox[(network, channel, recipient)]:
            hc.prnt(message)
        hc.prnt("")

def updateuserlists(userdata):
    for channel in hc.get_list("channels"):
        if channel.type == 2:
            if channel.network not in userlists:
                userlists[channel.network] = {}
            userlists[channel.network][channel.channel] = channel.context.get_list("users")

def on_quit(word, word_eol, userdata):
    quitter_mask = word[0][1:]
    quitter_nick = quitter_mask.split("!")[0]
    quitter_host = quitter_mask.split("!")[1]
    network = hc.get_info('network')
    for channel in hc.get_list("channels"):
        if channel.network != network: continue
        if channel.network not in ['freenode']: break
        if channel.network not in userlists: break
        if channel.channel not in userlists[channel.network]: continue
        if quitter_nick not in [x.nick for x in userlists[channel.network][channel.channel]]: continue
        if not check_banlist(network, channel.channel, 1): channel.context.command("say RIP " + quitter_nick)
    updateuserlists(None)

def on_part(word, word_eol, userdata):
    parter_nick = word[0][1:].split("!")[0]
    network = hc.get_info('network')
    channel = hc.get_info('channel')
    if (network in ['freenode','Slack']) and (not check_banlist(network, channel, 1)) and (parter_nick != hc.get_info("nick")): hc.command("say RIP " + parter_nick)
    updateuserlists(None)

def on_kick(word, word_eol, userdata):
    victim = word[3]
    network = hc.get_info('network')
    channel = hc.get_info('channel')
    if not check_banlist(network, channel, 1):
        if victim == hc.get_info("nick"):
            hc.command("timer 1 say Why? BibleThump")
        else:
            hc.command("say PogChamp {} got rekt PogChamp".format(victim))
    updateuserlists(None)

def on_whisper(word, word_eol, userdata):
    server = hc.get_info("server")
    channel = hc.get_info("channel")
    network = hc.get_info("network")
    speaker_mask = word[0]
    speaker_nick = speaker_mask.split('!')[0][1:]
    msg = word_eol[3][1:].split(' ')
    if len(msg) == 0:
        return hc.EAT_NONE
    while '' in msg:
        msg.remove('')
        if len(msg) == 0:
            return hc.EAT_NONE
#     msg = [parse_charcodes(x) for x in msg]
    msg_eol = [" ".join(msg[i:]) for i in xrange(len(msg))]
    hc.command("query -nofocus {}".format(speaker_nick))
    L = hc.find_context(server = server, channel = speaker_nick)
    L.prnt("\00302{}\00301\011{}".format(speaker_nick, msg_eol[0]))
    if re.match(owner_account[network], speaker_mask, re.I) and msg[0] == 'exec':
        hc.command('timer 1 ' + msg_eol[1])
    return hc.EAT_ALL

def on_client_msg(word, word_eol, userdata):
    global messaging
    if messaging:
        return
    messaging = True
    if hc.get_info("network") == "twitch" and not hc.get_info("channel").startswith("#"):
        hc.command("privmsg #jtv :/w {} {}".format(hc.get_info("channel"), word_eol[0]))
        hc.command("query -nofocus {} {}".format(hc.get_info("channel"), word_eol[0]))
    messaging = False
    return hc.EAT_NONE

hc.hook_server('QUIT', on_quit)
hc.hook_server('PRIVMSG', on_privmsg)
hc.hook_server('JOIN', on_join)
hc.hook_server('NICK', on_nick)
hc.hook_server('KICK', on_kick)
hc.hook_server('PART', on_part)
hc.hook_server('WHISPER', on_whisper)
hc.hook_command('msg', on_client_msg)
hc.hook_command('print_msg_inbox', print_msg_inbox)
hc.hook_timer(10000, resample_doot)
hc.hook_timer(60000, updateuserlists)
hc.prnt("Main script (local.py) loaded successfully.")
