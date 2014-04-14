#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Group management."""

import logging

from flask import Blueprint
from flask import request
from flask import jsonify

from luncho.helpers import ForceJSON
from luncho.helpers import auth

from luncho.server import db
from luncho.server import User
from luncho.server import Group
from luncho.server import Place

from luncho.exceptions import ElementNotFoundException
from luncho.exceptions import AccountNotVerifiedException
from luncho.exceptions import NewMaintainerDoesNotExistException
from luncho.exceptions import UserIsNotAdminException
from luncho.exceptions import UserIsNotMemberException


# ----------------------------------------------------------------------
#  The base group management
# ----------------------------------------------------------------------

groups = Blueprint('groups', __name__)

LOG = logging.getLogger('luncho.blueprints.groups')


@groups.route('', methods=['GET'])
@auth
def user_groups():
    """*Authenticated request*

    Return a list of the groups the user belongs or it's the owner.

    :header Authorization: Access token from `/token/`.

    :status 200: Success

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: text/json

            { "status": "OK", "groups": [ { "id": "<group id>" ,
                                            "name": "<group name>",
                                            "admin": <true if the user is
                                                admin>},
                                            ...] }

    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    user = request.user
    groups = {}
    for group in user.groups:
        groups[group.id] = {'id': group.id,
                            'name': group.name,
                            'admin': group.owner == user.username}

    return jsonify(status='OK',
                   groups=groups.values())


@groups.route('', methods=['POST'])
@ForceJSON(required=['name'])
@auth
def create_group():
    """*Authenticated request*

    Create a new group. Once the group is created, the user becomes the
    administrator of the group.

    **Example request**:

    .. sourcecode:: http

       { "name": "Name for the group" }

    :header Authorization: Access token from `/token/`.

    :status 200: Success

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: text/json

            { "status": "OK", "id": <new group id> }

    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    :status 412: Account not verified
        (:py:class:`AccountNotVerifiedException`)
    """
    user = request.user
    LOG.debug('User status: {verified}'.format(verified=user.verified))

    if not user.verified:
        raise AccountNotVerifiedException()

    json = request.get_json(force=True)
    new_group = Group(name=json['name'],
                      owner=user)

    LOG.debug('Current user groups: {groups}'.format(groups=user.groups))
    user.groups.append(new_group)

    db.session.add(new_group)
    db.session.commit()

    return jsonify(status='OK',
                   id=new_group.id)


@groups.route('<int:group_id>/', methods=['PUT'])
@ForceJSON()
@auth
def update_group(group_id):
    """*Authenticated request*

    Update group information. The user must be the administrator of the group
    to change any information. Partial requests are accepted and missing
    fields are not changed.

    The administrator of the group can be changed by sending the
    "admin" field with the username of the new administrator.

    **Example request**:

    .. sourcecode:: http

       { "name": "new group name": "admin": "newAdmin"}

    :header Authorization: Access token from `/token/`.

    :status 200: Success
    :status 400: Request not in JSON format
        (:py:class:`RequestMustBeJSONException`)
    :status 403: User is not the group administrator
        (:py:class:`UserIsNotAdminException`)
    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 404: New administrator does not exist
        (:py:class:`NewMaintainerDoesNotExistException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    user = request.user
    group = Group.query.get(group_id)
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


@groups.route('<int:group_id>/', methods=['DELETE'])
@auth
def delete_group(group_id):
    """*Authenticated request*

    Delete a group. Only the administrator of the group can delete it.

    :param group_id: The group Id

    :header Authorization: Access token from `/token/`.

    :status 200: Success
    :status 403: User is not the group administrator
        (:py:class:`UserIsNotAdminException`)
    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    user = request.user
    group = Group.query.get(group_id)
    if not group:
        raise ElementNotFoundException('Group')

    if not group.owner == user.username:
        raise UserIsNotAdminException()

    db.session.delete(group)
    db.session.commit()

    return jsonify(status='OK')

# ----------------------------------------------------------------------
#  Group users
# ----------------------------------------------------------------------

group_users = Blueprint('group_users', __name__)


@group_users.route('<int:group_id>/users/', methods=['PUT'])
@ForceJSON(required=['usernames'])
@auth
def add_users_to_group(group_id):
    """*Authenticated request*

    Add users to the group. Only the group administrator can add users to
    their groups.

    :param group_id: The group Id

    **Example request**:

    .. sourcecode:: http

        { "usernames": ["<username>", "<username>", ...] }

    :header Authorization: Access token from `/token/`.

    :status 200: Success. Users that couldn't be found will be returned in
        the "not_found" field.

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: text/json

            { "status": "OK", "not_found": [<user>, <user>, ...] }

    :status 400: Request not in JSON format
        (:py:class:`RequestMustBeJSONException`)
    :status 403: User is not the group administrator
        (:py:class:`UserIsNotAdminException`)
    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    user = request.user
    group = Group.query.get(group_id)
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
    db.session.commit()

    return jsonify(status='OK',
                   not_found=unknown)


@group_users.route('<int:group_id>/users/', methods=['GET'])
@auth
def list_group_members(group_id):
    """*Authenticated request*

    Return a list of the users in the group. The user must be part of the
    group to request this list.

    :param group_id: The group Id

    :header Authorization: Access token from `/token/`.

    :status 200: Success

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: text/json

            { "status": "OK", "users": [ { "username": "<username>",
                                            "full_name": "<full name>"},
                                            ...] }

    :status 403: The user is not a member of the group
        (:py:class:`UserIsNotMemberException`)
    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 404: Group not found
        (:py:class:`ElementNotFoundException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    group = Group.query.filter_by(id=group_id).first()
    if not group:
        raise ElementNotFoundException('Group')

    if request.user not in group.users:
        raise UserIsNotMemberException()

    users = []
    for user in group.users:
        users.append({'username': user.username,
                      'full_name': user.fullname})
    db.session.commit()

    return jsonify(status='OK', users=users)


# ----------------------------------------------------------------------
#  Group places
# ----------------------------------------------------------------------

group_places = Blueprint('group_places', __name__)


@group_places.route('<int:group_id>/places/', methods=['GET'])
@auth
def get_group_places(group_id):
    """*Authenticated request*

    Return the list of places for the group. The user must be a member of
    the group the get the list of places.

    :param group_id: The group Id

    :header Authorization: Access token from `/token/`.

    :status 200: Success

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: text/json

            { "status": "OK", "places": [ { "id": "<place id>",
                                            "name": "<place name>"},
                                            ...] }

    :status 403: The user is not a member of the group
        (:py:class:`UserIsNotMemberException`)
    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 404: Group does not exist
        (:py:class:`ElementNotFoundException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    group = Group.query.get(group_id)
    if not group:
        raise ElementNotFoundException('Group')

    if request.user not in group.users:
        raise UserIsNotMemberException()

    places = []
    for place in group.places:
        places.append({'id': place.id,
                       'name': place.name})

    return jsonify(status='OK',
                   places=places)


@group_places.route('<int:group_id>/places/', methods=['POST'])
@ForceJSON(required=['places'])
@auth
def group_add_places(group_id):
    """*Authenticated request*

    Add a list of places to the group. The user must be the admin of the group
    to add a place; the place must belong to one of the group members to be
    able to be added to the group.

    :param group_id: The group Id

    :header Authorization: Access token from `/token/`.

    :status 200: Success. If there are any places that do not belong to group
        members, those will be returned in the "rejected" field; places that
        don't exist will be returned in the "not_found" field.

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: text/json

           { "status": "OK",
             "rejected": [<place>, <place>, ...],
             "not_found": [<place>, <place>, ...] }

    :status 400: Request not in JSON format
        (:py:class:`RequestMustBeJSONException`)
    :status 403: User is not the group administrator
        (:py:class:`UserIsNotAdminException`)
    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    group = Group.query.get(group_id)
    if not group:
        LOG.debug('Cant find group with id {group_id}'.format(
            group_id=group_id))
        raise ElementNotFoundException('Group')

    if not group.owner == request.user.username:
        raise UserIsNotAdminException()

    not_found = []
    rejected = []
    group_users = [user.username for user in group.users]
    LOG.debug('Users in the group: {users}'.format(users=group_users))
    for place_id in request.as_json.get('places', []):
        place = Place.query.get(place_id)
        if not place:
            not_found.append(place_id)
            continue

        LOG.debug('Place {place_id} owner: {owner}'.format(
            place_id=place_id,
            owner=place.owner))
        if place.owner not in group_users:
            rejected.append(place_id)
            continue

        group.places.append(place)
    db.session.commit()

    return jsonify(status='OK',
                   not_found=not_found,
                   rejected=rejected)


@group_places.route('<int:group_id>/places/<int:place_id>/',
                    methods=['DELETE'])
@auth
def group_remove_place(group_id, place_id):
    """*Authenticated request*

    Remove a place from the group. The user must be the group owner.

    :param group_id: The group Id
    :param place_id: The place Id

    :header Authorization: Access token from `/token/`.

    :status 200: Success
    :status 403: User is not the group administrator
        (:py:class:`UserIsNotAdminException`)
    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 404: Group not found (:py:class:`ElementNotFoundException`)
    :status 404: Place is not part of the group
        (:py:class:`ElementNotFoundException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    group = Group.query.get(group_id)
    if not group:
        raise ElementNotFoundException('Group')

    index = -1
    LOG.debug('Places: {places}'.format(places=group.places))
    for (pos, place) in enumerate(group.places):
        LOG.debug('Place {pos} = {place} (search {search})'.format(
            pos=pos, place=place.id, search=place_id))
        if place.id == place_id:
            index = pos
            break

    LOG.debug('Index: {index}'.format(index=index))
    if index == -1:
        raise ElementNotFoundException('Place')

    del group.places[index]
    db.session.commit()
    return jsonify(status='OK')
