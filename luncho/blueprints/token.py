#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""User management."""

from flask import Blueprint
from flask import jsonify
from flask import request

from luncho.helpers import ForceJSON
from luncho.helpers import JSONError

from luncho.server import User
from luncho.server import db

token = Blueprint('token', __name__)

@token.route('', methods=['POST'])
@ForceJSON(required=['username', 'password'])
def get_token():
    """Return an access token to the user. Request must be:
    { "username": "username", "password": "hash" }"""
    json = request.get_json(force=True)

    user = User.query.filter_by(username=json['username']).first()
    if user is None:
        return JSONError(404, 'User does not exist')

    if not user.passhash == json['password']:
        return JSONError(401, 'Invalid password')

    return jsonify(status='OK',
                   token=user.get_token())
