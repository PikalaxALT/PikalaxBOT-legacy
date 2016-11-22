import numpy as np
import re

_balance_req = "you have P(?P<pokeyen>\d+) pokeyen T(?P<tokens>\d+) tokens"
balance_req = re.compile(_balance_req)

class PBRBot(object):
    def __init__(self, connection):
        self.connection = connection
        self.reset()

    def reset(self):
        self.balance = Bank(0, 0)
        self.bet = 0
        self.match_running = False
        self.move = '-'
        self.team = None

    def update_balance(self, *args):
        self.balance = Bank(int(args[0]), int(args[1]))

    def place_bet(self):
        if self.balance.pokeyen == 0:
            return
        self.bet = max(np.random.binomial(self.balance.pokeyen, 0.1), MIN_BET)
        self.team = np.random.choice(['red','blue'])
        whisper(self.connection, "tpp", "{} P{}".format(self.team, self.bet))
        print("Bet {} on {}".format(self.bet, self.team))

    def do_battle(self):
        if self.match_running:
            self.move = np.random.choice(MOVES)
            whisper(self.connection, "tpp", self.move)
            delay = np.random.randint(5, 20)
            print("Command: " + self.move)
            Timer(delay, self.do_battle).start()

    def start_battle(self):
        if self.team and self.bet:
            self.match_running = True
            self.do_battle()

