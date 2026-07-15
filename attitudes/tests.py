from otree.api import Bot, Submission
import random
import time
from . import *

class PlayerBot(Bot):
    def play_round(self):


        # 5) Submit
        yield Risk, {
            'risk': 7,
        }

        yield Confidence, {
            'confidence': 7,
        }

        yield Rank, {
            'rank': 100,
        }

        yield Disappointment, {
            'disappointment': 7,
        }

        yield Perfection, {
            'perfection': 7,
        }

