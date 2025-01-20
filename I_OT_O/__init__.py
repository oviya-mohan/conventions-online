from otree.api import *
from random import randint
import numpy as np


doc = """
CCL
"""

################################################################################
#CONSTANTS
#define constants used throught this app
#change num_rounds to the required number of rounds - must be a multiple of 21
class Constants(BaseConstants):
    name_in_url = 'I_OT_O'
    players_per_group = 2
    num_rounds = 294
    # for test runthroughs
    # num_rounds = 21

################################################################################
#CREATING SESSIONS
class Subsession(BaseSubsession):
    pass

#creating_session function creates a matrix of stimuli to be used in
#all rounds from colors defined in colors
def creating_session(subsession: Subsession):
    session = subsession.session
    #all 21 possible combinations of the 7 colors
    combinations = [[1, 2], [1, 3], [1, 4], [1, 5], [1, 6], [1, 7], [2, 3],
    [2, 4], [2, 5], [2, 6], [2, 7], [3, 4], [3, 5], [3, 6], [3, 7], [4, 5],
    [4, 6], [4, 7], [5, 6], [5, 7], [6, 7]]

    #creates a matrix of matrices with randomized order of the above
    #combinations for all rounds in the session (defined by num_rounds)
    #each set of 21 rounds has all possible combinations
    global matrices
    matrices = []
    for i in range(0, int(Constants.num_rounds/21)):
        np.random.shuffle(combinations)
        for j in range(0, len(combinations)):
            matrices.append(combinations[j])

    #for participant 1 - randomizing postion of two colored stimuli
    global color_1_list_1, color_2_list_1
    color_1_list_1, color_2_list_1 =[], []
    for i in range(0, Constants.num_rounds):
        color_1 = randint(0,1)
        if color_1 == 0:
            color_2 = 1
        else:
            color_2 = 0
        color_1_list_1.append(color_1)
        color_2_list_1.append(color_2)

    #for participant 2 - randomizing postion of two colored stimuli
    global color_1_list_2, color_2_list_2
    color_1_list_2, color_2_list_2 =[], []
    for i in range(0, Constants.num_rounds):
        color_1 = randint(0,1)
        if color_1 == 0:
            color_2 = 1
        else:
            color_2 = 0
        color_1_list_2.append(color_1)
        color_2_list_2.append(color_2)

################################################################################
#DEFINING GROUPS AND PLAYERS
class Group(BaseGroup):
    pass

#all inputs recieved from the participant throught the app is
#define here under class Player
class Player(BasePlayer):
############################ ONLY FOR FIRST APP ################################
    name = models.StringField(label = "Name: ")
    age = models.IntegerField(label = "Age: ")
    sex = models.StringField(label = "Sex: ")
    email = models.StringField(label = "Email: ")
################################################################################
    response = models.IntegerField()
    answered_time = models.IntegerField()
    Q = models.StringField(
        label = "What strategy did you use to maximize your reward in this session?"
    )

################################################################################
#FUNCTIONS

#set payoffs calculates the players' payoff at the end of each round
def set_payoffs(group):
    p1 = group.get_player_by_id(1)
    p2 = group.get_player_by_id(2)

    #for when colors are presented in the same orientation for both players
    #set payoff to 10 when both reposnses are the same
    if color_1_list_1[p1.round_number-1] == color_1_list_2[p2.round_number-1]:
        if p1.response == p2.response:
            p1.payoff = 10
            p2.payoff = 10
        else:
            p1.payoff = 0
            p2.payoff = 0
    #for when colors are NOT presented in the same orientation for both players
    #set payoff to 10 when both reposnses are NOT the same
    else:
        if p1.response == p2.response:
            p1.payoff = 0
            p2.payoff = 0
        else:
            p1.payoff = 10
            p2.payoff = 10

################################################################################
#PAGES
############################ ONLY FOR FIRST APP ################################
#Info - first page to be displayed for the session - get players' name
class Info(Page):
    form_model='player'
    form_fields = ['name', 'age', 'sex', 'email']

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1
################################################################################

