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


if __name__ == "__main__":

    # We need to make sure Flask knows about its views before we run
    # the app, so we import them. We could do it earlier, but there's
    # a risk that we may run into circular dependencies, so we do it at the
    # last minute here.

    #from views import *
    create_app().run("127.0.0.1", port=5000, debug=True)
