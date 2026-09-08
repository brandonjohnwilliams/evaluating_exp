from otree.api import *
import random

doc = """
Second-order evaluation: participants predict which profile the other group
most often chose in Part 1. Groups rotate according to the group_rotation
list stored in session.vars by Part 1. 
"""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class C(BaseConstants):
    NAME_IN_URL = 'second_order_seq'
    PLAYERS_PER_GROUP = None   # flexible groups
    NUM_ROUNDS = 25            # mirrors Part 1: 24 synthetic pairs + 1 real pair


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    # Core choice
    selected_transcript = models.IntegerField()

    # Derived from choice (populated in before_next_page)
    chosen_gender = models.StringField()
    chosen_name = models.StringField()
    chosen_gpa = models.FloatField()
    choice_type = models.StringField()  # real or synthetic
    chosen_display_position = models.StringField()  # was the chosen profile displayed first or second
    chosen_profile_index = models.StringField()  # was it profile_1 or profile_2 from JSON

    # identifies which grade pair from the original list we are evaluating
    pair_id = models.IntegerField()

    # Group metadata
    json_group = models.StringField()

    # shows which group we are evaluating from part 1, this is fixed according to the rotational structure
    target_group = models.StringField()

    # Whether this player's prediction matched the majority
    prediction_correct = models.BooleanField()

    # Displayed profiles
    name_1 = models.StringField()
    gender_1 = models.StringField()
    gpa_1 = models.FloatField()

    name_2 = models.StringField()
    gender_2 = models.StringField()
    gpa_2 = models.FloatField()

    grade_1_1 = models.StringField()
    grade_1_2 = models.StringField()
    grade_1_3 = models.StringField()
    grade_1_4 = models.StringField()

    grade_2_1 = models.StringField()
    grade_2_2 = models.StringField()
    grade_2_3 = models.StringField()
    grade_2_4 = models.StringField()

    # Store if it was displayed as in the original pairs or reverse
    displayed_order = models.StringField()

    # Comprehension check variable
    comprehension_q1 = models.StringField(
        label="1. What are you asked to do in Evaluation Task 2?",
        choices=[
            ['A', 'Identify which student profile is real'],
            ['B', 'Pick the lowest performing student'],
            ['C', 'Guess which student was selected by most other participants as getting the larger number of correct '
                  'answers on a multiple-choice economics quiz'],
            ['D', 'Guess which student got the larger number of correct answers on a multiple-choice economics quiz'],
        ],
        widget=widgets.RadioSelect,
        blank=False,
    )
    comprehension_q1_attempts = models.IntegerField(initial=1)

# ---------------------------------------------------------------------------
# Helper: populate chosen_* fields after a choice is submitted
# ---------------------------------------------------------------------------

def set_chosen_vars(player):
    # store the profile information on the chosen profile
    # player chose the left hand side option
    if player.selected_transcript == 1:
        player.chosen_gender = player.gender_1
        player.chosen_name = player.name_1
        player.chosen_gpa = player.gpa_1

        # note that this was first position
        player.chosen_display_position = "first"

        # store this as the location in the original JSON (for most pairs, left is min-blemish choice)
        if player.displayed_order == "profile_1,profile_2":
            player.chosen_profile_index = "profile_1"
        elif player.displayed_order == "profile_2,profile_1":
            player.chosen_profile_index = "profile_2"
        else:
            print("Unable to parse display order")

    # player chose the right hand side option
    elif player.selected_transcript == 2:
        player.chosen_gender = player.gender_2
        player.chosen_name = player.name_2
        player.chosen_gpa = player.gpa_2
        player.chosen_display_position = "second"

        # store this as the location in the original JSON (for most pairs, left is excellence choice)
        if player.displayed_order == "profile_1,profile_2":
            player.chosen_profile_index = "profile_2"
        elif player.displayed_order == "profile_2,profile_1":
            player.chosen_profile_index = "profile_1"
        else:
            print("Unable to parse display order")

    # store and evaluate special values for real pair
    if player.pair_id == 25:
        player.choice_type = "real pair"

    else:
        player.choice_type = "synthetic pair"


# ---------------------------------------------------------------------------
# Session setup
# ---------------------------------------------------------------------------

