import numpy as np
import re, subprocess, os, time, sys
from threading import Timer
from multiprocessing import Array, Value
import ctypes

PUNCTUATION = (".", "?", "!")
PUNCTUATION_PROBS = (0.7, 0.25, 0.05)
default_re = re.compile("$")
bag_lines = Array(ctypes.c_char_p, 500)
num_baglines = Value(ctypes.c_ushort, 0)

class RWMC(dict):
    def __init__(self, filename = None, timeout = 216000,
                 emote_regex = default_re, min_len = 50000,
                 commands_regex = default_re):
        self.timeout = timeout
        self.filename = filename
        self.emote_regex = emote_regex
        self.commands_regex = commands_regex
        self.min_len = min_len
        if timeout is not None:
            assert timeout >= 0
        if filename:
            assert os.path.exists(filename)
            logs = subprocess.Popen(["tail", "-n", "5000", filename], \
                stdout = subprocess.PIPE)
            for line in logs.stdout.readlines():
                if b"\t" not in line:
                    continue
                clean_line = line.decode().split("\t")[1]
                self.train_line(clean_line)
        if self.timeout:
            T = Timer(self.timeout, self.check_line_expire)
            T.start()

    def __len__(self):
        return sum([len(x) for x in self.values()])

    def train_line(self, line):
        # remove Kappa and friends
        clean_line = self.emote_regex.sub("", line).strip()
        # collapse spaces
        clean_line = re.sub(" {2,}", " ", clean_line)
        # don't process an empty line
        if len(clean_line) == 0:
            return
        # don't process a TPP command
        if clean_line.startswith("!") or self.commands_regex.match(clean_line):
            return
        # append random punctuation if needed
        if clean_line[-1] not in PUNCTUATION:
            clean_line += np.random.choice(PUNCTUATION, p = PUNCTUATION_PROBS)
        # process the line into the dictionary of triples
        words = ["", ""] + clean_line.split() + ["", ""]
        # words will expire over time if timeout is nonzero
        now = time.time()
        for i in range(len(words) - 2):
            cur_key = (words[i], words[i + 1])
            if cur_key in self:
                self[cur_key].append((words[i + 2], now))
            else:
                self[cur_key] = [(words[i + 2], now)]

    def check_line_expire(self):
        if len(self.keys()) > 0 and len(self) > self.min_len:
            for key, value in self.items():
                self[key] = [x for x in value if x[1] + self.timeout < now]
        T = Timer(min(self.timeout, 3600), self.check_line_expire)
        T.start()

    def build_chain(self, min_len = 200, max_len = 400):
        # Sentence start and end state is two empty strings
        construction = ["", ""]
        cur_key = ("", "")
        chain = ""
        # unit test
        assert len(self) > 0, "Nothing to build"
        assert cur_key in self, "Unable to start chain"
        # Iterate until you have a long-enough sentence.
        while True:
            cur_vals = self.get(cur_key)
            if cur_vals: # Continue the current sentence.
                # np.random.choice errors on a list of tuples
                idx = np.random.choice(len(cur_vals))
                construction.append(cur_vals[idx][0])
            else: # Reseed the current sentence.
                construction = ["", ""]
                if cur_vals is not None:
                    self.pop(cur_key)
            cur_key = (construction[-2], construction[-1])
            if cur_key == ("", "") and len(construction) > 2:
                sentence = " ".join(construction).strip()
                # print(sentence)
                if len(chain + " " + sentence) <= max_len:
                    chain += " " + sentence
                    chain = chain.strip()
                if len(chain) > min_len:
                    return chain
                construction = ["", ""]

def build_nebby():
    if np.random.rand() < .01:
        return '\x01ACTION gets in the bag\x01'
    phrase = 'Ppew!'
    markov = np.array([[0.00, 0.00, 1.00, 0.00, 0.00, 0.00],
                       [0.00, 0.10, 0.90, 0.00, 0.00, 0.00],
                       [0.00, 0.05, 0.80, 0.15, 0.00, 0.00],
                       [0.00, 0.00, 0.01, 0.10, 0.89, 0.00],
                       [0.00, 0.00, 0.00, 0.00, 0.20, 0.80]], dtype = float)
    output = ''
    idx = 0
    while idx < len(phrase):
        output += phrase[idx]
        idx = np.random.choice(len(phrase) + 1, p = markov[idx])
    return output

def sample_bag():
    load_bag()
    with num_baglines, bag_lines:
        cur_bag_idx = np.random.randint(num_baglines.value)
        bag_action = bag_lines[cur_bag_idx].decode()
    return bag_action

def add_bag(bag_line):
    if len(bag_line) > 100:
        sys.stdout.write('message too long\n')
        return False
    sys.stdout.write('passed size check\n')
    if re.search(r'(https?://)?(\w+?\.)?\w+?\.\w+?(/\S+)?', bag_line):
        sys.stdout.write('message has a url\n')
        return False
    sys.stdout.write('not a url\n')
    with num_baglines, bag_lines:
        if num_baglines.value >= 500:
            sys.stdout.write('bag is full\n')
            return False
        if bag_line in bag_lines:
            sys.stdout.write('line already exists\n')
            return False
        try:
            bag_lines[num_baglines.value] = bag_line.encode()
            num_baglines.value += 1
            sys.stdout.write('added line to bag\n')
        except:
            sys.stdout.write('unknown error\n')
            return False
    try:
        save_bag()
        sys.stdout.write('saved bag\n')
    except:
        with num_baglines, bag_lines:
            sys.stdout.write('failed to save bag, reverting action\n')
            num_baglines.value -= 1
            bag_lines[num_baglines.value] = None
            return False
    return True

def save_bag():
    with num_baglines, bag_lines:
        with open('data/nebby.txt', 'w') as O:
            for idx in range(num_baglines.value):
                O.write(baglines[idx])
                O.write('\n')

def load_bag():
    with num_baglines, bag_lines:
        if num_baglines.value == 0:
            with open('data/nebby.txt', 'r') as nebbyFile:
                for line in nebbyFile.readlines():
                    tmp = line.strip().encode()
                    bag_lines[num_baglines.value] = tmp
                    num_baglines.value += 1

def reset_bag():
    with num_baglines, bag_lines:
        tmp = ['refuses to get in the bag.',
               'stares at the bag mischievously.',
               'happily jumps in the bag.',
               'sniffs at the bag.',
               'pokes at the bag playfully.',
               'runs the other way!',
               'gets distracted by something shiny.']
        bag_lines[:len(tmp)] = tmp
        num_baglines.value = len(tmp)
    save_bag()

try:
    load_bag()
    with num_baglines:
        assert num_baglines.value > 0
except:
    reset_bag()