#Instructions - displsyed at the beggining of the app
class Instructions(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

#Make_Choice - participants are presented with the two stimuli
#they can make the choice by clicking on either one of the stimuli
#response and reaction time are recorded via HTML and JS in Make_Choice.html
class Make_Choice(Page):

    form_model = 'player'
    form_fields = ['response', 'answered_time']

    #sent to the HTML page Make_Choice.html to display appropriate stimuli
    #(stimuli_1 appears on the left and simutli_2 on the right)
    #position randomization of color is taken care of in creating_session
    @staticmethod
    def vars_for_template(player):
        if player.id_in_group == 1:
            return dict(
                stimuli_1 = 'images/{}.png'.format(matrices[player.round_number-1]
                [color_1_list_1[player.round_number-1]]),
                stimuli_2 = 'images/{}.png'.format(matrices[player.round_number-1]
                [color_2_list_1[player.round_number-1]]))
        else:
            return dict(
                stimuli_1 = 'images/{}.png'.format(matrices[player.round_number-1]
                [color_1_list_2[player.round_number-1]]),
                stimuli_2 = 'images/{}.png'.format(matrices[player.round_number-1]
                [color_2_list_2[player.round_number-1]]))


#Show_Choice - to highlight the chosen stimuli
#Chosen stimuli blinks a few time while the other stimuli disappears
class Show_Choice(Page):
    #change to adjust how long the blinking stimuli stay on the screen
    timeout_seconds = 0.8

    #sending to the HTML page Show_Choice.html to display chosen stimuli
    #black.png is used to "cover" the stimuli that was not chosen
    @staticmethod
    def vars_for_template(player):
        if player.id_in_group == 1:
            if player.response == 1:
                return dict(
                    stimuli_1 = 'images/{}.png'.format(matrices[player.round_number-1]
                    [color_1_list_1[player.round_number-1]]),
                    stimuli_2 = 'images/black.png')
            else:
                return dict(
                    stimuli_1 = 'images/black.png',
                    stimuli_2 = 'images/{}.png'.format(matrices[player.round_number-1]
                    [color_2_list_1[player.round_number-1]]))
        else:
            if player.response == 1:
                return dict(
                    stimuli_1 = 'images/{}.png'.format(matrices[player.round_number-1]
                    [color_1_list_2[player.round_number-1]]),
                    stimuli_2 = 'images/black.png')
            else:
                return dict(
                    stimuli_1 = 'images/black.png',
                    stimuli_2 = 'images/{}.png'.format(matrices[player.round_number-1]
                    [color_2_list_2[player.round_number-1]]))

#Results_Correct - page to display reward when both players choose the same
#stimuli - reward in presented in green text
class Results_Correct(Page):
     @staticmethod
     def is_displayed(player):
         return player.payoff == 10

#Red_Flash - screen flashes red when players do NOT choose the same color
class Red_Flash(Page):
    #duration of red flash
     timeout_seconds = 0.3

     @staticmethod
     def is_displayed(player):
         return player.payoff == 0

#Results_Wrong - page to display reward when both players do NOT choose the same
#stimuli - reward in presented in red text
class Results_Wrong(Page):
     @staticmethod
     def is_displayed(player):
         return player.payoff == 0

class WaitForPlayer(WaitPage):
    pass

#calculates payoff via set_payoff function once both
#players have made thier choice
class ResultsWaitPage(WaitPage):
    after_all_players_arrive = set_payoffs

#break page that only gets executed on certain round numbers
#can be decided based on how the total number of rounds are to be divided
#currently, breaks at one-third and two-thirds of the total numer of rounds
class Break(Page):
    @staticmethod
    def is_displayed(player):
        return (player.round_number == Constants.num_rounds/3 or
        player.round_number == 2*Constants.num_rounds/3)

#displayed only when all rounds are completed with
#final payoff calculations for the app
class Final_Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == Constants.num_rounds

#page with questions - defined in Constants
class Questions(Page):
    form_model = 'player'
    form_fields = ['Q']
    @staticmethod
    def is_displayed(player):
        return player.round_number == Constants.num_rounds

#Final page of app - use "Advance Slowest Users" after this to move to next app
class Thanks(Page):
    @staticmethod
    def is_displayed(player):
############################ ONLY FOR FIRST APP ################################
        #store total payoff for this app into a participant_field called
        #first_total defined in settings.py to access from second app
        sum = player.participant.payoff
        player.participant.first_total = sum
################################################################################
        return player.round_number == Constants.num_rounds

################################################################################
#defining sequences of pages to be presented in the app
page_sequence = [Info, Instructions, WaitForPlayer, Make_Choice, Show_Choice,
WaitForPlayer, ResultsWaitPage, Results_Correct, Red_Flash, Results_Wrong,
Break, Thanks]

#for quick testing purposes ONLY - omits initial pages
# page_sequence = [WaitForPlayer, Make_Choice, Show_Choice, WaitForPlayer,
# ResultsWaitPage, Results_Correct, Red_Flash, Results_Wrong, Break,
# Final_Results, Questions, Thanks]

################################################################################
#custom_export function to save customised data from each round in an csv file
#one csv file per app - download from DATA tab after completion of session
#Download, save and RESET DB, either from terimnal or Heroku Bash,
#before running AGAIN - THIS IS A MUST OR SESSION DATA WILL OVERWRITE!!
def custom_export(players):
    #header row #1
    #NAME IS ONLY FOR FIRST APP
    yield['participant_number', 'participant_code', 'age', 'sex', 'name', 'email']
    for p in players:
        answer = p.Q
        name = p.name
        age = p.age
        sex = p.sex
        email = p.email
        #write only for first (name) and last (answer) round
        if p.round_number == 1 or p.round_number == Constants.num_rounds:
            yield[p.id_in_group, p.participant.code, age, sex, name, email]

    # header row #2
    yield ['session', 'participant_code', 'round_number', 'participant_number',
    'left_stimuli', 'right_stimuli', 'response' , 'loser', 'answered_time',
    'payoff_round', 'total_payoff']

    for p in players:
        participant = p.participant
        session = p.session
        if p.id_in_group == 1 :
            left_stimuli = (matrices[p.round_number-1]
            [color_1_list_1[p.round_number-1]])
            right_stimuli = (matrices[p.round_number-1]
            [color_2_list_1[p.round_number-1]])
        else:
            left_stimuli = (matrices[p.round_number-1]
            [color_1_list_2[p.round_number-1]])
            right_stimuli = (matrices[p.round_number-1]
            [color_2_list_2[p.round_number-1]])
        if p.response == 1:
            response = left_stimuli
            loser = right_stimuli
        else:
            response = right_stimuli
            loser = left_stimuli
        yield [session.code, participant.code, p.round_number, p.id_in_group,
        left_stimuli, right_stimuli, response, loser, p.answered_time, p.payoff,
        participant.first_total]
