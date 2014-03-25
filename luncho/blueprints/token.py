#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""User management."""

from flask import Blueprint
from flask import jsonify
from flask import request

from luncho.helpers import ForceJSON

from luncho.server import User
from luncho.server import db

from luncho.exceptions import LunchoException


class UserDoesNotExistException(LunchoException):
    """There is no such user in the database."""
    def __init__(self):
        super(UserDoesNotExistException, self).__init__()
        self.status = 404
        self.message = 'User does not exist'


class InvalidPasswordException(LunchoException):
    """Invalid password."""
    def __init__(self):
        super(InvalidPasswordException, self).__init__()
        self.status = 401
        self.message = 'Invalid password'

token = Blueprint('token', __name__)

@token.route('', methods=['POST'])
@ForceJSON(required=['username', 'password'])
def get_token():
    """Return an access token to the user. Request must be:
    { "username": "username", "password": "hash" }"""
    json = request.get_json(force=True)

    user = User.query.filter_by(username=json['username']).first()
    if user is None:
        raise UserDoesNotExistException()

    if not user.passhash == json['password']:
        raise InvalidPasswordException()

    return jsonify(status='OK',
                   token=user.get_token())
