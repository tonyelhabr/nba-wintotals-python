# Created by: Anthony ElHabr
# Purpose: Extract scores for every NBA team for a given season (including current season) from espn.go.com
# Modified from: http://danielfrg.com/blog/2013/04/01/nba-scraping-data/
# Suggestions:
# 1) Rewrite the original code for getting all scores from a previous season
# so that it writes to a DataFrame directly
# 2) Rename 'team_schedule' to 'sched_team'
# TODO: NEED TO RERUN SCRIPT FOR ALL SEASONS BECAUSE THERE WAS AN ERROR
# WITH HOW SCORES WERE RECORDED

# import requests
from urllib.request import urlopen
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
                        scores_dict['home_score'].append(both_scores[1])
                        scores_dict['away_score'].append(both_scores[0])
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
                # pass

        end = datetime.now()
        time_diff = end - start
        print("Finished getting scores for {0} in {1} s".format(team_abbrv, time_diff))

    end_all = datetime.now()
    time_diff_all = end_all - start_all
    print("Finished getting all scores for {0} in {1} s".format(year, time_diff_all))

    for key, value in scores_dict.items():
        print(key, len(value))

    return scores_dict


def make_scores_df(scores_dict):
    return pd.DataFrame(scores_dict)


def save_scores_df_to_csv(scores_f, scores_df, year, timestamp):
    if not os.path.isfile(scores_f):
        scores_df.to_csv(scores_f, index=False)
        print("Created new file '{0}' at {1}.".format(scores_f, timestamp))
    else:
        print("Failed to log data to existing '{0}'' at {1}.".format(scores_f, timestamp))
        print("Please delete the existing file.")


def make_scores_dict_v2(year, url_template, teams_df, scores_f):
    # dateparse = lambda x: datetime.strptime(x, '%m/%d/%Y')
    # scores_df = pd.read_csv(scores_f, parse_dates=['game_date'], date_parser=dateparse)
    scores_df = pd.read_csv(scores_f, na_filter=False, parse_dates=['game_date'])
    scores_df2 = scores_df.loc[(scores_df['home_score'].str.contains('N/A')) & (scores_df['game_date'] < date.today())]


    scores_dict_keys = ['game_id', 'season_yr', 'game_date', 'team_schedule', 'win_flag', 'wins_to_date',
                        'losses_to_date', 'home_flag', 'home_team', 'home_score', 'away_team', 'away_score']
    scores_dict = OrderedDict((key, []) for key in scores_dict_keys)

    start_all = datetime.now()
    new_scores_count = 0
    for index, row in scores_df2.iterrows():
        start = datetime.now()

        sched_team = scores_df2.loc[index, 'team_schedule']
        team_url = teams_df.loc[
            teams_df['team_abbrv'] == sched_team, 'team_url_name'].to_string()

        # r = request.get(url_template.formatrow['home_team'].lower(), year, row['team_url_name'])
        # schedule_table = BeautifulSoup(r.text).table
        url = url_template.format(sched_team.lower(), year, team_url)
        html = urlopen(url)
        soup = BeautifulSoup(html, 'html.parser')

        sched_data = soup.find_all(
            name='tr', attrs={'class': re.compile('row')})

        # schedule_table = soup.table
        for row in sched_data:
            cols = row.find_all('td')

            home_bool = True if cols[1].li.text == 'vs' else False

            other_team = (cols[1].find_all('a')[1]['href'].split('/')[-2])
            home_team = sched_team if home_bool else other_team
            home_team = home_team.upper()

            away_team = sched_team if not home_bool else other_team
            away_team = away_team.upper()

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

            if sched_team == scores_df2.loc[index, 'team_schedule'] and\
                    home_team == scores_df2.loc[index, 'home_team'] and\
                    away_team == scores_df2.loc[index, 'away_team'] and\
                    game_date == scores_df2.loc[index, 'game_date']:

                try:
                    scores_dict['game_id'].append(
                        cols[2].a['href'].split('recap?id=')[1])

                    scores_dict['season_yr'].append(year)
                    scores_dict['game_date'].append(game_date_str)
                    scores_dict['team_schedule'].append(sched_team)
                    scores_dict['home_flag'].append('1' if home_bool else '0')
                    scores_dict['home_team'].append(home_team)
                    scores_dict['away_team'].append(away_team)

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
                            scores_dict['home_score'].append(both_scores[1])
                            scores_dict['away_score'].append(both_scores[0])
                    else:
                        if win_bool:
                            scores_dict['home_score'].append(both_scores[1])
                            scores_dict['away_score'].append(both_scores[0])
                        else:
                            scores_dict['home_score'].append(both_scores[0])
                            scores_dict['away_score'].append(both_scores[1])

                    new_scores_count += 1

                    end = datetime.now()
                    time_diff = end - start
                    print("Finished getting score for {0} at {1} on {2} in {3} s.".format(home_team, away_team, game_date_str, time_diff))

                except Exception as error:
                    # error for games in the past that have been postponed
                    # print error
                    """
                    default_str = 'N/A'
                    scores_dict['game_id'].append(default_str)
                    scores_dict['win_flag'].append(default_str)
                    scores_dict['wins_to_date'].append(default_str)
                    scores_dict['losses_to_date'].append(default_str)
                    scores_dict['home_score'].append(default_str)
                    scores_dict['away_score'].append(default_str)
                    """
                    pass

    end_all = datetime.now()
    time_diff_all = end_all - start_all
    print("Finished getting {0} new scores in {1} s".format(new_scores_count, time_diff_all))

    return scores_dict


