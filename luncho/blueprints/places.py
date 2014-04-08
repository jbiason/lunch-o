#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from flask import Blueprint
from flask import request
from flask import jsonify

from luncho.server import Place
from luncho.server import User
from luncho.server import db

from luncho.helpers import auth
from luncho.helpers import ForceJSON

from luncho.exceptions import AccountNotVerifiedException
from luncho.exceptions import ElementNotFoundException

places = Blueprint('places', __name__)


@places.route('', methods=['POST'])
@ForceJSON(required=['name'])
@auth
def create_place():
    """*Authenticated request* Create a new place. The user becomes the
    maintainer of the place once it is created.

    **Example request**:

    .. sourcecode:: http

        { "name": "<place name>" }

    **Success (200)**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: text/json

        { "status": "OK", "id": <new group id> }

    **User not found (via token) (404)**:
        :py:class:`UserNotFoundException`

    **Authorization required (412)**:
        :py:class:`AuthorizationRequiredException`

    **Account not verified (412)**:
        :py:class:`AccountNotVerifiedException`
    """
    if not request.user.verified:
        raise AccountNotVerifiedException()

    json = request.get_json(force=True)
    new_place = Place(name=json['name'], owner=request.user)
    db.session.add(new_place)
    db.session.commit()

    return jsonify(status='OK',
                   id=new_place.id)


@places.route('', methods=['GET'])
@auth
def get_places():
    """*Authenticated request* Return the list of places the user is the
    maintainer or belongs to one of the user's groups.

    **Success (200)**

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: text/json

       { "status": "OK", "places": [ { "id": "<placeId>",
                                       "name": "<place name>",
                                       "maintainer": <true if the user is the
                                                      group maintainer>},
                                      ...] }

    **User not found (via token) (404)**:
        :py:class:`UserNotFoundException`

    **Authorization required (412)**:
        :py:class:`AuthorizationRequiredException`
    """
    user = request.user
    places = {}
    for group in user.groups:
        for place in group.places:
            maintainer = place.owner == user.username
            places[place.id] = {'id': place.id,
                                'name': place.name,
                                'maintainer': maintainer}

    for place in Place.query.filter_by(owner=user.username):
        maintainer = place.owner == user.username
        places[place.id] = {'id': place.id,
                            'name': place.name,
                            'maintainer': maintainer}

    return jsonify(status='OK',
                   places=places.values())


@places.route('<placeId>/', methods=['PUT'])
@ForceJSON()
@auth
def update_place(placeId):
    """*Authenticated request* Update the place information. The user must be
    the maintainer of the place to change any information. Partial requests
    are accepted and missing fields will not be changed.

    **Example request**:

    .. sourcecode:: http

       { "name": "New name", "admin": "newAdmin" }

    **Success (200)**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Content-Type: text/json

    **Request not in JSON format (400)**:
        :py:class:`RequestMustBeJSONException`

    **User is not administrator of the group (403)**:
        :py:class:`UserIsNotAdminException`

    **User not found (via token) (404)**:
        :py:class:`UserNotFoundException`

    **The new admin does not exist (404)**:
        :py:class:`NewMaintainerDoesNotExistException`

    **The place does not exist (404)**:
        :py:class:`ElementNotFoundException`

    **Authorization required (412)**:
        :py:class:`AuthorizationRequiredException`
    """
    place = Place.query.get(placeId)
    if not place:
        raise ElementNotFoundException('Place')

    if not place.owner == request.user.username:
        raise UserIsNotAdminException()

    name = request.as_json.get('name')
    if name:
        place.name = name

    admin = request.as_json.get('admin')
    if admin:
        new_maintainer = User.query.get(admin)
        if not new_maintainer:
            raise NewMaintainerDoesNotExistException()

        place.owner = new_maintainer.username

    db.session.commit()
    return jsonify(status='OK')
