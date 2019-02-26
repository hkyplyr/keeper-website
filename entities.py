

class Pick():
    def __init__(self, pick_json):
        self.owning_team_id = pick_json['destination_team_key'][13:]
        self.original_team_id = pick_json['original_team_key'][13:]
        self.draft_round = pick_json['round']
    
    def get_insert_sql(self):
        return """INSERT INTO picks(owning_team_id, original_team_id, draft_round)
        VALUES({0}, {1}, {2}) ON CONFLICT (original_team_id, draft_round) DO UPDATE SET 
        owning_team_id={0};""".format(self.owning_team_id, self.original_team_id, self.draft_round)

class InitialPick():
    def __init__(self, original_team_id, owning_team_id, draft_round):
        self.owning_team_id = owning_team_id
        self.original_team_id = original_team_id
        self.draft_round = draft_round
    
    def get_insert_sql(self):
        return """INSERT INTO picks(owning_team_id, original_team_id, draft_round)
        VALUES({0}, {1}, {2}) ON CONFLICT (original_team_id, draft_round) DO UPDATE SET 
        owning_team_id={0};""".format(self.owning_team_id, self.original_team_id, self.draft_round)

class Transaction():
    def __init__(self, transaction_json):
        self.transaction_id = transaction_json['transaction_id']
        self.status = transaction_json['status']
        self.timestamp = transaction_json['timestamp']
        self.type = transaction_json['type']

    def parse_added_players(self, transaction_data):
        added_players = []
        added_players_json = transaction_data['players']
        for p in added_players_json:
            if (p == 'count'):
                continue
            print(added_players_json[p])


class AddDropTransaction(Transaction):
    def __init__(self, transaction_info, transaction_json):
        super().__init__(transaction_info)
        self.added_players = super().parse_added_players(transaction_json)
        #self.dropped_players = self.parse_dropped_players()

        self.added_player_id = self.parse_added_player_id(transaction_json)
        self.destination_id = self.parse_destination_id(transaction_json)
        self.source_id = self.parse_source_id(transaction_json)
        self.dropped_player_id = self.parse_dropped_player_id(transaction_json)

    def parse_destination_id(self, transaction_json):
        added_player = self.parse_added_player_json(transaction_json)
        return added_player[1]['transaction_data'][0]['destination_team_key'][13:]
    
    def parse_added_player_id(self, transaction_json):
        added_player = self.parse_added_player_json(transaction_json)
        return added_player[0][1]['player_id']

    def parse_added_player_json(self, transaction_json):
        return transaction_json['players']['0']['player']

    def parse_source_id(self, transaction_json):
        dropped_player = self.parse_dropped_player_json(transaction_json)
        return dropped_player[1]['transaction_data']['source_team_key'][13:]
    
    def parse_dropped_player_id(self, transaction_json):
        dropped_player = self.parse_dropped_player_json(transaction_json)
        return dropped_player[0][1]['player_id']

    def parse_dropped_player_json(self, transaction_json):
        return transaction_json['players']['1']['player']

    def get_insert_sql(self):
        return 

class Player():
    def __init__(self, player_json, owning_team):
        self.player_id = self.parse_player_id(player_json)
        self.first_name = self.parse_first_name(player_json)
        self.last_name = self.parse_last_name(player_json)
        self.team = self.parse_team(player_json)
        self.number = self.parse_number(player_json)
        self.headshot_url = self.parse_headshot_url(player_json)
        self.positions = self.parse_positions(player_json)
        self.owning_team_id = owning_team

    def parse_player_id(self, player_json):
        return get_value(player_json, 1, 'player_id')

    def parse_first_name(self, player_json):
        return get_value(player_json, 2, 'name')['first'].replace("'", "''")
    
    def parse_last_name(self, player_json):
        return get_value(player_json, 2, 'name')['last'].replace("'", "''")

    def parse_team(self, player_json):
        return get_value(player_json, 6, 'editorial_team_abbr').upper()

    def parse_number(self, player_json):
        number = get_value(player_json, 7, 'uniform_number')
        return 0 if number == "" else int(number)
    
    def parse_headshot_url(self, player_json):
        return get_value(player_json, 9, 'headshot')['url']

    def parse_positions(self, player_json):
        positions = get_value(player_json, 12, 'eligible_positions')
        return ','.join(p for p in list(filter(lambda p: 'IR' not in p and 'F' not in p, map(lambda p: p['position'], positions))))

    def get_insert_sql(self):
        return """INSERT INTO players(player_id, first_name, last_name, nhl_team, number, positions, team_id, headshot_url)
            VALUES({0}, '{1}', '{2}', '{3}', {4}, '{5}', {6}, '{7}')
            ON CONFLICT (player_id) DO UPDATE SET
            first_name='{1}', last_name='{2}', nhl_team='{3}', number={4}, positions='{5}', team_id={6}, headshot_url='{7}';
            """.format(self.player_id, self.first_name, self.last_name, self.team, self.number, self.positions, self.owning_team_id, self.headshot_url)

