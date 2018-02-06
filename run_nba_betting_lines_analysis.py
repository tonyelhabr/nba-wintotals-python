# Created by: Anthony ElHabr
# Purpose:

import pandas as pd
import os
from datetime import datetime, date
import csv


def get_timestamp():
    timestamp = datetime.now()
    return timestamp.strftime('%m/%d/%Y-%H:%M:%S')


def calc_bet_param_result(bet_df2, index, row, param, home_score, away_score, game_date):
    home_team = bet_df2.loc[index, 'home_team']
    away_team = bet_df2.loc[index, 'away_team']

    t = 'correct'
    f = 'incorrect'
    tie_str = 'N/A'
    tie_num = 0
    loss_num = -100
    try:
        if param == 'spread' or param == 'moneyline':
            if param == 'spread':
                # will throw exception if home_spread == 'N/A'
                home_spread = float(
                    bet_df2.loc[index, 'home_spread'])
                num = home_score + home_spread - away_score
            elif param == 'moneyline':
                # dummy variables to throw exception
                # will throw exception if away/home_moneyline == 'N/A'
                away_moneyline_payout = float(
                    bet_df2.loc[index, 'away_moneyline_payout'])
                home_moneyline_payout = float(
                    bet_df2.loc[index, 'home_moneyline_payout'])
                num = home_score - away_score
            str1 = home_team
            str2 = away_team
            str3 = 'home'
            str4 = 'away'
        elif param == 'point_total':
            point_total = float(
                bet_df2.loc[index, 'point_total'])
            # will throw exception if point_total == 'N/A'
            num = home_score + away_score - point_total
            str1 = 'o'
            str2 = 'u'
            str3 = 'over'
            str4 = 'under'

        if num > 0:
            bet_df2.loc[
                index, '{0}_{1}_pick'.format(t, param)] = str1
            bet_df2.loc[
                index, '{0}_{1}_pick'.format(f, param)] = str2
            bet_df2.loc[
                index, '{0}_{1}_diff'.format(t, param)] = num
            bet_df2.loc[
                index, '{0}_{1}_diff'.format(f, param)] = -num

            if float(bet_df2.loc[index, '{0}_{1}_payout'.format(str3, param)]) < 0:
                bet_df2.loc[index, '{0}_{1}_payout'.format(t, param)] = float(
                    100*(100/abs(float(bet_df2.loc[index, '{0}_{1}_payout'.format(str3, param)]))))
            else:
                bet_df2.loc[index, '{0}_{1}_payout'.format(t, param)] = float(
                    bet_df2.loc[index, '{0}_{1}_payout'.format(str3, param)])
            bet_df2.loc[
                index, '{0}_{1}_payout'.format(f, param)] = loss_num

        elif num < 0:
            bet_df2.loc[
                index, '{0}_{1}_pick'.format(t, param)] = str2
            bet_df2.loc[
                index, '{0}_{1}_pick'.format(f, param)] = str1
            bet_df2.loc[
                index, '{0}_{1}_diff'.format(t, param)] = -num
            bet_df2.loc[
                index, '{0}_{1}_diff'.format(f, param)] = num

            if float(bet_df2.loc[index, '{0}_{1}_payout'.format(str3, param)]) < 0:
                bet_df2.loc[index, '{0}_{1}_payout'.format(t, param)] = float(
                    100*(100/abs(float(bet_df2.loc[index, '{0}_{1}_payout'.format(str3, param)]))))
            else:
                bet_df2.loc[index, '{0}_{1}_payout'.format(t, param)] = float(
                    bet_df2.loc[index, '{0}_{1}_payout'.format(str3, param)])
            bet_df2.loc[
                index, '{0}_{1}_payout'.format(f, param)] = loss_num

        elif num == 0:
            bet_df2.loc[
                index, '{0}_{1}_pick'.format(t, param)] = tie_str
            bet_df2.loc[
                index, '{0}_{1}_pick'.format(f, param)] = tie_str
            bet_df2.loc[
                index, '{0}_{1}_diff'.format(t, param)] = tie_num
            bet_df2.loc[
                index, '{0}_{1}_diff'.format(f, param)] = tie_num
            bet_df2.loc[
                index, '{0}_{1}_payout'.format(t, param)] = tie_num
            bet_df2.loc[
                index, '{0}_{1}_payout'.format(f, param)] = tie_num
        else:
            print("Could not find score for game on {0}.".format(game_date))
    except ValueError as error:
        # print "Error: '{0}' for game on {1} at DataFrame index {2}.".format(error, game_date, index)
        # error is "ValueError: could not convert string to float: N/A"
        bet_df2.loc[
            index, '{0}_{1}_pick'.format(t, param)] = tie_str
        bet_df2.loc[
            index, '{0}_{1}_pick'.format(f, param)] = tie_str
        bet_df2.loc[
            index, '{0}_{1}_diff'.format(t, param)] = tie_str
        bet_df2.loc[
            index, '{0}_{1}_diff'.format(f, param)] = tie_str
        bet_df2.loc[
            index, '{0}_{1}_payout'.format(t, param)] = tie_str
        bet_df2.loc[
            index, '{0}_{1}_payout'.format(f, param)] = tie_str


