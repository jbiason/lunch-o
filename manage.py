#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import logging

from flask.ext.script import Manager

from luncho.server import app

manager = Manager(app)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    manager.run()