def creating_session(subsession):
    for player in subsession.get_players():
        # pulls from the dict saved in part 1
        shared_sequence = player.participant.vars['p2_shared_sequence']

        # Participant-specific randomised order of comparisons
        if 'p2_pair_sequence' not in player.participant.vars:
            order = list(range(len(shared_sequence)))
            random.shuffle(order)
            player.participant.vars['p2_pair_sequence'] = order

            # Participant-specific display order within each pair
            profile_order_sequence = [
                ('profile_1', 'profile_2') if random.choice([True, False])
                else ('profile_2', 'profile_1')
                for _ in order
            ]
            player.participant.vars['p2_profile_order_sequence'] = profile_order_sequence

        pair_index = player.participant.vars['p2_pair_sequence'][player.round_number - 1]
        pair = shared_sequence[pair_index]
        first_key, second_key = player.participant.vars['p2_profile_order_sequence'][player.round_number - 1]

        first_profile = pair[first_key]
        second_profile = pair[second_key]

        player.json_group = str(player.participant.vars['p1_json_group'])
        player.target_group = str(player.participant.vars['p2_target_group'])

        if player.id_in_subsession == 1 and player.round_number == 1:
            print("For player 1, own group from part 1 is stored as ", player.json_group, " and target group for part 2 is stored as ", player.target_group)

        player.pair_id = pair['pair_id']

        # store all the variables
        player.name_1 = first_profile['name']
        player.gender_1 = first_profile['gender']
        player.gpa_1 = first_profile['gpa']

        player.name_2 = second_profile['name']
        player.gender_2 = second_profile['gender']
        player.gpa_2 = second_profile['gpa']

        player.grade_1_1 = first_profile['grade_1']
        player.grade_1_2 = first_profile['grade_2']
        player.grade_1_3 = first_profile['grade_3']
        player.grade_1_4 = first_profile['grade_4']

        player.grade_2_1 = second_profile['grade_1']
        player.grade_2_2 = second_profile['grade_2']
        player.grade_2_3 = second_profile['grade_3']
        player.grade_2_4 = second_profile['grade_4']

        player.displayed_order = f"{first_key},{second_key}"

# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

class Welcome(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class Instructions(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player):
        return dict(
            pay_correct=player.session.config['pay_correct'],
            test=1 if player.session.config.get('test') else 0,
        )


class ComprehensionCheck(Page):
    form_model = 'player'
    form_fields = ['comprehension_q1']

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    def vars_for_template(player):
        choices1 = [
            ['A', 'Identify which student profile is real'],
            ['B', 'Pick the lowest performing student'],
            ['C', 'Guess which student was selected by most other participants as getting the larger number of correct '
                  'answers on a multiple-choice economics quiz'],
            ['D', 'Guess which student got the larger number of correct answers on a multiple-choice economics quiz'],
        ]

        # Shuffle once and persist the order
        if 'comprehension_q2_order' not in player.participant.vars:
            random.shuffle(choices1)
            player.participant.vars['comprehension_q2_order'] = choices1
        else:
            choices1 = player.participant.vars['comprehension_q2_order']

        selected1 = player.field_maybe_none('comprehension_q1')
        return dict(choices1=choices1,
                    selected1=selected1,
                    )

    def error_message(player, values):
        errors = False
        if values['comprehension_q1'] != 'C':
            player.comprehension_q1_attempts += 1
            errors = True
        if errors:
            return 'Your answer is incorrect, please try again.'

    def before_next_page(player, timeout_happened):
        if player.comprehension_q1_attempts < 2:
            player.participant.comprehension2pay = 1
        else:
            player.participant.comprehension2pay = 0


class Begin(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class Evaluation(Page):
    form_model = 'player'
    form_fields = ['selected_transcript']
    timeout_seconds = 120

    @staticmethod
    def vars_for_template(player):

        return dict(
            name1=player.name_1,
            name2=player.name_2,
            gpa1=player.gpa_1,
            gpa2=player.gpa_2,
            gpa1grade1=player.grade_1_1,
            gpa1grade2=player.grade_1_2,
            gpa1grade3=player.grade_1_3,
            gpa1grade4=player.grade_1_4,
            gpa2grade1=player.grade_2_1,
            gpa2grade2=player.grade_2_2,
            gpa2grade3=player.grade_2_3,
            gpa2grade4=player.grade_2_4,
        )

    @staticmethod
    def js_vars(player):
        return dict(test=1 if player.session.config.get('test') else 0)

    @staticmethod
    def before_next_page(player, timeout_happened):
        if timeout_happened or player.field_maybe_none('selected_transcript') is None:
            return

        subsession = player.subsession
        participant = player.participant

        set_chosen_vars(player)

        # --- lookups from participant.vars (set during part 2 group assignment) ---
        target_group = participant.vars.get('p2_target_group')

        pair_id = player.pair_id

        # --- part 1 results, saved at session level ---
        results = subsession.session.vars.get('p1_group_results', {})

        group_results = results.get(target_group, {})
        pair_result = group_results.get(pair_id)

        if player.session.config.get('test'):
            actual_winner = random.choice(['Profile_1', 'Profile_2'])
        else:
            actual_winner = pair_result['majority_choice']  # 'profile_1', 'profile_2', or 'tie'

        player_guess = player.chosen_profile_index

        # initialize running payoff tally
        if 'p2_correct' not in player.participant.vars:
            player.participant.vars['p2_correct'] = 0

        if actual_winner == 'tie':
            player.prediction_correct = True
        else:
            player.prediction_correct = (player_guess == actual_winner)

        if player.prediction_correct:
            player.participant.vars['p2_correct'] += 1

page_sequence = [
    Welcome,
    Instructions,
    ComprehensionCheck,
    Begin,
    Evaluation,
]