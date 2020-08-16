from api import YahooFantasyApi
from app import get_db
from datetime import timedelta, datetime
from sqlalchemy import func
from models import Team, Player, PlayerStats, GoalieStats, SelectedPositions, \
    Draft, Pick, Transaction, TransactionPicks, TransactonPlayers
from utils.date_utils import get_date_range, get_todays_date


yfs = YahooFantasyApi(league_id=5194)

db = get_db()
def update_teams():
    teams = yfs.get_teams()
    for t in teams:
        if t == 'count':
            continue

        team = Team.parse_json(teams[t]['team'][0])

        db.session.merge(team)
    db.session.commit()

def update_players():
    keeper_costs = get_keeper_cost()
    for i in range(0, 2500, 25):
        players = yfs.get_players(i)[1]['players']
        if len(players) == 0:
            break

        for p in players:
            if p == 'count':
                continue

            owning_team = players[p]['player'][1]
            player = Player.parse_json(players[p]['player'][0], owning_team, keeper_costs)
            db.session.merge(player)
        db.session.commit()


def update_draft_results():
    all_keepers = get_keepers()
    draft_results = yfs.get_draft_results()
    for dr in draft_results:
        if dr == 'count':
            continue
        draft_result = draft_results[dr]['draft_result']
        draft_pick = Draft.parse_json(draft_result, all_keepers)
        db.session.merge(draft_pick)
    db.session.commit()


def get_keepers():
    all_keepers = []
    for i in range(0, 2500, 25):
        keepers = yfs.get_keepers(i)[1]['players']
        if len(keepers) == 0:
            break

        for k in keepers:
            if k == 'count':
                continue

            player_id = keepers[k]['player'][0][1]['player_id']
            all_keepers.append(player_id)
    return all_keepers


"""
def update_matchups():
    for i in range(1, 24):
        matchups = yfs.get_scoreboard(i)[1]['scoreboard']['0']['matchups']

        for m in matchups:
            if m == 'count':
                continue

            matchup = Matchup(matchups[m]['matchup'])

            if matchup.status != 'postevent':
                break

            cur = conn.cursor()
            cur.execute(matchup.get_insert_sql())
        conn.commit()
"""


def get_trans():
    transactions = yfs.get_transactions()
    for t in reversed(range(transactions['count'])):
        transaction = transactions[str(t)]['transaction']

        t_type = transaction[0]['type']
        transaction_id = transaction[0]['transaction_id']
        t_date = datetime.fromtimestamp(int(transaction[0]['timestamp']))
        faab_bid = parse_faab_bid(t_type, transaction[0])
        db.session.merge(Transaction(transaction_id, t_date, t_type, faab_bid))

        if t_type == 'trade':
            draft_picks = parse_draft_picks(transaction[0], transaction_id)
            for pick in draft_picks:
                print(f'Round {pick.draft_round} ({pick.original_id}) traded to {pick.destination_id} from {pick.source_id}')
                db.session.merge(pick)
                traded_pick = Pick(pick.original_id, pick.destination_id,
                                   pick.draft_round)
                print(f'Round {traded_pick.draft_round} ({traded_pick.original_team_id}) traded to {pick.destination_id}')
                db.session.merge(traded_pick)
            players = parse_players(transaction[1], transaction_id)
            for player in players:
                db.session.merge(player)
        elif t_type == 'add':
            player = parse_added_player(transaction[1], transaction_id)
            db.session.merge(player)
        elif t_type == 'drop':
            player = parse_dropped_player(transaction[1], transaction_id)
            db.session.merge(player)
        elif t_type == 'add/drop':
            players = parse_add_dropped_players(transaction[1], transaction_id)
            for player in players:
                db.session.merge(player)
        elif t_type != 'commish':
            print('Unknown transaction type: ', t_type)
    db.session.commit()


def parse_faab_bid(transaction_type, transaction_info):
    if transaction_type in ['trade', 'drop', 'commish']:
        return None
    if 'faab_bid' in transaction_info:
        return transaction_info['faab_bid']
    else:
        return 0


def parse_team_id(team_key):
    return team_key[13:]


def parse_draft_picks(transaction_info, transaction_id):
    draft_picks = []
    if 'picks' in transaction_info:
        for pick in transaction_info['picks']:
            source_team_id = parse_team_id(pick['pick']['source_team_key'])
            dest_team_id = parse_team_id(pick['pick']['destination_team_key'])
            original_team_id = parse_team_id(pick['pick']['original_team_key'])
            draft_round = pick['pick']['round']

            draft_picks.append(TransactionPicks(transaction_id, source_team_id,
                                                dest_team_id, draft_round,
                                                original_team_id))
    return draft_picks


