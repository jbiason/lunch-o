#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from flask import Blueprint
from flask import request
from flask import jsonify

from luncho.server import Place
from luncho.server import db

from luncho.helpers import auth
from luncho.helpers import ForceJSON

from luncho.exceptions import AccountNotVerifiedException

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
    new_place = Place(name=json['name'], owner=request.user.username)
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
