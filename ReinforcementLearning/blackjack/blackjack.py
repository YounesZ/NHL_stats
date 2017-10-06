"""
    This module implements blackjack game rules and two different methods for finding the best policy:
    - method1: MC policy evaluation with episode simulation
    - method2: MC policy evaluation with episode averaging

    An episode is a game of blackjack that starts with the dealer giving two cards to the agent/player and two for
    himself (one face up, one face down) and ends when either agent busts, dealer busts or when both of them stick and
    compare their hands for determining win (+1 reward), lose (-1 reward) or draw (0 reward) outcomes

    Two types of games can be played:
    - type1: finite card deck (without replacement, dealer picks a new deck after depletion)
    - type2: infinite card deck (with replacement, dealer picks a new deck after each episode)

    This exercise is drawn from the book of Sutton and Berto (2002) p.108

    TODO:
        -   Debug game execution
        -   Hand evaluation at game start to check for "naturals"
        -   Implement infinite card deck
        -   Monte-Carlo method for finding optimal policy by simulating state-action
        -   Monte-Carlo method for finding optimal policy by sampling state-action
"""

#==== IMPORTS
import numpy as np
from random import shuffle
from Utils.programming import ut_remove_value
from copy import deepcopy


class blackJack:

    def __init__(self, gameType='infinite'):
        # Data location
        self.gameType   =   gameType
        # Initiate data structures
        self.replace=   {'jack':'10', 'queen':'10', 'king':'10'}
        self.history=   []
        self.drawn  =   0
        # Initiate game deck
        self.deck_new()

    def deck_new(self):
        # Make a new card deck
        colors      =   ['Heart', 'Diamond', 'Club', 'Spade']
        numbers     =   [str(x + 1) for x in range(10)] + ['jack', 'queen', 'king']
        self.deck   =   list( np.concatenate([[x+'_'+y for x in numbers] for y in colors][:]) )
        shuffle(self.deck)
        self.game_start()

    def game_start(self):
        self.agent  =   {'hand': [], 'shown': [], 'plays': [], 'value': 0, 'status': 'On'}
        self.dealer =   {'hand': [], 'shown': [], 'plays': [], 'value': 0, 'status': 'On'}
        if self.drawn<49:
            # Dealer gives two cards to agent
            self.agent['hand'].append(self.deck.pop(0))
            self.agent['hand'].append(self.deck.pop(0))
            self.agent['shown'] =   [True] * 2
            # Dealer gives two cards to himself
            self.dealer['hand'].append(self.deck.pop(0))
            self.dealer['hand'].append(self.deck.pop(0))
            self.dealer['shown']=   [True, False]
            self.drawn  +=  4
            # Evaluate new hand value
            self.turn   =   'agent'
            self.hand_value()
            # Evaluate game status
            self.game_status()
        else:
            # Deck exhausted
            print('\tDeck exhausted, reshuffling')
            shuffle(self.deck)
            self.drawn  =   0
            self.game_start()

    def hand_hit(self):
        # Take a card from the deck and put into agent's head
        player  =   self.turn
        plDict  =   getattr(self, player)
        if player=='dealer' and self.agent['status']=='On':
            print('\tWrong play: dealer must wait for agent to stick or bust')
            return
        elif plDict['status']=='stick':
            print('\tWrong play: '+player+' chose to stick')
            return
        elif plDict['status']=='bust':
            print('\tWrong play: '+player+' busted already')
            return
        if self.drawn==52:
            print('\tDeck emptied, game restarted')
            self.dealer_clear_table()
            shuffle(self.deck)
            self.drawn  =   0
            self.game_start()
        else:
            if player=='dealer' and not self.dealer['shown'][-1]:
                self.dealer['shown'][-1]    =   True
            else:
                plDict['hand'].append(self.deck.pop(0))
                plDict['shown'].append(True)
                self.drawn  +=  1
                setattr(self, player, plDict)
            # Evaluate new hand value
            self.hand_value()
            # Evaluate game status
            self.game_status()

    def hand_value(self):
        # Evaluate player's hand
        player          =   self.turn
        plDict          =   getattr(self, player)
        # Make sure all cards are converted to value
        cards           =   [x.split('_')[0] for x in plDict['hand']]
        cards           =   [self.replace[x] if x in list(self.replace.keys()) else x for x in cards]
        cards           =   [int(x) for x in cards]
        plDict['plays'] =  [deepcopy(cards)]
        # Check for usable aces
        if 1 in cards:
            idx         =   cards.index(1)
            cards[idx]  =   11
            plDict['plays'] +=  [deepcopy(cards)]
        # Compute values
        plDict['value'] =   [sum(x) for x in plDict['plays']]
        # Check if busting
        bust            =   [x>21 for x in plDict['value']]
        bkjack          =   [x==21 for x in plDict['value']]
        if any(bust):
            plDict['usable']=   False
        if all(bust):
            plDict['status']=   'bust'
        if any(bkjack):
            plDict['status']=   'blackjack'
        setattr(self, player, plDict)

    def game_status(self):
        # Check agent's hand
        if self.agent['status'] == 'bust':
            msg         =   'Agent loses, busted'
            status      =   -1
            self.turn   =   'dealer'
        elif self.dealer['status'] == 'bust':
            msg         =   'Agent wins, dealer busted'
            status      =   1
            self.turn   = 'agent'
        elif self.agent['status'] == 'On':
            msg         =   "Game is on, agent's turn"
            status      =   2
        elif self.dealer['status'] == 'On':
            msg         =   "Game is on, dealer's turn"
            status      =   2
            self.turn   =   'dealer'
        else:  # both stuck
            # Agent value
            agent   =   ut_remove_value.main(self.agent['value'], '>21')
            dealer  =   ut_remove_value.main(self.dealer['value'], '>21')
            if agent > dealer:
                msg     =   'Agent wins, higher value'
                status  =   1
            elif agent < dealer:
                msg     =   'Agent loses, lower value'
                status  =   -1
            else:
                print('\tTied game')
                status  =   0
        if status < 2:
            # Episode over
            msg     =   'Game is over, draw new hand'
            self.history.append(status)
            self.dealer_clear_table()
            self.game_start()
        self.status_print(msg, status)

    def dealer_clear_table(self):
        # Put cards back in the deck
        self.deck += self.agent['hand']
        self.deck += self.dealer['hand']
        # Remove them from hands
        self.agent['hand']  = []
        self.dealer['hand'] = []

    def status_print(self, msg, status):
        # Common prints
        dlh     =   []
        for ii,jj in zip(self.dealer['hand'], self.dealer['shown']):
            if jj:
                dlh.append(ii)
            else:
                dlh.append('Hidden')
        print('======GAME #'+str(len(self.history)+1)+'======')
        print('\tAgent hand: '+', '.join(self.agent['hand']))
        print('\tDealer hand: ' + ', '.join(dlh))
        print('\t'+msg)
        # Follwing status
        if status:
            print('======\n\n')
        else:
            print('\tNew draw...\n')



# Demo
game    =   blackJack()
game.hand_hit()
