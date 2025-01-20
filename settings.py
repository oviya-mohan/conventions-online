from os import environ

SESSION_CONFIGS = [
    dict(
        name='I_OT',
        display_name = "Collective Cognition Lab",
        app_sequence=['I_OT_O', 'I_OT_T'],
        num_demo_participants=2,
        # use_browser_bots = True,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

#defining first_total to pass total payoff in first app to second
#mostly for display purposes for players
PARTICIPANT_FIELDS = ['first_total']
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

POINTS_CUSTOM_NAME = " "

SECRET_KEY = '7610452390128'
