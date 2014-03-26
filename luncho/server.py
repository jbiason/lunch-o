#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import logging
import json
import hmac
import datetime

from operator import itemgetter

from flask import Flask
from flask import jsonify

from luncho.exceptions import LunchoException


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

userGroups = db.Table('user_groups',
                      db.Column('username',
                                db.String,
                                db.ForeignKey('user.username')),
                      db.Column('group_id',
                                db.Integer,
                                db.ForeignKey('group.id')))


class User(db.Model):
    username = db.Column(db.String, primary_key=True)
    fullname = db.Column(db.String, nullable=False)
    passhash = db.Column(db.String, nullable=False)
    token = db.Column(db.String)
    issued_date = db.Column(db.Date)
    validated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False)
    groups = db.relationship('Group',
                             secondary=userGroups,
                             backref=db.backref('groups', lazy='dynamic'))

    def __init__(self, username, fullname, passhash, token=None,
                 issued_date=None, verified=False):
        self.username = username
        self.fullname = fullname
        self.passhash = passhash
        self.token = token
        self.verified = verified
        self.created_at = datetime.datetime.now()

    def get_token(self):
        """Generate a user token or return the current one for the day."""
        # create a token for the day
        self.token = self._token()
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


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    owner = db.Column(db.String, db.ForeignKey('user.username'))

    def __init__(self, name, owner):
        self.name = name
        self.owner = owner

    def __repr__(self):
        return 'Group {id}-{name}-{owner}'.format(id=self.id,
                                                  name=self.name,
                                                  owner=self.owner)

# ----------------------------------------------------------------------
#  Blueprints
# ----------------------------------------------------------------------
from blueprints.users import users
from blueprints.token import token
from blueprints.groups import groups

app.register_blueprint(token, url_prefix='/token/')
app.register_blueprint(users, url_prefix='/user/')
app.register_blueprint(groups, url_prefix='/group/')


# ----------------------------------------------------------------------
#  The index is a special case
# ----------------------------------------------------------------------
@app.route('/', methods=['GET'])
def show_api():
    """Return the list of APIs."""
    routes = []

    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        if endpoint == 'static':
            # the server does not have a static path, but  Flask automatically
            # registers it. so we just ignore it.
            continue

        path = str(rule)
        # methods = rule.methods
        doc = app.view_functions[endpoint].__doc__

        # make the doc a little more... pretty
        summary = doc.split('\n\n')[0]
        summary = ' '.join(line.strip() for line in summary.split('\n'))

        routes.append([
            path,
            summary
        ])

    routes.sort(key=itemgetter(0))
    return jsonify(status='OK', api=routes)


# ----------------------------------------------------------------------
#  Error management
# ----------------------------------------------------------------------
@app.errorhandler(LunchoException)
def handle_luncho_exception(error):
    """Normal luncho error."""
    return error.response()
