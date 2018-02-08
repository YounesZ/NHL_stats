# -*- coding: utf-8 -*-
"""Example of Line Recommendation.

This module demonstrates the usage of a line recommender.

Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::

        $ python example_google.py

Attributes:

Todo:
    * Nothing for now.

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""
import pickle
from os import path

import numpy as np

from ReinforcementLearning.NHL.playbyplay.playbyplay_data import Season, Game
from ReinforcementLearning.NHL.player.player_type import PlayerType
from ReinforcementLearning.NHL.lines.category import CategoryFetcher
from ReinforcementLearning.NHL.lines.valuation import QValuesFetcherFromDict
from ReinforcementLearning.NHL.lines.recommender import LineRecommender

from typing import Set

def get_MTL_players(players_classes) -> Set[int]:
    return set(players_classes[players_classes["team"] == "MTL"].index)

def do_it_together():
    from ReinforcementLearning.NHL.playbyplay.state_space_data import HockeySS
    """Initialization"""
    db_root = '/Users/luisd/dev/NHL_stats/data'
    repoCode = '/Users/luisd/dev/NHL_stats'
    # Montreal received Ottawa on march 13, 2013, let's convert game date to game code
    gameId = Season.get_game_id(db_root=db_root, home_team_abbr='MTL', date_as_str='2013-03-13')

    repoModel = path.join(repoCode,
                               'ReinforcementLearning/NHL/playerstats/offVSdef/Automatic_classification/MODEL_perceptron_1layer_10units_relu')

    # Now lets get game data
    season = Season(db_root=db_root, year_begin=2012)  # Season.from_year_begin(2012) # '20122013'
    mtlott = season.pick_game(gameId)

    players_classes = mtlott.pull_players_classes_from_repo_address(True, True, 20, repoModel, number_of_games=30)

    # prediction of the lines that the 'away' team will use:
    df, away_lines = mtlott.get_away_lines(accept_repeated=True)

    # === Now we get the indices in the Q-values tables corresponding to lines

    # Line translation table
    linedict  = HockeySS(db_root)
    linedict.make_line_dictionary()
    linedict  = linedict.line_dictionary

    # Get lines and translate them
    playersCode  =   mtlott.encode_line_players()
    linesCode    =   np.array( [[mtlott.recode_line(linedict, a) for a in b] for b in playersCode] )


    # Load the Qvalues table
    Qvalues = \
    pickle.load(open(path.join(repoCode, 'ReinforcementLearning/NHL/playbyplay/data/stable/RL_action_values.p'), 'rb'))[
        'action_values']

    # Visualize it dimensions (period x differential x away line's code x home line's code)
    print('Q-table dimensions: ', Qvalues.shape)

    # Get the Q-value for that specific line
    iShift = 0  # First shift
    lineShifts = mtlott.lineShifts.as_df(team='both', equal_strength=mtlott.shifts_equal_strength,
                                       regular_time=mtlott.shifts_regular_time, min_duration=20)

    plList = list(mtlott.player_classes.loc[lineShifts['playersID'].iloc[iShift][0]]['firstlast'].values) + \
             list(mtlott.player_classes.loc[lineShifts['playersID'].iloc[iShift][1]]['firstlast'].values)
    diff = mtlott.recode_differential(lineShifts.iloc[iShift].differential)
    period = mtlott.recode_period(lineShifts.iloc[iShift].period)
    q_values = Qvalues[period, diff, linesCode[iShift, 0], linesCode[iShift, 1]]
    print('[diff = %d, period = %d] First shift: \n\thome team: %s, %s, %s \n\taway team: %s, %s, %s \n\tQvalue: %.2f' % (
    diff, period, plList[0], plList[1], plList[2], plList[3], plList[4], plList[5], q_values))



    q_value_tuples = [
        ([PlayerType.NEUTRAL, PlayerType.NEUTRAL, PlayerType.OFFENSIVE],
         [PlayerType.OFFENSIVE, PlayerType.DEFENSIVE, PlayerType.DEFENSIVE],
        25),
        ([PlayerType.NEUTRAL, PlayerType.NEUTRAL, PlayerType.OFFENSIVE],
         [PlayerType.NEUTRAL, PlayerType.NEUTRAL, PlayerType.NEUTRAL],
        12),
        ([PlayerType.NEUTRAL, PlayerType.NEUTRAL, PlayerType.NEUTRAL],
         [PlayerType.OFFENSIVE, PlayerType.DEFENSIVE, PlayerType.DEFENSIVE],
        20),
        ([PlayerType.NEUTRAL, PlayerType.NEUTRAL, PlayerType.NEUTRAL],
         [PlayerType.NEUTRAL, PlayerType.NEUTRAL, PlayerType.NEUTRAL],
        1),
    ]

    line_rec = LineRecommender(
        player_category_fetcher=CategoryFetcher(data_for_game=mtlott),
        q_values_fetcher=QValuesFetcherFromDict.from_tuples(q_value_tuples))

    home_lines_rec = line_rec.recommend_lines_maximize_average(
                                    home_team_players_ids=get_MTL_players(players_classes),
                                    away_team_lines = away_lines, examine_max_first_lines=None)
    print(home_lines_rec)

if __name__ == '__main__':
    import cProfile
    cProfile.run('do_it_together()', '/tmp/restats')
    import pstats

    see_top = 25

    p = pstats.Stats('/tmp/restats')
    p.sort_stats('cumulative').print_stats(see_top)

    p.sort_stats('time').print_stats(see_top)