def parse_add_dropped_players(transaction_info, trans_id):
    added_player = transaction_info['players']['0']['player']
    a_trans_data = added_player[1]['transaction_data'][0]
    a_player_id = added_player[0][1]['player_id']
    a_source_id = 99 if a_trans_data['source_type'] == 'waivers' else 0
    a_dest_id = parse_team_id(a_trans_data['destination_team_key'])

    dropped_player = transaction_info['players']['1']['player']
    d_trans_data = dropped_player[1]['transaction_data']
    d_player_id = dropped_player[0][1]['player_id']
    d_source_id = parse_team_id(d_trans_data['source_team_key'])
    d_dest_id = 99 if d_trans_data['destination_type'] == 'waivers' else 0

    return [TransactonPlayers(trans_id, a_source_id, a_dest_id, a_player_id),
            TransactonPlayers(trans_id, d_source_id, d_dest_id, d_player_id)]


def parse_added_player(transaction_info, transaction_id):
    player = transaction_info['players']['0']['player']
    player_id = player[0][1]['player_id']

    transaction_data = player[1]['transaction_data'][0]
    source_id = 99 if transaction_data['source_type'] == 'waivers' else 0
    dest_id = parse_team_id(transaction_data['destination_team_key'])
    return TransactonPlayers(transaction_id, source_id, dest_id, player_id)


def parse_dropped_player(transaction_info, transaction_id):
    player = transaction_info['players']['0']['player']
    player_id = player[0][1]['player_id']

    transaction_data = player[1]['transaction_data']
    dest_id = 99 if transaction_data['destination_type'] == 'waivers' else 0
    source_id = parse_team_id(transaction_data['source_team_key'])
    return TransactonPlayers(transaction_id, source_id, dest_id, player_id)


def parse_players(transaction_info, transaction_id):
    players = []
    players_data = transaction_info['players']
    for p in players_data:
        if p == 'count':
            continue
        player_data = players_data[p]['player'][0]
        transaction_data = players_data[p]['player'][1]['transaction_data'][0]

        player_id = player_data[1]['player_id']
        source_team_id = parse_team_id(transaction_data['source_team_key'])
        dest_team_id = parse_team_id(transaction_data['destination_team_key'])

        players.append(TransactonPlayers(transaction_id, source_team_id,
                                         dest_team_id, player_id))
    return players


def parse_players_for_drop(transaction_info):
    players = {}
    players_data = transaction_info['players']
    for p in players_data:
        if p == 'count':
            continue
        player_data = players_data[p]['player'][0]
        transaction_data = players_data[p]['player'][1]['transaction_data'][0]

        player_id = player_data[1]['player_id']
        dest_team_id = parse_team_id(transaction_data['destination_team_key'])

        if dest_team_id in players:
            players[dest_team_id] += [player_id]
        else:
            players[dest_team_id] = [player_id]

    return players


def initialize_picks():
    for draft_round in range(1, 25):
        for team in range(1, 11):
            pick = Pick(team, team, draft_round)

            db.session.merge(pick)
        db.session.commit()


def check_player_played(player):
    if 'player_stats' in player[2]:
        player_stats = player[2]['player_stats']['stats']
    else:
        player_stats = player[3]['player_stats']['stats']
    stat_value = player_stats[0]['stat']['value']
    return stat_value != '-'


def get_start_date():
    last_updated_date = db.session.query(func.max(SelectedPositions.date))
    if last_updated_date[0][0] is not None:
        return last_updated_date[0][0] - timedelta(1)
    else:
        return yfs.get_league_metadata()[0].get('start_date')


def update_statistics():
    date_range = get_date_range(get_start_date(), get_todays_date())
    for d in date_range:
        print("Adding stats for {}".format(d.date()))

        for i in range(0, 2500, 25):
            print("Adding stats for players {}-{}".format(i, i + 25))
            players = yfs.get_stats_players(i, d)[1].get('players')
            if len(players) == 0:
                break

            for p in players:
                if p == 'count':
                    continue
                player_base = players[p]['player']
                player = Player.parse_json(player_base[0], player_base[1])
                player_stats = player_base[2]['player_stats']['stats']
                player_points = player_base[2]['player_points']
                if player.positions == 'G':
                    stat = GoalieStats.parse_json(player_stats, player_points,
                                                  player, d)
                    if stat.w == '-':
                        continue
                else:
                    stat = PlayerStats.parse_json(player_stats, player_points,
                                                  player, d)
                    if stat.g == '-':
                        continue
                db.session.merge(stat)
            db.session.commit()

        for i in range(1, 11):
            print("Adding stats for team {}".format(i))
            players = yfs.get_stats(i, d)[1].get('roster').get('0') \
                .get('players')

            if len(players) == 0:
                break

            for p in players:
                if p == 'count':
                    continue

                player_base = players[p]['player']

                player_id = player_base[0][1]['player_id']
                pos = player_base[1]['selected_position'][1]['position']
                selected_position = SelectedPositions(player_id, d, i, pos)
                db.session.merge(selected_position)
            db.session.commit()    

def get_keeper_cost():
    costs = Draft.query \
       .add_columns(
           Draft.player_id,
           Draft.round)
    ddict = {}
    for row in costs:
        ddict[row[1]] = row[2] - 1
    return ddict

if __name__ == '__main__':
    #update_teams()
    initialize_picks()
    #update_players()
    #update_draft_results()
    get_trans()
    #update_statistics()

