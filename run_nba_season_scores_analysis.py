# Created by: Anthony ElHabr
# Purpose: Model how different projection systems would have picked
#          every game for a given NBA season and compare to the actual outcome
# 1) model1: use preseason win total
# 2) model2: use record to date of game
# 3) model3: use Tony's preseason over-under pick in a normal distribution
#    a) use the number directly above/below win total as the mean
#    b) use confidence rating to determine the standard deviation
# 4) model4: use Andrew's preseason over-under pick in the same manner as
#       model3
#
# Suggestions for improvements:
# 1) Build models with DataFrames directly
# 2) Use DataFrames methods to get summary statistics instead
#    of creating a separate dict
# 3) Figure out what correlates most closely with win totals
# 4) Create additional models that incorporate:
#    a) w-l record in past 5-10 games <- EASY
#    b) offensive/defensive rating of each team <- MEDIUM
#    c) win shares of each player <- MEDIUM
#    d) WOWY (or plus-minus) of each player weighted by average minutes played
#       by each player or a given 5-man unit <- HARD
#    e) rest time since previous game <- EASY
#    f) travel distance from previous game <- MEDIUM
#    g) comparison of team profiles to historical matchups with teams with
#       similar profiles <- REALLY HARD
# 5) Figure out the probability that the team finished with their
#    actual w-l record by considering:
#    a) preseason win total
#    b) Pythagorean wins
#    c) net rating
#    d) injury luck
#    e) strength of schedule


import os
from collections import OrderedDict
from datetime import datetime, date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# import seaborn as sns



def get_model1_game_winner(this_t, other_t, home_flag, this_t_wt, other_t_wt):
    if (this_t_wt > other_t_wt) or (this_t_wt == other_t_wt and home_flag):
        return this_t
    else:
        return other_t


def get_model2_game_winner(this_t, other_t, home_flag, this_t_wins_to_date, game_date, scores_df):
    other_t_df = scores_df.loc[scores_df['team_schedule'] == other_t]
    other_t_wins_to_date = int(
        other_t_df.loc[other_t_df['game_date'] == game_date]['wins_to_date'])

    if (this_t_wins_to_date > other_t_wins_to_date) or (this_t_wins_to_date == other_t_wins_to_date and home_flag):
        return this_t
    else:
        return other_t


def get_model3_mu_num(wt_df, t, t_wt, this_t, home_flag):
    try:
        tony_wt_pick_flag = str(
            wt_df.loc[wt_df['team_abbrv'] == t]['tony_win_total_pick_flag'])
        # account for case in which number (in addition to 'o' or 'u') is gven for win total
        # tony_wt_pick_num = int(wt_df.loc[wt_df['team_abbrv'] == t]['tony_win_total_pick_num'])

        if tony_wt_pick_flag == 'o':
            # use number above team's win total if 'over'
            mu_num = int(round(t_wt+1))
        else:
            # use number below team's win total if 'under'
            mu_num = int(round(t_wt))

    except Exception as e:
        # print e
        mu_num = float(t_wt)

    # account for home court advantage
    HOME_HANDICAP = 4

    if t == this_t:
        # print "Debugging: home_flag type is {0}".format(type(home_flag))
        if home_flag == 1:
            mu_num += float(HOME_HANDICAP/2)
        elif home_flag == 0:
            mu_num -= float(HOME_HANDICAP/2)
    else:
        if home_flag == 0:
            mu_num += float(HOME_HANDICAP/2)
        elif home_flag == 1:
            mu_num -= float(HOME_HANDICAP/2)

    return mu_num


def get_model3_sigma_num(wt_df, t, num_teams):
    DEFAULT_CONFIDENCE = float((num_teams+1)/2)
    try:
        tony_wt_confidence = int(
            wt_df.loc[wt_df['team_abbrv'] == t]['tony_win_total_confidence'])

        # account for 'tony_win_total_confidence' = None in older
        # 'nba-season-win-totals-yyyy.csv' files
        if tony_wt_confidence == None:
            tony_wt_confidence = DEFAULT_CONFIDENCE
            # print "No 'tony_win_total_confidence' for {0}".format(t)
            # print "Using a default value"

    except Exception as e:
        # print e
        tony_wt_confidence = DEFAULT_CONFIDENCE

    return float((num_teams+1)-tony_wt_confidence)


def get_model3_wt_pick_num(mu_num, sigma_num):
    return sigma_num * np.random.randn() + mu_num


