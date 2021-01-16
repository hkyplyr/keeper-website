from keeper_website.database import db
from keeper_website.utils.json_utils import get_value
from sqlalchemy.ext.hybrid import hybrid_method


class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    name = db.Column(db.Text)
    manager = db.Column(db.Text)
    url = db.Column(db.Text)
    logo = db.Column(db.Text)

    def __init__(self, id, name, url, logo, manager):
        self.id = id
        self.name = name
        self.url = url
        self.logo = logo
        self.manager = manager

    @staticmethod
    def parse_json(json):
        id = get_value(json, 1, 'team_id')
        name = get_value(json, 2, 'name').replace("'", "''")
        url = get_value(json, 4, 'url')
        logo = get_value(json, 5, 'team_logos')[0]['team_logo']['url']
        manager = get_value(json, 19, 'managers')[0]['manager']['nickname']

        return Team(id, name, url, logo, manager)


class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    first_name = db.Column(db.String(20))
    last_name = db.Column(db.String(20))
    nhl_team = db.Column(db.String(3))
    number = db.Column(db.Integer)
    positions = db.Column(db.String(7))
    team_id = db.Column(db.Integer)
    keeper_cost = db.Column(db.Integer)

    def __init__(self, id, first_name, last_name, nhl_team, number,
                 positions, team_id, keeper_cost):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.nhl_team = nhl_team
        self.number = number
        self.positions = positions
        self.team_id = team_id
        self.keeper_cost = keeper_cost

    @staticmethod
    def parse_json(info_json, owner_json, keeper_costs):
        id = int(get_value(info_json, 1, 'player_id'))
        first_name = get_value(info_json, 2, 'name')['first'] \
            .replace("'", "''")
        last_name = get_value(info_json, 2, 'name')['last'] \
            .replace("'", "''")
        nhl_team = get_value(info_json, 6, 'editorial_team_abbr').upper()

        # Parse the uniform number
        number = get_value(info_json, 7, 'uniform_number')
        number = 0 if number == "" else int(number)

        # Parse the eligible positions
        positions = get_value(info_json, 12, 'eligible_positions')
        positions = ','.join(
            p for p in list(
                filter(
                    lambda p: 'IR' not in p and 'F' not in p,
                    map(lambda p: p['position'], positions))))

        # Parse the owning team
        ownership = owner_json['ownership']
        if ownership['ownership_type'] == 'freeagents':
            team_id = 0
        elif ownership['ownership_type'] == 'waivers':
            team_id = 99
        else:
            team_id = ownership['owner_team_key'][14:]
        
        # Get the keeper cost for the player
        keeper_cost = keeper_costs.get(id, 14)

        return Player(id, first_name, last_name, nhl_team, number,
                      positions, team_id, keeper_cost)


class Draft(db.Model):
    __tablename__ = 'draftresults'

    player_id = db.Column(db.Integer, db.ForeignKey(Player.id),
                          primary_key=True, autoincrement=False)
    team_id = db.Column(db.Integer, db.ForeignKey(Team.id))
    pick = db.Column(db.Integer)
    round = db.Column(db.Integer)
    keeper = db.Column(db.Boolean)

    def __init__(self, player_id, team_id, pick, round, keeper):
        self.player_id = player_id
        self.team_id = team_id
        self.pick = pick
        self.round = round
        self.keeper = keeper

    @staticmethod
    def parse_json(json, keepers):
        player_id = json['player_key'][6:]
        team_id = json['team_key'][14:]
        pick = json['pick']
        round = json['round']
        keeper = player_id in keepers

        return Draft(player_id, team_id, pick, round, keeper)


class Pick(db.Model):
    __tablename__ = 'picks'

    original_team_id = db.Column(db.Integer, db.ForeignKey(Team.id),
                                 primary_key=True, autoincrement=False)
    draft_round = db.Column(db.Integer, primary_key=True, autoincrement=False)
    owning_team_id = db.Column(db.Integer, db.ForeignKey(Team.id))

    def __init__(self, original_team, owning_team, draft_round):
        self.original_team_id = original_team
        self.owning_team_id = owning_team
        self.draft_round = draft_round

    @staticmethod
    def parse_json(json):
        original_team = json['original_team_key'][14:]
        destination_team = json['destination_team_key'][14:]
        draft_round = json['round']
        return Pick(original_team, destination_team, draft_round)


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    timestamp = db.Column(db.DateTime)
    transaction_type = db.Column(db.String(10))
    faab_bid = db.Column(db.Integer)

    def __init__(self, id, timestamp, transaction_type, faab_bid):
        self.id = id
        self.timestamp = timestamp
        self.transaction_type = transaction_type
        self.faab_bid = faab_bid


class TransactonPlayers(db.Model):
    __tablename__ = 'transaction_players'

    transaction_id = db.Column(db.Integer, db.ForeignKey(Transaction.id),
                               primary_key=True)
    source_id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey(Player.id),
                          primary_key=True)

    def __init__(self, transaction_id, source_id, destination_id, player_id):
        self.transaction_id = transaction_id
        self.source_id = source_id
        self.destination_id = destination_id
        self.player_id = player_id


