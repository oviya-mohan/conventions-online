from . import *
from otree.api import Bot, Submission
import random

# ==========================================
# ⚙️ HUMAN SIMULATION TOGGLE
# Change this to 'RANDOM' or 'FIXED' to test different behaviors
HUMAN_STRATEGY = 'RANDOM'

# The hierarchy the simulated human will use if set to 'FIXED'. 
# Note: Since Constants.COLORS uses integers [1, 2, 3, 4, 5, 6, 7], 
# the keys here must also be integers.
HUMAN_HIERARCHY = {
    1: 7, 
    2: 6, 
    3: 5, 
    4: 4, 
    5: 3, 
    6: 2, 
    7: 1
}
# ==========================================

class PlayerBot(Bot):
    def play_round(self):
        
        # --- 1. Handle Intro Pages (Only Round 1) ---
        if self.round_number == 1:
            yield Consent
            # The Info page requires 'age' and 'sex' inputs[cite: 1]
            yield Info, dict(age=28, sex='Female')
            yield Instructions_no_player

        # --- 2. Read the colors shown on screen ---
        left_color = self.participant.vars['matrices'][self.round_number-1][self.participant.vars['color_1_list'][self.round_number-1]]
        right_color = self.participant.vars['matrices'][self.round_number-1][self.participant.vars['color_2_list'][self.round_number-1]]

        # --- 3. Determine Human Choice ---
        if HUMAN_STRATEGY == 'RANDOM':
            # Human blindly mashes buttons
            human_choice = random.choice([1, 2])
            
        elif HUMAN_STRATEGY == 'FIXED':
            # Human strictly follows their internal hierarchy
            if HUMAN_HIERARCHY[left_color] > HUMAN_HIERARCHY[right_color]:
                human_choice = 1  # 1 submits a Left click[cite: 1]
            else:
                human_choice = 2  # Submits a Right click

        # --- 4. Submit the Choice Page ---
        # The Make_Choice page requires 'response' and 'answered_time'[cite: 1]
        yield Make_Choice, dict(response=human_choice, answered_time=1200)

        # --- 5. Handle Feedback & Intermediate Pages ---
        # Bypasses the HTML button check for auto-advancing pages
        yield Submission(Show_Choice, check_html=False)
        
        # Yield BotThinking if it is configured to display
        if self.session.config.get('bot_max_wait', 0) > 0:
            yield Submission(BotThinking, check_html=False)
            
        # The server calculates payoff right after Make_Choice. 
        # We use it to determine which feedback pages the bot needs to click through.
        if self.player.payoff == 1:
            yield Submission(Results_Correct, check_html=False)
        else:
            yield Submission(Red_Flash, check_html=False)
            yield Submission(Results_Wrong, check_html=False)
            
        # The Break page displays at exactly 1/3 and 2/3 of the total rounds
        if self.round_number == Constants.num_rounds / 3 or self.round_number == 2 * Constants.num_rounds / 3:
            # If your Break page has a Next button, you can just use `yield Break`. 
            # If it auto-advances or you hid the button, use the Submission wrapper:
            yield Submission(Break, check_html=False)

        # --- 6. Handle Exit Pages (Only Last Round) ---
        if self.round_number == Constants.num_rounds:
            yield Final_Results
            # The Questions page requires a 'Q' string[cite: 1]
            yield Questions, dict(Q="I followed a strict hierarchy.")
            # The Questions_1 page requires a 'Q_1' string[cite: 1]
            yield Questions_1, dict(Q_1="Just rank the colors in your head.")
            yield Submission(Thanks, check_html=False)