def get_model4_mu_num(wt_df, t, t_wt, this_t, home_flag):
    try:
        andrew_wt_pick_flag = str(
            wt_df.loc[wt_df['team_abbrv'] == t]['andrew_win_total_pick_flag'])
        # account for case in which number (in addition to 'o' or 'u') is gven for win total
        # andrew_wt_pick_num = int(wt_df.loc[wt_df['team_abbrv'] == t]['andrew_win_total_pick_num'])

        if andrew_wt_pick_flag == 'o':
            # use number above team's win total if 'over'
            mu_num = int(round(t_wt+1))
        else:
            # use number below team's win total if 'under'
            mu_num = int(round(t_wt))

    except Exception as e:
        # print e
        mu_num = float(t_wt)

    # account for home court advantage
    HOME_HANDICAP = 4

    if t == this_t:
        # print "Debugging: home_flag type is {0}".format(type(home_flag))
        if home_flag == 1:
            mu_num += float(HOME_HANDICAP/2)
        elif home_flag == 0:
            mu_num -= float(HOME_HANDICAP/2)
    else:
        if home_flag == 0:
            mu_num += float(HOME_HANDICAP/2)
        elif home_flag == 1:
            mu_num -= float(HOME_HANDICAP/2)

    return mu_num


def get_model4_sigma_num(wt_df, t, num_teams):
    DEFAULT_CONFIDENCE = float((num_teams+1)/2)
    try:
        andrew_wt_confidence = int(
            wt_df.loc[wt_df['team_abbrv'] == t]['andrew_win_total_confidence'])

        # account for 'andrew_win_total_confidence' = None in older
        # 'nba-season-win-totals-yyyy.csv' files
        if andrew_wt_confidence == None:
            andrew_wt_confidence = DEFAULT_CONFIDENCE
            # print "No 'andrew_win_total_confidence' for {0}".format(t)
            # print "Using a default value"

    except Exception as e:
        # print e
        andrew_wt_confidence = DEFAULT_CONFIDENCE

    return float((num_teams+1)-andrew_wt_confidence)


def get_model4_wt_pick_num(mu_num, sigma_num):
    return sigma_num * np.random.randn() + mu_num


def update_model3_dict2_for_game(model3_dict2, t_mu_num, t_sigma_num, t_wt_pick_num, t, this_t):
    if t == this_t:
        model3_dict2['this_t_mu'].append(t_mu_num)
        model3_dict2['this_t_sigma'].append(t_sigma_num)
        model3_dict2['this_t_wt_pick'].append(t_wt_pick_num)
    else:
        model3_dict2['other_t_mu'].append(t_mu_num)
        model3_dict2['other_t_sigma'].append(t_sigma_num)
        model3_dict2['other_t_wt_pick'].append(t_wt_pick_num)


def get_model3_game_winner(this_t, other_t, this_t_wt, other_t_wt, home_flag, wt_df, num_teams, model3_dict2):
    # mean of normal distribution
    this_t_mu_num = get_model3_mu_num(
        wt_df, this_t, this_t_wt, this_t, home_flag)
    other_t_mu_num = get_model3_mu_num(
        wt_df, other_t, other_t_wt, this_t, home_flag)

    # standard deviation of normal distribution
    this_t_sigma_num = get_model3_sigma_num(wt_df, this_t, num_teams)
    other_t_sigma_num = get_model3_sigma_num(wt_df, other_t, num_teams)

    # calculate normal distribution N(mu, sigma^2)
    this_t_wt_pick_num = get_model3_wt_pick_num(
        this_t_mu_num, this_t_sigma_num)
    other_t_wt_pick_num = get_model3_wt_pick_num(
        other_t_mu_num, other_t_sigma_num)

    update_model3_dict2_for_game(model3_dict2, this_t_mu_num, this_t_sigma_num,
                                 this_t_wt_pick_num, this_t, this_t)
    update_model3_dict2_for_game(
        model3_dict2, other_t_mu_num, other_t_sigma_num, other_t_wt_pick_num, other_t, this_t)

    if (this_t_wt_pick_num > other_t_wt_pick_num) or (this_t_wt_pick_num == other_t_wt_pick_num and home_flag):
        return this_t
    else:
        return other_t


def get_model4_game_winner(this_t, other_t, this_t_wt, other_t_wt, home_flag, wt_df, num_teams, model4_dict2):
    return get_model3_game_winner(this_t, other_t, this_t_wt, other_t_wt, home_flag, wt_df, num_teams, model4_dict2)


def is_game_pick_correct(game_winner, this_t, win_flag):
    if game_winner == this_t:
        if win_flag == 1:
            return 1
        elif win_flag == 0:
            return 0
        else:
            return -1
    else:
        if win_flag == 0:
            return 1
        elif win_flag == 1:
            return 0
        else:
            return -1


