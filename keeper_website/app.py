import os
from keeper_website.database import db
from flask import Flask
from keeper_website.views import bp


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    print(app.config['SQLALCHEMY_DATABASE_URI'])
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    db.init_app(app)
    app.register_blueprint(bp)
    return app