def make_bet_df2(bet_f, year):
    teams_f = "csvs\\nba-teams.csv"
    teams_df = pd.read_csv(teams_f, index_col=False)
    # all_teams = list(teams_df.team_abbrv.values.flatten())

    scores_f = "csvs\\nba-season-scores-{0}.csv".format(year)
    scores_df = pd.read_csv(scores_f, na_filter=False, parse_dates=['game_date'])

    bet_df = pd.read_csv(bet_f, index_col=False, na_filter=False, parse_dates=['game_date'])
    bet_df2 = bet_df.loc[bet_df['home_score'] == '']

    start_all = datetime.now()
    for index, row in bet_df2.iterrows():
        tie_val = 'N/A'

        # shorter methods:
        # 1) home_team = row['home_team']
        # 2) home_team = row.home_team
        # NOTE: The above methods are only acceptable for reading values
        # but not for writing values
        home_team = bet_df2.loc[index, 'home_team']
        away_team = bet_df2.loc[index, 'away_team']
        game_date = bet_df2.loc[index, 'game_date']

        # need to reformat game_date because it is stripped of leading 0's
        # game_date = datetime.strptime(game_date, '%m/%d/%Y')
        # game_date = game_date.strftime('%m/%d/%Y')

        game_df = scores_df.loc[(scores_df['team_schedule'] == home_team) & (
            scores_df['away_team'] == away_team) & (scores_df['game_date'] == game_date)]

        # NOTE: Must use bet_df2.loc[index, 'home_score'] instead of
        # row['home_score'] or row.home_score in order to write value to original DataFrame.
        # Other methods simply write to a view of the DataFrame (i.e. a copy of
        # the orignal DataFrame)
        try:
            bet_df2.loc[index, 'home_score'] = float(game_df['home_score'])
            bet_df2.loc[index, 'away_score'] = float(game_df['away_score'])

            home_score = float(game_df['home_score'])
            away_score = float(game_df['away_score'])

            calc_bet_param_result(
                bet_df2, index, row, 'spread', home_score, away_score, game_date)
            calc_bet_param_result(
                bet_df2, index, row, 'point_total', home_score, away_score, game_date)
            calc_bet_param_result(
                bet_df2, index, row, 'moneyline', home_score, away_score, game_date)
        except Exception as error:
            # print "Error: '{0}' for game on {1} at DataFrame index {2}.".format(error, game_date, index)
            # will throw exception if score has not been recorded yet
            # print "Cannot run analysis."
            # print "Cannot find score for {0} at {1} on {2} at index {3}.".format(home_team, away_team, game_date, index)
            print(error)
            pass

    return bet_df2


def save_bet_df2_to_csv(bet_f, bet_df2, year, timestamp):
    bet_f_temp = 'csvs\\nba-betting-lines-{0}-temp-for-analysis.csv'.format(year)
    bet_f_backup = 'csvs\\nba-betting-lines-{0}-backup-for-analysis.csv'.format(year)

    in_file_bool = False

    if not os.path.isfile(bet_f):
        bet_f_text = open(bet_f, 'w')
        bet_df2.to_csv(bet_f, index=False)
        bet_f_text.close()
        print("Created new file '{0}' at {1}.".format(bet_f, timestamp))
    else:
        # using the 'with' keyword ensures that the file is closed at the end
        # of the execution of the code
        with open(bet_f, 'rb') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                # matchup date is in second column
                if row[15] == '':
                    print("Found potential data for which to run analysis.")
                    print("That is, there is some data for which there is no score reported.")
                    print("However, no analysis for a game can be done if there is no score reported yet.")
                    in_file_bool = True
                    break

        answer = ''
        if not in_file_bool:
            bet_df2.to_csv(bet_f, mode='a', header=False, index=False)
            print("Cannot find data for which to run analysis in existing '{0}'.".format(bet_f))
        else:
            while answer != 'y' or answer != 'n':
                answer = input(
                    "Do you want to try to run analysis on this data? [y/n]: ")
                in_file_bool2 = False
                if answer == 'y':
                    with open(bet_f, 'rb') as f_in, open(bet_f_temp, 'wb') as f_out:
                        reader = csv.reader(f_in, delimiter=',')
                        writer = csv.writer(
                            f_out, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        for row in reader:
                            if row[15] == '':
                                in_file_bool2 = True
                            else:
                                writer.writerow(row)
                            if in_file_bool2:
                                break

                    if os.path.isfile(bet_f_backup):
                        os.remove(bet_f_backup)
                    os.rename(bet_f, bet_f_backup)
                    os.rename(bet_f_temp, bet_f)
                    bet_df2.to_csv(bet_f, mode='a', header=False, index=False)
                    print("Appended analyzed data to existing '{0}' at {1}.".format(bet_f, timestamp))
                    break
                elif answer == 'n':
                    print("Chose not to analyze data in existing '{0}' at {1}.".format(bet_f, timestamp))
                    break
                else:
                    print("Please enter either 'y' or 'n'.")

    log_f = 'csvs\\nba-betting-lines-log-{0}.txt'.format(year)

    if not os.path.isfile(log_f):
        log_f_text = open(log_f, 'w')
        log_f_text.write("Created new file at {0}.\n".format(timestamp))
        log_f_text.close()
    else: 
        with open(log_f, 'a') as f:
            if not in_file_bool:
                f.write("Did not find data for which to run analysis at {0}.\n".format(timestamp))
            else:
                if answer == 'y':
                    f.write("Appended analyze data at {0}.\n".format(timestamp))
                if answer == 'n':
                    f.write("Chose not to analyze data at {0}.\n".format(timestamp))

            print("Logging timestamp to '{0}' at {1}.".format(log_f, timestamp))


def main1():
    year = 2016

    timestamp = get_timestamp()

    bet_f = 'csvs\\nba-betting-lines-{0}.csv'.format(year)
    if not os.path.isfile(bet_f):
        print("No file '{0}' exists.".format(bet_f))
    else:
        print("Calculating new results in existing '{0}'.".format(bet_f))

        bet_df2 = make_bet_df2(bet_f, year)

        save_bet_df2_to_csv(bet_f, bet_df2, year, timestamp)


if __name__ == '__main__':
    main1()
