#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""User management."""

from flask import Blueprint
from flask import request
from flask import jsonify

from sqlalchemy.exc import IntegrityError

from luncho.helpers import ForceJSON

from luncho.server import User
from luncho.server import db

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
                        validated=False)

        db.session.add(new_user)
        db.session.commit()

        return jsonify(status='OK')
    except IntegrityError:
        resp = jsonify(status='ERROR',
                       error='username already exists')
        resp.status_code = 409
        return resp
