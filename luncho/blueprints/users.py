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
    """The username is already taken."""
    def __init__(self):
        super(UsernameAlreadyExistsException, self).__init__()
        self.status = 409
        self.message = 'Username already exists'


@users.route('', methods=['PUT'])
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
       Content-Type: text/json

       { "status": "OK" }

    **User already exists (409)**: :py:class:`UsernameAlreadyExistsException`
    """
    json = request.get_json(force=True)

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


@users.route('', methods=['POST'])
@ForceJSON()
@auth
def update_user():
    """*Authenticated request* Update user information. Only the fields send
    with be changed.

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
       Content-Type: text/json

       { "status": "OK" }

    **Request not in JSON format (400)**:
        :py:class:`RequestMustBeJSONException`

    **User not found (via token) (404)**:
        :py:class:`UserNotFoundException`

    **Authorization required (412)**:
        :py:class:`AuthorizationRequiredException`
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
       Content-Type: text/json

       { "status": "OK" }

    **User not found (via token) (404)**:
        :py:class:`UserNotFoundException`

    **Authorization required (412)**:
        :py:class:`AuthorizationRequiredException`
    """
    db.session.delete(request.user)
    db.session.commit()
    return jsonify(status='OK')
