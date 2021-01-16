from app import db
from api import YahooFantasyApi
import sys
from sqlalchemy.sql import or_
from models import Team, Player, PlayerStats, GoalieStats, SelectedPositions
from utils.date_utils import get_dates_from_week

yfs = YahooFantasyApi(league_id=5194)


def get_potential_points(week):
    date_range = get_dates_from_week(yfs, week)
    for i in range(1, 11):
        team_name = get_team_name(i)
        total_for_week = 0
        for d in date_range:
            total_for_week += get_optimal(i, d.date())
        print('Optimal Points for {} is {:.2f}'
              .format(team_name, round(total_for_week, 2)))


def get_team_name(team_id):
    return db.session.query(Team.name).filter(Team.id == team_id).scalar()


def get_optimal(team_id, date):
    center = get_players_by_position('C', 5, team_id, date)
    leftwing = get_players_by_position('LW', 4, team_id, date)
    rightwing = get_players_by_position('RW', 4, team_id, date)
    defense = get_players_by_position('D', 5, team_id, date)
    goalie = get_goalies(team_id, date)
    skaters = get_skaters(team_id, date)

    optimal_c_lw_rw = get_c_lw_rw(center, leftwing, rightwing, skaters)
    optimal_c_rw_lw = get_c_rw_lw(center, leftwing, rightwing, skaters)
    optimal_lw_c_rw = get_lw_c_rw(center, leftwing, rightwing, skaters)
    optimal_lw_rw_c = get_lw_rw_c(center, leftwing, rightwing, skaters)
    optimal_rw_c_lw = get_rw_c_lw(center, leftwing, rightwing, skaters)
    optimal_rw_lw_c = get_rw_lw_c(center, leftwing, rightwing, skaters)
    optimal_forwards = max(optimal_c_lw_rw, optimal_c_rw_lw, optimal_lw_c_rw,
                           optimal_lw_rw_c, optimal_rw_c_lw, optimal_rw_lw_c)
    optimal_defense = get_optimal_d(defense)
    optimal_goalie = get_optimal_g(goalie)
    optimal_total = optimal_forwards + optimal_defense + optimal_goalie

    # print('Optimal Forwards: {}'.format(optimal_forwards))
    # print('Optimal Defense: {}'.format(optimal_defense))
    # print('Optimal Goalies: {}'.format(optimal_goalie))
    # print('Optimal Total: {}'.format(optimal_total))
    return optimal_total


def get_skaters(team_id, date):
    return db.session.query(Player.id,
                            Player.first_name,
                            Player.last_name,
                            Player.positions,
                            PlayerStats.points) \
        .join(SelectedPositions, SelectedPositions.player_id == Player.id)\
        .join(PlayerStats,
              (PlayerStats.player_id == SelectedPositions.player_id)
              & (PlayerStats.date == SelectedPositions.date))\
        .filter(or_(Player.positions.contains('C'),
                    Player.positions.contains('LW'),
                    Player.positions.contains('RW')))\
        .filter(SelectedPositions.date == date)\
        .filter(SelectedPositions.team_id == team_id)\
        .filter(PlayerStats.points > 0)\
        .order_by(PlayerStats.points.desc())


def get_goalies(team_id, date):
    return db.session.query(Player.id,
                            Player.first_name,
                            Player.last_name,
                            Player.positions,
                            GoalieStats.points) \
        .join(SelectedPositions, SelectedPositions.player_id == Player.id)\
        .join(GoalieStats,
              (GoalieStats.player_id == SelectedPositions.player_id)
              & (GoalieStats.date == SelectedPositions.date))\
        .filter(Player.positions.contains('G'))\
        .filter(SelectedPositions.date == date)\
        .filter(SelectedPositions.team_id == team_id)\
        .filter(GoalieStats.points > 0)\
        .order_by(GoalieStats.points.desc())\
        .limit(2)


