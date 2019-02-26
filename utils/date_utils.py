import pandas
from datetime import date

def get_dates_from_week(yfs, week):
    data = yfs.get_game_weeks()['fantasy_content']['game'][1]['game_weeks']
    start = data[str(week-1)]['game_week']['start']
    end = data[str(week-1)]['game_week']['end']
    return get_date_range(start, end)

def get_date_range(start, end):
    return pandas.date_range(start, end)

def get_todays_date():
    return str(date.today())