def update_model_dict_for_game(model_dict, model_game_winner, this_t, other_t, win_flag):
    model_game_pick_correct_bool = -1
    if model_game_winner == this_t:
        model_dict['game_pick'].append(this_t)
        if win_flag == 1:
            model_game_pick_correct_bool = 1
        elif win_flag == 0:
            model_game_pick_correct_bool = 0
        else:
            model_game_pick_correct_bool = -1

        model_dict['game_win_flag'].append(1)
        model_dict['game_loss_flag'].append(0)
    else:
        model_dict['game_pick'].append(other_t)
        if win_flag == 0:
            model_game_pick_correct_bool = 1
        elif win_flag == 1:
            model_game_pick_correct_bool = 0
        else:
            model_game_pick_correct_bool = -1

        model_dict['game_win_flag'].append(0)
        model_dict['game_loss_flag'].append(1)

    model_dict['game_pick_correct_flag'].append(model_game_pick_correct_bool)


def is_model_wt_pick_correct(this_t_wt, actual_sum_win_num, model_sum_win_num):
    if actual_sum_win_num > this_t_wt:
        if model_sum_win_num > this_t_wt:
            return 1
        elif model_sum_win_num < this_t_wt:
            return 0
        elif model_sum_win_num == this_t_wt:
            return 0.5
    elif actual_sum_win_num < this_t_wt:
        if model_sum_win_num > this_t_wt:
            return 0
        elif model_sum_win_num < this_t_wt:
            return 1
        elif model_sum_win_num == this_t_wt:
            return 0.5
    elif actual_sum_win_num == this_t_wt:
        return 0.5


def update_actual_dict_for_team(actual_dict, this_t, actual_sum_win_num, actual_sum_loss_num):
    actual_dict['team_abbrv'].append(this_t)
    actual_dict['sum_win'].append(actual_sum_win_num)
    actual_dict['sum_loss'].append(actual_sum_loss_num)


def update_model_dict_for_team(model_dict, this_t_wt, actual_sum_win_num, old_model_sum_win_num, old_model_sum_loss_num):

    model_sum_win_num = sum(model_dict['game_win_flag'])-old_model_sum_win_num
    model_sum_loss_num = sum(
        model_dict['game_loss_flag'])-old_model_sum_loss_num
    model_dict['sum_win'].append(model_sum_win_num)
    model_dict['sum_loss'].append(model_sum_loss_num)

    model_wt_pick_correct_bool = is_model_wt_pick_correct(
        this_t_wt, actual_sum_win_num, model_sum_win_num)
    model_sum_error_num = abs(actual_sum_win_num-model_sum_win_num)
    model_dict['wt_pick_correct_flag'].append(model_wt_pick_correct_bool)
    model_dict['sum_error'].append(model_sum_error_num)


def make_model_dicts(year, all_teams, scores_df, wt_df, actual_dict, model1_dict, model2_dict, model3_dict, model4_dict, model3_dict2, model4_dict2):
    start_all = datetime.now()

    num_teams = len(all_teams)

    for t in all_teams:
        start = datetime.now()

        this_t = t
        # need to convert type from pandas.series to float
        this_t_wt = float(
            wt_df.loc[wt_df['team_abbrv'] == this_t]['win_total'])

        this_t_df = scores_df.loc[scores_df['team_schedule'] == this_t]

        actual_sum_win_num = this_t_df['wins_to_date'].iloc[-1]
        actual_sum_loss_num = this_t_df['losses_to_date'].iloc[-1]

        old_model1_sum_win_num = sum(model1_dict['game_win_flag'])
        old_model1_sum_loss_num = sum(model1_dict['game_loss_flag'])
        old_model2_sum_win_num = sum(model2_dict['game_win_flag'])
        old_model2_sum_loss_num = sum(model2_dict['game_loss_flag'])
        old_model3_sum_win_num = sum(model3_dict['game_win_flag'])
        old_model3_sum_loss_num = sum(model3_dict['game_loss_flag'])
        old_model4_sum_win_num = sum(model4_dict['game_win_flag'])
        old_model4_sum_loss_num = sum(model4_dict['game_loss_flag'])

        # type of 'row' would be tuple without 'index'
        # type of 'row' is pandas.series with 'index'
        for index, row in this_t_df.iterrows():
            home_flag = int(row.loc['home_flag'])
            win_flag = int(row.loc['win_flag'])

            if home_flag == 1:
                other_t = row.loc['away_team']
            else:
                other_t = row.loc['home_team']

            # need to convert type from pandas.series to float
            other_t_wt = float(
                wt_df.loc[wt_df['team_abbrv'] == other_t]['win_total'])

            # calculate game winner for each model
            # calculate game winner for model1
            model1_game_winner = get_model1_game_winner(
                this_t, other_t, home_flag, this_t_wt, other_t_wt)

            # calculate game winner for model2
            this_t_wins_to_date = row.loc['wins_to_date']
            game_date = row.loc['game_date']
            model2_game_winner = get_model2_game_winner(
                this_t, other_t, home_flag, this_t_wins_to_date, game_date, scores_df)

            # calculate game winner for model3
            model3_game_winner = get_model3_game_winner(
                this_t, other_t, this_t_wt, other_t_wt, home_flag, wt_df, num_teams, model3_dict2)

            # calculate game winner for model4 in same way as for model3
            model4_game_winner = get_model4_game_winner(
                this_t, other_t, this_t_wt, other_t_wt, home_flag, wt_df, num_teams, model4_dict2)

            # update each model after calculating game winner
            update_model_dict_for_game(
                model1_dict, model1_game_winner, this_t, other_t, win_flag)
            update_model_dict_for_game(
                model2_dict, model2_game_winner, this_t, other_t, win_flag)
            update_model_dict_for_game(
                model3_dict, model3_game_winner, this_t, other_t, win_flag)
            update_model_dict_for_game(
                model4_dict, model4_game_winner, this_t, other_t, win_flag)
            # if index<10:
            #     print this_t, other_t, win_flag, model4_game_winner, model4_dict['game_pick_correct_flag'][-1]

        # update each model after calculating game winner for each game on
        # team's schedule
        update_actual_dict_for_team(
            actual_dict, this_t, actual_sum_win_num, actual_sum_loss_num)
        update_model_dict_for_team(
            model1_dict, this_t_wt, actual_sum_win_num, old_model1_sum_win_num, old_model1_sum_loss_num)
        update_model_dict_for_team(
            model2_dict, this_t_wt, actual_sum_win_num, old_model2_sum_win_num, old_model2_sum_loss_num)
        update_model_dict_for_team(
            model3_dict, this_t_wt, actual_sum_win_num, old_model3_sum_win_num, old_model3_sum_loss_num)
        update_model_dict_for_team(
            model4_dict, this_t_wt, actual_sum_win_num, old_model4_sum_win_num, old_model4_sum_loss_num)
        # print actual_sum_win_num, model4_dict['sum_win'], model4_dict['sum_error']

        end = datetime.now()
        time_diff = end - start
        print("Finished running analysis for {0} in {1} s".format(t, time_diff))
        # break

    end_all = datetime.now()
    time_diff_all = end_all - start_all
    print("Finished running all analysis for {0} in {1} s".format(year, time_diff_all))


