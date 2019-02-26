from app import db
from utils.json_utils import get_value

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

    def __init__(self, id, first_name, last_name, nhl_team, number, positions, team_id):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.nhl_team = nhl_team
        self.number = number
        self.positions = positions
        self.team_id = team_id

    @staticmethod
    def parse_json(info_json, owner_json):
        id = get_value(info_json, 1, 'player_id')
        first_name = get_value(info_json, 2, 'name')['first'].replace("'", "''")
        last_name = get_value(info_json, 2, 'name')['last'].replace("'", "''")
        nhl_team = get_value(info_json, 6, 'editorial_team_abbr').upper()

        # Parse the uniform number
        number = get_value(info_json, 7, 'uniform_number')
        number = 0 if number == "" else int(number)

        # Parse the eligible positions 
        positions = get_value(info_json, 12, 'eligible_positions')
        positions = ','.join(p for p in list(filter(lambda p: 'IR' not in p and 'F' not in p, map(lambda p: p['position'], positions))))

        # Parse the owning team
        ownership = owner_json['ownership']
        if ownership['ownership_type'] == 'freeagents' or ownership['ownership_type'] == 'waivers':
            team_id = 0
        else:
            team_id = ownership['owner_team_key'][13:]
        
        return Player(id, first_name, last_name, nhl_team, number, positions, team_id)

class Draft(db.Model):
    __tablename__ = 'draftresults'

    player_id = db.Column(db.Integer, db.ForeignKey(Player.id), primary_key=True, autoincrement=False)
    team_id = db.Column(db.Integer, db.ForeignKey(Team.id))
    pick = db.Column(db.Integer)
    round = db.Column(db.Integer)

class Pick(db.Model):
    __tablename__ = 'picks'

    original_team_id = db.Column(db.Integer, db.ForeignKey(Team.id), primary_key=True, autoincrement=False)
    draft_round = db.Column(db.Integer, primary_key=True, autoincrement=False)
    owning_team_id = db.Column(db.Integer, db.ForeignKey(Team.id))

class Transaction(db.Model):
    __tablename__ = 'transactions'

    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    timestamp = db.Column(db.DateTime)
    transaction_type = db.Column(db.String(10))
    acquired_players = db.Column(db.JSON)
    acquired_picks = db.Column(db.JSON)
    relinquished_players = db.Column(db.JSON)
    relinquished_picks = db.Column(db.JSON)

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

    def __init__(self, player, date, g, a, pm, ppp, shp, sog, hit, blk, points):
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
        return PlayerStats(player, date, g, a, pm, ppp, shp, sog, hit, blk, points)

class SelectedPositions(db.Model):
    __tablename__ = 'selected_positions'

    player_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    position = db.Column(db.Text)

    def __init__(self, player_id, date, position):
        self.player_id = player_id
        self.date = date
        self.position = position

class GoalieStats(db.Model):
    __tablename__ = 'goalie_stats'

    player_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    team_id = db.Column(db.Integer)
    w = db.Column(db.Integer)
    l = db.Column(db.Integer)
    ga = db.Column(db.Integer)
    sv = db.Column(db.Integer)
    so = db.Column(db.Integer)
    points = db.Column(db.Float)

    def __init__(self, player, date, w, l, ga, sv, so, points):
        self.player_id = player.id
        self.date = date
        self.team_id = player.team_id
        self.w = w
        self.l = l
        self.ga = ga
        self.sv = sv
        self.so = so
        self.points = points

    @staticmethod
    def parse_json(stat_json, point_json, player, date):
        w = stat_json[0]['stat']['value']
        l = stat_json[1]['stat']['value']
        ga = stat_json[2]['stat']['value']
        sv = stat_json[3]['stat']['value']
        so = stat_json[4]['stat']['value']
        points = point_json['total']
        return GoalieStats(player, date, w, l, ga, sv, so, points)

if __name__ == "__main__":
    # Run this file directly to create the database tables.
    print("Creating database tables...")
    db.create_all()
    print("Done!")