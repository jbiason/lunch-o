#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Group management."""

import logging

from flask import Blueprint
from flask import request
from flask import jsonify

from luncho.helpers import ForceJSON
from luncho.helpers import user_from_token

from luncho.server import User
from luncho.server import Group
from luncho.server import db

from luncho.exceptions import LunchoException
from luncho.exceptions import ElementNotFoundException


class AccountNotVerifiedException(LunchoException):
    """The account isn't verified."""
    def __init__(self):
        super(AccountNotVerifiedException, self).__init__()
        self.status = 412
        self.message = 'Account not verified'


class NewMaintainerDoesNotExistException(LunchoException):
    """The account for the new maintainer does not exist."""
    def __init__(self):
        super(NewMaintainerDoesNotExistException, self).__init__()
        self.status = 412
        self.message = 'New maintainer not found'


class UserIsNotAdminException(LunchoException):
    """The user is not the admin of the group."""
    def __init__(self):
        super(UserIsNotAdminException, self).__init__()
        self.status = 401
        self.message = 'User is not admin'


groups = Blueprint('groups', __name__)

LOG = logging.getLogger('luncho.blueprints.groups')


@groups.route('<token>/', methods=['GET'])
def user_groups(token):
    """Return a list of the groups the user belongs or it's the owner."""
    user = user_from_token(token)
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
    user = user_from_token(token)
    LOG.debug('User status: {verified}'.format(verified=user.verified))

    if not user.verified:
        raise AccountNotVerifiedException()

    json = request.get_json(force=True)
    new_group = Group(name=json['name'],
                      owner=user.username)

    LOG.debug('Current user groups: {groups}'.format(groups=user.groups))
    user.groups.append(new_group)

    db.session.add(new_group)
    db.session.commit()

    return jsonify(status='OK',
                   id=new_group.id)


@groups.route('<token>/<groupId>/', methods=['POST'])
@ForceJSON()
def update_group(token, groupId):
    """Update group information."""
    user = user_from_token(token)
    group = Group.query.get(groupId)
    if not group:
        raise ElementNotFoundException('Group')

    if not group.owner == user.username:
        raise UserIsNotAdminException()

    LOG.debug('Group = {group}'.format(group=group))

    json = request.get_json(force=True)
    if 'name' in json:
        group.name = json['name']

    if 'maintainer' in json:
        new_maintainer = User.query.get(json['maintainer'])
        if not new_maintainer:
            raise NewMaintainerDoesNotExistException()

        group.owner = new_maintainer.username

    db.session.commit()
    return jsonify(status='OK')


@groups.route('<token>/<groupId>/', methods=['DELETE'])
def delete_group(token, groupId):
    """Delete a group."""
    user = user_from_token(token)
    group = Group.query.get(groupId)
    if not group:
        raise ElementNotFoundException('Group')

    if not group.owner == user.username:
        raise UserIsNotAdminException()

    db.session.delete(group)
    db.session.commit()

    return jsonify(status='OK')
