#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Voting"""

import datetime
import logging
import operator

from flask import Blueprint
from flask import jsonify
from flask import request
from flask import current_app

from luncho.helpers import ForceJSON
from luncho.helpers import auth

from luncho.server import db
from luncho.server import Group
from luncho.server import Vote
from luncho.server import CastedVote
from luncho.server import Place

from luncho.exceptions import LunchoException
from luncho.exceptions import UserIsNotMemberException
from luncho.exceptions import ElementNotFoundException

LOG = logging.getLogger('luncho.blueprints.voting')

voting = Blueprint('voting', __name__)


# ----------------------------------------------------------------------
#  Exceptions
# ----------------------------------------------------------------------

class VoteAlreadyCastException(LunchoException):
    """The user already voted today.

    .. sourcecode:: http
       HTTP/1.1 406 Not Acceptable
       Content-Type: text/json

       { "status": "ERROR", "message": "User already voted today" }
    """
    def __init__(self):
        super(VoteAlreadyCastException, self).__init__()
        self.status = 406
        self.message = 'User already voted today'


class InvalidNumberOfPlacesCastedException(LunchoException):
    """The number of places in the vote casted is invalid.

    .. sourcecode:: http
       HTTP/1.1 406 Not Acceptable
       Content-Type: text/json

       { "status": "ERROR",
         "message": "The vote must register {places} places" }
    """
    def __init__(self, places):
        super(InvalidNumberOfPlacesCastedException, self).__init__()
        self.status = 406
        self.message = 'The vote must register {places} places'.format(
            places=places)


class PlaceDoesntBelongToGroupException(LunchoException):
    """The indicated places do not belong to the group.

    .. sourcecode:: http
       http/1.1 404 Not Found
       Content-Type: text/json

       { "status": "ERROR",
         "message": "Places are not part of this group",
         "places": [<place>, <place>, ...]}
    """
    def __init__(self, places):
        super(PlaceDoesntBelongToGroupException, self).__init__()
        self.status = 404
        self.message = 'Places are not part of this group'
        self.places = places

    def _json(self):
        super(PlaceDoesntBelongToGroupException, self)._json()
        self.json['places'] = self.places


class PlacesVotedMoreThanOnceException(LunchoException):
    """The indicated places were voted more than once. Only a vote
    per place is allowed.

    .. sourcecode:: http
       HTTP/1.1 409 Conflict
       Content-Type: text/json

       { "status": "ERROR",
         "message": "Places voted more than once",
         "places": [<place>, <place>, ...]}
    """
    def __init__(self, places):
        super(PlacesVotedMoreThanOnceException, self).__init__()
        self.status = 409
        self.message = 'Places voted more than once'
        self.places = places
        return

    def _json(self):
        super(PlacesVotedMoreThanOnceException, self)._json()
        self.json['places'] = list(self.places)


# ----------------------------------------------------------------------
#  Voting
# ----------------------------------------------------------------------

