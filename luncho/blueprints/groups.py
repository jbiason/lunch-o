#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Group management."""

import logging

from flask import Blueprint
from flask import request
from flask import jsonify

from sqlalchemy.exc import IntegrityError

from luncho.helpers import ForceJSON
from luncho.helpers import JSONError
from luncho.helpers import user_or_error

from luncho.server import User
from luncho.server import Group
from luncho.server import db

groups = Blueprint('groups', __name__)

LOG = logging.getLogger('luncho.blueprints.groups')


@groups.route('<token>/', methods=['GET'])
def user_groups(token):
    """Return a list of the groups the user belongs or it's the owner."""
    (user, error) = user_or_error(token)
    if error:
        return error

    groups = {}
    for group in user.groups:
        groups[group.id] = {'id': group.id,
                            'name': group.name,
                            'admin': group.owner == user.username}

    return jsonify(status='OK',
                   groups=groups.values())


@groups.route('<token>/', methods=['PUT'])
@ForceJSON(required=['name'])
def create_group(token):
    """Create a new group belonging to the user."""
    (user, error) = user_or_error(token)
    if error:
        return error

    LOG.debug('User status: {verified}'.format(verified=user.verified))

    if not user.verified:
        return JSONError(412, 'Account not verified')

    json = request.get_json(force=True)
    try:
        new_group = Group(name=json['name'],
                          owner=user.username)

        LOG.debug('Current user groups: {groups}'.format(groups=user.groups))
        user.groups.append(new_group)

        db.session.add(new_group)
        db.session.commit()
    except IntegrityError:
        return JSONError(500, 'Unknown error')

    return jsonify(status='OK',
                   id=new_group.id)


@groups.route('<token>/<groupId>/', methods=['POST'])
@ForceJSON()
def update_group(token, groupId):
    """Update group information."""
    (user, error) = user_or_error(token)
    if error:
        return error

    group = Group.query.get(groupId)
    if not group:
        return JSONError(404, 'Group not found')

    LOG.debug('Group = {group}'.format(group=group))

    json = request.get_json(force=True)
    if 'name' in json:
        group.name = json['name']

    if 'maintainer' in json:
        new_maintainer = User.query.get(json['maintainer'])
        if not new_maintainer:
            return JSONError(401, 'New maintainer not found')
        group.owner = new_maintainer.username

    db.session.commit()
    return jsonify(status='OK')


@groups.route('<token>/<groupId>/', methods=['DELETE'])
def delete_group(token, groupId):
    """Delete a group."""
    (user, error) = user_or_error(token)
    if error:
        return error

    group = Group.query.get(groupId)
    if not group:
        return JSONError(404, 'Group not found')

    if not group.owner == user.username:
        return JSONError(401, 'User is not admin')

    db.session.delete(group)
    db.session.commit()

    return jsonify(status='OK')
