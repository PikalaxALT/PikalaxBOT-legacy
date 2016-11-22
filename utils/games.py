import numpy as np

monlist = tuple(open("/home/pi/data/pkmnlist.txt").read().split('\n')) # Make it immutable

class Hangman(object):
    def __init__(self):
        self.monlist = monlist
        self.stop()

    def stop(self):
        self.active = False
        self.solution = None
        self.prompt = None
        self.guesses = -1
        self.incorrect = []
        self.channel = None

    def start(self, channel):
        self.solution = np.random.choice(self.monlist)
        self.prompt = ["-" for char in self.solution]
        self.guesses = 8
        self.active = True
        self.channel = channel

    def check_guess(self, guess):
        guess = guess.upper()
        if (len(guess) == 1) and (guess in self.solution):
            if guess in self.prompt:
                return 0
            for i, x in enumerate(self.solution):
                if x == guess:
                    self.prompt[i] = x
            if "".join(self.prompt) == self.solution:
                return 2
            return 1
        elif self.solution == guess:
            return 2
        else:
            if guess not in self.incorrect:
                self.incorrect.append(guess)
                self.guesses -= 1
            return 0

class Anagram(object):
    def __init__(self):
        self.monlist = monlist
        self.stop()

    def stop(self):
        self.active = False
        self.solution = None
        self.prompt = None
        self.guesses = -1
        self.incorrect = []
        self.channel = None

    def start(self, channel):
        self.solution = np.random.choice(self.monlist)
        self.prompt = self.solution
        while self.prompt == self.solution:
            L = list(self.solution)
            np.random.shuffle(L)
            self.prompt = "".join(L)
        self.guesses = 3
        self.active = True
        self.channel = channel

    def check_guess(self, guess):
        if self.solution == guess.upper():
            return True
        else:
            self.incorrect.append(guess.upper())
            self.guesses -= 1
            return False
