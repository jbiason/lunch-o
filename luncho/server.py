#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import datetime
import logging

from flask import Flask


# ----------------------------------------------------------------------
#  Config
# ----------------------------------------------------------------------
class Settings(object):
    SQLITE_FILENAME = './luncho.db3'

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
from pony.orm import db_session
from pony.orm import Database
from pony.orm import PrimaryKey
from pony.orm import Optional
from pony.orm import Required

db = Database("sqlite", app.config['SQLITE_FILENAME'], create_db=True)


class User(db.Entity):
    """Users."""
    username = PrimaryKey(unicode)
    fullname = Required(unicode)
    passhash = Required(unicode)
    token = Optional(unicode)   # 1. if the user never logged in, they will
                                #    not have a token.
                                # 2. This forces the user to have a single
                                #    login everywhere, per day.
    issue_date = Optional(datetime.datetime)
    validated = Required(bool, default=False)

db.generate_mapping(create_tables=True)
app.wsgi_app = db_session(app.wsgi_app)

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
