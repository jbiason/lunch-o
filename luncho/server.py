#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import logging
import json
import hmac
import datetime

from flask import Flask
from flask import jsonify

from flask.json import JSONEncoder

from luncho.exceptions import LunchoException


# ----------------------------------------------------------------------
#  JSON encoding with date support
# ----------------------------------------------------------------------
class DateEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return str(obj)
        return json.JSONEncoder.default(self, obj)


# ----------------------------------------------------------------------
#  Config
# ----------------------------------------------------------------------
class Settings(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite://./luncho.db3'
    DEBUG = True
    PLACES_IN_VOTE = 3  # number of places the user can vote

log = logging.getLogger('luncho.server')

# ----------------------------------------------------------------------
#  Load the config
# ----------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Settings)
app.config.from_envvar('LUNCHO_CONFIG', True)
app.json_encoder = DateEncoder

# ----------------------------------------------------------------------
#  Database
# ----------------------------------------------------------------------
from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

user_groups = db.Table('user_groups',
                       db.Column('username',
                                 db.String,
                                 db.ForeignKey('user.username')),
                       db.Column('group_id',
                                 db.Integer,
                                 db.ForeignKey('group.id')))


group_places = db.Table('group_places',
                        db.Column('group',
                                  db.Integer,
                                  db.ForeignKey('group.id')),
                        db.Column('place',
                                  db.Integer,
                                  db.ForeignKey('place.id')))


class User(db.Model):
    username = db.Column(db.String, primary_key=True)
    fullname = db.Column(db.String, nullable=False)
    passhash = db.Column(db.String, nullable=False)
    token = db.Column(db.String)
    issued_date = db.Column(db.Date)
    validated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False)
    groups = db.relationship('Group',
                             secondary=user_groups,
                             backref=db.backref('users', lazy='select'))

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

    def __repr__(self):
        return 'User {username}-{fullname}'.format(
            username=self.username,
            fullname=self.fullname)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    owner = db.Column(db.String, db.ForeignKey('user.username'))
    places = db.relationship('Place',
                             secondary=group_places,
                             backref=db.backref('groups', lazy='select'))

    def __init__(self, name, owner):
        self.name = name
        self.owner = owner.username

    def __repr__(self):
        return 'Group {id}-{name}-{owner}'.format(id=self.id,
                                                  name=self.name,
                                                  owner=self.owner)


class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    owner = db.Column(db.String, db.ForeignKey('user.username'))

    def __init__(self, name, owner=None):
        self.name = name
        self.owner = owner.username

    def __repr__(self):
        return 'Place {id}-{name}-{owner}'.format(id=self.id,
                                                  name=self.name,
                                                  owner=self.owner)


class Vote(db.Model):
    cast = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String, db.ForeignKey('user.username'))
    created_at = db.Column(db.Date, nullable=False)
    group = db.Column(db.Integer, db.ForeignKey('group.id'))

    def __init__(self, user, group):
        self.user = user.username
        self.created_at = datetime.date.today()
        self.group = group
        return

    def __repr__(self):
        values = {'cast': self.cast,
                  'user': self.user,
                  'created_at': self.created_at,
                  'group': self.group}
        return 'Vote {cast}-{user}-{created_at}-{group}'.format(**values)


class CastedVote(db.Model):
    vote = db.Column(db.Integer, db.ForeignKey('vote.cast'), primary_key=True)
    order = db.Column(db.Integer, nullable=False, primary_key=True)
    place = db.Column(db.Integer, db.ForeignKey('place.id'))

    def __init__(self, vote, order, place):
        self.vote = vote.cast
        self.order = order
        self.place = place
        return

    def __repr__(self):
        return 'Cast {vote}-{order}-{place}'.format(vote=self.vote,
                                                    order=self.order,
                                                    place=self.place)


# ----------------------------------------------------------------------
#  Blueprints
# ----------------------------------------------------------------------
from blueprints.users import users
from blueprints.token import token
from blueprints.groups import groups
from blueprints.groups import group_users
from blueprints.groups import group_places
from blueprints.places import places
from blueprints.voting import voting

app.register_blueprint(token, url_prefix='/token/')
app.register_blueprint(users, url_prefix='/user/')
app.register_blueprint(groups, url_prefix='/group/')
app.register_blueprint(group_users, url_prefix='/group/')
app.register_blueprint(group_places, url_prefix='/group/')
app.register_blueprint(places, url_prefix='/place/')
app.register_blueprint(voting, url_prefix='/vote/')


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
        doc = app.view_functions[endpoint].__doc__

        # make the doc a little more... pretty
        summary = doc.split('\n\n')[0]
        summary = ' '.join(line.strip() for line in summary.split('\n'))

        for method in rule.methods:
            if method not in ['GET', 'POST', 'PUT', 'DELETE']:
                # other methods are not required
                continue

            routes.append([
                method.upper() + ' ' + path,
                summary
            ])

    routes.sort(key=lambda url: url[0].split()[1])
    return jsonify(status='OK',
                   api=routes)


# ----------------------------------------------------------------------
#  Error management
# ----------------------------------------------------------------------
@app.errorhandler(LunchoException)
def handle_luncho_exception(error):
    """Normal luncho error."""
    return error.response()
