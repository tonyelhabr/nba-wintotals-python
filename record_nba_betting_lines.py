# Created by: Anthony ElHabr
# Purpose: Extract NBA betting lines from espn.go.com

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


def get_game_date(date_raw, year):
    date_raw2 = date_raw[re.search(', ', date_raw).end():]

    game_date = datetime.strptime(date_raw2, '%B %d')
    return game_date.replace(year=year)

def make_data_dict(all_data, sportsbooks_count):
    data_nested = []
    for row in range(len(all_data)):
        row_extended = []

        for col in all_data[row].find_all('td', recursive=False):
            row_extended.append(col.text)

        data_nested.append(row_extended)

    """
    # example of data_nested
    [[u'Oklahoma City at Boston, 7:00 PM ET (608)'],
     [u'Westgate',
      u'-5+5OKC: -110BOS: -110',
      u'220o: -110u: -110',
      u'OKC: -210BOS: +180'],
     [u'PinnacleSports.com',
      u'-5+5OKC: 100BOS: -110',
      u'220o: -105u: -105',
      ...
        u'OKC: -210BOS: +180'],
     [u'SportsBetting.ag',
      u'EVEN',
      utie_str,
      u'OKC: 0BOS: 0'],
     [u'Preview \xbb PickCenter  \xbb '],
     [u'Orlando at Charlotte, 7:00 PM ET (602)'],
     [u'Westgate',
      u'+9.5-9.5ORL: -110CHA: -110',
      ...
      u'221.5o: -110u: -110',
      u'NY: +1375GS: -2200'],
     [u'SportsBetting.ag', u'EVEN', utie_str, u'NY: 0GS: 0'],
     [u'Preview \xbb PickCenter  \xbb ']]
     """

    # convert data_nested to a dict
    # key is "away_team_city at home_team_city... (rotation_num)"
    # value for each key is a list comprised of 6 lists (one for
    # each sportsbook), each having 4 elements:
    # 1) sportsbook_name
    # 2) away/home_spread, away/home_spread_payout
    # 3) point_total, away/home_team, over/under_payout
    # 4) away/home_team, away/home_moneyline
    data_dict = {}
    # +1 here to account for the "Preview" table data cell
    # that is not stored in data_dict
    data_table_cols_num = 1 + sportsbooks_count

    for i in range(0, len(data_nested), data_table_cols_num+1):
        data_table = []
        for j in range(1, data_table_cols_num):
            data_table.append(data_nested[i+j])

        key = "".join(data_nested[i])
        data_dict[key] = data_table

    """
    # example of data_dict
    # note that the matchups have been reorded because a dict uses hashing
    {u'Atlanta at Detroit, 7:30 PM ET (610)':
   [[u'Westgate',
     u'EVEN',
     u'199.5o: -110u: -110',
     u'ATL: -110DET: -110'],
    [u'PinnacleSports.com',
     u'+1-1ATL: -106DET: -104',
     u'199.5o: -105u: -105',
   ...
    [u'SportsBetting.ag',
     u'EVEN',
     utie_str,
     u'ATL: 0DET: 0']],
     u'Bulls at Washington, 7:00 PM ET (606)':
   [[u'Westgate',
     u'+5-5CHI: -110WSH: -110',
     ...
     u'212o: -110u: -110',
     u'ORL: +430CHA: -525'],
    [u'SportsBetting.ag',
     u'EVEN', utie_str,
     u'ORL: 0CHA: 0']]}
   """

    return data_dict


