from otree.api import Bot
from . import *
# from __init__.py import matrices, color_1_list_1, color_2_list_1, color_1_list_2, color_2_list_2
# import __init__.py
from random import randint

#defining bots for testing
class PlayerBot(Bot):

    def play_round(self):
        # if self.round_number == 1:
            # yield Instructions

        #giving the bot_1 a hierarchy to follow (choosing the higher number) and bot_2 choses randomly
        if self.player.id_in_group == 1 :
            left_stimuli = matrices[self.round_number-1][color_1_list_1[self.round_number-1]]
            right_stimuli = matrices[self.round_number-1][color_2_list_1[self.round_number-1]]
            if left_stimuli > right_stimuli:
                choice = 1
            else:
                choice = 2
        else:
            choice = randint(1,2)

        yield Make_Choice, dict(response = choice, answered_time = 500)
        yield Submission(Show_Choice, check_html = False)
        if self.player.payoff == 10:
            yield Results_Correct
        else:
            yield Submission(Red_Flash, check_html = False)
            yield Results_Wrong
        if self.round_number == Constants.num_rounds/3 or self.round_number == 2*Constants.num_rounds/3:
            yield Break
        if self.round_number == Constants.num_rounds:
            yield Final_Results
            yield Questions, dict(Q = "foo")
            
