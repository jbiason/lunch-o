#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import datetime

from pony.orm import Database
from pony.orm import PrimaryKey
from pony.orm import Optional
from pony.orm import Required
# from pony.orm import Set

db = Database("sqlite", "tagallery.db", create_db=True)

class User(db.Entity):
    """Users."""
    username = PrimaryKey(unicode)
    passhash = Required(unicode)
    token = Optional(unicode)   # 1. if the user never logged in, they will
                                #    not have a token.
                                # 2. This forces the user to have a single
                                #    login everywhere, per day.
    issue_date = Optional(datetime.datetime)

db.generate_mapping(create_tables=True)
