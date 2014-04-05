#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""User management."""

from flask import Blueprint
from flask import jsonify
from flask import request

from luncho.helpers import ForceJSON

from luncho.server import User

from luncho.exceptions import LunchoException


# ----------------------------------------------------------------------
#  Exceptions
# ----------------------------------------------------------------------

class UserDoesNotExistException(LunchoException):
    """There is no such user in the database.

    .. sourcecode:: http

       HTTP/1.1 404 Not found
       Content-Type: text/json

       { "status": "ERROR", "message": "User does not exist" }
    """
    def __init__(self):
        super(UserDoesNotExistException, self).__init__()
        self.status = 404
        self.message = 'User does not exist'


class InvalidPasswordException(LunchoException):
    """Invalid password.

    .. sourcecode:: http

       HTTP/1.1 401 Unauthorized
       Content-Type: text/json

       { "status": "ERROR", "message": "Invalid password" }
    """
    def __init__(self):
        super(InvalidPasswordException, self).__init__()
        self.status = 401
        self.message = 'Invalid password'

# ----------------------------------------------------------------------
#  The blueprint
# ----------------------------------------------------------------------

token = Blueprint('token', __name__)


@token.route('', methods=['POST'])
@ForceJSON(required=['username', 'password'])
def get_token():
    """Return the access token. Most of the other requests require a valid
    token; a token will be valid for a whole day and you should only request a
    token when you either don't have one or you receive a status 400.

    **Example request**:

    .. sourcecode:: http

       { "username": "myUsername", "password": "myPassword" }

    **Success (200)**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: text/json

       { "status": "OK", "token": "access_token" }

    **Invalid password (401)**: :py:class:`InvalidPasswordException`

    **Unknown user (404)**: :py:class:`UserDoesNotExistException`
    """
    json = request.get_json(force=True)

    user = User.query.filter_by(username=json['username']).first()
    if user is None:
        raise UserDoesNotExistException()

    if not user.passhash == json['password']:
        raise InvalidPasswordException()

    return jsonify(status='OK',
                   token=user.get_token())
