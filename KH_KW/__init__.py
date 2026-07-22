from otree.api import *
from random import randint
import numpy as np
import uuid
import math


doc = """
CCL
"""

################################################################################
#CONSTANTS
#define constants used throught this app
#change num_rounds to the required number of rounds - must be a multiple of 21 for 7 colors, 10 for 5 colors
class Constants(BaseConstants):
    name_in_url = 'KH_KW'
    players_per_group = None  # Crucial: Forces a 1-player game structure
    num_rounds = 294
    
    # --- BOT PARAMETERS ---
    COLORS = [1, 2, 3, 4, 5, 6, 7]
    KW_HIERARCHY = {7: 7, 6: 6, 5: 5, 4: 4, 3: 3, 2: 2, 1: 1}
    K_FACTOR = 100.0

#add waiting page for "Room"
# class RoomWaitPage(Page):
#     pass

#add waiting page where grouping happens
# class GroupWaitPage(WaitPage):
#     template_name = 'KH_KW/GroupWaitPage.html'
#     # group_by_arrival_time = True
    
#     @staticmethod
#     def is_displayed(player):
#         # Only show this page in round 1 for initial grouping
#         return player.round_number == 1
    
#     @staticmethod
#     def after_all_players_arrive(group):
#         # This function is executed after each group is formed
#         pass

################################################################################
#CREATING SESSIONS
class Subsession(BaseSubsession):
    pass

#creating_session function creates a matrix of stimuli to be used in
#all rounds from colors defined in colors
def creating_session(subsession: Subsession):
    import numpy as np
    
    combinations = [[1, 2], [1, 3], [1, 4], [1, 5], [1, 6], [1, 7], [2, 3],
    [2, 4], [2, 5], [2, 6], [2, 7], [3, 4], [3, 5], [3, 6], [3, 7], [4, 5],
    [4, 6], [4, 7], [5, 6], [5, 7], [6, 7]]

    if subsession.round_number == 1:
        for p in subsession.get_players():
            # 1. Initialize Bot Memory
            p.participant.vars['bot_elo'] = {c: 1000.0 for c in Constants.COLORS}
            p.participant.vars['bot_pairs_seen'] = set()
            # p.participant.vars['human_seen'] = set()
            
            # 2. Generate UNIQUE randomized matrices for THIS specific participant
            p_matrices = []
            for i in range(0, int(Constants.num_rounds/21)):
                np.random.shuffle(combinations)
                for j in range(0, len(combinations)):
                    p_matrices.append(combinations[j])
            p.participant.vars['matrices'] = p_matrices
            
            # 3. Generate UNIQUE left/right orientations for THIS participant
            p_color_1_list = []
            p_color_2_list = []
            from random import randint
            for i in range(0, Constants.num_rounds):
                color_1 = randint(0,1)
                color_2 = 1 if color_1 == 0 else 0
                p_color_1_list.append(color_1)
                p_color_2_list.append(color_2)
                
            p.participant.vars['color_1_list'] = p_color_1_list
            p.participant.vars['color_2_list'] = p_color_2_list

################################################################################
#DEFINING GROUPS AND PLAYERS
class Group(BaseGroup):
    pass

