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
from luncho.exceptions import UserIsNotAdminException
from luncho.exceptions import NewMaintainerDoesNotExistException

places = Blueprint('places', __name__)


@places.route('', methods=['POST'])
@ForceJSON(required=['name'])
@auth
def create_place():
    """*Authenticated request*

    Create a new place. The user becomes the maintainer of the place once it
    is created.

    **Example request**:

    .. sourcecode:: http

        { "name": "<place name>" }

    :reqheader Authorization: The token received in `/token/`.

    :statuscode 200: Success, the new place id will be returned in the
        response

        .. sourcecode:: http

            { "status": "OK", "id": <place id> }
    :statuscode 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :statuscode 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    :statuscode 412: Account not verified
        (:py:class:`AccountNotVerifiedException`)
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
    """*Authenticated request*

    Return the list of places the user is the maintainer or belongs to one of
    the user's groups.

    :reqheader Authorization: Access token received from `/token/`

    :statuscode 200: Success

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            { "status": "OK", "places": [ { "id": "<placeId>",
                                            "name": "<place name>",
                                            "maintainer": <true if the user is
                                                the group maintainer>},
                                            ...] }

    :statuscode 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :statuscode 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    places = {}
    for group in request.user.groups:
        for place in group.places:
            maintainer = place.owner == request.user.username
            places[place.id] = {'id': place.id,
                                'name': place.name,
                                'maintainer': maintainer}

    for place in Place.query.filter_by(owner=request.user.username):
        maintainer = place.owner == request.user.username
        places[place.id] = {'id': place.id,
                            'name': place.name,
                            'maintainer': maintainer}

    return jsonify(status='OK',
                   places=places.values())


@places.route('<placeId>/', methods=['PUT'])
@ForceJSON()
@auth
def update_place(placeId):
    """*Authenticated request*

    Update the place information. The user must be the maintainer of the place
    to change any information. Partial requests are accepted and missing
    fields will not be changed.

    :param placeId: Id for the place, as returned via GET or POST.

    **Example request**:

    .. sourcecode:: http

       { "name": "New name", "admin": "newAdmin" }

    :reqheader Authorization: Access token received from `/token/`.

    :status 200: Success
    :status 400: Request must be in JSON format
        (:py:class:`RequestMustBeJSONException`)
    :status 403: User is not administrator of the group
        (:py:class:`UserIsNotAdminException`)
    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 404: New maintainer does not exist
        (:py:class:`NewMaintainerDoesNotExistException`)
    :status 404: Place does not exist (:py:class:`ElementNotFoundException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
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


@places.route('<placeId>/', methods=['DELETE'])
@auth
def delete_place(placeId):
    """*Authenticated request*

    Delete the place. The user must be the maintainer of the place to delete
    it.

    :param placeId: The place Id, as returned by GET or POST

    :header Authorization: Access token from `/token/`

    :status 200: Success
    :status 403: User is not the group administrator
        (:py:class:`UserIsNotAdminException`)
    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 404: Place does not exist
        (:py:class:`ElementNotFoundException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    place = Place.query.get(placeId)
    if not place:
        raise ElementNotFoundException('Place')

    if not place.owner == request.user.username:
        raise UserIsNotAdminException()

    db.session.delete(place)
    db.session.commit()

    return jsonify(status='OK')
