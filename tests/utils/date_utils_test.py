import json
import pytest
import pytest_mock

from datetime import datetime
from keeper_website.utils import date_utils


def test_get_date_range():
    start = '2020-02-01'
    end = '2020-02-28'
    date_range = date_utils.get_date_range(start, end)
    assert len(date_range) == 28
    assert date_range[0] == datetime.strptime(start, '%Y-%m-%d')
    assert date_range[-1] == datetime.strptime(end, '%Y-%m-%d')


def test_get_dates_from_week(mocker):
    yfs = mocker.Mock()
    mocker.patch.object(yfs, 'get_game_weeks')

    with open('tests/utils/resources/game_weeks_payload.json') as f:
        yfs.get_game_weeks.return_value = json.loads(f.read())

    date_range = date_utils.get_dates_from_week(yfs, 1)
    assert date_range[0] == datetime.strptime('2019-10-02', '%Y-%m-%d')
    assert date_range[-1] == datetime.strptime('2019-10-13', '%Y-%m-%d')
