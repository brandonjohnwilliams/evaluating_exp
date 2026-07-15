from otree.api import *

# need for loading randomization
import json

# used for randomizing the order of display
import random

doc = """
First-order evaluation: participants pick who they think will perform better
on an economics quiz. Results are tallied per subgroup and stored in
session.vars for Part 2 (second_order) to consume.
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class C(BaseConstants):
    NAME_IN_URL = 'first_order'

    # flexible groups, same as Part 2
    PLAYERS_PER_GROUP = None

    # 24 synthetic pairs + 1 real pair
    NUM_ROUNDS = 25


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):

    # this is the main choice we care about, saves as 1 or 2
    selected_transcript = models.IntegerField(blank=True)

    # derived from the main choice (populated in before_next_page)
    chosen_gender = models.StringField()
    chosen_name = models.StringField()
    chosen_gpa = models.FloatField()
    choice_type = models.StringField()  # real or synthetic
    chosen_display_position = models.StringField()  # was the chosen profile displayed first or second
    chosen_profile_index = models.StringField()  # was it profile_1 or profile_2 from JSON

    # identifies which grade pair from the original list we are evaluating
    pair_id = models.IntegerField()

    # Group metadata
    json_group = models.IntegerField()

    # Profile 1 fields (as displayed – may be profile_1 or profile_2 from JSON)
    name_1 = models.StringField()
    gender_1 = models.StringField()
    gpa_1 = models.FloatField()
    grade_1_1 = models.StringField()
    grade_1_2 = models.StringField()
    grade_1_3 = models.StringField()
    grade_1_4 = models.StringField()

    # Profile 2 fields (as displayed – may be profile_1 or profile_2 from JSON)
    name_2 = models.StringField()
    gender_2 = models.StringField()
    gpa_2 = models.FloatField()
    grade_2_1 = models.StringField()
    grade_2_2 = models.StringField()
    grade_2_3 = models.StringField()
    grade_2_4 = models.StringField()

    # Store if it was displayed as in the original pairs or reverse
    displayed_order = models.StringField()

    # whether the player correctly identified the better real performer (pair 25)
    # null for all except one real pair pairs
    real_pair_correct = models.BooleanField(initial=None)

    # Comprehension check variable
    comprehension_q1 = models.StringField(
        label="1. What are you asked to do in Evaluation Task 1?",
        choices=[
            ['A', 'A. Choose the student with the highest GPA'],
            ['B', 'B. Guess which student got the larger number of correct answers on a multiple-choice economics quiz'],
            ['C', 'C. Identify which student is real'],
            ['D', 'D. Rank the students from best to worst'],
            ['E', 'E. Select the student with the most math classes'],
        ],
        widget=widgets.RadioSelect,
        blank=False,
    )
    comprehension_q1_attempts = models.IntegerField(initial=1)


# ---------------------------------------------------------------------------
# Functions and Helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Helper: create and assign groups
# ---------------------------------------------------------------------------

def get_group_sizes(n):
    # Returns a list of group sizes for a given number of participants, based on the fixed session-size table
    sub_group = {
        15: [3, 3, 4, 5],
        16: [3, 3, 5, 5],
        17: [3, 4, 5, 5],
        18: [3, 3, 3, 3, 3, 3],
        19: [3, 3, 3, 3, 3, 4],
        20: [3, 3, 3, 3, 3, 5],
        21: [3, 3, 3, 3, 4, 5],
        22: [3, 3, 3, 3, 5, 5],
        23: [3, 3, 3, 4, 5, 5],
        24: [3, 3, 3, 3, 3, 3, 3, 3],
        25: [3, 3, 3, 3, 3, 3, 3, 4],
        26: [3, 3, 3, 3, 3, 3, 3, 5],
    }

    if n not in sub_group:
        raise ValueError(
            f"No group configuration defined for {n} participants."
        )

    return sub_group[n]


def make_subgroup_matrix(players):
    random.shuffle(players)

    # should be value between 3 and 5
    sizes = get_group_sizes(len(players))

    # create the player matrix
    matrix, start = [], 0

    # loop through all groups and assign players, then return for saving
    for size in sizes:
        matrix.append(players[start:start + size])
        start += size
    return matrix


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
        # Correct answer read from session config (set to 'profile_1' always)
        correct_answer = player.session.config.get('real_pair_correct_answer')
        player.real_pair_correct = (player.chosen_profile_index == correct_answer)

        # Store on participant.vars so Part 2 feedback page can display it
        player.participant.vars['p1_real_pair_correct'] = player.real_pair_correct
        player.participant.vars['p1_real_pair_chosen_name'] = player.chosen_name

    else:
        player.choice_type = "synthetic pair"


# ---------------------------------------------------------------------------
# Helper: tally Part 1 results into session.vars for Part 2 to read
#
# Structure written to session.vars['p1_group_results']:
#
# The 'majority_choice' is the canonical JSON key ('profile_1' or 'profile_2'),
# NOT the displayed position (1 or 2), so Part 2 can look up profile attributes
# independently of display order.
#
# Ties are broken randomly so every pair always has a declared majority.
# ---------------------------------------------------------------------------

def tally_p1_results(subsession):
    # initialize the vote count
    votes = {}

    for subsession in subsession.in_all_rounds():
        for p in subsession.get_players():

            # pull the group and pair_id to determine vote location
            sg = p.participant.vars.get('p1_json_group')
            pid = p.pair_id

            # look at the player choice
            chosen_canon = p.chosen_profile_index

            # initialize if the subgroup hasn't been encountered yet
            if sg not in votes:
                votes[sg] = {}

            # initialize if the subgroup-pair_id hasn't been encountered yet
            if pid not in votes[sg]:
                votes[sg][pid] = {'profile_1': 0, 'profile_2': 0, '_ref': p}

            # add to the correct vote
            votes[sg][pid][chosen_canon] += 1
            votes[sg][pid]['_ref'] = p

    # initialize and then count the votes to save the winners
    results = {}

    for sg, pairs in votes.items():
        results[sg] = {}
        for pid, counts in pairs.items():

            # store the counts and note if tied
            v1, v2 = counts['profile_1'], counts['profile_2']

            # check for winner or ties
            if v1 > v2:
                majority_canon = 'profile_1'
            elif v2 > v1:
                majority_canon = 'profile_2'
            else:
                majority_canon = 'tie'

            # store the results as a dict
            results[sg][pid] = dict(
                majority_choice=majority_canon,
                votes_profile_1=v1,
                votes_profile_2=v2,
            )

    # save the results to session variables
    subsession.session.vars['p1_group_results'] = results


# ---------------------------------------------------------------------------
# Session setup
# ---------------------------------------------------------------------------

def creating_session(subsession):
    # Groups are fixed in round 1, then preserved
    if subsession.round_number == 1:
        players = subsession.get_players()
        matrix = make_subgroup_matrix(players)
        subsession.set_group_matrix(matrix)
        # debug
        print("Group matrix assignments: ", subsession.session.num_participants , " players assigned to ", len(subsession.get_groups()),
              " groups with structure ", subsession.get_groups(),)

        # check which group to start with (this must be entered manually)
        starting_group = int(subsession.session.config.get('starting_group'))

        # save for reference for the next session (-1 for JSON index)
        last_group = starting_group + len(subsession.get_groups()) - 1
        subsession.session.vars['last_group_assigned'] = last_group

    else:
        subsession.group_like_round(1)

    # Load JSON from the predetermined JSON
    with open('group_assignment.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for group in subsession.get_groups():
        starting_group = int(subsession.session.config.get('starting_group'))

        # group index is the group number in session (min 1 max 8) - 1 (to match JSON index) + previous groups
        # so e.g. group 3 in session 2 (where session 1 had 6 group) is indexed to 3 - 1 + 6 = 8
        group_idx = int(group.id_in_subsession) - 1 + starting_group

        # debug
        print("Group assigned: ", group_idx)

        #
        shared_sequence = data[str(group_idx)]

        for player in group.get_players():
            if subsession.round_number == 1:
                player.participant.vars['p1_shared_sequence'] = shared_sequence
                player.participant.vars['p1_json_group'] = group_idx
                player.participant.vars['subgroup_id'] = group.id_in_subsession

                # Participant-specific randomised order of comparisons
                order = list(range(len(shared_sequence)))
                random.shuffle(order)
                player.participant.vars['p1_pair_sequence'] = order

                # Participant-specific display order within each pair
                profile_order_sequence = [
                    ('profile_1', 'profile_2') if random.choice([True, False])
                    else ('profile_2', 'profile_1')
                    for _ in order
                ]
                player.participant.vars['p1_profile_order_sequence'] = profile_order_sequence

            sequence = player.participant.vars['p1_shared_sequence']
            pair_index = player.participant.vars['p1_pair_sequence'][player.round_number - 1]
            pair = sequence[pair_index]
            first_key, second_key = player.participant.vars['p1_profile_order_sequence'][player.round_number - 1]

            first_profile = pair[first_key]
            second_profile = pair[second_key]

            player.json_group = player.participant.vars['p1_json_group']
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


# Write session-level lookup tables for Part 2 on round 1 only.
    # These are built after the player loop so all groups are processed.
    if subsession.round_number == 1:
        # Part 2 uses this to show each participant the exact pairs their target group evaluated in Part 1

        for group in subsession.get_groups():
            # own group index is calculated as before
            starting_group = int(subsession.session.config.get('starting_group'))
            group_idx = int(group.id_in_subsession) - 1 + starting_group

            # your target group is one behind you (group 2 sees 1, 3 sees 2, and group 1 sees the last)
            if group_idx == starting_group:
                target_group = starting_group + len(subsession.get_groups()) - 1
                target_sequence = data[str(target_group)]

                for player in group.get_players():
                    player.participant.vars['p2_shared_sequence'] = target_sequence
                    player.participant.vars['p2_json_group'] = group_idx
                    player.participant.vars['p2_target_group'] = target_group

                    # print("Group ", group_idx, " assigned to target group: ", target_group,
                    #       " with structure: ", player.participant.vars['p2_shared_sequence'])

            else:
                target_group = group_idx - 1
                target_sequence = data[str(target_group)]

                for player in group.get_players():
                    player.participant.vars['p2_shared_sequence'] = target_sequence
                    player.participant.vars['p2_json_group'] = group_idx
                    player.participant.vars['p2_target_group'] = target_group

                    # print("Group ", group_idx, " assigned to target group: ", target_group,
                    #       " with structure: ", player.participant.vars['p2_shared_sequence'])

# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

class Welcome(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class MyWaitPage(WaitPage):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1 and not player.session.config.get('test')


class Intro(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player):
        return dict(test=1 if player.session.config.get('test') else 0)


class Pause(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player):
        return dict(test=1 if player.session.config.get('test') else 0)


class ComprehensionCheck(Page):
    form_model = 'player'
    form_fields = ['comprehension_q1']

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    def vars_for_template(player):
        choices1 = [
            ['A', 'Choose the student with the highest GPA'],
            ['B', 'Guess which student got the larger number of correct answers on a multiple-choice economics quiz'],
            ['C', 'Identify which student is real'],
            ['D', 'Rank the students from best to worst'],
            ['E', 'Select the student with the most math classes'],
        ]
        # Shuffle once and persist the order
        if 'comprehension_q1_order' not in player.participant.vars:
            random.shuffle(choices1)
            player.participant.vars['comprehension_q1_order'] = choices1
        else:
            choices1 = player.participant.vars['comprehension_q1_order']

        selected1 = player.field_maybe_none('comprehension_q1')
        return dict(
            choices1=choices1,
            selected1=selected1,
        )

    def error_message(player, values):
        errors = False
        q1_attempts = 0
        if values['comprehension_q1'] != 'B':
            q1_attempts += 1
            player.comprehension_q1_attempts = q1_attempts
            errors = True
        if errors:
            return 'Your answer is incorrect, please try again.'

    def before_next_page(player, timeout_happened):
        if player.comprehension_q1_attempts < 2:
            player.participant.comprehension1pay = 1
        else:
            player.participant.comprehension1pay = 0



class Begin(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class Evaluation(Page):
    form_model = 'player'
    form_fields = ['selected_transcript']
    timeout_seconds = 120

    @staticmethod
    def error_message(player, values):
        if values.get('selected_transcript') is None:
            return 'Please select one of the options before submitting.'

    @staticmethod
    def vars_for_template(player):
        indifference = 1 if player.session.config.get('indifference') else 0
        return dict(
            indifference=indifference,
            name1=player.name_1,         name2=player.name_2,
            gpa1=player.gpa_1,           gpa2=player.gpa_2,
            gpa1grade1=player.grade_1_1, gpa1grade2=player.grade_1_2,
            gpa1grade3=player.grade_1_3, gpa1grade4=player.grade_1_4,
            gpa2grade1=player.grade_2_1, gpa2grade2=player.grade_2_2,
            gpa2grade3=player.grade_2_3, gpa2grade4=player.grade_2_4,
        )

    @staticmethod
    def js_vars(player):
        return dict(test=1 if player.session.config.get('test') else 0)

    @staticmethod
    def before_next_page(player, timeout_happened):
        set_chosen_vars(player)


class TallyWaitPage(WaitPage):

    # After the final round of Part 1, aggregate votes across ALL groups and
    # write the results into session.vars so Part 2 can consume them

    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player):
        # don't display unless we reach the last round (and not in test mode)
        return player.round_number == C.NUM_ROUNDS and not player.session.config.get('test')

    @staticmethod
    def after_all_players_arrive(subsession):
        tally_p1_results(subsession)


page_sequence = [
    Welcome,
    MyWaitPage,
    Intro,
    Pause,
    ComprehensionCheck,
    Begin,
    Evaluation,
    TallyWaitPage
]
