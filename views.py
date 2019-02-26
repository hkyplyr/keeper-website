from flask import render_template, request
from sqlalchemy import func
from models import Team, Player, PlayerStats, GoalieStats
from app import app, db

@app.route('/')
def index():
    teams = Team.query.all()
    return render_template('index.html', teams=teams)

@app.route('/team/<teamid>')

@app.route('/draft/<clazz>')
def draft(clazz):
    players = Player.query.join(Draft).add_columns(Player.player_id, Player.first_name, Player.last_name, Draft.team_id, Player.positions, Player.nhl_team, Player.keeper).order_by(Draft.pick.asc())
    teams = Team.query.all()
    return render_template('draft.html', teams=teams, players=players, clazz=clazz)

@app.route('/teams/<team_id>')
def team(team_id):
    team_id = int(team_id)
    if team_id > 10:
        abort(404)

    skaters = db.session.query(Player.id, func.count(Player.id).label('gp'), Player.positions, Player.first_name, Player.last_name, func.sum(PlayerStats.g).label('g'), func.sum(PlayerStats.a).label('a'), func.sum(PlayerStats.g + PlayerStats.a).label('p'), func.sum(PlayerStats.pm).label('pm'), func.sum(PlayerStats.ppp).label('ppp'), func.sum(PlayerStats.shp).label('shp'), func.sum(PlayerStats.sog).label('sog'), func.sum(PlayerStats.hit).label('hit'), func.sum(PlayerStats.blk).label('blk')) \
        .join(PlayerStats, PlayerStats.player_id == Player.id).filter(Player.team_id == team_id).group_by(Player.id, Player.first_name, Player.last_name, Player.positions).order_by(func.sum(PlayerStats.g + PlayerStats.a).desc())

    goalies = db.session.query(Player.id, func.count(Player.id).label('gp'), Player.positions, Player.first_name, Player.last_name, func.sum(GoalieStats.w).label('w'), func.sum(GoalieStats.l).label('l'), func.sum(GoalieStats.ga).label('ga'), func.sum(GoalieStats.sv).label('sv'), func.sum(GoalieStats.so).label('so')) \
        .join(GoalieStats, GoalieStats.player_id == Player.id).filter(Player.team_id == team_id).group_by(Player.id, Player.first_name, Player.last_name, Player.positions).order_by(func.sum(GoalieStats.w).desc())

    teams = Team.query.all()
    return render_template('team.html', skaters=skaters, goalies=goalies, teams=teams, team_id=team_id-1)

@app.route('/players/')
def players():
    skaters = db.session.query(Player.id, func.count(Player.id).label('gp'), Player.positions, Player.first_name, Player.last_name, func.sum(PlayerStats.g).label('g'), func.sum(PlayerStats.a).label('a'), func.sum(PlayerStats.g + PlayerStats.a).label('p'), func.sum(PlayerStats.pm).label('pm'), func.sum(PlayerStats.ppp).label('ppp'), func.sum(PlayerStats.shp).label('shp'), func.sum(PlayerStats.sog).label('sog'), func.sum(PlayerStats.hit).label('hit'), func.sum(PlayerStats.blk).label('blk')) \
        .join(PlayerStats, PlayerStats.player_id == Player.id).group_by(Player.id, Player.first_name, Player.last_name, Player.positions).order_by(func.sum(PlayerStats.g + PlayerStats.a).desc())

    goalies = db.session.query(Player.id, func.count(Player.id).label('gp'), Player.positions, Player.first_name, Player.last_name, func.sum(GoalieStats.w).label('w'), func.sum(GoalieStats.l).label('l'), func.sum(GoalieStats.ga).label('ga'), func.sum(GoalieStats.sv).label('sv'), func.sum(GoalieStats.so).label('so')) \
        .join(GoalieStats, GoalieStats.player_id == Player.id).group_by(Player.id, Player.first_name, Player.last_name, Player.positions).order_by(func.sum(GoalieStats.w).desc())
    
    teams = Team.query.all()
    return render_template('players.html', skaters=skaters, goalies=goalies, teams=teams)