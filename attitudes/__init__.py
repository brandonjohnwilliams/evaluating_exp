from otree.api import *
import json
import random
import csv, os


doc = """
attitudes
"""


class C(BaseConstants):

    NAME_IN_URL = 'attitudes'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    # responses
    risk = models.IntegerField(label="", widget=widgets.RadioSelect, choices=[1,2,3,4,5,6,7])
    confidence = models.IntegerField(label="", widget=widgets.RadioSelect, choices=[1, 2, 3, 4, 5, 6, 7])
    rank = models.IntegerField(min=0, max=100, initial=0)
    disappointment = models.IntegerField(label="", widget=widgets.RadioSelect, choices=[1, 2, 3, 4, 5, 6, 7])
    perfection = models.IntegerField(label="", widget=widgets.RadioSelect, choices=[1, 2, 3, 4, 5, 6, 7])



# FUNCTIONS

# PAGES

# class Intro(Page):
#     pass

class Risk(Page):
    form_model = 'player'
    form_fields = ['risk']

class Confidence(Page):
    form_model = 'player'
    form_fields = ['confidence']

class Rank(Page):
    form_model = 'player'
    form_fields = ['rank']

class Disappointment(Page):
    form_model = 'player'
    form_fields = ['disappointment']

class Perfection(Page):
    form_model = 'player'
    form_fields = ['perfection']

page_sequence = [Risk, Confidence, Rank, Disappointment, Perfection]