def get_players_by_position(position, cutoff, team_id, date):
    return db.session.query(Player.id,
                            Player.first_name,
                            Player.last_name,
                            Player.positions,
                            PlayerStats.points) \
        .join(SelectedPositions, SelectedPositions.player_id == Player.id)\
        .join(PlayerStats,
              (PlayerStats.player_id == SelectedPositions.player_id)
              & (PlayerStats.date == SelectedPositions.date))\
        .filter(Player.positions.contains(position))\
        .filter(SelectedPositions.date == date)\
        .filter(SelectedPositions.team_id == team_id)\
        .filter(PlayerStats.points > 0)\
        .order_by(PlayerStats.points.desc())\
        .limit(cutoff)


def get_c_lw_rw(center, leftwing, rightwing, skaters):
    used_ids = []
    optimal_c, used_ids = get_optimal_c(center, used_ids)
    optimal_lw, used_ids = get_optimal_lw(leftwing, used_ids)
    optimal_rw, used_ids = get_optimal_rw(rightwing, used_ids)
    optimal_f, used_ids = get_optimal_players(skaters, 2, used_ids)
    return optimal_c + optimal_lw + optimal_rw + optimal_f


def get_c_rw_lw(center, leftwing, rightwing, skaters):
    used_ids = []
    optimal_c, used_ids = get_optimal_c(center, used_ids)
    optimal_rw, used_ids = get_optimal_rw(rightwing, used_ids)
    optimal_lw, used_ids = get_optimal_lw(leftwing, used_ids)
    optimal_f, used_ids = get_optimal_players(skaters, 2, used_ids)
    return optimal_c + optimal_lw + optimal_rw + optimal_f


def get_lw_c_rw(center, leftwing, rightwing, skaters):
    used_ids = []
    optimal_lw, used_ids = get_optimal_lw(leftwing, used_ids)
    optimal_c, used_ids = get_optimal_c(center, used_ids)
    optimal_rw, used_ids = get_optimal_rw(rightwing, used_ids)
    optimal_f, used_ids = get_optimal_players(skaters, 2, used_ids)
    return optimal_c + optimal_lw + optimal_rw + optimal_f


def get_lw_rw_c(center, leftwing, rightwing, skaters):
    used_ids = []
    optimal_lw, used_ids = get_optimal_lw(leftwing, used_ids)
    optimal_rw, used_ids = get_optimal_rw(rightwing, used_ids)
    optimal_c, used_ids = get_optimal_c(center, used_ids)
    optimal_f, used_ids = get_optimal_players(skaters, 2, used_ids)
    return optimal_c + optimal_lw + optimal_rw + optimal_f


def get_rw_c_lw(center, leftwing, rightwing, skaters):
    used_ids = []
    optimal_rw, used_ids = get_optimal_rw(rightwing, used_ids)
    optimal_c, used_ids = get_optimal_c(center, used_ids)
    optimal_lw, used_ids = get_optimal_lw(leftwing, used_ids)
    optimal_f, used_ids = get_optimal_players(skaters, 2, used_ids)
    return optimal_c + optimal_lw + optimal_rw + optimal_f


def get_rw_lw_c(center, leftwing, rightwing, skaters):
    used_ids = []
    optimal_rw, used_ids = get_optimal_rw(rightwing, used_ids)
    optimal_lw, used_ids = get_optimal_lw(leftwing, used_ids)
    optimal_c, used_ids = get_optimal_c(center, used_ids)
    optimal_f, used_ids = get_optimal_players(skaters, 2, used_ids)
    return optimal_c + optimal_lw + optimal_rw + optimal_f


def get_optimal_players(players, limit, used):
    optimal_points = 0
    counter = 0
    for p in players:
        if counter >= limit or p.id in used:
            continue

        counter += 1
        optimal_points += p.points
        used.append(p.id)
    return optimal_points, used


def get_optimal_rw(players, used):
    return get_optimal_players(players, 2, used)


def get_optimal_c(players, used):
    return get_optimal_players(players, 3, used)


def get_optimal_lw(players, used):
    return get_optimal_players(players, 2, used)


def get_optimal_d(players):
    points, _ = get_optimal_players(players, 5, [])
    return points


def get_optimal_g(players):
    points, _ = get_optimal_players(players, 2, [])
    return points


get_potential_points(int(sys.argv[1]))
