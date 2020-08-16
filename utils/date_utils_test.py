import json
import pytest
import pytest_mock

from api import YahooFantasyApi
from datetime import datetime
from utils import date_utils


def test_get_date_range():
    start = '2020-02-01'
    end = '2020-02-28'
    date_range = date_utils.get_date_range(start, end)
    assert len(date_range) == 28
    assert date_range[0] == datetime.strptime(start, '%Y-%m-%d')
    assert date_range[-1] == datetime.strptime(end, '%Y-%m-%d')


GAME_WEEKS_DATA = '''
[{"game_key": "396", "game_id": "396", "name": "Hockey", "code": "nhl", "type": "full", "url": "https://hockey.fantasysports.yahoo.com/hockey", "season": "2019", "is_registration_over": 0, "is_game_over": 0, "is_offseason": 0}, {"game_weeks": {"0": {"game_week": {"week": "1", "display_name": "1", "start": "2019-10-02", "end": "2019-10-13"}}, "1": {"game_week": {"week": "2", "display_name": "2", "start": "2019-10-14", "end": "2019-10-20"}}, "2": {"game_week": {"week": "3", "display_name": "3", "start": "2019-10-21", "end": "2019-10-27"}}, "3": {"game_week": {"week": "4", "display_name": "4", "start": "2019-10-28", "end": "2019-11-03"}}, "4": {"game_week": {"week": "5", "display_name": "5", "start": "2019-11-04", "end": "2019-11-10"}}, "5": {"game_week": {"week": "6", "display_name": "6", "start": "2019-11-11", "end": "2019-11-17"}}, "6": {"game_week": {"week": "7", "display_name": "7", "start": "2019-11-18", "end": "2019-11-24"}}, "7": {"game_week": {"week": "8", "display_name": "8", "start": "2019-11-25", "end": "2019-12-01"}}, "8": {"game_week": {"week": "9", "display_name": "9", "start": "2019-12-02", "end": "2019-12-08"}}, "9": {"game_week": {"week": "10", "display_name": "10", "start": "2019-12-09", "end": "2019-12-15"}}, "10": {"game_week": {"week": "11", "display_name": "11", "start": "2019-12-16", "end": "2019-12-22"}}, "11": {"game_week": {"week": "12", "display_name": "12", "start": "2019-12-23", "end": "2019-12-29"}}, "12": {"game_week": {"week": "13", "display_name": "13", "start": "2019-12-30", "end": "2020-01-05"}}, "13": {"game_week": {"week": "14", "display_name": "14", "start": "2020-01-06", "end": "2020-01-12"}}, "14": {"game_week": {"week": "15", "display_name": "15", "start": "2020-01-13", "end": "2020-01-19"}}, "15": {"game_week": {"week": "16", "display_name": "16", "start": "2020-01-20", "end": "2020-02-02"}}, "16": {"game_week": {"week": "17", "display_name": "17", "start": "2020-02-03", "end": "2020-02-09"}}, "17": {"game_week": {"week": "18", "display_name": "18", "start": "2020-02-10", "end": "2020-02-16"}}, "18": {"game_week": {"week": "19", "display_name": "19", "start": "2020-02-17", "end": "2020-02-23"}}, "19": {"game_week": {"week": "20", "display_name": "20", "start": "2020-02-24", "end": "2020-03-01"}}, "20": {"game_week": {"week": "21", "display_name": "21", "start": "2020-03-02", "end": "2020-03-08"}}, "21": {"game_week": {"week": "22", "display_name": "22", "start": "2020-03-09", "end": "2020-03-15"}}, "22": {"game_week": {"week": "23", "display_name": "23", "start": "2020-03-16", "end": "2020-03-22"}}, "23": {"game_week": {"week": "24", "display_name": "24", "start": "2020-03-23", "end": "2020-04-04"}}, "count": 24}}]
'''


def test_get_dates_from_week(mocker):
    yfs = mocker.Mock()
    mocker.patch.object(yfs, 'get_game_weeks')
    yfs.get_game_weeks.return_value = json.loads(GAME_WEEKS_DATA)
    date_range = date_utils.get_dates_from_week(yfs, 1)
    assert date_range[0] == datetime.strptime('2019-10-02', '%Y-%m-%d')
    assert date_range[-1] == datetime.strptime('2019-10-13', '%Y-%m-%d')
