#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import logging

from flask.ext.script import Manager

from luncho.server import app

manager = Manager(app)


@manager.command
def create_db():
    """Create the database."""

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.config.DEBUG = True
    manager.run()
