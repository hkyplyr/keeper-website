from flask import Blueprint, render_template, request, url_for, abort, send_file
from sqlalchemy import func, and_, desc
from sqlalchemy.sql.expression import case
from keeper_website.models import Team, Player, PlayerStats, GoalieStats, SelectedPositions, \
    Pick, Draft
from keeper_website.database import db
from keeper_website.utils.date_utils import get_prev_date, get_next_date, convert_to_date, get_todays_date
from keeper_website.utils.json_utils import get_ordinal
import itertools
import csv
import os


bp = Blueprint('bp', __name__)

@bp.route('/')
def index():
    teams = Team.query.all()
    return render_template('index.html', teams=teams)

@bp.route('/player/<player_id>')
def player(player_id):
    teams = Team.query.all()
    player_data = db.session.query(Player.first_name, Player.last_name) \
        .filter(Player.id == player_id).all()
    player_name = f'{player_data[0][0]} {player_data[0][1]}'
    return render_template('player.html', player_name=player_name, teams=teams)

@bp.route('/draft/<clazz>')
def draft(clazz):
    players = Player.query \
        .join(Draft) \
        .add_columns(
            Player.id,
            Player.first_name,
            Player.last_name,
            Draft.team_id,
            Player.positions,
            Player.nhl_team,
            Draft.keeper) \
        .order_by(Draft.pick.asc())
    teams = Team.query.all()
    return render_template(
        'draft.html',
        teams=teams,
        players=players,
        clazz=clazz)


@bp.route('/teams/<team_id>')
def team(team_id):
    team_id = int(team_id)
    if team_id > 12:
        abort(404)

    date = request.args.get('date', type=str)

    if date is None:
        prev_date = prev_url = next_date = next_url = valid_date = None
        max_date = db.session.query(func.max(SelectedPositions.date))
        skaters = db.session.query(Player.id,
                                   func.count(PlayerStats.player_id).label('gp'),
                                   Player.positions.label('pos'),
                                   Player.first_name, Player.last_name,
                                   func.sum(PlayerStats.g).label('g'),
                                   func.sum(PlayerStats.a).label('a'),
                                   func.sum(PlayerStats.g + PlayerStats.a)
                                   .label('p'),
                                   func.sum(PlayerStats.pm).label('pm'),
                                   func.sum(PlayerStats.ppp).label('ppp'),
                                   func.sum(PlayerStats.shp).label('shp'),
                                   func.sum(PlayerStats.sog).label('sog'),
                                   func.sum(PlayerStats.hit).label('hit'),
                                   func.sum(PlayerStats.blk).label('blk'),
                                   func.sum(points_case).label('points'),
                                   Player.keeper_cost
                                   )\
            .outerjoin(PlayerStats, PlayerStats.player_id == Player.id) \
            .join(SelectedPositions, SelectedPositions.player_id == Player.id)\
            .filter(SelectedPositions.team_id == team_id) \
            .filter(SelectedPositions.date == max_date) \
            .filter(Player.positions != 'G') \
            .group_by(
                SelectedPositions.position,
                Player.id,
                Player.first_name,
                Player.last_name,
                Player.positions) \
            .order_by(desc('points'))

        goalies = db.session.query(Player.id,
                                   func.count(GoalieStats.player_id).label('gp'),
                                   Player.positions.label('pos'),
                                   Player.first_name,
                                   Player.last_name,
                                   func.sum(GoalieStats.w).label('w'),
                                   func.sum(GoalieStats.loss).label('l'),
                                   func.sum(GoalieStats.ga).label('ga'),
                                   func.sum(GoalieStats.sv).label('sv'),
                                   func.sum(GoalieStats.so).label('so'),
                                   func.sum(g_points_case).label('points'),
                                   Player.keeper_cost
                                   ) \
            .outerjoin(GoalieStats, GoalieStats.player_id == Player.id) \
            .join(SelectedPositions, SelectedPositions.player_id == Player.id)\
            .filter(SelectedPositions.team_id == team_id) \
            .filter(SelectedPositions.date == max_date) \
            .filter(Player.positions == 'G')\
            .group_by(
                SelectedPositions.position,
                Player.id,
                Player.first_name,
                Player.last_name,
                Player.positions) \
            .order_by(desc('points'))
    else:
        date_query = db.session.query(func.min(SelectedPositions.date)
                                      .label('min'),
                                      func.max(SelectedPositions.date)
                                      .label('max'))\
            .one()
        valid_date = date_query.min if convert_to_date(date) < date_query.min \
            else convert_to_date(date)
        valid_date = date_query.max if valid_date > date_query.max \
            else valid_date

        prev_date = get_prev_date(valid_date)
        next_date = get_next_date(valid_date)
        next_url = None if next_date > date_query.max \
            else url_for('bp.team', team_id=team_id, date=next_date)
        prev_url = None if prev_date < date_query.min \
            else url_for('bp.team', team_id=team_id, date=prev_date)

        skaters = db.session.query(Player.id,
                                   SelectedPositions.position.label('pos'),
                                   Player.first_name,
                                   Player.last_name,
                                   PlayerStats.g,
                                   PlayerStats.a,
                                   PlayerStats.p().label('p'),
                                   PlayerStats.pm,
                                   PlayerStats.ppp,
                                   PlayerStats.shp,
                                   PlayerStats.sog,
                                   PlayerStats.hit,
                                   PlayerStats.blk,
                                   PlayerStats.points) \
            .join(SelectedPositions, SelectedPositions.player_id == Player.id)\
            .outerjoin(
                PlayerStats,
                and_(
                    PlayerStats.player_id == Player.id,
                    PlayerStats.date == SelectedPositions.date)) \
            .filter(SelectedPositions.team_id == team_id) \
            .filter(SelectedPositions.date == valid_date) \
            .filter(Player.positions != 'G') \
            .order_by(player_order_by)

        goalies = db.session.query(Player.id,
                                   SelectedPositions.position.label('pos'),
                                   Player.first_name,
                                   Player.last_name,
                                   GoalieStats.w,
                                   GoalieStats.loss,
                                   GoalieStats.ga,
                                   GoalieStats.sv,
                                   GoalieStats.so,
                                   GoalieStats.points) \
            .join(SelectedPositions, SelectedPositions.player_id == Player.id)\
            .outerjoin(
                GoalieStats,
                and_(
                    GoalieStats.player_id == Player.id,
                    GoalieStats.date == SelectedPositions.date)) \
            .filter(SelectedPositions.team_id == team_id) \
            .filter(SelectedPositions.date == valid_date) \
            .filter(Player.positions == 'G') \
            .order_by(goalie_order_by)

    picks = db.session.query(Pick.original_team_id,
                             Pick.draft_round,
                             Pick.owning_team_id,
                             Team.name) \
        .join(Team, Pick.original_team_id == Team.id) \
        .filter(Pick.owning_team_id == team_id) \
        .order_by(Pick.draft_round)
    
    formatted_picks = []
    for i, pick in enumerate(picks):
        text = f'{get_ordinal(pick.draft_round)}'
        formatted_picks.append(text)

    teams = db.session.query(Team.id, Team.name, Team.manager)\
              .order_by(Team.id)
    return render_template(
        'team.html',
        skaters=skaters,
        goalies=goalies,
        teams=teams,
        picks=formatted_picks,
        team_id=team_id - 1,
        date=valid_date,
        prev_date=prev_date,
        prev_url=prev_url,
        next_date=next_date,
        next_url=next_url)