def get_timestamp():
    timestamp = datetime.now()
    return timestamp.strftime('%m/%d/%Y, %H:%M:%S')


def make_analysis_df(model1_dict, model2_dict, model3_dict, model4_dict, model3_dict2, model4_dict2):
    analysis_dict_keys = []
    analysis_dict_vals = []

    model1_dict_items = list(model1_dict.items())
    for key, value in model1_dict_items[:4]:
        analysis_dict_keys.append("model1_"+key)
        analysis_dict_vals.append(value)

    model2_dict_items = list(model2_dict.items())
    for key, value in model2_dict_items[:4]:
        analysis_dict_keys.append("model2_"+key)
        analysis_dict_vals.append(value)

    model3_dict_items = list(model3_dict.items())
    for key, value in model3_dict_items[:4]:
        analysis_dict_keys.append("model3_"+key)
        analysis_dict_vals.append(value)

    model4_dict_items = list(model4_dict.items())
    for key, value in model4_dict_items[:4]:
        analysis_dict_keys.append("model4_"+key)
        analysis_dict_vals.append(value)

    model3_dict2_items = list(model3_dict2.items())
    for key, value in model3_dict2_items[::2]:
        analysis_dict_keys.append("model3_"+key)
        analysis_dict_vals.append(value)

    model4_dict2_items = list(model4_dict2.items())
    for key, value in model4_dict2_items[::2]:
        analysis_dict_keys.append("model4_"+key)
        analysis_dict_vals.append(value)

    analysis_dict = OrderedDict(list(zip(analysis_dict_keys, analysis_dict_vals)))

    return pd.DataFrame(analysis_dict)


def extend_scores_df(scores_df, analysis_df):
    return pd.concat([scores_df, analysis_df], axis=1)


def update_model3_dict2_for_analysis(model_num, model3_dict2, t, this_t, this_t_df2):
    # TODO: improve this code so it is less repetitious between
    # 'this' and 'other'
    if t == this_t:
        t_mu_mean_num = float(
            sum(this_t_df2['model{0}_this_t_mu'.format(model_num)])/len(this_t_df2['model{0}_this_t_mu'.format(model_num)]))
        t_sigma_mean_num = float(
            sum(this_t_df2['model{0}_this_t_sigma'.format(model_num)])/len(this_t_df2['model{0}_this_t_sigma'.format(model_num)]))
        t_wt_pick_mean_num = float(
            sum(this_t_df2['model{0}_this_t_wt_pick'.format(model_num)])/len(this_t_df2['model{0}_this_t_wt_pick'.format(model_num)]))

        model3_dict2['this_t_mu_mean'].append(t_mu_mean_num)
        model3_dict2['this_t_sigma_mean'].append(t_sigma_mean_num)
        model3_dict2['this_t_wt_pick_mean'].append(t_wt_pick_mean_num)
    else:
        t_mu_mean_num = float(
            sum(this_t_df2['model{0}_other_t_mu'.format(model_num)])/len(this_t_df2['model{0}_other_t_mu'.format(model_num)]))
        t_sigma_mean_num = float(
            sum(this_t_df2['model{0}_other_t_sigma'.format(model_num)])/len(this_t_df2['model{0}_other_t_sigma'.format(model_num)]))
        t_wt_pick_mean_num = float(
            sum(this_t_df2['model{0}_other_t_wt_pick'.format(model_num)])/len(this_t_df2['model{0}_other_t_wt_pick'.format(model_num)]))

        model3_dict2['other_t_mu_mean'].append(t_mu_mean_num)
        model3_dict2['other_t_sigma_mean'].append(t_sigma_mean_num)
        model3_dict2['other_t_wt_pick_mean'].append(t_wt_pick_mean_num)