class TransactionPicks(db.Model):
    __tablename__ = 'transaction_picks'

    transaction_id = db.Column(db.Integer, db.ForeignKey(Transaction.id),
                               primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey(Team.id), primary_key=True)
    destination_id = db.Column(db.Integer, db.ForeignKey(Team.id),
                               primary_key=True)
    draft_round = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.Integer, db.ForeignKey(Team.id),
                            primary_key=True)

    def __init__(self, transaction_id, source_id, destination_id, draft_round,
                 original_id):
        self.transaction_id = transaction_id
        self.source_id = source_id
        self.destination_id = destination_id
        self.draft_round = draft_round
        self.original_id = original_id


class PlayerStats(db.Model):
    __tablename__ = 'player_stats'

    player_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    position = db.Column(db.Text)
    g = db.Column(db.Integer)
    a = db.Column(db.Integer)
    pm = db.Column(db.Integer)
    ppp = db.Column(db.Integer)
    shp = db.Column(db.Integer)
    sog = db.Column(db.Integer)
    hit = db.Column(db.Integer)
    blk = db.Column(db.Integer)
    points = db.Column(db.Float)

    @hybrid_method
    def p(self):
        return self.g + self.a

    @p.expression
    def p(cls):
        return cls.g + cls.a

    def __init__(self, player, date, g, a, pm, ppp, shp, sog, hit, blk,
                 points):
        self.player_id = player.id
        self.date = date
        self.team_id = player.team_id
        self.g = g
        self.a = a
        self.pm = pm
        self.ppp = ppp
        self.shp = shp
        self.sog = sog
        self.hit = hit
        self.blk = blk
        self.points = points

    @staticmethod
    def parse_json(stat_json, point_json, player, date):
        g = stat_json[0]['stat']['value']
        a = stat_json[1]['stat']['value']
        pm = stat_json[2]['stat']['value']
        ppp = stat_json[3]['stat']['value']
        shp = stat_json[4]['stat']['value']
        sog = stat_json[5]['stat']['value']
        hit = stat_json[6]['stat']['value']
        blk = stat_json[7]['stat']['value']
        points = point_json['total']
        return PlayerStats(player, date, g, a, pm, ppp, shp, sog, hit, blk,
                           points)

    @staticmethod
    def getColumnForSort(column_name):
        if (column_name == 'g'):
            return PlayerStats.g
        elif (column_name == 'a'):
            return PlayerStats.a
        elif (column_name == 'p'):
            return PlayerStats.p()
        elif (column_name == 'pm'):
            return PlayerStats.pm
        elif (column_name == 'ppp'):
            return PlayerStats.ppp
        elif (column_name == 'shp'):
            return PlayerStats.shp
        elif (column_name == 'sog'):
            return PlayerStats.sog
        elif (column_name == 'hit'):
            return PlayerStats.hit
        elif (column_name == 'blk'):
            return PlayerStats.blk
        else:
            return PlayerStats.points


class SelectedPositions(db.Model):
    __tablename__ = 'selected_positions'

    player_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    team_id = db.Column(db.Integer)
    position = db.Column(db.Text)

    def __init__(self, player_id, date, team_id, position):
        self.player_id = player_id
        self.date = date
        self.team_id = team_id
        self.position = position


class GoalieStats(db.Model):
    __tablename__ = 'goalie_stats'

    player_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    team_id = db.Column(db.Integer)
    w = db.Column(db.Integer)
    loss = db.Column(db.Integer)
    ga = db.Column(db.Integer)
    sv = db.Column(db.Integer)
    so = db.Column(db.Integer)
    points = db.Column(db.Float)

    def __init__(self, player, date, w, loss, ga, sv, so, points):
        self.player_id = player.id
        self.date = date
        self.team_id = player.team_id
        self.w = w
        self.loss = loss
        self.ga = ga
        self.sv = sv
        self.so = so
        self.points = points

    @staticmethod
    def parse_json(stat_json, point_json, player, date):
        w = stat_json[0]['stat']['value']
        loss = stat_json[1]['stat']['value']
        ga = stat_json[2]['stat']['value']
        sv = stat_json[3]['stat']['value']
        so = stat_json[4]['stat']['value']
        points = point_json['total']
        return GoalieStats(player, date, w, loss, ga, sv, so, points)

    @staticmethod
    def getColumnForSort(column_name):
        if (column_name == 'w'):
            return GoalieStats.w
        elif (column_name == 'l'):
            return GoalieStats.l
        elif (column_name == 'ga'):
            return GoalieStats.ga
        elif (column_name == 'sv'):
            return GoalieStats.sv
        elif (column_name == 'so'):
            return GoalieStats.so
        else:
            return GoalieStats.points


if __name__ == "__main__":
    # Run this file directly to create the database tables.
    print("Creating database tables...")
    db.create_all()
    print("Done!")