points_case = case([
    (PlayerStats.points == None, 0),
    (PlayerStats.points != None, PlayerStats.points)
])

g_points_case = case([
    (GoalieStats.points == None, 0),
    (GoalieStats.points != None, GoalieStats.points)
])

player_order_by = case([
    (SelectedPositions.position == 'C', 0),
    (SelectedPositions.position == 'LW', 1),
    (SelectedPositions.position == 'RW', 2),
    (SelectedPositions.position == 'F', 3),
    (SelectedPositions.position == 'D', 4),
    (SelectedPositions.position == 'BN', 5),
    (SelectedPositions.position == 'IR+', 6),
    (SelectedPositions.position == 'IR', 7)])


goalie_order_by = case([
    (SelectedPositions.position == 'G', 0),
    (SelectedPositions.position == 'BN', 1),
    (SelectedPositions.position == 'IR+', 2),
    (SelectedPositions.position == 'IR', 3)])


@bp.route('/skaters')
def skaters():
    page = request.args.get('page', default=0, type=int)
    sort = request.args.get('sort', default="fp", type=str)

    skaters = db.session.query(Player.id,
                               func.count(Player.id).label('gp'),
                               Player.positions,
                               Player.first_name,
                               Player.last_name,
                               func.sum(PlayerStats.g).label('g'),
                               func.sum(PlayerStats.a).label('a'),
                               func.sum(PlayerStats.g + PlayerStats.a)
                               .label('p'),
                               func.sum(PlayerStats.pm).label('pm'),
                               func.sum(PlayerStats.ppp).label('ppp'),
                               func.sum(PlayerStats.shp).label('shp'),
                               func.sum(PlayerStats.sog).label('sog'),
                               func.sum(PlayerStats.hit).label('hit'),
                               func.sum(PlayerStats.blk).label('blk'),
                               func.sum(PlayerStats.points).label('pts')) \
        .join(PlayerStats, PlayerStats.player_id == Player.id) \
        .group_by(
            Player.id,
            Player.first_name,
            Player.last_name,
            Player.positions) \
        .order_by(func.sum(PlayerStats.getColumnForSort(sort)).desc()) \
        .paginate(page, 25, False)
    next_url = url_for('bp.skaters', page=skaters.next_num, sort=sort) \
        if skaters.has_next else None
    prev_url = url_for('bp.skaters', page=skaters.prev_num, sort=sort) \
        if skaters.has_prev else None

    teams = Team.query.all()
    return render_template(
        'skaters.html',
        skaters=skaters.items,
        teams=teams,
        prev_url=prev_url,
        next_url=next_url,
        sort_key=sort)


