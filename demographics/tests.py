from otree.api import Bot, Submission
import random
import time
from . import *

class PlayerBot(Bot):
    def play_round(self):

        yield Submission(Survey, dict(
            age=20,
            gender=0,
            race_raw='White',
            english=0,
            year=1,
            major=3,
            secondmajor=10,
            gpa=3.5,
        ), check_html=False)

        yield Pay
        yield Submission(Conclusion, check_html=False)