def update_model4_dict2_for_analysis(model_num2, model4_dict2, t, this_t, this_t_df2):
    update_model3_dict2_for_analysis(
        model_num2, model4_dict2, t, this_t, this_t_df2)


def make_analysis_summary_df(actual_dict, model1_dict, model2_dict, model3_dict, model4_dict, model3_dict2, model4_dict2, all_teams, scores_df2):
    for t in all_teams:
        this_t = t
        this_t_df2 = scores_df2.loc[scores_df2['team_schedule'] == this_t]

        # dummy variable used for the update_model3_dict2_for_analysis function
        other_t = ''

        model_num = 3
        update_model3_dict2_for_analysis(
            model_num, model3_dict2, this_t, this_t, this_t_df2)
        update_model3_dict2_for_analysis(
            model_num, model3_dict2, other_t, this_t, this_t_df2)

        model_num = 4
        update_model4_dict2_for_analysis(
            model_num, model4_dict2, this_t, this_t, this_t_df2)
        update_model4_dict2_for_analysis(
            model_num, model4_dict2, other_t, this_t, this_t_df2)

    analysis_summary_dict_keys = []
    analysis_summary_dict_vals = []

    actual_dict_items = list(actual_dict.items())
    for key, value in actual_dict_items[:]:
        analysis_summary_dict_keys.append(key)
        analysis_summary_dict_vals.append(value)

    model1_dict_items = list(model1_dict.items())
    for key, value in model1_dict_items[4:]:
        analysis_summary_dict_keys.append("model1_"+key)
        analysis_summary_dict_vals.append(value)

    model2_dict_items = list(model2_dict.items())
    for key, value in model2_dict_items[4:]:
        analysis_summary_dict_keys.append("model2_"+key)
        analysis_summary_dict_vals.append(value)

    model3_dict_items = list(model3_dict.items())
    for key, value in model3_dict_items[4:]:
        analysis_summary_dict_keys.append("model3_"+key)
        analysis_summary_dict_vals.append(value)

    model3_dict2_items = list(model3_dict2.items())
    for key, value in model3_dict2_items[1::2]:
        analysis_summary_dict_keys.append("model3_"+key)
        analysis_summary_dict_vals.append(value)

    model4_dict_items = list(model4_dict.items())
    for key, value in model4_dict_items[4:]:
        analysis_summary_dict_keys.append("model4_"+key)
        analysis_summary_dict_vals.append(value)

    model4_dict2_items = list(model4_dict2.items())
    for key, value in model4_dict2_items[1::2]:
        analysis_summary_dict_keys.append("model4_"+key)
        analysis_summary_dict_vals.append(value)

    analysis_summary_dict = OrderedDict(
        list(zip(analysis_summary_dict_keys, analysis_summary_dict_vals)))

    return pd.DataFrame(analysis_summary_dict)


def extend_analysis_summary_df(analysis_summary_df):
    # sum_row = analysis_summary_df.sum()
    # mean_row = analysis_summary_df.mean()
    sum_row = analysis_summary_df[analysis_summary_df.columns[1:]].sum()
    mean_row = analysis_summary_df[analysis_summary_df.columns[1:]].mean()

    sum_df = pd.DataFrame(sum_row).T
    sum_df = sum_df.reindex(columns=analysis_summary_df.columns)
    mean_df = pd.DataFrame(mean_row).T
    mean_df = mean_df.reindex(columns=analysis_summary_df.columns)

    analysis_summary_df2 = analysis_summary_df.append(
        sum_df, ignore_index=True)
    analysis_summary_df3 = analysis_summary_df2.append(
        mean_df, ignore_index=True)

    return analysis_summary_df3