def save_scores_df_to_csv_v2(scores_f, scores_df, year, timestamp):
    scores_f_add = 'csvs\\nba-season-scores-{0}-add.csv'.format(year)
    scores_f_temp = 'csvs\\nba-season-scores-{0}-temp.csv'.format(year)
    scores_f_backup = 'csvs\\nba-season-scores-{0}-backup.csv'.format(
        year)

    scores_f_add_text = open(scores_f_add, 'w')
    scores_df.to_csv(scores_f_add, index=False)
    scores_f_add_text.close()
    print("Created new file with game scores to add '{0}' at {1}.".format(scores_f_add, timestamp))

    if not os.path.isfile(scores_f):
        scores_f_text = open(scores_f, 'w')
        scores_df.to_csv(scores_f, index=False)
        scores_f_text.close()
        print("Created new file '{0}' at {1}.".format(scores_f, timestamp))
    else:
        # using the 'with' keyword ensures that the file is closed at the end
        # of the execution of the code
        scores_df = pd.read_csv(
            scores_f_add, na_filter=False, parse_dates=['game_date'])
        scores_df2 = pd.read_csv(scores_f_add, na_filter=False)

        in_file_bool = False

        with open(scores_f, 'rb') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                # skip first row with column headers
                if not row[0] == 'game_id':
                    date_raw = datetime.strptime(row[2], '%m/%d/%Y')
                    game_date = date(
                        date_raw.year, date_raw.month, date_raw.day)
                    if row[9] == 'N/A' and game_date < date.today():
                        print("Found game for which to get score.")
                        in_file_bool = True
                        break

        answer = ''
        if not in_file_bool:
            print("Cannot find game for which to get score in existing '{0}'.".format(scores_f))
        else:
            while answer != 'y' or answer != 'n':
                answer = input(
                    "Do you want to get scores for games that have finished but whose scores have not been recorded? [y/n]: ")
                if answer == 'y':
                    with open(scores_f, 'rb') as f_in, open(scores_f_temp, 'wb') as f_out:
                        reader = csv.reader(f_in, delimiter=',')
                        writer = csv.writer(
                            f_out, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        index = 0
                        for row in reader:
                            if not row[0] == 'game_id':
                                date_raw = datetime.strptime(
                                    row[2], '%m/%d/%Y')
                                game_date = date(
                                    date_raw.year, date_raw.month, date_raw.day)
                                if row[9] == 'N/A' and game_date < date.today() and index < len(scores_df['game_date']):
                                    writer.writerow(scores_df2.iloc[index])
                                    index += 1
                                else:
                                    writer.writerow(row)
                            elif row[0] == 'game_id':
                                # write column headers in first row
                                writer.writerow(row)

                    if os.path.isfile(scores_f_backup):
                        os.remove(scores_f_backup)
                    os.rename(scores_f, scores_f_backup)
                    os.rename(scores_f_temp, scores_f)
                    print("Appended new data to existing '{0}' at {1}.".format(scores_f, timestamp))
                    break
                elif answer == 'n':
                    print("Chose not to get new data in existing '{0}' at {1}.".format(scores_f, timestamp))
                    break
                else:
                    print("Please enter either 'y' or 'n'.")

    log_f = 'csvs\\nba-season-scores-log-{0}.txt'.format(year)

    if not os.path.isfile(log_f):
        log_f_text = open(log_f, 'w')
        log_f_text.write("Created new file at {0}.\n".format(timestamp))
        log_f_text.close()
    else:
        with open(log_f, 'a') as f:
            if not in_file_bool:
                f.write(
                    "Did not find data for which to get scores at {0}.\n".format(timestamp))
            else:
                if answer == 'y':
                    f.write("Appended new data at {0}.\n".format(timestamp))
                if answer == 'n':
                    f.write(
                        "Chose not to get new data at {0}.\n".format(timestamp))

            print("Logging timestamp to '{0}' at {1}.".format(log_f, timestamp))


def main1():
    year = 2016
    url_template = "http://espn.go.com/nba/team/schedule/_/name/{0}/year/{1}/{2}"
    teams_f = "csvs\\nba-teams.csv"
    teams_df = pd.read_csv(teams_f, index_col=False)
    all_teams = list(teams_df.team_abbrv.values.flatten())

    timestamp = get_timestamp()

    scores_f = 'csvs\\nba-season-scores-{0}.csv'.format(year)
    if not os.path.isfile(scores_f):
        print("Creating new file '{0}'.".format(scores_f))

        scores_dict = make_scores_dict(year, url_template, teams_df)

        scores_df = make_scores_df(scores_dict)

        save_scores_df_to_csv(scores_f, scores_df, year, timestamp)

    else:
        print("Updating existing '{0}' with new game scores.".format(scores_f))

        scores_dict = make_scores_dict_v2(
            year, url_template, teams_df, scores_f)

        scores_df = make_scores_df(scores_dict)

        save_scores_df_to_csv_v2(scores_f, scores_df, year, timestamp)



if __name__ == '__main__':
    main1()
