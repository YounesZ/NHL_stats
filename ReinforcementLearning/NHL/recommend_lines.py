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
import datetime
from os import path

import numpy as np

from ReinforcementLearning.NHL.playbyplay.season import Season
from ReinforcementLearning.NHL.player.player_type import PlayerType
from ReinforcementLearning.NHL.lines.category import CategoryFetcher
from ReinforcementLearning.NHL.lines.valuation import QValuesFetcherFromDict, QValuesFetcherFromGameData
from ReinforcementLearning.NHL.lines.recommender import LineRecommender
from ReinforcementLearning.NHL.playbyplay.game import Game, get_lines_for


def do_it_together():
    from ReinforcementLearning.NHL.playbyplay.state_space_data import HockeySS
    """Initialization"""
    db_root = '/Users/luisd/dev/NHL_stats/data'
    repoCode = '/Users/luisd/dev/NHL_stats'

    repoModel = path.join(repoCode,
                               'ReinforcementLearning/NHL/playerstats/offVSdef/Automatic_classification/MODEL_perceptron_1layer_10units_relu')


    season = Season(db_root=db_root, year_begin=2012, repo_model=repoModel)

    # Now lets get game data
    base_date = datetime.date(year=2013, month=3, day=13)
    result = season.get_game_at_or_just_before(game_date=base_date, home_team_abbr='MTL')
    assert (result is not None)
    gameId, d = result
    print("Fetched game %d, played on %s" % (gameId, d))
    data_for_a_game = Game(season, gameId)

    # prediction of the lines that the 'away' team will use:
    formation = get_lines_for(season, base_date, how_many_days_back=1, team_abbrev=data_for_a_game.away_team)
    away_lines_names = formation.as_names
    away_lines = formation.as_categories
    print(away_lines_names)
    print(away_lines)

    # === Now we get the indices in the Q-values tables corresponding to lines

    # Line translation table
    linedict  = HockeySS(db_root)
    linedict.make_line_dictionary()
    linedict  = linedict.line_dictionary

    # Get lines and translate them
    playersCode  =   data_for_a_game.encode_line_players()
    linesCode    =   np.array( [[data_for_a_game.recode_line(linedict, a) for a in b] for b in playersCode] )


    # Load the Qvalues table
    Qvalues = \
    pickle.load(open(path.join(repoCode, 'ReinforcementLearning/NHL/playbyplay/data/stable/RL_action_values.p'), 'rb'))[
        'action_values']

    # Visualize it dimensions (period x differential x away line's code x home line's code)
    print('Q-table dimensions: ', Qvalues.shape)

    # Get the Q-value for that specific line
    iShift = 0  # First shift
    lineShifts = data_for_a_game.lineShifts.as_df(team='both', equal_strength=data_for_a_game.shifts_equal_strength,
                                       regular_time=data_for_a_game.shifts_regular_time, min_duration=20)

    player_classes = data_for_a_game.players_classes_mgr.get(equal_strength=True, regular_time=True, min_duration=20, nGames=30) # TODO: why these parameters?
    plList = list(player_classes.loc[lineShifts['playersID'].iloc[iShift][0]]['firstlast'].values) + \
             list(player_classes.loc[lineShifts['playersID'].iloc[iShift][1]]['firstlast'].values)
    diff = data_for_a_game.recode_differential(lineShifts.iloc[iShift].differential)
    period = data_for_a_game.recode_period(lineShifts.iloc[iShift].period)
    q_values = Qvalues[period, diff, linesCode[iShift, 0], linesCode[iShift, 1]]
    print('[diff = %d, period = %d] First shift: \n\thome team: %s, %s, %s \n\taway team: %s, %s, %s \n\tQvalue: %.2f' % (
    diff, period, plList[0], plList[1], plList[2], plList[3], plList[4], plList[5], q_values))

    q_values_fetcher_from_game_data = QValuesFetcherFromGameData(game_data=data_for_a_game, lines_dict=linedict, q_values=Qvalues)

    line_rec = LineRecommender(
        game=data_for_a_game,
        player_category_fetcher=CategoryFetcher(data_for_game=data_for_a_game),
        q_values_fetcher=q_values_fetcher_from_game_data) # q_values_fetcher_from_tuples)

    home_lines_rec = line_rec.recommend_lines_maximize_average(
                                    home_team_players_ids=data_for_a_game.get_ids_of_home_players(),
                                    away_team_lines = away_lines, examine_max_first_lines=2) # None)
    print(home_lines_rec)

    print(data_for_a_game.formation_ids_to_str(home_lines_rec))

    # let's examine actual decisions and how it compares with optimal:
    seconds = {'bad': 0, 'good': 0}
    for data in lineShifts[['home_line', 'away_line', 'iceduration']].itertuples():
        home_line = data.home_line
        away_line = data.away_line
        num_seconds = data.iceduration
        away_line_cats = data_for_a_game.classes_of_line(away_line)
        if None in away_line_cats:
            print("Can't get category of one of away players")
        else:
            away_line_cats = tuple(np.sort(away_line_cats))
            if away_line_cats not in away_lines:
                print("%s (categories %s): no optimal calculated" % (away_line, away_line_cats))
            else:
                idx_of_away = away_lines.index(away_line_cats)
                cats_of_optimal = data_for_a_game.classes_of_line(home_lines_rec[idx_of_away])
                home_line_cats = data_for_a_game.classes_of_line(home_line)
                if set(cats_of_optimal) == set(home_line_cats):
                    seconds['good'] += num_seconds
                else:
                    seconds['bad'] += num_seconds
    print(seconds)
    print("Home coach's score (in [0,1]) is %.2f" % (seconds['good'] / (seconds['good'] + seconds['bad'])))

if __name__ == '__main__':
    import cProfile
    cProfile.run('do_it_together()', '/tmp/restats')
    import pstats

    see_top = 25

    p = pstats.Stats('/tmp/restats')
    p.sort_stats('cumulative').print_stats(see_top)

    p.sort_stats('time').print_stats(see_top)
