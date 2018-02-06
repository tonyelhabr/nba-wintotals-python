# Created by: Anthony ElHabr
# Purpose: Extract scores for every NBA team for a given season (including current season) from espn.go.com
# Modified from: http://danielfrg.com/blog/2013/04/01/nba-scraping-data/

# import requests
from urllib2 import urlopen
import pandas as pd
from bs4 import BeautifulSoup
import re
import os
from collections import OrderedDict
from datetime import datetime, date
import csv


def get_timestamp():
    timestamp = datetime.now()
    return timestamp.strftime('%m/%d/%Y-%H:%M:%S')


def make_scores_dict(year, url_template, teams_df):
    scores_dict_keys = ['game_id', 'season_yr', 'game_date', 'team_schedule', 'win_flag', 'wins_to_date',
                       'losses_to_date', 'home_flag', 'home_team', 'home_score', 'away_team', 'away_score']
    scores_dict = OrderedDict((key, []) for key in scores_dict_keys)

    start_all = datetime.now()
    for index, row in teams_df.iterrows():
        start = datetime.now()

        team_abbrv = row['team_abbrv']

        # r = request.get(url_template.formatrow['team_abbrv'].lower(), year, row['team_url_name'])
        # schedule_table = BeautifulSoup(r.text).table
        url = url_template.format(
            row['team_abbrv'].lower(), year, row['team_url_name'])
        html = urlopen(url)
        soup = BeautifulSoup(html, 'html.parser')

        # schedule_table = soup.table
        # sched_data = soup.find_all(name='tr', attrs={'class':re.compile('oddrow'), 'class':re.compile('evenrow')})
        sched_data = soup.find_all(
            name='tr', attrs={'class': re.compile('row')})

        # function call here
        for row in sched_data:
            cols = row.find_all('td')

            scores_dict['season_yr'].append(year)

            try:
                date_raw = cols[0].text
                date_nums = datetime.strptime(date_raw, '%a, %b %d')
                date_month = date_nums.month
                date_day = date_nums.day

                if date_month > 7:
                    date_fixed = date(year-1, date_month, date_day)
                else:
                    date_fixed = date(year, date_month, date_day)
            except Exception as error:
                # print error
                # error = "day is out of range for month"
                # exception for leap year
                date_fixed = date(year, 2, 29)

            game_date = date_fixed.strftime('%m/%d/%Y')
            scores_dict['game_date'].append(game_date)

            scores_dict['team_schedule'].append(team_abbrv)

            home_bool = True if cols[1].li.text == 'vs' else False
            scores_dict['home_flag'].append('1' if home_bool else '0')

            # text == '@' if team is away_team
            # other_team = cols[1].find_all('a')[1].text
            other_team_abbrv = cols[1].find_all('a')[1]['href'].split('/')[-2]

            home_team = team_abbrv if home_bool else other_team_abbrv
            home_team = home_team.upper()
            scores_dict['home_team'].append(home_team)

            away_team = team_abbrv if not home_bool else other_team_abbrv
            away_team = away_team.upper()
            scores_dict['away_team'].append(away_team)

            try:
                scores_dict['game_id'].append(
                    cols[2].a['href'].split('recap?id=')[1])

                win_bool = True if cols[2].span.text == 'W' else False
                scores_dict['win_flag'].append('1' if win_bool else '0')

                wl_record = cols[3].text.split('-')
                scores_dict['wins_to_date'].append(wl_record[0])
                scores_dict['losses_to_date'].append(wl_record[1])

                # split(' ') is to ignore possible 'OT' label
                both_scores = cols[2].a.text.split(' ')[0].split('-')
                if home_bool:
                    if win_bool:
                        scores_dict['home_score'].append(both_scores[0])
                        scores_dict['away_score'].append(both_scores[1])
                    else:
                        scores_dict['home_score'].append(both_scores[0])
                        scores_dict['away_score'].append(both_scores[1])
                else:
                    if win_bool:
                        scores_dict['home_score'].append(both_scores[1])
                        scores_dict['away_score'].append(both_scores[0])
                    else:
                        scores_dict['home_score'].append(both_scores[0])
                        scores_dict['away_score'].append(both_scores[1])
            except Exception as error:
                # print error
                default_val = 'N/A'
                scores_dict['game_id'].append(default_val)
                scores_dict['win_flag'].append(default_val)
                scores_dict['wins_to_date'].append(default_val)
                scores_dict['losses_to_date'].append(default_val)
                scores_dict['home_score'].append(default_val)
                scores_dict['away_score'].append(default_val)

        end = datetime.now()
        time_diff = end - start
        print "Finished getting scores for {0} in {1} s".format(team_abbrv, time_diff)

    end_all = datetime.now()
    time_diff_all = end_all - start_all
    print "Finished getting all scores for {0} in {1} s".format(year, time_diff_all)

    return scores_dict