def save_scores_df_to_csv(scores_df2, year, timestamp):
    scores_f2 = 'csvs\\nba-season-scores-analysis-{0}.csv'.format(
        year)
    if not os.path.isfile(scores_f2):
        scores_df2.to_csv(scores_f2, index=False)
        print("Creating new file '{0}' at {1}.".format(scores_f2, timestamp))
    else:
        print("Need to delete existing {0} before creating new one".format(scores_f2))
        # print "Overwriting existing '{0}'".format(analysis_summary_f)

def save_analysis_summary_df_to_csv(analysis_summary_df2, year, timestamp):
    analysis_summary_f = 'csvs\\nba-season-scores-analysis-summary-{0}.csv'.format(
        year)
    if not os.path.isfile(analysis_summary_f):
        analysis_summary_df2.to_csv(analysis_summary_f, index=False)
        print("Creating new file '{0}' at {1}.".format(analysis_summary_f, timestamp))
    else:
        print("Need to delete existing {0} before creating new one".format(analysis_summary_f))
        # print "Overwriting existing '{0}'".format(analysis_summary_f)


def save_fig_to_pdf(fig, filename):
    if not os.path.isfile(filename):
        fig.savefig(filename)
    else:
        os.remove(filename)
        fig.savefig(filename)



def plot_wt(year, all_teams, wt_df, analysis_summary_df, timestamp):
    # num_teams = len(all_teams)
    num_teams = 30

    y_vals = analysis_summary_df.index[:num_teams]
    x_vals00 = wt_df.win_total[:]
    # x_vals00 = wt_df.win_total[:3]
    x_vals0 = analysis_summary_df.sum_win[:num_teams]
    # x_vals1 = analysis_summary_df.model1_sum_win[:num_teams]
    # x_vals2 = analysis_summary_df.model2_sum_win[:num_teams]
    x_vals3 = analysis_summary_df.model3_sum_win[:num_teams]
    # x_vals31 = analysis_summary_df.model3_this_t_wt_pick_mean[:num_teams]
    # x_vals32 = analysis_summary_df.model3_this_t_mu_mean[:num_teams]
    # x_err32 = analysis_summary_df.model3_this_t_sigma_mean[:num_teams]
    x_vals4 = analysis_summary_df.model4_sum_win[:num_teams]

    sns.set_style("dark")

    fig, ax = plt.subplots(figsize=(10, 15))
    title = (
        "Predicted # of Wins for {0} - {1} Regular Season".format(year-1, year))
    ax.set_title(title, fontsize=16, y=1.07)

    ax.set_ylabel('Team', fontsize=14)
    ax.set_xlabel('# of Wins', fontsize=14)
    ax.set_ylim(num_teams, -1)
    ax.set_xlim(0, 82)

    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')

    ax.xaxis.grid(color='k')
    ax.set_axisbelow(False)

    plt.yticks(
        list(range(num_teams)), analysis_summary_df.team_abbrv[:num_teams], size='large')

    height1 = 0.2
    height2 = 0.4

    rects00 = ax.barh(bottom=y_vals-3*height1, width=x_vals00,
                      height=height1, left=0, color='b', align='edge', label='line')
    rects0 = ax.barh(bottom=y_vals-2*height1, width=x_vals0,
                     height=height1, left=0, color='c', align='edge', label='actual')
    # rects1 = ax.barh(bottom=y_vals-height1, width=x_vals1,
    #                  height=height1, left=0, color='b', align='edge', label='model1')
    # rects2 = ax.barh(bottom=y_vals-height1, width=x_vals2,
    # height=height1, left=0, color='c', align='edge', label='model2')
    rects3 = ax.barh(bottom=y_vals-1*height1, width=x_vals3, height=height1,
                     left=0, color='k', align='edge', label='tony')
    # rects31 = ax.barh(bottom=y_vals, width=x_vals31, height=height1, left=0, color='r', align='edge', label='tony')
    # rects32 = ax.barh(bottom=y_vals, width=x_vals32, height=height1, left=0,color='r', align='edge', label='tony', xerr=x_err32)
    rects4 = ax.barh(bottom=y_vals-0*height1, width=x_vals4, height=height1,
                     left=0, color='r', align='edge', label='andrew')

    def label_rects(rects):
        for rect in rects:
            width = rect.get_width()
            height = rect.get_y() + rect.get_height()/2
            ax.text(x=1.01*width, y=height, s='%d' %
                    int(width), ha='left', va='center', fontsize='11', weight='bold')

    label_rects(rects00)
    label_rects(rects0)
    # label_rects(rects1)
    # label_rects(rects2)
    label_rects(rects3)
    # label_rects(rects31)
    # label_rects(rects32)
    label_rects(rects4)

    plt.legend()

    plt.text(0, 30.5, 'Created by: Anthony ElHabr at {0}'.format(timestamp), fontsize=14)

    filename = 'pdfs\\wt-models-num-games-{0}.pdf'.format(year)
    save_fig_to_pdf(fig, filename)

    # plt.show()