#all inputs recieved from the participant throught the app is
#define here under class Player
class Player(BasePlayer):
    age = models.IntegerField(label="Age: ")
    sex = models.StringField(label="Sex: ")
    completion_code = models.StringField()
    
    answered_time = models.IntegerField()
    response = models.IntegerField()
    bot_choice = models.IntegerField() # Added to track the bot's move
    bot_answered_time = models.IntegerField(blank=True, null=True) # added to save random decision-making time for bot
    
    Q = models.LongStringField(
        label="Describe the strategy you used to solve the task. Be as detailed as possible. (max. 50 words, please do not use AI generated responses)"
    )
    Q_1 = models.LongStringField(
        label="How would you explain the best way to solve this task to someone who is about to do it for the first time? (max. 50 words, please do not use AI generated responses)"
    )

    def process_round(self):
        import random
        import math

        # 1. Identify the exact colors shown to the human on this round
        left_color = self.participant.vars['matrices'][self.round_number-1][self.participant.vars['color_1_list'][self.round_number-1]]
        right_color = self.participant.vars['matrices'][self.round_number-1][self.participant.vars['color_2_list'][self.round_number-1]]

        # 2. Map human's button click (1 = Left) to the actual color chosen
        human_color_choice = left_color if self.response == 1 else right_color

        # 3. Load Bot Memory
        strategy = self.session.config.get('bot_strategy', 'KW_MINIMAL')
        bot_elo = self.participant.vars.get('bot_elo', {})
        bot_pairs_seen = self.participant.vars.get('bot_pairs_seen', set())

        # 4. Pair-Based Novelty Check
        # We sort them so (Red, Blue) and (Blue, Red) are recognized as the exact same pair
        current_pair = tuple(sorted([left_color, right_color]))
        bot_novel = current_pair not in bot_pairs_seen

        # 5. Determine Base Bot Choice
        if strategy == 'KW_MINIMAL':
            # KW Bot relies strictly on hardcoded hierarchy
            if Constants.KW_HIERARCHY[left_color] > Constants.KW_HIERARCHY[right_color]:
                base_choice = left_color
            else:
                base_choice = right_color

        elif strategy == 'KH_MINIMAL':
            # KH Bot relies on its dynamic Elo memory
            r_left = bot_elo[left_color]
            r_right = bot_elo[right_color]

            if r_left > r_right:
                base_choice = left_color
            elif r_right > r_left:
                base_choice = right_color
            else:
                base_choice = random.choice([left_color, right_color])

        # 6. Apply Pair-Based Mimicry Override (KH Only)
        if strategy == 'KH_MINIMAL' and bot_novel:
            self.bot_choice = human_color_choice
        else:
            self.bot_choice = base_choice

        # 7. Calculate Coordination Payoff
        if human_color_choice == self.bot_choice:
            self.payoff = 1
        else:
            self.payoff = 0
            
        # bot_rejected = right_color if self.bot_choice == left_color else left_color

        # 8. Update Elo Memory (KH Only)
        if strategy == 'KH_MINIMAL':
            human_rejected = right_color if human_color_choice == left_color else left_color
            r_winner = bot_elo[human_color_choice]
            r_loser = bot_elo[human_rejected]
            #logistic curve, normprob = FALSE in Elo-Ratings for R
            # expected_winner = 1.0 / (1.0 + math.pow(10.0, (r_loser - r_winner) / 400.0))
            # normal CDF, normprob = TRUE/default in Elo-Ratings for R
            expected_winner = (1.0 + math.erf((r_winner - r_loser) / 400.0)) / 2.0
            
            bot_elo[human_color_choice] = r_winner + Constants.K_FACTOR * (1.0 - expected_winner)
            bot_elo[human_rejected] = r_loser - Constants.K_FACTOR * (1.0 - expected_winner)

        # 9. Save State for Next Round
        bot_pairs_seen.add(current_pair)
        self.participant.vars['bot_elo'] = bot_elo
        self.participant.vars['bot_pairs_seen'] = bot_pairs_seen

        # 10. Generate and Save Bot Thinking Time
        max_wait = self.session.config.get('bot_max_wait', 0)
        if max_wait > 0:
            # Generate random seconds and convert to milliseconds
            wait_secs = random.uniform(0.5, max_wait)
            self.bot_answered_time = int(wait_secs * 1000)
        else:
            self.bot_answered_time = 0

################################################################################
#FUNCTIONS

#set payoffs calculates the players' payoff at the end of each round
# def set_payoffs(group):
#     p1 = group.get_player_by_id(1)
#     p2 = group.get_player_by_id(2)

#     #for when colors are presented in the same orientation for both players
#     #set payoff to 10 when both reposnses are the same
#     if color_1_list_1[p1.round_number-1] == color_1_list_2[p2.round_number-1]:
#         if p1.response == p2.response:
#             p1.payoff = 1
#             p2.payoff = 1
#         else:
#             p1.payoff = 0
#             p2.payoff = 0
#     #for when colors are NOT presented in the same orientation for both players
#     #set payoff to 10 when both reposnses are NOT the same
#     else:
#         if p1.response == p2.response:
#             p1.payoff = 0
#             p2.payoff = 0
#         else:
#             p1.payoff = 1
#             p2.payoff = 1

################################################################################
#PAGES
############################ ONLY FOR FIRST APP ################################