@voting.route('<int:group_id>/', methods=['POST'])
@ForceJSON(required=['choices'])
@auth
def cast_vote(group_id):
    """*Authenticated request*

    Cast a vote for a group. A user can cast a vote in a single group
    per day.

    :header Authorization: Access token from '/token/'.

    :status 200: Success
    :status 400: Request MUST be in JSON format
        (:pyu:class:`RequestMustBeJSONException`)
    :status 400: Missing fields
        (:py:class:`MissingFieldsException`)
    :status 403: User is not member of this group
        (:py:class:`UserIsNotMemberException`)
    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 404: Group not found
        (:py:class:`ElementNotFoundException`)
    :status 404: Place not found
        (:py:class:`ElementNotFoundException`)
    :status 404: Place doesn't belong to the group
        (:py:class:`PlaceDoesntBelongToGroupException`)
    :status 406: User already voted today
        (:py:class:`VoteAlreadyCastException`)
    :status 406: Number of places vote doesn't match the required
        (:py:class:`InvalidNumberOfPlacesCastedException`)
    :status 409: Places voted more than once
        (:py:class:`PlacesVotedMoreThanOnceException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    # check if the group exists
    group = Group.query.get(group_id)
    if not group:
        raise ElementNotFoundException('Group')

    # check if the user belongs to the group
    if request.user not in group.users:
        LOG.debug('User is not member')
        raise UserIsNotMemberException()

    choices = request.as_json.get('choices')

    # check if the user voted today already, for any group
    _already_voted(request.user.username)

    # check if the user is trying to vote in the same place twice
    _check_duplicates(choices)

    # check the number of votes the user casted
    _check_place_count(choices, group.places)

    # check if the places exist and are part of the group
    # (don't vote yet, so we can stop the whole thing if there is anything
    #  wrong)
    _check_places(choices, group.places)

    # finally, cast the vote
    vote = Vote(request.user, group_id)
    LOG.debug('User {user} casted vote {vote}'.format(user=request.user,
                                                      vote=vote))
    db.session.add(vote)
    db.session.commit()     # so vote gets an id
    for (pos, place_id) in enumerate(request.as_json.get('choices')):
        place = CastedVote(vote, pos, place_id)
        LOG.debug('\tVoted {place} in {pos} position'.format(place=place,
                                                             pos=pos))
        db.session.add(place)

    db.session.commit()

    return jsonify(status='OK')


@voting.route('<int:group_id>/', methods=['GET'])
@auth
def get_vote(group_id):
    """*Authenticated request*

    Return the current voting status for the group.

    :header Authorization: Access token from '/token/'.

    :status 200: Success

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-type: text/json

           { "status": "OK",
             "closed": <True if all members voted>,
             "results": [ {"id": <place id>,
                           "name": "<place name>",
                           "points": <points> },
                          {"id": <place id>,
                           "name": "<place name>",
                           "points": <points> },
                          ...  ] }
    :status 403: User is not member of this group
        (:py:class:`UserIsNotMemberException`)
    :status 404: User not found (via token)
        (:py:class:`UserNotFoundException`)
    :status 404: Group not found
        (:py:class:`ElementNotFoundException`)
    :status 412: Authorization required
        (:py:class:`AuthorizationRequiredException`)
    """
    # check if the group exists
    group = Group.query.get(group_id)
    if not group:
        raise ElementNotFoundException('Group')

    # check if the user belongs to the group
    if request.user not in group.users:
        LOG.debug('User is not member')
        raise UserIsNotMemberException()

    # calculate the decrementating value, based on the number of places
    max_places = min(current_app.config['PLACES_IN_VOTE'],
                     len(group.places))
    if max_places == 0:
        # this means the group have no places at all, so the result will
        # *always* be an empty list, closed.
        return jsonify(status='OK',
                       results=[],
                       closed=True)

    decrement = round(1.0 / float(max_places), 1)
    LOG.debug('For {places}, the decrement factor is {decrement}'.format(
        places=max_places, decrement=decrement))

    # get the votes for today
    today = datetime.date.today()
    group_votes = Vote.query.filter_by(group=group.id,
                                       created_at=today)
    points = {}
    votes = 0
    for vote in group_votes:
        votes += 1
        # get the casted votes
        vote_value = 1.0
        for cast in CastedVote.query.filter_by(vote=vote.cast):
            if cast.place not in points:
                points[cast.place] = 0.0
            points[cast.place] += vote_value
            vote_value -= decrement

    LOG.debug('Unsorted results: {results}'.format(results=points))

    # check if the voting is closed. for that, the number of votes must be
    # equal to the number of users in the group
    closed = False
    if votes == len(group.users):
        closed = True

    # sort the results from most voted to least voted
    # (turn the dictionary into a list with place,points values, then sort
    #  them by points)
    result = []
    for (place_id, points) in sorted(points.items(),
                                     key=operator.itemgetter(1)):
        place = Place.query.get(place_id)
        result.append({'id': place.id,
                       'name': place.name,
                       'points': points})

    return jsonify(status='OK',
                   closed=closed,
                   results=result)


# ----------------------------------------------------------------------
#  Helpers
# ----------------------------------------------------------------------

def _already_voted(username):
    """Check if the user already voted today."""
    today = datetime.date.today()
    today_vote = Vote.query.filter_by(user=username,
                                      created_at=today).first()
    if today_vote:
        LOG.debug('User already voted today')
        raise VoteAlreadyCastException()
    return


def _check_place_count(choices, group_places):
    """Check if the user voted in the right number of places."""
    # maybe the group have less than PLACES_IN_VOTE choices...
    max_places = min(current_app.config['PLACES_IN_VOTE'],
                     len(group_places))
    if len(choices) != max_places:
        LOG.debug('Max places = {max_places}, voted for {choices}'.format(
                  max_places=max_places, choices=len(choices)))
        raise InvalidNumberOfPlacesCastedException(max_places)
    return


def _check_places(choices, group_places):
    """Check if the places the user voted exist and belong to the group."""
    for place_id in choices:
        place = Place.query.get(place_id)
        if not place:
            raise ElementNotFoundException('Place')

        if place not in group_places:
            raise PlaceDoesntBelongToGroupException(place_id)
    return


def _check_duplicates(choices):
    """Check if the places the user voted are listed more than once."""
    duplicates = set([x for x in choices if choices.count(x) > 1])
    if len(duplicates) > 0:
        raise PlacesVotedMoreThanOnceException(duplicates)
    return