def get_analysis_summary_df2_from_csv(year):
    analysis_summary_f = 'csvs\\nba-season-scores-analysis-summary-{0}.csv'.format(
        year)
    if not os.path.isfile(analysis_summary_f):
        print("Could not find file '{0}'".format(analysis_summary_f))
    else:
        print("Retrieved existing {0}".format(analysis_summary_f))
        return pd.read_csv(analysis_summary_f, index_col=False)


def plot_sum_error(year, all_teams, analysis_summary_df, timestamp):
    # num_teams = len(all_teams)
    num_teams = 30

    y_vals = analysis_summary_df.index[:num_teams]
    # x_vals00 = wt_df.win_total[:]
    # x_vals0 = analysis_summary_df.sum_win[:num_teams]
    # x_vals1 = analysis_summary_df.model1_sum_error[:num_teams]
    # x_vals2 = analysis_summary_df.model2_sum_error[:num_teams]
    x_vals3 = analysis_summary_df.model3_sum_error[:num_teams]
    x_vals4 = analysis_summary_df.model4_sum_error[:num_teams]

    sns.set_style("dark")

    fig, ax = plt.subplots(figsize=(10, 15))
    title = (
        "Error in Predicted # of Wins for {0} - {1} Regular Season".format(year-1, year))
    ax.set_title(title, fontsize=16, y=1.07)

    ax.set_ylabel('Team', fontsize=14)
    ax.set_xlabel('# of Wins', fontsize=14)
    ax.set_ylim(num_teams, -1)
    ax.set_xlim(0, 41)

    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')

    ax.xaxis.grid(color='k')
    ax.set_axisbelow(False)

    plt.yticks(
        list(range(num_teams)), analysis_summary_df.team_abbrv[:num_teams], size='large')

    height1 = 0.2
    height2 = 0.4

    # rects00 = ax.barh(bottom=y_vals-3*height1, width=x_vals00,
    #                  height=height1, left=0, color='b', align='edge', label='line')
    # rects0 = ax.barh(bottom=y_vals-2*height1, width=x_vals0,
    #                  height=height1, left=0, color='c', align='edge', label='actual')
    # rects1 = ax.barh(bottom=y_vals-height1, width=x_vals1,
    #                  height=height1, left=0, color='b', align='edge', label='model1')
    # rects2 = ax.barh(bottom=y_vals-height1, width=x_vals2,
    # height=height1, left=0, color='c', align='edge', label='model2')
    rects3 = ax.barh(bottom=y_vals-1*height2, width=x_vals3, height=height2,
                     left=0, color='k', align='edge', label='tony')
    rects4 = ax.barh(bottom=y_vals-0*height2, width=x_vals4, height=height2,
                     left=0, color='r', align='edge', label='andrew')

    def label_rects(rects):
        for rect in rects:
            width = rect.get_width()
            height = rect.get_y() + rect.get_height()/2
            ax.text(x=1.01*width, y=height, s='%d' %
                    int(width), ha='left', va='center', fontsize='11', weight='bold')

    # label_rects(rects00)
    # label_rects(rects0)
    # label_rects(rects1)
    # label_rects(rects2)
    label_rects(rects3)
    label_rects(rects4)

    plt.legend()

    plt.text(0, 30.5, 'Created by: Anthony ElHabr at {0}'.format(timestamp), fontsize=14)

    filename = 'pdfs\\wt-models-sum-error-{0}.pdf'.format(year)
    save_fig_to_pdf(fig, filename)

    # plt.show()