def make_matchup_dict(data_dict, sportsbooks_count, timestamp, game_date):
    matchup_dict_keys = ['timestamp', 'away_team_city', 'home_team_city', 'game_date', 'rotation_num', 'sportsbook_name', 'away_team', 'home_team', 'away_spread', 'home_spread', 'away_spread_payout', 'home_spread_payout', 'point_total', 'over_payout', 'under_payout', 'away_moneyline', 'home_moneyline']
    matchup_dict = OrderedDict((key, []) for key in matchup_dict_keys)

    tie_str = 'N/A'

    # number of keys = number of games
    for key in data_dict:
        # debugging check
        if re.search('\)', key[-1]) == 'None':
            print(key)

        for i in range(sportsbooks_count):

            matchup_dict['timestamp'].append(timestamp)

            matchup_dict['game_date'].append(game_date)
            # example of string to parse:
            # u'Cleveland at Sacramento, 10:00 PM ET (514)'
            matchup_dict['away_team_city'].append(
                key[:re.search(' at', key).start()])

            matchup_dict['away_team_city'].append(
                key[re.search(' at ', key).end():re.search(', ', key).start()])

            matchup_dict['rotation_num'].append(
                key[re.search('\(', key).end():-1])

            # example of string to parse:
            # u'CLE: -275SAC: +225'
            matchup_dict['away_team'].append(
                data_dict[key][i][3][:re.search('[A-Z]: ', data_dict[key][i][3]).start()+1])

            matchup_dict['home_team'].append(data_dict[key][i][3][re.search(
                '[0-9][A-Z]', data_dict[key][i][3]).start()+1:re.search('[0-9][A-Z]+:', data_dict[key][i][3]).end()-1])

            # example of string to parse:
            # u'Westgate'
            matchup_dict['sportsbook_name'].append(data_dict[key][i][0])

            # example of string to parse:
            # u'-7+7CLE: -105SAC: -115'
            if data_dict[key][i][1] != 'EVEN':
                matchup_dict['away_spread'].append(
                    data_dict[key][i][1][:re.search('[0-9][+-]', data_dict[key][i][1]).start()+1])

                matchup_dict['home_spread'].append(data_dict[key][i][1][re.search(
                    '[0-9][+-][0-9]', data_dict[key][i][1]).start()+1:re.search('[0-9][+-]([0-9]+)', data_dict[key][i][1]).end()])

                matchup_dict['away_spread_payout'].append(data_dict[key][i][1][re.search(
                    ': [+-]*[0-9]+[A-Z]', data_dict[key][i][1]).start()+2:re.search(': [+-]*[0-9]+[A-Z]', data_dict[key][i][1]).end()-1])

                matchup_dict['home_spread_payout'].append(
                    data_dict[key][i][1][re.search(': [+-]*[0-9]+[A-Z]+: ', data_dict[key][i][1]).end():])
            else:
                matchup_dict['away_spread'].append(tie_str)
                matchup_dict['home_spread'].append(tie_str)

                matchup_dict['away_spread_payout'].append(tie_str)
                matchup_dict['home_spread_payout'].append(tie_str)

            # example of string to parse:
            # u'217o: -110u: -110'
            if data_dict[key][i][2] != tie_str:
                matchup_dict['point_total'].append(
                    data_dict[key][i][2][:re.search('o: ', data_dict[key][i][2]).start()])

                matchup_dict['over_payout'].append(data_dict[key][i][2][re.search(
                    'o: ', data_dict[key][i][2]).end():re.search('u', data_dict[key][i][2]).start()])

                matchup_dict['under_payout'].append(
                    data_dict[key][i][2][re.search('u: ', data_dict[key][i][2]).end():])
            else:
                matchup_dict['point_total'].append(tie_str)
                matchup_dict['over_payout'].append(tie_str)
                matchup_dict['under_payout'].append(tie_str)

            # example of string to parse:
            # u'CLE: -275SAC: +225'
            if (data_dict[key][i][3][re.search(
                '[A-Z]+: ', data_dict[key][i][3]).end():re.search('[0-9][A-Z]+:', data_dict[key][i][3]).start()+1]) != 0:
                matchup_dict['away_moneyline'].append(data_dict[key][i][3][re.search(
                    '[A-Z]+: ', data_dict[key][i][3]).end():re.search('[0-9][A-Z]+:', data_dict[key][i][3]).start()+1])
            else:
                matchup_dict['away_moneyline'].append(tie_str)
            if (data_dict[key][i][3][re.search('[0-9][A-Z]+: ', data_dict[key][i][3]).end():]) != 0:
                matchup_dict['home_moneyline'].append(
                data_dict[key][i][3][re.search('[0-9][A-Z]+: ', data_dict[key][i][3]).end():])
            else:
                matchup_dict['home_moneyline'].append(tie_str)

    return matchup_dict


def make_matchup_df(matchup_dict):
    matchup_dict_keys = []
    matchup_dict_vals = []

    matchup_dict_keys.append(list(matchup_dict.keys())[0])
    matchup_dict_vals.append(list(matchup_dict.values())[0])
    matchup_dict_items = list(matchup_dict.items())
    # ignore 'away/home_team_city' items
    for key, value in matchup_dict_items[3:]:
        matchup_dict_keys.append(key)
        matchup_dict_vals.append(value)

    matchup_dict2 = OrderedDict(list(zip(matchup_dict_keys, matchup_dict_vals)))
    return pd.DataFrame(matchup_dict2)


