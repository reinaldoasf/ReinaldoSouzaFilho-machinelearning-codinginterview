import os

from flask import Flask
from search_app.views import search_app
from scripts.load_news import load_news

BASE_DIR = os.path.join(os.path.realpath(__file__))


def create_app():
    app = Flask(__name__)

    with app.app_context():
        app.config["BASE_DIR"] = BASE_DIR
        app.cli.add_command(load_news)
        app.register_blueprint(search_app)
        return app
