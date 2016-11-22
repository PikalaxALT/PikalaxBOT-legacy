from .discord import discord, client
from .irc import twitch, freenode
import sys, asyncio, traceback, time, logging
from websockets.exceptions import ConnectionClosed
from multiprocessing import Process, active_children, ProcessError
from irc.bot import ServerSpec, SingleServerIRCBot

logging.basicConfig(format = '%(levelname)s %(asctime)s: %(message)s',
                    filename = 'pikalaxbot_irc_client.log',
                    datefmt = '%Y/%m/%d %H:%M:%S',
                    level = logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())
logger = logging.getLogger("PikalaxBOT")

with open('/home/pi/.oauth/discord') as F:
    token = F.read().rstrip()
    print('Loaded DISCORD token')

# Set up Twitch bot
with open("/home/pi/.oauth/twitch") as Token:
    servers = [ServerSpec("irc.chat.twitch.tv", password = Token.read().rstrip())]
    Twitch = SingleServerIRCBot(servers, "pikalaxbot", "pikalaxbot")
    print('Loaded TWITCH token')
Twitch.connection.add_global_handler("whisper", twitch.on_whisper)
Twitch.connection.add_global_handler("pubmsg", twitch.on_pubmsg)
Twitch.connection.add_global_handler("action", twitch.on_pubmsg)
Twitch.connection.add_global_handler("ctcp", twitch.on_ctcp)
Twitch.connection.add_global_handler("endofmotd", twitch.on_endofmotd)
Twitch.connection.logs_dir = "/home/pi/irclogs/twitch/"
Twitch.connection._error = False
# Set up Freenode bot
with open("/home/pi/.oauth/freenode") as Token:
    servers = [ServerSpec("chat.freenode.net", password = Token.read().rstrip())]
    Freenode = SingleServerIRCBot(servers, "PikalaxBOT", "PikalaxBOT")
    print('Loaded FREENODE token')
Freenode.connection.add_global_handler("privmsg", freenode.on_privmsg)
Freenode.connection.add_global_handler("pubmsg", freenode.on_pubmsg)
Freenode.connection.add_global_handler("action", freenode.on_pubmsg)
Freenode.connection.add_global_handler("ctcp", freenode.on_ctcp)
Freenode.connection.add_global_handler("endofmotd", freenode.on_endofmotd)
Freenode.connection.add_global_handler("part", freenode.on_part)
Freenode.connection.add_global_handler("quit", freenode.on_quit)
Freenode.connection.logs_dir = "/home/pi/irclogs/freenode/"
Freenode.connection._error = False

# Let each bot interact with the other's connection
Twitch.connection.partner = Freenode.connection
Freenode.connection.partner = Twitch.connection

# Start the bots
processes = []
processes.append(Process(target = Twitch.start, name = 'Twitch'))
processes.append(Process(target = Freenode.start, name = 'Freenode'))

for process in processes:
    process.start()
    print('Started process ' + process.name)

asyncio.ensure_future(discord.client.run(token))

while sum([process.is_alive() for process in processes]) == 2:
    time.sleep(60)

for process in processes:
    if process.is_alive():
        process.terminate()
    else:
        print('Process ' + process.name + ' crashed!!')
raise ProcessError
