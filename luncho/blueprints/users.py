#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""User management."""

import logging

from flask import Blueprint
from flask import request
from flask import jsonify

from sqlalchemy.exc import IntegrityError

from luncho.helpers import ForceJSON
from luncho.helpers import auth

from luncho.server import User
from luncho.server import db

from luncho.exceptions import LunchoException

LOG = logging.getLogger('luncho.blueprints.users')

users = Blueprint('users', __name__)


class UsernameAlreadyExistsException(LunchoException):
    """The username is already taken.

    ..sourcecode:: http

       HTTP/1.1 409 Conflict
       Content-Type: application/json

       { "status": "ERROR", "message": "Username already exists" }
    """
    def __init__(self):
        super(UsernameAlreadyExistsException, self).__init__()
        self.status = 409
        self.message = 'Username already exists'


class InvalidUsernameException(LunchoException):
    """The chosen username has invalid characters.

    .. sourcecode:: http

       HTTP/1.1 406 Not Acceptable
       Content-Type: application/json

       { "status": "ERROR": "message": "Invalid characters in username" }
    """
    def __init__(self):
        super(InvalidUsernameException, self).__init__()
        self.status = 406
        self.message = 'Invalid characters in username'


@users.route('', methods=['POST'])
@ForceJSON(required=['username', 'full_name', 'password'])
def create_user():
    """Create a new user.

    **Example request**

    .. sourcecode:: http

       { "username": "username",
         "full_name": "I'm a person",
         "password": "MyPassword!" }

    **Success (200)**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       { "status": "OK" }

    :statuscode 200: Success
    :statuscode 406: Invalid characters in username
        (:py:class:`InvalidUsernameException`)
    :statuscode 409: Username already exists
        (:py:class:`UsernameAlreadyExistsException`)
    """
    json = request.get_json(force=True)
    invalid_characters = ' !@#$%^&*()|[]{}/\\\'"`~"'
    for char in invalid_characters:
        if char in json['username']:
            raise InvalidUsernameException()

    try:
        new_user = User(username=json['username'],
                        fullname=json['full_name'],
                        passhash=json['password'],
                        verified=False)

        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        raise UsernameAlreadyExistsException()

    return jsonify(status='OK')


@users.route('', methods=['PUT'])
@ForceJSON()
@auth
def update_user():
    """*Authenticated request*

    Update user information. Only the fields send with be changed.

    **Example request**

    Change everything:

    .. sourcecode:: http

        { "full_name": "My New Full Name", "password": "newPassword" }

    Change only the user password:

    .. sourcecode:: http

        { "password": "newPassowrd" }

    **Succcess (200)**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       { "status": "OK" }

    :reqheader Authorization: Token received in `/token/`

    :statuscode 200: Success
    :statuscode 400: Request not in JSON format
        (:py:class:`RequestMustBeJSONException`)
    :statuscode 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :statuscode 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    json = request.get_json(force=True)
    user = request.user

    if 'full_name' in json:
        LOG.debug('Fullname = {fullname}'.format(fullname=json['full_name']))
        user.fullname = json['full_name']

    if 'password' in json:
        LOG.debug('Passhash = {password}'.format(password=json['password']))
        user.passhash = json['password']

    db.session.commit()
    return jsonify(status='OK')


@users.route('', methods=['DELETE'])
@auth
def delete_user():
    """*Authenticated request* Delete a user.

    **Success (200)**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: application/json

       { "status": "OK" }

    :statuscode 200: Success
    :statuscode 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :statuscode 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    db.session.delete(request.user)
    db.session.commit()
    return jsonify(status='OK')
