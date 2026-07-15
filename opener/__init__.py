from otree.api import *
import json
import random



doc = """
Resumes
"""


class C(BaseConstants):
    NAME_IN_URL = 'symmetricGPA'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


# FUNCTIONS

# PAGES
class Introduction(Page):
   pass



page_sequence = [Introduction]
