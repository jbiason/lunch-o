#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import logging

from flask import Flask


# ----------------------------------------------------------------------
#  Config
# ----------------------------------------------------------------------
class Settings(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite://./luncho.db3'
    DEBUG = True

log = logging.getLogger('luncho.server')

# ----------------------------------------------------------------------
#  Load the config
# ----------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Settings)
app.config.from_envvar('LUCNHO_CONFIG', True)

# ----------------------------------------------------------------------
#  Database
# ----------------------------------------------------------------------
from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)


class User(db.Model):
    username = db.Column(db.String, primary_key=True)
    full_name = db.Column(db.String, nullable=False)
    passhash = db.Column(db.String, nullable=False)
    token = db.Column(db.String)
    issued_date = db.Column(db.Date)
    validated = db.Column(db.Boolean, default=False)

    def __init__(self, username, full_name, passhash):
        self.username = username
        self.full_name = full_name
        self.passhash = passhash

# ----------------------------------------------------------------------
#  Blueprints
# ----------------------------------------------------------------------
from blueprints.index import index
from blueprints.users import users

app.register_blueprint(index, url_prefix='/')
app.register_blueprint(users, url_prefix='/user/')


# ----------------------------------------------------------------------
#  Main
# ----------------------------------------------------------------------
if __name__ == '__main__':
    log.warning('Use manage.py to run the server.')
    sys.exit(1)
