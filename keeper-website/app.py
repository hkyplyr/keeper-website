import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


def get_db():
    db = SQLAlchemy(__create_app())
    return db


def __get_db():
    db = SQLAlchemy()
    return db


def __create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
    return app


def create_app():
    db = __get_db()
    app = __create_app()
    db.init_app(app)
    from views import bp
    app.register_blueprint(bp)
    return app

