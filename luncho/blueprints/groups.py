#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Group management."""

import logging

from flask import Blueprint
from flask import request
from flask import jsonify

from luncho.helpers import ForceJSON
from luncho.helpers import auth

from luncho.server import User
from luncho.server import Group
from luncho.server import db

from luncho.exceptions import LunchoException
from luncho.exceptions import ElementNotFoundException


class AccountNotVerifiedException(LunchoException):
    """The account isn't verified.

    .. sourcecode:: http

       HTTP/1.1 412 Precondition Failed
       Content-Type: test/json

       { "status": "ERROR", "message": "Account not verified" }
    """
    def __init__(self):
        super(AccountNotVerifiedException, self).__init__()
        self.status = 412
        self.message = 'Account not verified'


class NewMaintainerDoesNotExistException(LunchoException):
    """The account for the new admin does not exist.

    .. sourcecode:: http

       HTTP/1.1 404 Not found
       Content-Type: test/json

       { "status": "ERROR", "message": "New admin not found" }
    """
    def __init__(self):
        super(NewMaintainerDoesNotExistException, self).__init__()
        self.status = 404
        self.message = 'New admin not found'


class UserIsNotAdminException(LunchoException):
    """The user is not the admin of the group.

    .. sourcecode:: http

       HTTP/1.1 403 Forbidden
       Content-Type: test/json

       { "status": "ERROR", "message": "User is not admin" }
    """
    def __init__(self):
        super(UserIsNotAdminException, self).__init__()
        self.status = 403
        self.message = 'User is not admin'


class UserIsNotMemberException(LunchoException):
    """The user is not the admin of the group.

    .. sourcecode:: http

       HTTP/1.1 403 Forbidden
       Content-Type: test/json

       { "status": "ERROR", "message": "User is not member of this group" }
    """
    def __init__(self):
        super(UserIsNotMemberException, self).__init__()
        self.status = 403
        self.message = 'User is not member of this group'


class SomeUsersNotFoundException(LunchoException):
    """Some users in the add list do not exist.

    .. sourcecode:: http

       HTTP/1.1 404 Not Found
       Content-Type: text/json

       { "status": "ERROR",
         "message", "Some users in the add list do not exist",
         "users": ["<username>", "<username>", ...]}
    """
    def __init__(self, users=None):
        super(SomeUsersNotFoundException, self).__init__()
        self.status = 404
        self.message = 'Some users in the add list do not exist'
        self.users = users

    def response(self):
        json = {'status': 'ERROR',
                'message': self.message}
        if self.users:
            json['users'] = self.users
        response = jsonify(json)
        response.status_code = self.status
        return response


groups = Blueprint('groups', __name__)

LOG = logging.getLogger('luncho.blueprints.groups')


@groups.route('', methods=['GET'])
@auth
def user_groups():
    """*Authenticated request* Return a list of the groups the user belongs or
    it's the owner.

    **Success (200)**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: text/json

       { "status": "OK", "groups": [ { "id": "<group id>" ,
                                       "name": "<group name>",
                                       "admin": <true if the user is admin>},
                                       ...] }

    **User not found (via token) (404)**:
        :py:class:`UserNotFoundException`

    **Authorization required (412)**:
        :py:class:`AuthorizationRequiredException`

    """
    user = request.user
    groups = {}
    for group in user.groups:
        groups[group.id] = {'id': group.id,
                            'name': group.name,
                            'admin': group.owner == user.username}

    return jsonify(status='OK',
                   groups=groups.values())


@groups.route('', methods=['PUT'])
@ForceJSON(required=['name'])
@auth
def create_group():
    """*Authenticated request* Create a new group. Once the group is created,
    the user becomes the administrator of the group.

    **Example request**:

    .. sourcecode:: http

       { "name": "Name for the group" }

    **User not found (via token) (404)**:
        :py:class:`UserNotFoundException`

    **Authorization required (412)**:
        :py:class:`AuthorizationRequiredException`

    **Account not verified (412)**:
        :py:class:`AccountNotVerifiedException`

    """
    user = request.user
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


