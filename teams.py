from api import YahooFantasyApi
from app import db
from models import *
from utils.date_utils import get_date_range, get_todays_date


yfs = YahooFantasyApi(league_id=1994)   

def update_teams():
    teams = yfs.get_teams()['fantasy_content']['league'][1]['teams']
    for t in teams:
        if t == 'count':
            continue

        team = Team.parse_json(teams[t]['team'][0])

        db.session.merge(team)
    db.session.commit()

def update_players():
    for i in range(0,2500, 25):
        players = yfs.get_players(i)['fantasy_content']['league'][1]['players']
        if len(players) == 0:
            break
        
        for p in players:
            if p == 'count':
                continue

            ownership = players[p]['player'][1]['ownership']
            if ownership['ownership_type'] == 'freeagents' or ownership['ownership_type'] == 'waivers':
                owning_team = 0
            else:
                owning_team = ownership['owner_team_key'][13:]

            player = Player.parse_json(players[p]['player'][0], owning_team)
            db.session.merge(player)
        db.session.commit()

def update_draft_results():
    draft_results = yfs.get_draft()['fantasy_content']['league'][1]['draft_results']
    for dr in draft_results:
        if dr == 'count':
            continue

        draft_pick = DraftPick(draft_results[dr]['draft_result'])
        cur = conn.cursor()
        cur.execute(draft_pick.get_insert_sql())
    conn.commit()

def get_keepers():
    for i in range(0, 2500, 25):
        keepers = yfs.get_keepers(i)['fantasy_content']['league'][1]['players']
        if len(keepers) == 0:
            break
        
        for k in keepers:
            if k == 'count':
                continue
            
            player_id = keepers[k]['player'][0][1]['player_id']
            print(player_id)
            cur = conn.cursor()
            cur.execute("""UPDATE players SET keeper=True 
            WHERE player_id={}""".format(player_id))
        conn.commit()

def update_matchups():
    for i in range(1, 24):
        matchups = yfs.get_scoreboard(i)['fantasy_content']['league'][1]['scoreboard']['0']['matchups']

        for m in matchups:
            if m == 'count':
                continue

            matchup = Matchup(matchups[m]['matchup'])

            if matchup.status != 'postevent':
                break

            cur = conn.cursor()
            cur.execute(matchup.get_insert_sql())
        conn.commit()

