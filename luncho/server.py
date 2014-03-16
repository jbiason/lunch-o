#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import logging
import json
import hmac
import datetime

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
    fullname = db.Column(db.String, nullable=False)
    passhash = db.Column(db.String, nullable=False)
    token = db.Column(db.String)
    issued_date = db.Column(db.Date)
    validated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, username, fullname, passhash, token=None,
                 issued_date=None, validated=False):
        self.username = username
        self.fullname = fullname
        self.passhash = passhash
        self.token = token
        self.issued_date = issued_date
        self.validated = validated
        self.created_at = datetime.datetime.now()

    def get_token(self):
        """Generate a user token or return the current one for the day."""
        if self.token and self.issued_date == datetime.date.today():
            return self.token

        # create a token for the day
        self.token = self._token()
        self.issued_date = datetime.date.today()
        db.session.commit()
        return self._token()

    def valid_token(self, token):
        """Check if the user token is valid."""
        return (self.token == self._token())

    def _token(self):
        """Generate a token with the user information and the current date."""
        phrase = json.dumps({'username': self.username,
                             'issued_date': datetime.date.today().isoformat()})
        return hmac.new(self.created_at.isoformat(), phrase).hexdigest()


# ----------------------------------------------------------------------
#  Blueprints
# ----------------------------------------------------------------------
from blueprints.index import index
from blueprints.users import users
from blueprints.token import token

app.register_blueprint(index, url_prefix='/')
app.register_blueprint(token, url_prefix='/token/')
app.register_blueprint(users, url_prefix='/user/')


# ----------------------------------------------------------------------
#  Main
# ----------------------------------------------------------------------
if __name__ == '__main__':
    log.warning('Use manage.py to run the server.')
    sys.exit(1)
