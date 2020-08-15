from api import YahooFantasyApi
from utils.date_utils import get_todays_date
import argparse
import csv
import itertools

TEAM_MAP = {}

yfs = YahooFantasyApi(league_id=5194)

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', default=False, help='Output useful debug information')
args = parser.parse_args()

def __get_draft_costs():
    """Get drafted player keeper costs using the Yahoo Fantasy API.
    Return a map of player ids to their keeper costs.
    """
    draft_picks = yfs.get_draft_results()
    keeper_costs = {}
    for d in draft_picks:
        if d == 'count':
            continue
        draft_pick = draft_picks[d]['draft_result']
        player_id = draft_pick['player_key'][6:]
        cost = draft_pick['round'] - 1
        keeper_costs[player_id] = cost
    return keeper_costs

def __parse_manager_name(team_info):
    """Parse and format a manager's name from their team info JSON.
    If a manager has first and list name or is not capitalized, we
    drop the last name and capitalize the first name accordingly.

    Keyword arguments:
    team_info -- the JSON data containing the team and manager's info   
    """
    return team_info[19]['managers'][0]['manager']['nickname'].split(' ', 1)[0].capitalize()

def __get_roster_costs(draft_costs, team_id):
    """Get keeper costs for each player on a given team's roster.
    If the player does not have a calculated keeper cost from the draft_costs
    map we default to 18th round.

    Keywor arguments:
    draft_costs -- the draft costs map, mapping a player to their cost
    team_id -- the id of the team to get the roster for
    """
    team = yfs.get_roster(team_id)
    team_map = __get_team_map()

    team_roster = team['0']['players']
    players = []
    for p in team_roster:
        if p == 'count':
            continue
        player = team_roster[p]['player'][0]
        player_id = player[1]['player_id']
        player_name = player[2]['name']['full']
        players.append((player_name, draft_costs.get(player_id, 18)))
    return team_map[team_id], sorted(players, key=lambda x: (x[1], x[0]))

def __combine_lists(data, fillvalue=(None, None)):
    """Combine an arbitrary number of lists such that the first n
    values are the first values in each individual list, the next n
    values are the second value in each individual list and so on.
    
    If the lists are not the same length we use a default value to
    pad the resulting list.
    
    Keyword arguments:
    data -- the list of lists to be combined
    fillvalue -- the value to use to pad the list lengths
    """
    zipped = list(itertools.zip_longest(*data, fillvalue=fillvalue))
    for i, row in enumerate(zipped):
        zipped[i] = [item for sublist in row for item in sublist]
    return zipped

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

def __generate_initial_picks():
    """Generate a map of lists of initial draft picks for each team.
    """
    picks_by_team = {}
    for team in range(1, 11):
        picks = []
        for pick in range(1, 25):
            picks.append((pick, team))
        picks_by_team[team] = picks
    return picks_by_team

def __get_updated_picks():
    """Update the list of initial picks by checking the list of transactions
    from the Yahoo Fantasy API. If a pick is traded we add the pick to the 
    destination team's list and remove it from the source team's list.
    """
    initial_picks = __generate_initial_picks()
    transactions = yfs.get_transactions()
    for t in reversed(range(int(transactions['count']))):
        transaction = transactions[str(t)]['transaction'][0]
        transaction_type = transaction['type']
        
        if transaction_type != 'trade':
            # Picks are only moved in a trade.
            continue

        if 'picks' not in transaction:
            # If a trade does not contain picks, we don't care.s
            continue

        picks = transaction['picks']
        for p in picks:
            pick = p['pick']
            rnd = int(pick['round'])
            source = int(pick['source_team_key'][13:])
            dest = int(pick['destination_team_key'][13:])
            original = int(pick['original_team_key'][13:])

            moved_pick = (rnd, original)
            initial_picks[source].remove(moved_pick)
            initial_picks[dest].append(moved_pick)

    return initial_picks

def __get_team_map():
    """Create or retrieve a map of team information (manager name),
    keyed by the team id.
    """
    if TEAM_MAP:
        return TEAM_MAP

    teams = yfs.get_teams()
    for t in teams:
        if t == 'count':
            continue
        team = teams[t]['team'][0]
        team_id = int(team[1]['team_id'])
        manager = team[19]['managers'][0]['manager']['nickname'].split(' ', 1)[0].capitalize()
        TEAM_MAP[team_id] = manager
    return TEAM_MAP

def log(text_to_print, debug=args.debug):
    if debug:
        print(text_to_print)

def get_current_date_time():
    return datetime.now().strftime('%Y-%m-%d %I:%M:%S%p')

def get_rosters_for_csv():
    """Retrieve the list of players for each team, formatted for printing
    in columns to a csv file.
    """
    keeper_costs = __get_draft_costs()
    headers = []
    rosters = []
    for i in range(1, 11):
        name, costs = __get_roster_costs(keeper_costs, i)
        log(f'\n{name}')
        for player in costs:
            log(f'{player[0]}, {player[1]}')
        headers.append(name)
        headers.append(None)
        rosters.append(costs)
    return headers, __combine_lists(rosters)

def get_picks_for_csv():
    """Retrieve the list of draft picks for each team, formatted for printing
    in columns to a csv file.
    """
    team_map = __get_team_map()
    picks_by_team = __get_updated_picks()
    pick_matrix = []
    for team, picks in picks_by_team.items():
        pick_list = []
        sorted_picks = sorted(picks, key=lambda x: (x[0]))
        for pick in sorted_picks:
            text = f'{pick[0]}{__get_ordinal(pick[0])} Round'
            if pick[1] != team:
                text = text + f' ({team_map[pick[1]]})'
            pick_list.append((text, pick[0]))
        pick_matrix.append(pick_list)
        
    return __combine_lists(pick_matrix)

def output_csv(teams, rosters, picks, file_prefix='keepercosts'):
    """Output the provided data to a csv file.

    Keyword arguments:
    filename -- the name of the file to create/open for writing
    teams -- the list of team names to use as the header
    rosters -- the row-formatted lists of players with hteir keeper cost
    picks -- the row-formatted list of draft picks
    """
    todays_date = get_todays_date()
    filename = f'reports/{file_prefix}-{todays_date}.csv'

    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(teams)
        writer.writerows(rosters)
        writer.writerows(picks)
        writer.writerow([f'Data pulled on {todays_date}'])


if __name__ == '__main__':
    teams, rosters = get_rosters_for_csv()
    picks = get_picks_for_csv()
    output_csv(teams, rosters, picks)