def main1():
    """
    args = sys.argv[1:]
    this_f = "nba-season-scores-analysis.py"
    if not args:
        sys.exit(1)

    if args[0] > 2012 and args[0] < 2016:
        pass
    """

    def print_dir(dir):
        filenames = os.listdir(dir)
        for f in filenames:
            # to print "filename.txt"
            print(f)
            # to print "dir\filename.txt"
            # print os.path.join(dir, f)
            # to print "\Users\Tony\...\dir\filename.txt
            # print os.path.abspath(os.path.join(dir, f)

    csvs_dir = "csvs\\"
    year_list = [2012, 2013, 2014, 2015]

    print("This script runs analysis for NBA scores for a given season.")
    print("The year is defined as the year for which the playoffs occur")
    print("(i.e. 2016 is the 2015 - 2016 Regular Season).")
    print()
    print("This script can be run for a range of years,")
    print("but at least one year must be given.")
    print("Currently, data is only available for 2012 through 2015.")
    print()
    print("The following is a list of years from which you may choose.")
    print(year_list)
    print()
    print("This script outputs results to csvs in the 'csvs' directory.")
    print("If csvs already exists for a given year, then they")
    print("must be deleted before new ones are created.")
    print()
    answer = ''
    while answer != 'y' or answer != 'n':
        print("Do you want to see a lists of csvs")
        answer = input("currently in the 'csvs' directory? [y/n]: ")
        if answer == 'y':
            print(print_dir(csvs_dir))
            break
        elif answer == 'n':
            break
        else:
            print("Please enter either 'y' or 'n'.")
    year = 0
    year2 = 0
    while year not in year_list:
        year = int(input("Please enter a (start) year: "))
        year2 = year
        if not year in year_list:
            print("Sorry, but you must enter a year from the list of valid years {0}.".format(year_list))
        else:
            if year != year_list[:-1]:
                answer2 = ''
                while answer2 != 'y' or answer != 'n':
                    answer2 = input(
                        "Do you want to run this script for a range of years? [y/n]: ")
                    if answer2 == 'y':
                        while year2 <= year:
                            year2 = int(
                                input("Please enter the end year: "))
                            if year2 <= year:
                                print("You must enter a year greater than {0}".format(year))
                                print("from the list of valid years {0}.".format(year_list))
                        print("You have chosen to run this script for the range")
                        print("of years from {0} to {1}.".format(year, year2))
                        break
                    elif answer2 == 'n':
                        print("You have chosen to run this script only for the year {0}.".format(year))
                        break
                    else:
                        print("Please enter either 'y' or 'n'.")
            elif year == year_list[:-1]:
                print("You have chosen to run this script only for the year {0}.".format(year))
            else:
                print("An unexpected input has been encountered.")
                print("Restarting now.")
                sys.exit(1)

    while year < year2+1:
        main2(year)
        year += 1
        if year > 2015:
            break


def main2(year):

    scores_f = "csvs\\nba-season-scores-{0}.csv".format(year)
    wt_f = "csvs\\nba-season-win-totals-{0}.csv".format(year)

    scores_df = pd.read_csv(scores_f)
    wt_df = pd.read_csv(wt_f, index_col=False)

    all_teams = wt_df['team_abbrv']
    # all_teams = all_teams[:5]

    actual_dict_keys = ['team_abbrv', 'sum_win', 'sum_loss']
    actual_dict = OrderedDict((key, []) for key in actual_dict_keys)

    # must create model_dicts outside of a function because
    # a function cannot return multiple objects
    model_dict_keys = ['game_pick', 'game_pick_correct_flag', 'game_win_flag',
                       'game_loss_flag', 'sum_win', 'sum_loss', 'sum_error', 'wt_pick_correct_flag']
    model1_dict = OrderedDict((key, []) for key in model_dict_keys)
    model2_dict = OrderedDict((key, []) for key in model_dict_keys)
    model3_dict = OrderedDict((key, []) for key in model_dict_keys)
    model4_dict = OrderedDict((key, []) for key in model_dict_keys)

    model3_dict2_keys = ['this_t_mu', 'this_t_mu_mean', 'this_t_sigma', 'this_t_sigma_mean', 'this_t_wt_pick', 'this_t_wt_pick_mean',
                        'other_t_mu', 'other_t_mu_mean', 'other_t_sigma', 'other_t_sigma_mean', 'other_t_wt_pick', 'other_t_wt_pick_mean']
    model3_dict2 = OrderedDict((key, []) for key in model3_dict2_keys)
    model4_dict2 = OrderedDict((key, []) for key in model3_dict2_keys)

    make_model_dicts(year, all_teams, scores_df, wt_df, actual_dict,
                       model1_dict, model2_dict, model3_dict, model4_dict, model3_dict2, model4_dict2)

    timestamp = get_timestamp()

    analysis_df = make_analysis_df(
        model1_dict, model2_dict, model3_dict, model4_dict, model3_dict2, model4_dict2)
    # print analysis_df.head()

    scores_df2 = extend_scores_df(scores_df, analysis_df)
    # print scores_df2.head()

    analysis_summary_df = make_analysis_summary_df(
        actual_dict, model1_dict, model2_dict, model3_dict, model4_dict, model3_dict2, model4_dict2, all_teams, scores_df2)
    # print analysis_summary_df.head()

    analysis_summary_df2 = extend_analysis_summary_df(analysis_summary_df)
    # print analysis_summary_df2.tail()

    save_scores_df_to_csv(scores_df2, year, timestamp)
    save_analysis_summary_df_to_csv(analysis_summary_df2, year, timestamp)

    plot_wt(year, all_teams, wt_df, analysis_summary_df2, timestamp)
    plot_sum_error(year, all_teams, analysis_summary_df2, timestamp)


def main3(year):
    analysis_summary_df2 = get_analysis_summary_df2_from_csv(year)
    all_teams = analysis_summary_df2['team_abbrv']
    # plot_wt(year, all_teams, analysis_summary_df2)
    plot_sum_error(year, all_teams, analysis_summary_df2)


if __name__ == '__main__':
    main1()
    # main2(2015)
    # main3(2015)
