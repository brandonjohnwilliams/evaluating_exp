from otree.api import Bot, Submission
import random
import time
from . import *

class PlayerBot(Bot):
    def play_round(self):

        yield Submission(Survey, dict(
            age=random.randint(18, 25),
            gender=random.choice([0, 1]),
            race_raw=random.choice(['White', 'Black', 'Asian', 'Hispanic', 'Other']),
            english=random.choice([0, 3]),
            year=random.randint(1, 4),
            major=random.randint(0, 9),
            secondmajor=random.choice([10]*7 + list(range(0, 9))),
            gpa=round(random.uniform(2.5, 4.0), 2),
        ), check_html=False)

        yield Pay
        yield Submission(Conclusion, check_html=False)