@bp.route('/goalies')
def goalies():
    page = request.args.get('page', default=0, type=int)
    sort = request.args.get('sort', default='fp', type=str)

    goalies = db.session.query(Player.id,
                               func.count(GoalieStats.player_id).label('gp'),
                               Player.positions, Player.first_name,
                               Player.last_name, func.sum(GoalieStats.w)
                               .label('w'),
                               func.sum(GoalieStats.loss).label('l'),
                               func.sum(GoalieStats.ga).label('ga'),
                               func.sum(GoalieStats.sv).label('sv'),
                               func.sum(GoalieStats.so).label('so'),
                               func.sum(GoalieStats.points).label('pts')) \
        .join(GoalieStats, GoalieStats.player_id == Player.id) \
        .group_by(
            Player.id,
            Player.first_name,
            Player.last_name,
            Player.positions) \
        .order_by(func.sum(GoalieStats.getColumnForSort(sort)).desc()) \
        .paginate(page, 25, False)

    next_url = url_for('bp.goalies', page=goalies.next_num, sort=sort) \
        if goalies.has_next else None
    prev_url = url_for('bp.goalies', page=goalies.prev_num, sort=sort) \
        if goalies.has_prev else None

    teams = Team.query.all()
    return render_template(
        'goalies.html',
        goalies=goalies.items,
        teams=teams,
        prev_url=prev_url,
        next_url=next_url)
    
@bp.route('/keeper-costs')
def keeper_costs():
    filename = f'keeper-costs-{get_todays_date()}.csv'
    filepath = f'reports/{filename}'
    if os.path.exists(filepath):
        print("EXISTS")
        return send_file(filepath, attachment_filename=filename, as_attachment=True, cache_timeout=-1)

    players = db.session.query(Team.name,
                               Player.first_name,
                               Player.last_name,
                               Player.keeper_cost) \
        .join(Player, Player.team_id == Team.id) \
        .order_by(Player.keeper_cost.asc()) \
        .all()
    
    keeper_map = {}
    for player in players:
        team_name = player[0]
        player_name = f'{player[1]} {player[2]}'
        keeper_cost = player[3]

        if team_name not in keeper_map:
            keeper_map[team_name] = []
        keeper_map[team_name].append((player_name, keeper_cost))
    
    rosters = list(itertools.zip_longest(*keeper_map.values(), fillvalue=[None, None]))
    for i, row in enumerate(rosters):
        rosters[i] = [item for sublist in row for item in sublist]

    teams = db.session.query(Team.id, Team.name) \
        .all()
    team_map = {}
    for team in teams:
        team_map[team[0]] = team[1]

    picks = db.session.query(Pick.draft_round,
                             Pick.original_team_id,
                             Pick.owning_team_id) \
        .order_by(Pick.draft_round) \
        .all()
    pick_map = {}
    for pick in picks:
        owner_team = team_map[pick[2]]
        original_team = team_map[pick[1]]
        draft_value = pick[0]
        draft_round = f'{draft_value}{__get_ordinal(draft_value)} Round'
        if original_team != owner_team:
            draft_round = f'{draft_round} ({original_team})'
        if owner_team not in pick_map:
            pick_map[owner_team] = []
        pick_map[owner_team].append((draft_round, draft_value))
    draft_picks = list(itertools.zip_longest(*pick_map.values(), fillvalue=[None, None]))
    for i, row in enumerate(draft_picks):
        draft_picks[i] = [item for sublist in row for item in sublist]



    teams = []
    for team in keeper_map.keys():
        teams.append(team)
        teams.append(None)

    with open(filepath, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(teams)
        writer.writerows(rosters)
        writer.writerows(draft_picks)

    return send_file(filepath, attachment_filename=filename, as_attachment=True, cache_timeout=-1)

def __get_ordinal(value):
    """Provides the ordinal value for a given integer
    For example `1` returns 'st', `2` returns 'nd', etc.

    Keyword arguments:
    value -- the integer used to retrieve the ordinal
    """
    value = int(value)
    if value % 100//10 !=1:
        if value % 10 == 1:
            return "st"
        elif value % 10 == 2:
            return "nd"
        elif value % 10 == 3:
            return "rd"
        else:
            return "th"
    else:
        return "th"