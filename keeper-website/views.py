from flask import Blueprint, render_template, request, url_for, abort
from sqlalchemy import func, and_
from sqlalchemy.sql.expression import case
from models import Team, Player, PlayerStats, GoalieStats, SelectedPositions, \
    Pick, Draft
from app import get_db
from utils.date_utils import get_prev_date, get_next_date, convert_to_date
from utils.json_utils import get_ordinal

bp = Blueprint('bp', __name__)
db = get_db()

@bp.route('/')
def index():
    teams = Team.query.all()
    return render_template('index.html', teams=teams)


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
    if team_id > 10:
        abort(404)

    date = request.args.get('date', type=str)

    if date is None:
        prev_date = prev_url = next_date = next_url = valid_date = None
        max_date = db.session.query(func.max(SelectedPositions.date))
        skaters = db.session.query(Player.id,
                                   func.count(Player.id).label('gp'),
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
                                   func.sum(PlayerStats.points).label('points'),
                                   Player.keeper_cost
                                   )\
            .join(PlayerStats, PlayerStats.player_id == Player.id) \
            .join(SelectedPositions, SelectedPositions.player_id == Player.id)\
            .filter(SelectedPositions.team_id == team_id) \
            .filter(SelectedPositions.date == max_date) \
            .group_by(
                SelectedPositions.position,
                Player.id,
                Player.first_name,
                Player.last_name,
                Player.positions) \
            .order_by(func.sum(PlayerStats.points).desc())

        goalies = db.session.query(Player.id,
                                   func.count(Player.id).label('gp'),
                                   Player.positions.label('pos'),
                                   Player.first_name,
                                   Player.last_name,
                                   func.sum(GoalieStats.w).label('w'),
                                   func.sum(GoalieStats.loss).label('l'),
                                   func.sum(GoalieStats.ga).label('ga'),
                                   func.sum(GoalieStats.sv).label('sv'),
                                   func.sum(GoalieStats.so).label('so'),
                                   func.sum(GoalieStats.points).label('points'),
                                   Player.keeper_cost
                                   ) \
            .join(GoalieStats, GoalieStats.player_id == Player.id) \
            .join(SelectedPositions, SelectedPositions.player_id == Player.id)\
            .filter(SelectedPositions.team_id == team_id) \
            .filter(SelectedPositions.date == max_date) \
            .group_by(
                SelectedPositions.position,
                Player.id,
                Player.first_name,
                Player.last_name,
                Player.positions) \
            .order_by(func.sum(GoalieStats.points).desc())
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
            else url_for('team', team_id=team_id, date=next_date)
        prev_url = None if prev_date < date_query.min \
            else url_for('team', team_id=team_id, date=prev_date)

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
        text = f'{get_ordinal(pick.draft_round)} Round'

        #if pick.original_team_id != team_id:
        #    text = text + f' ({pick.name})'
        
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
        next_url=next_url)


@bp.route('/goalies')
def goalies():
    page = request.args.get('page', default=0, type=int)
    sort = request.args.get('sort', default='fp', type=str)

    goalies = db.session.query(Player.id,
                               func.count(Player.id).label('gp'),
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