def save_matchup_df_to_csv(bet_f, matchup_df, year, timestamp):
    # TODO: update this so it is more like save_bet_df2_to_csv from
    # run-nba-betting-lines-analysis.py

    bet_f_temp = 'csvs\\nba-betting-lines-{0}-temp-for-record.csv'.format(year)
    bet_f_backup = 'csvs\\nba-betting-lines-{0}-backup-for-record.csv'.format(year)

    in_file_bool = False

    if not os.path.isfile(bet_f):
        bet_f_text = open(bet_f, 'w')
        matchup_df.to_csv(bet_f, index=False)
        bet_f_text.close()
        print("Created new file '{0}' at {1}.".format(bet_f, timestamp))
    else: 
        # using the 'with' keyword ensures that the file is closed at the end
        # of the execution of the code
        timestamp_date = timestamp[:re.search('-', timestamp).start()]

        with open(bet_f, 'rb') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                # skip the first row with column headers
                if not row[1] == 'game_date':
                    try:
                        date_raw = datetime.strptime(row[1], '%m/%d/%Y')
                    except:
                        date_raw = datetime.strptime(row[1], '%Y-%d-%m')
                    game_date = date_raw.strftime('%m/%d/%Y')
                    if game_date == timestamp_date:
                        print("Found game that already has data.")
                        in_file_bool = True
                        break

        answer = ''
        answer2 = ''
        if not in_file_bool:
            while answer != 'y' or answer != 'n':
                answer = input("Do you want to append new data? [y/n]: ")
                if answer == 'y':
                    with open(bet_f, 'rb') as f_in, open(bet_f_backup, 'wb') as f_out:
                        reader = csv.reader(f_in, delimiter=',')
                        writer = csv.writer(f_out, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        for row in reader:
                            writer.writerow(row)

                    matchup_df.to_csv(bet_f, mode='a', header=False, index=False)
                    print("Appended new data to existing '{0}' at {1}.".format(bet_f, timestamp))
                    break
                elif answer == 'n':
                    print("Chose not to append new data.")
                    break
                else:
                    print("Please enter either 'y' or 'n'.")
        else:
            print("There is no new data to record.")
            while answer != 'y' or answer != 'n':
                answer = input("Do you want to append redundant data or overwrite data for today? [y/n]: ")
                if answer == 'y':
                    while answer2 != 'a' or answer2 != 'w':
                        answer2 = input("Do you want to append or overwrite data for today? [a/w]: ")
                        in_file_bool2 = False
                        if answer2 == 'a':
                            matchup_df.to_csv(bet_f, mode='a', header=False, index=False)
                            print("Appended redundant data to existing '{0}' at {1}.".format(bet_f, timestamp))
                            break
                        elif answer2 == 'w':
                            with open(bet_f, 'rb') as f_in, open(bet_f_temp, 'wb') as f_out:
                                reader = csv.reader(f_in, delimiter=',')
                                writer = csv.writer(f_out, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                                for row in reader:
                                    if row[1] == timestamp_date:
                                        in_file_bool2 = True
                                    else:
                                        writer.writerow(row)
                                    if in_file_bool2:
                                        break

                            if os.path.isfile(bet_f_backup):
                                os.remove(bet_f_backup)
                            os.rename(bet_f, bet_f_backup)
                            os.rename(bet_f_temp, bet_f)
                            matchup_df.to_csv(bet_f, mode='a', header=False, index=False)
                            print("Overwrote data in existing '{0}' at {1}.".format(bet_f, timestamp))
                            break
                        else:
                            print("Please enter either 'a' or 'w'.")
                    break
                elif answer == 'n':
                    print("Chose not to log redundant data to existing '{0}' at {1}.".format(bet_f, timestamp))
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
                if answer == 'y':
                    f.write("Appended new data at {0}.\n".format(timestamp))
                elif answer == 'n':
                    f.write("Chose not to append new data at {0}.\n".format(timestamp))
            else:
                if answer == 'y':
                    if answer2 == 'a':
                        f.write("Appended redundant data at {0}.\n".format(timestamp))
                    elif answer2 == 'w':
                        f.write("Overwrote data at {0}.\n".format(timestamp))
                elif answer == 'n':
                    f.write("Chose not to log redundant data at {0}.\n".format(timestamp))

            print("Logging timestamp to '{0}' at {1}.".format(log_f, timestamp))


def main1():
    year = 2016
    sportsbooks = ['Westage', 'PinnacleSports.com', '5Dimes.eu',
                   'BOVADA.lv', 'BETONLINE.ag', 'SportsBetting.ag']
    sportsbooks_count = len(sportsbooks)
    url = "http://www.espn.go.com/nba/lines"
    # r = requests.get(url)
    # all_data = BeautifulSoup(r.text)
    html = urlopen(url)
    soup = BeautifulSoup(html, 'html.parser')

    all_data = soup.find_all(
        name='tr', attrs={'class': ['oddrow', 'evenrow', 'stathead']})

    timestamp = get_timestamp()

    date_raw = soup.find('h1').text
    game_date = get_game_date(date_raw, year)

    data_dict = make_data_dict(all_data, sportsbooks_count)

    matchup_dict = make_matchup_dict(data_dict, sportsbooks_count, timestamp, game_date)

    matchup_df = make_matchup_df(matchup_dict)

    bet_f = 'csvs\\nba-betting-lines-{0}.csv'.format(year)
    save_matchup_df_to_csv(bet_f, matchup_df, year, timestamp)


if __name__ == '__main__':
    main1()
