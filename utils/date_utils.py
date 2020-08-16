import pandas
from datetime import date, timedelta, datetime


def get_dates_from_week(yfs, week):
    data = yfs.get_game_weeks()[1]['game_weeks']
    start = data[str(week - 1)]['game_week']['start']
    end = data[str(week - 1)]['game_week']['end']
    return get_date_range(start, end)


def get_date_range(start, end):
    return pandas.date_range(start, end)


def get_todays_date():
    return str(date.today())


def convert_to_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').date()


def get_next_date(date):
    return date + timedelta(days=1)


def get_prev_date(date):
    return date - timedelta(days=1)
