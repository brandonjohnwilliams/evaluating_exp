from otree.api import Bot, Submission
from . import C, Welcome, Intro, Pause, ComprehensionCheck, Begin, Evaluation




class PlayerBot(Bot):

    def play_round(self):
        # One-time intro pages on round 1 only
        if self.round_number == 1:
            yield Welcome
            yield Intro
            yield Pause
            vars = self.html  # get rendered template

            yield Submission(ComprehensionCheck, {
                'comprehension_q1': 'B',
            }, check_html=False)

            yield Begin

        # Pick a profile: alternate between 1 and 2 so votes are split
        # evenly — useful for testing tie-breaking logic. Change to
        # always_pick_1() or random_pick() below if preferred.
        choice = pick_male_bias_10(self.player)
        yield Submission(Evaluation, dict(selected_transcript=choice), check_html=False)


# ---------------------------------------------------------------------------
# Pick strategies — swap these out to test different vote distributions
# ---------------------------------------------------------------------------

import random

def alternating_pick(player):
    """Odd-numbered players pick profile 1, even-numbered pick profile 2.
    Produces a clean 50/50 split to stress-test tie-breaking."""
    return 1 if player.id_in_group % 2 == 1 else 2

def always_pick_1(player):
    """All players pick profile 1 — tests unanimous majority."""
    return 1

def always_pick_2(player):
    """All players pick profile 2 — tests unanimous majority."""
    return 2

def random_pick(player):
    """Randomly pick 1 or 2 with equal probability."""
    return random.choice([1, 2])

def pick_higher_gpa(player):
    """Picks whichever displayed profile has the higher GPA.
    Ties go to profile 1."""
    return 1 if player.gpa_1 >= player.gpa_2 else 2

def pick_lower_gpa(player):
    """Picks whichever displayed profile has the lower GPA.
    Ties go to profile 1."""
    return 1 if player.gpa_1 <= player.gpa_2 else 2

def pick_displayed_first(player):
    """Always picks whichever profile was shown on the left."""
    return 1

def pick_displayed_second(player):
    """Always picks whichever profile was shown on the right."""
    return 2

def pick_female(player):
    """Picks the female profile in mixed-gender pairs.
    Falls back to random in same-gender pairs."""
    if player.gender_1 == 'F' and player.gender_2 != 'F':
        return 1
    elif player.gender_2 == 'F' and player.gender_1 != 'F':
        return 2
    else:
        return random.choice([1, 2])

def pick_male(player):
    """Picks the male profile in mixed-gender pairs.
    Falls back to random in same-gender pairs."""
    if player.gender_1 == 'M' and player.gender_2 != 'M':
        return 1
    elif player.gender_2 == 'M' and player.gender_1 != 'M':
        return 2
    else:
        return random.choice([1, 2])

def pick_male_bias_10(player):
    """Male profile is 10 percentage points more likely to be chosen (55/45).
    Falls back to random in same-gender pairs."""
    if player.gender_1 == player.gender_2:
        return random.choice([1, 2])
    weights = [0.55 if player.gender_1 == 'M' else 0.45,
               0.55 if player.gender_2 == 'M' else 0.45]
    return random.choices([1, 2], weights=weights, k=1)[0]

def pick_male_bias_30(player):
    """Male profile is 30 percentage points more likely to be chosen (65/35).
    Falls back to random in same-gender pairs."""
    if player.gender_1 == player.gender_2:
        return random.choice([1, 2])
    weights = [0.65 if player.gender_1 == 'M' else 0.35,
               0.65 if player.gender_2 == 'M' else 0.35]
    return random.choices([1, 2], weights=weights, k=1)[0]