def make_scores_df(scores_dict):
    return pd.DataFrame(scores_dict)


def save_scores_df_to_csv(scores_df, year, timestamp):
    scores_f = 'csvs\\nba-season-scores-{0}.csv'.format(year)
    if not os.path.isfile(scores_f):
        scores_df.to_csv(scores_f, index=False)
        print "Created new file '{0}' at {1}.".format(scores_f, timestamp)
    else:
        print "Failed to log data to existing '{0}'' at {1}.".format(scores_f, timestamp)
        print "Please delete the existing file."


def main1():
    year = 2016
    sportsbooks = ['Westage', 'PinnacleSports.com', '5Dimes.eu',
                   'BOVADA.lv', 'BETONLINE.ag', 'SportsBetting.ag']
    url_template = "http://espn.go.com/nba/team/schedule/_/name/{0}/year/{1}/{2}"
    teams_f = "csvs\\nba-teams.csv"
    teams_df = pd.read_csv(teams_f, index_col=False)

    timestamp = get_timestamp()

    scores_f = 'csvs\\nba-season-scores-{0}.csv'.format(year)
    if not os.path.isfile(scores_f):
        # MAYBEDO: make this main2
        print "Creating new file '{0}'.".format(scores_f)

        scores_dict = make_scores_dict(year, url_template, teams_df)

        scores_df = make_scores_df(scores_dict)

        save_scores_df_to_csv(scores_df, year, timestamp)
    else:
        # MAYBEDO: make this main3
        # TODO:
        # 1) find games in betting_df without scores recorded
        # 2) record scores
        # 3) calculate betting line results
        # teams_df = pd.read_csv(teams_f, index_col=False, usecols=['team_abbrv'])
        all_teams = list(teams_df.team_abbrv.values.flatten())

        scores_f = "csvs\\nba-season-scores-{0}.csv".format(year)
        scores_df = pd.read_csv(scores_f)


        betting_f = 'csvs\\nba-betting-lines2.csv'
        betting_df = pd.read_csv(betting_f, index_col=False, na_filter=False)
        betting_df2 = betting_df.loc[betting_df['home_score'] == '']
        betting_df2 = betting_df2[:5*6:6]

        """
        actual_dict_keys = ['home_score', 'away_score']
        actual_dict = OrderedDict((key, []) for key in actual_dict_keys)
        result_dict_keys = ['spread_pick', 'spread_diff', 'spread_payout', 'point_total_pick', 'point_total_payout', 'moneyline_pick', 'moneyline_payout']
        correct_dict = OrderedDict(("correct_"+key, []) for key in result_dict_keys)
        incorrect_dict = OrderedDict(("incorrect_"+key, []) for key in result_dict_keys)
        """

        for index, row in betting_df2.iterrows():
            tie_val = 'N/A'

            home_team = row.home_team
            away_team = row.away_team
            game_date = row.game_date
            # need to reformat game_date because it is stripped of leading 0's
            game_date = datetime.strptime(game_date, '%m/%d/%Y')
            game_date = game_date.strftime('%m/%d/%Y')

            game_df = scores_df.loc[(scores_df.team_schedule == home_team) & (scores_df.away_team == away_team) & (scores_df.game_date == game_date)]

            home_score = row.home_score = float(game_df.home_score)
            away_score = row.away_score = float(game_df.away_score)

            print game_date, away_team, home_team, home_score, away_score

            # TODO: make the following operation functions
            # 1) 1 big apply function called 'calculate' that takes the row (i.e. pandas series)
            # 2) 3 internal apply function calls (called 'calculate_spread_result', 'calculate_point_total_result', and 'calculate_moneyline_result')
            # NOTE (about pandas functions): apply works on a row / column basis of a DataFrame, applymap works element-wise on a DataFrame, and map works element-wise on a Series.

            try:
                home_spread = float(row.home_spread)
                spread_num = home_score + home_spread - away_score
                if spread_num > 0:
                    row.correct_spread_pick = home_team
                    row.incorrect_spread_pick = away_team
                    row.correct_spread_pick_diff = spread_num
                    row.incorrect_spread_pick_diff = -spread_num
                    if float(row.home_spread_payout) < 0:
                        row.correct_spread_payout = abs(float(row.home_spread_payout)/100)
                    else:
                        row.correct_spread_payout = float(row.home_spread_payout)
                    row.incorrect_spread_payout = -100
                elif spread_num < 0:
                    row.correct_spread_pick = away_team
                    row.incorrect_spread_pick = home_team
                    row.correct_spread_pick_diff = -spread_num
                    row.incorrect_spread_pick_diff = spread_num
                    if float(row.away_spread_payout) < 0:
                        row.correct_spread_payout = abs(float(row.away_spread_payout)/100)
                    else:
                        row.correct_spread_payout = float(row.away_spread_payout)
                    row.incorrect_spread_payout = -100
                else:
                    row.correct_spread_pick = tie_val
                    row.incorrect_spread_pick = tie_val
                    row.correct_spread_pick_diff = 0
                    row.incorrect_spread_pick_diff = 0
                    row.correct_spread_payout = 0
                    row.incorrect_spread_payout = 0
            except ValueError as error:
                # ValueError: could not convert string to float: N/A
                # for home_spread
                print error
                

            try:
                point_total = float(row.point_total)
                point_total_num = home_score + away_score - point_total

                if point_total_num > 0:
                    row.correct_point_total_pick = 'o'
                    row.incorrect_point_total_pick = 'u'
                    row.correct_point_total_diff = point_total_num
                    row.incorrect_point_total_diff = -point_total_num
                    if float(row.over_payout) < 0:
                        row.correct_point_total_payout = abs(float(row.over_payout)/100)
                    else:
                        row.correct_point_total_payout = float(row.over_payout)
                    row.incorrect_point_total_payout = -100
                elif point_total_num < 0:
                    row.correct_point_total_pick = 'u'
                    row.incorrect_point_total_pick = 'o'
                    row.correct_point_total_diff = -point_total_num
                    row.incorrect_point_total_diff = point_total_num
                    if float(row.under_payout) < 0:
                        row.correct_point_total_payout = abs(float(row.under_payout)/100)
                    else:
                        row.correct_point_total_payout = float(row.under_payout)
                    row.incorrect_point_total_payout = -100
                else:
                    row.correct_point_total_pick = tie_val
                    row.incorrect_point_total_pick = tie_val
                    row.correct_point_total_diff = 0
                    row.incorrect_point_total_diff = 0
                    row.correct_point_total_payout = 0
                    row.incorrect_point_total_payout = 0
            except ValueError as error:
                # ValueError: could not convert string to float: N/A
                # for point_total
                print error



            moneyline_num = home_score - away_score
            if moneyline_num > 0:
                row.correct_moneyline_pick = home_team
                row.incorrect_moneyline_pick = away_team
                row.correct_moneyline_diff = moneyline_num
                row.incorrect_moneyline_diff = -moneyline_num
                if float(row.home_moneyline) < 0:
                    row.correct_moneyline_payout = abs(float(row.home_moneyline)/100)
                elif float(row.home_moneyline) > 0:
                    row.correct_moneyline_payout = float(row.home_moneyline)
                else:
                    row.correct_moneyline_payout = tie_val
                row.incorrect_moneyline_payout = -100
            elif point_total_num < 0:
                row.correct_moneyline_pick = away_team
                row.incorrect_moneyline_pick = home_team
                row.correct_moneyline_diff = -moneyline_num
                row.incorrect_moneyline_diff = moneyline_num
                if float(row.away_moneyline) < 0:
                    row.correct_moneyline_payout = abs(float(row.awat_moneyline_payout)/100)
                elif float(row.away_moneyline) > 0:
                    row.correct_moneyline_payout = float(row.away_moneyline)
                else:
                    row.correct_moneyline_payout = tie_val
                row.incorrect_moneyline_payout = -100
            else:
                    row.correct_moneyline_pick = tie_val
                    row.incorrect_moneyline_pick = tie_val
                    row.correct_moneyline_diff = 0
                    row.incorrect_moneyline_diff = 0
                    row.correct_moneyline_payout = 0
                    row.incorrect_moneyline_payout = 0

            print row
            

        print betting_df2.iloc[:,[1,4,5,15,16]]


if __name__ == '__main__':
    main1()
