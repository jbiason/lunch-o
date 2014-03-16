#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""User management."""

from flask import Blueprint
from flask import request
from flask import jsonify
# from flask import current_app

from pony.orm import commit

from luncho.helpers import ForceJSON

from luncho.server import User

users = Blueprint('users', __name__)


@users.route('', methods=['PUT'])
@ForceJSON(required=['username', 'full_name', 'password'])
def create_user():
    """Create a new user. Request must be:
    { "username": "username", "full_name": "Full Name", "password": "hash" }"""
    json = request.get_json(force=True)
    new_user = User(username=json['username'],
                    fullname=json['full_name'],
                    passhash=json['password'],
                    validated=False)
    commit()

    return jsonify(status='OK')