def get_transactions():
    data = yfs.get_transactions()
    transactions = data['fantasy_content']['league'][1]['transactions']
    transaction_count = transactions['count'] - 1
    for t in range(transaction_count):
        transaction = transactions[str(t)]['transaction']
        transaction_info = transaction[0]
        transaction_data = transaction[1]

        transaction_type = transaction_info['type']
        if transaction_type == 'trade':
            continue
            #players = transaction['players']
            #for p in players:
            #    if p == 'count':
            #        continue
            #    player_id = players[p]['player'][0][1]['player_id']
                #check_if_player_exists(player_id)
            #    transaction_data = players[p]['player'][1]['transaction_data'][0]

            #    source_id = transaction_data['source_team_key'][12:]
            #    destination_id = transaction_data['destination_team_key'][12:]

                #owner_vo = Ownership(player_id=player_id, team_id=destination_id)
                #db.session.merge(owner_vo)
                #db.session.commit()

            picks = transaction_info['picks']
            for pick in picks:
                pick_vo = Pick(pick['pick'])
                cur = conn.cursor()
                cur.execute(pick_vo.get_insert_sql())
                conn.commit()

                #print(Pick(pick['pick']).get_insert_sql())

                #source_id = pick['pick']['source_team_key'][12:]
                #destination_id = pick['pick']['destination_team_key'][12:]
                #original_id = pick['pick']['original_team_key'][12:]
                #draft_round = pick['pick']['round']

                #pick_vo = Pick(original_id=original_id, draft_round=draft_round, owner_id=destination_id)
                #db.session.merge(pick_vo)
                #db.session.commit()
        if transaction_type == 'add':
            continue
            #player = transaction['players']['0']['player']
            #player_id = player[0][1]['player_id']

            #transaction_data = player[1]['transaction_data'][0]
            #team_id = transaction_data['destination_team_key'][12:]

            #if player_id == '3344' and team_id == '1':
            #    print(t)
            #    print('Vanek added')

            #owner_vo = Ownership(player_id=player_id, team_id=team_id)
            #db.session.merge(owner_vo)
            #db.session.commit()
        
        if transaction_type == 'drop':
            continue


            #player = transaction['players']['0']['player']
            #player_id = player[0][1]['player_id']

            #transaction_data = player[1]['transaction_data']
            #team_id = transaction_data['source_team_key'][12:]

            #if player_id == '3344' and team_id == '1':
            #    print(t)
            #    print('Vanek dropped')

            #owner_vo = Ownership.query.get(player_id)
            #if owner_vo is not None:
            #    db.session.delete(owner_vo)
            #db.session.commit()

        if transaction_type == 'add/drop':
            adtrans = AddDropTransaction(transaction_info, transaction_data)

            #added_player = transaction['players']['0']['player']
            #added_id = added_player[0][1]['player_id']

            #add_transaction = added_player[1]['transaction_data'][0]
            #destination_id = add_transaction['destination_team_key'][12:]

            #dropped_player = transaction['players']['1']['player']
            #dropped_id = dropped_player[0][1]['player_id']

            #drop_transaction = dropped_player[1]['transaction_data']
            #source_id = drop_transaction['source_team_key'][12:]

            #added_owner_vo = Ownership(player_id=added_id, team_id=destination_id)
            #db.session.merge(added_owner_vo)
            
            #dropped_owner_vo = Ownership.query.get(dropped_id)
            #if dropped_owner_vo is not None:
            #    db.session.delete(dropped_owner_vo)
            
            #db.session.commit()
 


def initialize_picks():
    for draft_round in range(1,25):
        for team in range(1,11):
            pick = InitialPick(team, team, draft_round)

            cur = conn.cursor()
            cur.execute(pick.get_insert_sql())
            print("Inserting team {} in round {}".format(team, draft_round))
        conn.commit()

#initialize_picks()
#update_draft_results()
#update_teams()
#update_players()
#get_keepers()
#update_matchups()
#get_transactions()
#update_stats()

def check_player_played(player):
    if 'player_stats' in player[2]:
        player_stats = player[2]['player_stats']['stats']
    else:
        player_stats = player[3]['player_stats']['stats']
    stat_value = player_stats[0]['stat']['value']
    return stat_value != '-'

start_week = yfs.get_league_metadata()['fantasy_content']['league'][0]['start_date']
date_range = get_date_range(start_week, get_todays_date())
for d in date_range:
    for i in range(0, 2500, 25):
        players = yfs.get_stats_players(i, d)['fantasy_content']['league'][1]['players']
        if len(players) == 0:
            break

        for p in players:
            if p == 'count':
                continue
            player_base = players[p]['player']
            player = Player.parse_json(player_base[0], player_base[1])
            if player.positions == 'G':
                stat = GoalieStats.parse_json(player_base[2]['player_stats']['stats'], player_base[2]['player_points'], player, d)
                if stat.w == '-':
                    continue
            else:
                stat = PlayerStats.parse_json(player_base[2]['player_stats']['stats'], player_base[2]['player_points'], player, d)
                if stat.g == '-':
                    continue
            db.session.merge(stat)
        db.session.commit()

    for i in range(1, 11):
        players = yfs.get_stats(i, d)['fantasy_content']['team'][1]['roster']['0']['players']
        if len(players) == 0:
            break
        
        for p in players:
            if p == 'count':
                continue
            
            player_base = players[p]['player']
            if not check_player_played(player_base):
                continue

            player_id = player_base[0][1]['player_id']
            position = player_base[1]['selected_position'][1]['position']
            selected_position = SelectedPositions(player_id, d, position)
            db.session.merge(selected_position)
        db.session.commit()
    

            
            

            