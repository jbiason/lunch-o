#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Helper functions."""

import logging

from functools import wraps

from flask import request

from luncho.server import User

from luncho.exceptions import RequestMustBeJSONException
from luncho.exceptions import InvalidTokenException
from luncho.exceptions import MissingFieldsException
from luncho.exceptions import UserNotFoundException
from luncho.exceptions import AuthorizationRequiredException

LOG = logging.getLogger('luncho.helpers')


class ForceJSON(object):
    """Decorator to check if the request is in JSON format."""
    def __init__(self, required=None):
        self.required = required or []

    def __call__(self, func):
        @wraps(func)
        def check_json(*args, **kwargs):
            json = request.get_json(force=True, silent=True)
            if not json:
                raise RequestMustBeJSONException()

            # now we have the JSON, let's check if all the fields are here.
            missing = []
            for field in self.required or []:
                if not field in json:
                    missing.append(field)

            if missing:
                raise MissingFieldsException(missing)

            request.as_json = json     # replace with a forced json
            return func(*args, **kwargs)
        return check_json


def auth(func):
    """Decorator to make the request authenticated via token. If the token
    is missing or it is invalid, the decorator will raise the proper
    exceptions (and return the proper error codes). If the token is valid,
    a "user" property will be added to the request object with the current
    user."""
    @wraps(func)
    def check_auth(*args, **kwargs):
        if not request.authorization:
            LOG.debug('There is no basic auth in the headers')
            raise AuthorizationRequiredException

        token = request.authorization.username
        user = User.query.filter_by(token=token).first()
        if not user:
            LOG.debug('No user with token {token}'.format(token=token))
            raise UserNotFoundException()

        if not user.valid_token(token):
            raise InvalidTokenException()

        request.user = user

        return func(*args, **kwargs)
    return check_auth
