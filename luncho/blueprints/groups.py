#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Group management."""

from flask import Blueprint
# from flask import request
from flask import jsonify

# from luncho.helpers import ForceJSON
from luncho.helpers import JSONError

from luncho.server import User
# from luncho.server import Group

groups = Blueprint('groups', __name__)


@groups.route('<token>/', methods=['GET'])
def user_groups(token):
    """Return a list of the groups the user belongs or it's the owner."""
    user = User.query.filter_by(token=token).first()
    if not user:
        return JSONError(404, 'User not found (via token)')

    if not user.valid_token(token):
        return JSONError(400, 'Invalid token')

    groups = {}
    for group in user.groups:
        groups[group.id] = {'id': group.id,
                            'name': group.name,
                            'admin': group.owner.username == user.username}

    return jsonify(status='OK',
                   groups=groups.values())
