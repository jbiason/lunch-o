#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys

from flask import Flask

# ----------------------------------------------------------------------
#  Config
# ----------------------------------------------------------------------
SQLITE_FILENAME = './luncho.db3'

# ----------------------------------------------------------------------
#  Load the config
# ----------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('LUCNHO_CONFIG', True)

# ----------------------------------------------------------------------
#  Blueprints
# ----------------------------------------------------------------------
from blueprints.index import index

app.register_blueprint(index, url_prefix='/')

# ----------------------------------------------------------------------
#  Database
# ----------------------------------------------------------------------
from pony.orm import db_session
app.wsgi_app = db_session(app.wsgi_app)

# ----------------------------------------------------------------------
#  Main
# ----------------------------------------------------------------------
if __name__ == '__main__':
    log.warning('Use manage.py to run the server.')
    sys.exit(1)

