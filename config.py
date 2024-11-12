import os
from flask_moment import Moment
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database

SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:abc@localhost:5432/fyurr'
SQLALCHEMY_TRACK_MODIFICATIONS = False


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
