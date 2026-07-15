from os import environ

SESSION_CONFIGS = [
    dict(
        # first and second order beliefs are elicited in evaluating profiles
        name='first_and_second',
        display_name="First and Second Order",

        # app sequence defines the order in which to display parts of the exp
        # 1. First order (with instructions and introduction)
        # 2. Second order (with instructions)
        # 3. Open-ended response on parts 1 and 2 reasoning
        # 4. Survey questions about  psychological attitudes
        # 5. Demographics, which also includes the payment app
        app_sequence=[
            'first_order',
            'second_order_seq',
            'reasoning',
            'attitudes',
            'demographics'
        ],
        # anything here can be changed when setting up the session, these are defaults
        starting_group='0',  # this determines which group to assign first, continuing from previous session if needed
        num_demo_participants=20,
        use_browser_bots=False,
        test=False,
        pay_correct=1,

        # 'profile_1' is always the better performer in real evaluation
        real_pair_correct_answer='profile_1',
    ),
    dict(
        # this app automatically launches a link in multiple tabs
        # this is useful for generating data using bots, which require browsers to run
        name='opener',
        display_name="opener",
        app_sequence=[
            'opener',
        ],
        num_demo_participants=1,
    ),
]

# unused
SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

# these are defined at the participant level
PARTICIPANT_FIELDS = [

    # This sets the group that a participant will stick with for the duration of exp
    # Set in Part 1, read in both parts
    'subgroup_id',

    # Part 1 sequence data (prefixed to avoid collision)
    'p1_shared_sequence',
    'p1_json_group',
    'p1_pair_sequence',
    'p1_profile_order_sequence',

    # tallying
    'first_order_player_set'

    # Part 2 sequence data
    'p2_shared_sequence',
    'p2_json_group',
    'p2_pair_sequence',
    'p2_profile_order_sequence',
    'p2_target_group',

    # Set in Part 2 creating_session, read in Evaluation
    'target_subgroup_id',
    'p1_target_results',

    # Running payment total accumulated in Part 2
    'p2_correct',

    # Pay for Part 1
    'p1_real_pair_correct',
    'p1_real_pair_chosen_name',

    # Comprehension checks
    'comprehension_q1_order',
    'comprehension_q2_order',
    'comprehension1pay',
    'comprehension2pay',
]

SESSION_FIELDS = [
    # Written by Part 1 TallyWaitPage, read by Part 2 creating_session
    'p1_group_results',
    'p1_sequences',
    'group_rotation',
    'json_group_to_sg',
    'real_pair_assignment',

    # Which group did we end on
    'last_group_assigned'

]

# default for oTree or unused
LANGUAGE_CODE = 'en'
DEMO_PAGE_INTRO_HTML = """ """

# do not use currency conversion
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = False

ROOMS = [
    dict(
        name='room',
        display_name='Room',
    )
]

# backend login and debugging
AUTH_LEVEL = environ.get('OTREE_AUTH_LEVEL')
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')
DEBUG = (environ.get('OTREE_PRODUCTION') in {None, '', '0'})
SECRET_KEY = '3896147596707'