@groups.route('<groupId>/', methods=['POST'])
@ForceJSON()
@auth
def update_group(groupId):
    """*Authenticated request* Update group information. The user must be
    the administrator of the group to change any information. Partial requests
    are accepted and missing fields are not changed.

    The administrator of the group can be changed by sending the
    "admin" field with the username of the new administrator.

    **Example request**:

    .. sourcecode:: http

       { "name": "new group name": "admin": "newAdmin"}

    **Success (200)**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: text/json

       { "status": "OK" }

    **Request not in JSON format (400)**:
        :py:class:`RequestMustBeJSONException`

    **User is not administrator of the group (403)**:
        :py:class:`UserIsNotAdminException`

    **User not found (via token) (404)**:
        :py:class:`UserNotFoundException`

    **The new admin does not exist (404)**:
        :py:class:`NewMaintainerDoesNotExistException`

    **Authorization required (412)**:
        :py:class:`AuthorizationRequiredException`
    """
    user = request.user
    group = Group.query.get(groupId)
    if not group:
        raise ElementNotFoundException('Group')

    if not group.owner == user.username:
        raise UserIsNotAdminException()

    LOG.debug('Group = {group}'.format(group=group))

    json = request.get_json(force=True)
    if 'name' in json:
        group.name = json['name']

    if 'admin' in json:
        new_maintainer = User.query.get(json['admin'])
        if not new_maintainer:
            raise NewMaintainerDoesNotExistException()

        group.owner = new_maintainer.username
        LOG.debug("new owner of {group} = {new_maintainer}".format(
            group=group, new_maintainer=new_maintainer))

    db.session.commit()
    return jsonify(status='OK')


@groups.route('<groupId>/', methods=['DELETE'])
@auth
def delete_group(groupId):
    """*Authenticated request* Delete a group. Only the administrator of the
    group can delete it.

    **Success (200)**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: text/json

       { "status": "OK" }

    **User is not administrator of the group (403)**:
        :py:class:`UserIsNotAdminException`

    **User not found (via token) (404)**:
        :py:class:`UserNotFoundException`

    **Authorization required (412)**:
        :py:class:`AuthorizationRequiredException`
    """
    user = request.user
    group = Group.query.get(groupId)
    if not group:
        raise ElementNotFoundException('Group')

    if not group.owner == user.username:
        raise UserIsNotAdminException()

    db.session.delete(group)
    db.session.commit()

    return jsonify(status='OK')


@groups.route('<groupId>/users/', methods=['PUT'])
@ForceJSON(required=['usernames'])
@auth
def add_users_to_group(groupId):
    """*Authenticated request* Add users to the group. Only the group
    administrator can add users to their groups.

    **Example request**:

    .. sourcecode:: http

        { "usernames": ["<username>", "<username>", ...] }

    **Success (200)**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: text/json

       { "status": "OK" }

    **Request not in JSON format (400)**:
        :py:class:`RequestMustBeJSONException`

    **User is not administrator of the group (403)**:
        :py:class:`UserIsNotAdminException`

    **User not found (via token) (404)**:
        :py:class:`UserNotFoundException`

    **Incomplete request, some users not found (404)**:
        :py:class:`SomeUsersNotFoundException`

    **Authorization required (412)**:
        :py:class:`AuthorizationRequiredException`
    """
    user = request.user
    group = Group.query.get(groupId)
    if not group:
        raise ElementNotFoundException('Group')

    if not group.owner == user.username:
        raise UserIsNotAdminException()

    json = request.get_json(force=True)
    unknown = []
    for user in json['usernames']:
        user_obj = User.query.get(user)
        if not user_obj:
            unknown.append(user)
            continue

        user_obj.groups.append(group)

    if unknown:
        raise SomeUsersNotFoundException(unknown)

    return jsonify(status='OK')


@groups.route('<groupId>/users/', methods=['GET'])
@auth
def list_group_members(groupId):
    """*Authenticated request* Return a list of the users in the group. The
    user must be part of the group to request this list.

    **Success (200)**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: text/json

       { "status": "OK", "users": [ { "username": "<username>",
                                      "full_name": "<full name>"},
                                      ...] }

    **User is not member of the group (403)**:
        :py:class:`UserIsNotMemberException`

    **User not found (via token) (404)**:
        :py:class:`UserNotFoundException`

    **Incomplete request, some users not found (404)**:
        :py:class:`SomeUsersNotFoundException`

    **Authorization required (412)**:
        :py:class:`AuthorizationRequiredException`
    """
    user = request.user
    group = Group.query.get(groupId)
    if not group:
        raise ElementNotFoundException('Group')

    LOG.debug('user groups: {groups}'.format(groups=user.groups))

    if not group in user.groups:
        raise UserIsNotMemberException()

    users = []
    for user in group.users:
        users.append({'username': user.username,
                      'full_name': user.fullname})

    return jsonify(status='OK', users=users)
