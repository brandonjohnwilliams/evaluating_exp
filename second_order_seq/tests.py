from otree.api import Bot, Submission
from . import C, Evaluation, Welcome, Instructions, Begin, ComprehensionCheck
import random


def pick_randomly(player, pair, first_key, second_key):
    """Picks profile_1 or profile_2 with equal probability."""
    return random.choice([1, 2])

def pick_higher_gpa(player, pair, first_key, second_key):
    """Always picks whichever profile has the higher GPA.
    Ties broken randomly."""
    gpa1 = pair['profile_1']['gpa']
    gpa2 = pair['profile_2']['gpa']
    if gpa1 > gpa2:
        return 1
    elif gpa2 > gpa1:
        return 2
    else:
        return random.choice([1, 2])

def pick_lower_gpa(player, pair, first_key, second_key):
    """Always picks whichever profile has the lower GPA.
    Ties broken randomly."""
    gpa1 = pair['profile_1']['gpa']
    gpa2 = pair['profile_2']['gpa']
    if gpa1 < gpa2:
        return 1
    elif gpa2 < gpa1:
        return 2
    else:
        return random.choice([1, 2])

def pick_displayed_first(player, pair, first_key, second_key):
    """Always picks whichever profile was shown on the left (displayed first).
    Returns the canonical profile number (1 or 2) of that profile."""
    return 1 if first_key == 'profile_1' else 2

def pick_displayed_second(player, pair, first_key, second_key):
    """Always picks whichever profile was shown on the right (displayed second)."""
    return 1 if second_key == 'profile_1' else 2

def pick_female(player, pair, first_key, second_key):
    """Picks the female profile if one exists, otherwise picks randomly.
    If both are female, picks randomly."""
    g1 = pair['profile_1']['gender']
    g2 = pair['profile_2']['gender']
    if g1 == 'F' and g2 != 'F':
        return 1
    elif g2 == 'F' and g1 != 'F':
        return 2
    else:
        return random.choice([1, 2])

def pick_male(player, pair, first_key, second_key):
    """Picks the male profile if one exists, otherwise picks randomly.
    If both are male, picks randomly."""
    g1 = pair['profile_1']['gender']
    g2 = pair['profile_2']['gender']
    if g1 == 'M' and g2 != 'M':
        return 1
    elif g2 == 'M' and g1 != 'M':
        return 2
    else:
        return random.choice([1, 2])

def pick_male_bias_10(player):
    """Male profile is 10% more likely to be chosen than female.
    In mixed-gender pairs: male chosen with 55% probability, female with 45%.
    In same-gender pairs: picks randomly."""
    g1 = player.gender_1
    g2 = player.gender_2
    if g1 == g2:
        return random.choice([1, 2])
    weights = [0.55 if g1 == 'M' else 0.45,
               0.55 if g2 == 'M' else 0.45]
    return random.choices([1, 2], weights=weights, k=1)[0]


def pick_male_bias_30(player):
    """Male profile is 30% more likely to be chosen than female.
    In mixed-gender pairs: male chosen with 65% probability, female with 35%.
    In same-gender pairs: picks randomly."""
    g1 = player.gender_1
    g2 = player.gender_2
    if g1 == g2:
        return random.choice([1, 2])
    weights = [0.65 if g1 == 'M' else 0.35,
               0.65 if g2 == 'M' else 0.35]
    return random.choices([1, 2], weights=weights, k=1)[0]

class PlayerBot(Bot):
    def play_round(self):
        if self.player.round_number == 1:
            yield Submission(Welcome, check_html=False)
            yield Submission(Instructions, check_html=False)
            yield Submission(ComprehensionCheck, {'comprehension_q1': 'C'}, check_html=False)
            yield Submission(Begin, check_html=False)

        choice = pick_male_bias_10(self.player)

        yield Submission(Evaluation, dict(selected_transcript=choice), check_html=False)
