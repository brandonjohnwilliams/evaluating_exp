from otree.api import Bot, Submission
import random
import time
from . import *

class PlayerBot(Bot):
    def play_round(self):

        yield Risk, {
            'risk': random.randint(1, 7),
        }

        yield Confidence, {
            'confidence': random.randint(1, 7),
        }

        yield Rank, {
            'rank': random.randint(1, 100),
        }

        yield Disappointment, {
            'disappointment': random.randint(1, 7),
        }

        yield Perfection, {
            'perfection': random.randint(1, 7),
        }