def already_participated(label):
    from otree.models import Participant
    return Participant.objects.filter(label=label).exists()

class RepeatParticipant(Page):
    @staticmethod
    def is_displayed(player):
        label = player.participant.label
        return label and already_participated(label)

    @staticmethod
    def vars_for_template(player):
        return dict(worker_id=player.participant.label)

#Info - first page to be displayed for the session - get players' name
class Info(Page):
    form_model='player'
    form_fields = [ 'age', 'sex']
    # form_fields = ['name']
    
    @staticmethod
    def is_displayed(player):
        if player.round_number != 1:
            return False
        label = player.participant.label
        if label and already_participated(label):
            # participant already exists in DB
            return False
        return True
################################################################################

###############################################################################
#Consent form for Prolific

class Consent(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1
    

#Instructions - displsyed at the beggining of the app
class Instructions_with_inst(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1
    
class Instructions_no_inst(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1
    
class Instructions_no_player(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

#Make_Choice - participants are presented with the two stimuli
#they can make the choice by clicking on either one of the stimuli
#response and reaction time are recorded via HTML and JS in Make_Choice.html
class Make_Choice(Page):
    form_model = 'player'
    form_fields = ['response', 'answered_time']

    @staticmethod
    def vars_for_template(player):
        return dict(
            stimuli_1 = 'images/{}.png'.format(player.participant.vars['matrices'][player.round_number-1][player.participant.vars['color_1_list'][player.round_number-1]]),
            stimuli_2 = 'images/{}.png'.format(player.participant.vars['matrices'][player.round_number-1][player.participant.vars['color_2_list'][player.round_number-1]])
        )
            
    @staticmethod
    def before_next_page(player, timeout_happened):
        player.process_round()

class Show_Choice(Page):
    timeout_seconds = 0.8

    @staticmethod
    def vars_for_template(player):
        if player.response == 1:
            return dict(
                stimuli_1 = 'images/{}.png'.format(player.participant.vars['matrices'][player.round_number-1][player.participant.vars['color_1_list'][player.round_number-1]]),
                stimuli_2 = 'images/black.png')
        else:
            return dict(
                stimuli_1 = 'images/black.png',
                stimuli_2 = 'images/{}.png'.format(player.participant.vars['matrices'][player.round_number-1][player.participant.vars['color_2_list'][player.round_number-1]]))
        
class BotThinking(Page):
    @staticmethod
    def is_displayed(player):
        return player.session.config.get('bot_max_wait', 0) > 0
        
    @staticmethod
    def get_timeout_seconds(player):
        # Read the saved milliseconds and convert back to seconds for the timer
        return player.bot_answered_time / 1000.0        
#Results_Correct - page to display reward when both players choose the same
#stimuli - reward in presented in green text
class Results_Correct(Page):
     @staticmethod
     def is_displayed(player):
         return player.payoff == 1
############################ ONLY FOR SECOND APP ###############################
     def vars_for_template(player):
        #Calucuate participant.payoff for second session by subtracting
        #first_total from participant.payoff
        return dict(current_total = player.participant.payoff)
################################################################################

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
############################ ONLY FOR SECOND APP ###############################
     def vars_for_template(player):
       #Calucuate participant.payoff for second session by subtracting
       #first_total from participant.payoff
        return dict( current_total = player.participant.payoff)
################################################################################

# class WaitForPlayer(WaitPage):
#     title_text = "Loading next round... \n Do not switch tabs or leave this page."
#     body_text = " "
#     pass

# class WaitForPlayerResults(WaitPage):
#     title_text = "Processing choice..."
#     body_text = " "
#     pass

#calculates payoff via set_payoff function once both
#players have made thier choice
# class ResultsWaitPage(WaitPage):
#     title_text = "Processing choice..."
#     body_text = " "
#     after_all_players_arrive = set_payoffs

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
############################ ONLY FOR SECOND APP ###############################
    def vars_for_template(player):
      #Calucuate participant.payoff for second session by subtracting
      #first_total from participant.payoff
       return dict(current_total = player.participant.payoff)
################################################################################

#page with questions - defined in Constants
class Questions(Page):
    form_model = 'player'
    form_fields = ['Q']
    @staticmethod
    def is_displayed(player):
        return player.round_number == Constants.num_rounds
    
class Questions_1(Page):
    form_model = 'player'
    form_fields = ['Q_1']
    @staticmethod
    def is_displayed(player):
        return player.round_number == Constants.num_rounds

#Final page of app - use "Advance Slowest Users" after this to move to next app
class Thanks(Page):
    @staticmethod
    def is_displayed(player):
        # Your existing logic to only show this page on the last round
        return player.round_number == Constants.num_rounds

    @staticmethod
    def vars_for_template(player: Player):
        # Use participant.code as the completion code
        return {
            'completion_code': player.participant.code,
        }

################################################################################
#defining sequences of pages to be presented in the app
# with rooms # need to add FinalResults and Questions

########################### For Prolific ########################################
page_sequence = [Consent, Info, Instructions_no_player, Make_Choice, Show_Choice, BotThinking, Results_Correct, Red_Flash, Results_Wrong, Break, Final_Results, Questions, Questions_1, Thanks]

# without room
# page_sequence = [Instructions_with_inst, WaitForPlayer, Make_Choice, Show_Choice, WaitForPlayerResults, ResultsWaitPage, Results_Correct, Red_Flash, Results_Wrong,
# Break, Thanks]

# demo_seq
# page_sequence = [GroupWaitPage, Info, demo_instructions, WaitForPlayer, Make_Choice, Show_Choice, WaitForPlayer, ResultsWaitPage, Results_Correct, Red_Flash, Results_Wrong,Thanks]

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
    # ==========================================
    # HEADER 1: Demographics & Strategy
    # ==========================================
    yield ['participant_number', 'participant_code', 'age', 'sex', 'answer', 'answer_1']
    
    for p in players:
        # 🟢 SAFETY CHECK: Skip players from aborted/empty sessions
        if 'matrices' not in p.participant.vars:
            continue
            
        # Only export the demographic rows once per participant (on round 1)
        if p.round_number == 1 or p.round_number == Constants.num_rounds:
            # Grab the final round's player object to get the survey answers
            # p_last = p.in_all_rounds()[-1]
            
           # Yield Human Demographics (Participant 1)
            # Hardcoded to 1 because id_in_group is always 1 in a single-player config
            yield [1, p.participant.code, p.age, p.sex, p.Q, p.Q_1]
            
            # Yield Bot Demographics (Participant 2)
            bot_code = f"{p.participant.code}_bot"
            yield [2, bot_code, "", "", "", ""]

    # ==========================================
    # HEADER 2: Trial-by-Trial Data
    # ==========================================
    yield ['session', 'participant_code', 'round_number', 'participant_number', 'left_stimuli', 'right_stimuli', 'response', 'loser', 'answered_time', 'payoff_round', 'total_payoff']

    for p in players:
        # 🟢 SAFETY CHECK: Skip players from aborted/empty sessions
        if 'matrices' not in p.participant.vars:
            continue
            
        # 1. Reconstruct the human's screen and choices
        left_stimuli = p.participant.vars['matrices'][p.round_number-1][p.participant.vars['color_1_list'][p.round_number-1]]
        right_stimuli = p.participant.vars['matrices'][p.round_number-1][p.participant.vars['color_2_list'][p.round_number-1]]
        
        human_response = left_stimuli if p.response == 1 else right_stimuli
        human_loser = right_stimuli if p.response == 1 else left_stimuli
        
        # --- YIELD HUMAN ROW (Participant 1) ---
        yield [
            p.session.code, 
            p.participant.code, 
            p.round_number, 
            1, # participant_number
            left_stimuli, 
            right_stimuli, 
            human_response, 
            human_loser, 
            p.answered_time, 
            p.payoff, 
            p.participant.payoff
        ]
        
        # 2. Reconstruct the bot's choices (mimicking screen orientation)
        bot_loser = right_stimuli if p.bot_choice == left_stimuli else left_stimuli
        bot_code = f"{p.participant.code}_bot"
        
        # --- YIELD BOT ROW (Participant 2) ---
        yield [
            p.session.code, 
            bot_code, 
            p.round_number, 
            2, # participant_number
            left_stimuli, 
            right_stimuli, 
            p.bot_choice, 
            bot_loser, 
            p.bot_answered_time, # Simulated time saved in process_round
            p.payoff, 
            p.participant.payoff
        ]