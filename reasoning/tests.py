from otree.api import Bot, Submission
import random
import time
from . import *

class PlayerBot(Bot):
    def play_round(self):

        yield Introduction

        # 5) Submit
        yield Response1, {
            'reasoning1': 'test',
        }

        yield Response2, {
            'reasoning2': 'test',
        }

