from otree.api import *


doc = """
Consent form prior to pairing in I_OT_O
"""


class Constants(BaseConstants):
    name_in_url = 'consent'
    players_per_group = None
    num_rounds = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


class Consent(Page):
    pass


page_sequence = [Consent]
