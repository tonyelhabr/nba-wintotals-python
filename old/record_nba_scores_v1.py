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
            team_abbrv.lower(), year, row['team_url_name'])
        html = urlopen(url)
        soup = BeautifulSoup(html, 'html.parser')

        # schedule_table = soup.table
        sched_data = soup.find_all(
            name='tr', attrs={'class': re.compile('row')})

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
                # error for games in the future that have not been played
                # error for games in the past that have been postponed
                # print error
                default_str = 'N/A'
                scores_dict['game_id'].append(default_str)
                scores_dict['win_flag'].append(default_str)
                scores_dict['wins_to_date'].append(default_str)
                scores_dict['losses_to_date'].append(default_str)
                scores_dict['home_score'].append(default_str)
                scores_dict['away_score'].append(default_str)

        end = datetime.now()
        time_diff = end - start
        print "Finished getting scores for {0} in {1} s".format(team_abbrv, time_diff)

    end_all = datetime.now()
    time_diff_all = end_all - start_all
    print "Finished getting all scores for {0} in {1} s".format(year, time_diff_all)

    return scores_dict


def make_scores_df(scores_dict):
    return pd.DataFrame(scores_dict)


def save_scores_df_to_csv(scores_f, scores_df, year, timestamp):
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
    all_teams = list(teams_df.team_abbrv.values.flatten())

    timestamp = get_timestamp()

    scores_f = 'csvs\\nba-season-scores-{0}.csv'.format(year)
    if not os.path.isfile(scores_f):
        print "Creating new file '{0}'.".format(scores_f)

        scores_dict = make_scores_dict(year, url_template, teams_df)

        scores_df = make_scores_df(scores_dict)

        save_scores_df_to_csv(scores_f, scores_df, year, timestamp)
    else:
        # dateparse = lambda x: datetime.strptime(x, '%m/%d/%Y')
        # scores_df = pd.read_csv(scores_f, na_filter=False, parse_dates=['game_date'], date_parser=dateparse)
        scores_df = pd.read_csv(
            scores_f, na_filter=False, parse_dates=['game_date'])
        scores_df2 = scores_df.loc[
            (scores_df['home_score'] == 'N/A') & (scores_df['game_date'] < date.today())]
        print "Updating '{0}' with new game scores.".format(scores_f)
        scores_df2 = scores_df2.iloc[:5]

        start_all = datetime.now()
        new_scores_count = 0
        for index, row in scores_df2.iterrows():
            start = datetime.now()

            home_team = scores_df2.loc[index, 'home_team']
            team_url_name = teams_df.loc[
                teams_df['team_abbrv'] == home_team, 'team_url_name'].to_string()

            # r = request.get(url_template.formatrow['home_team'].lower(), year, row['team_url_name'])
            # schedule_table = BeautifulSoup(r.text).table
            url = url_template.format(home_team.lower(), year, team_url_name)
            html = urlopen(url)
            soup = BeautifulSoup(html, 'html.parser')

            sched_data = soup.find_all(
                name='tr', attrs={'class': re.compile('row')})

            # schedule_table = soup.table
            for row in sched_data:
                cols = row.find_all('td')

                other_team = (
                    cols[1].find_all('a')[1]['href'].split('/')[-2]).upper()

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
                    # exception for leap year
                    date_fixed = date(year, 2, 29)

                game_date_str = date_fixed.strftime('%m/%d/%Y')
                game_date = datetime.strptime(game_date_str, '%m/%d/%Y')

                if other_team == scores_df2.loc[index, 'away_team'] and\
                        game_date == scores_df2.loc[index, 'game_date']:
                    try:
                        scores_df2.loc[index, 'game_id'] = cols[
                            2].a['href'].split('recap?id=')[1]
                        win_bool = True if cols[2].span.text == 'W' else False
                        scores_df2.loc[
                            index, 'win_flag'] = '1' if win_bool else '0'

                        wl_record = cols[3].text.split('-')
                        scores_df2.loc[index, 'wins_to_date'] = wl_record[0]
                        scores_df2.loc[index, 'losses_to_date'] = wl_record[1]

                        new_scores_count += 1

                        end = datetime.now()
                        time_diff = end - start
                        print "Finished getting score for {0} at {1} on {2} in {3} s.".format(home_team, other_team, game_date_str, time_diff)

                    except Exception as error:
                        # Error for games in the past that have been postponed
                        # print error
                        pass

        end_all = datetime.now()
        time_diff_all = end_all - start_all
        print "Finished getting {0} new scores in {1} s".format(new_scores_count, time_diff_all)


if __name__ == '__main__':
    main1()
