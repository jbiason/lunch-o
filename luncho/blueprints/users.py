#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""User management."""

import logging

from flask import Blueprint
from flask import request
from flask import jsonify

from sqlalchemy.exc import IntegrityError

from luncho.helpers import ForceJSON
from luncho.helpers import JSONError

from luncho.server import User
from luncho.server import db

LOG = logging.getLogger('luncho.blueprints.users')

users = Blueprint('users', __name__)


@users.route('', methods=['PUT'])
@ForceJSON(required=['username', 'full_name', 'password'])
def create_user():
    """Create a new user. Request must be:
    { "username": "username", "full_name": "Full Name", "password": "hash" }"""
    json = request.get_json(force=True)

    try:
        new_user = User(username=json['username'],
                        fullname=json['full_name'],
                        passhash=json['password'],
                        verified=False)

        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        return JSONError(409, 'Username already exists')

    return jsonify(status='OK')


@users.route('<token>/', methods=['POST'])
@ForceJSON()
def update_user(token):
    """Update user information. Request can have the following fields:
    { "full_name": "Full name", "password": "hash" }
    Any other field will be ignored; only fields that need to be changed
    must be send."""
    json = request.get_json(force=True)

    user = User.query.filter_by(token=token).first()
    if not user:
        return JSONError(404, 'User not found (via token)')

    if not user.valid_token(token):
        return JSONError(400, 'Invalid token')

    if 'full_name' in json:
        LOG.debug('Fullname = {fullname}'.format(fullname=json['full_name']))
        user.fullname = json['full_name']

    if 'password' in json:
        LOG.debug('Passhash = {password}'.format(password=json['password']))
        user.passhash = json['password']

    db.session.commit()
    return jsonify(status='OK')


@users.route('<token>/', methods=['DELETE'])
def delete_user(token):
    """Delete a user. No confirmation is send."""
    user = User.query.filter_by(token=token).first()
    if not user:
        return JSONError(404, 'User not found (via token)')

    if not user.valid_token(token):
        return JSONError(400, 'Invalid token')

    db.session.delete(user)
    db.session.commit()
    return jsonify(status='OK')
