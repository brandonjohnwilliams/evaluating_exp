from otree.api import *
import random


doc = """
Demographics
"""


class C(BaseConstants):
    NAME_IN_URL = 'demographics'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    single = 0

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    # survey variables

    age = models.IntegerField(label='What is your age?', min=18, max=100)

    gender = models.IntegerField(
        choices=[[0, 'Male'], [1, 'Female'], [2, 'Non-binary / third gender'], [3, 'Prefer not to say']],
        label='Please select your gender',
        widget=widgets.RadioSelectHorizontal,

    )
    race_raw = models.LongStringField(blank=True)
    race = models.LongStringField(blank=True)

    english = models.IntegerField(
        choices=[[0, 'All of my life'], [1, 'More than ten years'], [2, 'More than five years'], [3, 'More than two years'], [4, 'Less than two years'], [5, 'Prefer not to say']],
        label='How many years have you lived in the U.S.?',
        widget=widgets.RadioSelect,
    )
    year = models.IntegerField(
        choices=[[0, 'Freshman'], [1, 'Sophomore'], [2, 'Junior'], [3, 'Senior'], [4, 'Graduate Student'], [5, 'Other']],
        label='What is your year in school?',
        widget=widgets.RadioSelect,
    )
    major = models.IntegerField(
        choices=[[0, 'Accounting / Finance'], [1, 'Bio / Chem'], [2, 'Business / Marketing'], [3, 'Economics'],
                 [4, 'Humanities'], [5, 'Nursing'], [6, 'Other STEM'], [7, 'Psychology'], [8, 'Social Sciences'],
                 [9, 'Other']],
        label='What is your major?',
    )

    secondmajor = models.IntegerField(
        choices=[[0, 'Accounting / Finance'], [1, 'Bio / Chem'], [2, 'Business / Marketing'], [3, 'Economics'],
                 [4, 'Humanities'], [5, 'Nursing'], [6, 'Other STEM'], [7, 'Psychology'], [8, 'Social Sciences'],
                 [9, 'Other'], [10, 'None']],
        label='What is your second major? (You may select none.)',
        blank=True,
        initial=None,
    )

    gpa = models.FloatField(
        label='What is your approximate GPA?',
        min=0, max=4
    )

    totalPay = models.IntegerField()
    Eval1Pay = models.IntegerField(initial = 0)
    Eval2Pay = models.IntegerField(initial = 0)
    ComprehensionPay = models.IntegerField(initial = 0)
    playerID = models.IntegerField()


def creating_session(subsession):
    pass

# PAGES
class Survey(Page):
    form_model = 'player'
    form_fields = ['race_raw', 'gender', 'age', 'gpa', 'year', 'english', 'major', 'secondmajor']

    def before_next_page(player, timeout_happened):
        test = 1 if player.session.config.get("test") else 0
        if test == 1:
            player.Eval1Pay = int(player.participant.vars.get('p1_real_pair_correct',0))*10
            player.Eval2Pay = 18
            player.ComprehensionPay = (
                    int(player.participant.vars.get('comprehension1pay', 0)) +
                    int(player.participant.vars.get('comprehension2pay', 0))
            )
            player.totalPay = int(player.Eval1Pay) + int(player.Eval2Pay) + int(player.ComprehensionPay) + 12
        else:
            player.Eval1Pay = int(player.participant.vars.get('p1_real_pair_correct', 0)) * 10
            player.Eval2Pay = int(player.participant.vars.get('p2_correct', 0))
            player.ComprehensionPay = (
                    int(player.participant.vars.get('comprehension1pay', 0)) +
                    int(player.participant.vars.get('comprehension2pay', 0))
            )
            player.totalPay = int(player.Eval1Pay) + int(player.Eval2Pay) + int(player.ComprehensionPay) + 12
        player.playerID = random.randint(1,100000)
        player.race = player.race_raw or ""

class Pay(Page):
    @staticmethod
    def vars_for_template(player):
        pay = player.totalPay
        return dict(
            pay=pay,
            Eval1Pay=player.Eval1Pay,
            Eval2Pay=player.Eval2Pay,
            ComprehensionPay=player.ComprehensionPay,
            id=player.playerID,
        )

class Conclusion(Page):
    @staticmethod
    def vars_for_template(player):
        return dict(
            id=player.playerID
        )

page_sequence = [Survey, Pay, Conclusion]