class Team:
    def __init__(self, team_json):
        self.team_id = self.parse_team_id(team_json)
        self.team_name = self.parse_team_name(team_json)
        self.team_url = self.parse_team_url(team_json)
        self.team_logo = self.parse_team_logo(team_json)
        self.manager = self.parse_manager(team_json)

    def parse_team_id(self, team_json):
        return get_value(team_json, 1, 'team_id')

    def parse_team_name(self, team_json):
        return get_value(team_json, 2, 'name').replace("'", "")
    
    def parse_team_url(self, team_json):
        return get_value(team_json, 4, 'url')
    
    def parse_team_logo(self, team_json):
        return get_value(team_json, 5, 'team_logos')[0]['team_logo']['url']
    
    def parse_manager(self, team_json):
        return get_value(team_json, 19, 'managers')[0]['manager']['nickname']

    def get_insert_sql(self):
        return """INSERT INTO fantasyteams(team_id, team_name, team_url, team_logo, manager)
            VALUES({0}, '{1}', '{2}', '{3}', '{4}')
            ON CONFLICT (team_id) DO UPDATE SET
            team_name='{1}', team_url='{2}', team_logo='{3}', manager='{4}';
            """.format(self.team_id, self.team_name, self.team_url, self.team_logo, self.manager)

class DraftPick:
    def __init__(self, draft_json):
        self.pick = draft_json['pick']
        self.round = draft_json['round']
        self.team_id = draft_json['team_key'][13:]
        self.player_id = draft_json['player_key'][6:]
    
    def get_insert_sql(self):
        return """INSERT INTO draftresults(pick, round, team_id, player_id)
        VALUES({0}, {1}, {2}, {3}) ON CONFLICT DO NOTHING;
        """.format(self.pick, self.round, self.team_id, self.player_id)

class Matchup:
    def __init__(self, matchup_json):
        self.team_one_id = self.parse_team_id('0', matchup_json)
        self.team_one_pts = self.parse_team_points('0', matchup_json)
        self.team_one_gp = self.parse_team_games('0', matchup_json)
        self.team_two_id = self.parse_team_id('1', matchup_json)
        self.team_two_pts = self.parse_team_points('1', matchup_json)
        self.team_two_gp = self.parse_team_games('1', matchup_json)
        self.winning_team = self.team_one_id if self.team_one_pts > self.team_two_pts else self.team_two_id
        self.losing_team = self.team_two_id if self.winning_team == self.team_one_id else self.team_one_id

        self.is_consolation = False if matchup_json['is_consolation'] == '0' else True
        self.is_playoffs = False if matchup_json['is_playoffs'] == '0' else True
        self.status = matchup_json['status']
        self.week = matchup_json['week']

    def parse_team_id(self, index, matchup_json):
        team_json = matchup_json['0']['teams'][index]['team'][0]
        return int(get_value(team_json, 1, 'team_id'))
    
    def parse_team_points(self, index, matchup_json):
        team_json = matchup_json['0']['teams'][index]['team'][1]
        return float(team_json['team_points']['total'])

    def parse_team_games(self, index, matchup_json):
        team_json = matchup_json['0']['teams'][index]['team'][1]
        return int(team_json['team_remaining_games']['total']['completed_games'])

    def get_insert_sql(self):
        return """
        INSERT INTO matchups(week, winning_team_id, losing_team_id, consolation, playoffs, status) 
        VALUES({0}, {1}, {2}, {3}, {4}, '{5}') ON CONFLICT (week, winning_team_id, losing_team_id) DO NOTHING;

        INSERT INTO scores(week, team_id, team_pts, team_gp) VALUES({0}, {6}, {7}, {8}) 
        ON CONFLICT (week, team_id) DO UPDATE SET team_pts={7}, team_gp={8};

        INSERT INTO scores(week, team_id, team_pts, team_gp) VALUES({0}, {9}, {10}, {11}) 
        ON CONFLICT (week, team_id) DO UPDATE SET team_pts={10}, team_gp={11};
        """.format(self.week, self.winning_team, self.losing_team, self.is_consolation, self.is_playoffs, self.status,
        self.team_one_id, self.team_one_pts, self.team_one_gp, self.team_two_id, self.team_two_pts, self.team_two_gp)
 