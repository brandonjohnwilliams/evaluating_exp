from otree.api import *
import json
import random
import csv, os


doc = """
open questions
"""


class C(BaseConstants):

    NAME_IN_URL = 'reasoning'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    # responses
    reasoning1 = models.LongStringField(label="")
    reasoning2 = models.LongStringField(label="")


# FUNCTIONS

# PAGES
class Introduction(Page):
    pass

class Response1(Page):
    form_model = 'player'
    form_fields = ['reasoning1']

class Response2(Page):
    form_model = 'player'
    form_fields = ['reasoning2']


page_sequence = [Introduction, Response1, Response2]