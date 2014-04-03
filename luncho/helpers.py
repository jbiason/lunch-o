#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Helper functions."""

from functools import wraps

from flask import request

from luncho.server import User

from luncho.exceptions import RequestMustBeJSONException
from luncho.exceptions import InvalidTokenException
from luncho.exceptions import MissingFieldsException
from luncho.exceptions import UserNotFoundException
from luncho.exceptions import AuthorizationRequiredException


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

            return func(*args, **kwargs)
        return check_json


class Auth(object):
    """Validate the token in the Basic Auth header."""

    def __call__(self, func):
        @wraps(func)
        def check_auth(*args, **kwargs):
            if not request.authorization:
                raise AuthorizationRequiredException

            token = request.authorization.username
            user = User.query.filter_by(token=token).first()
            if not user:
                raise UserNotFoundException()

            if not user.valid_token(token):
                raise InvalidTokenException()

            return func(*args, **kwargs)


def user_from_token(token):
    """Returns a tuple with the user that owns the token and the error. If the
    token is valid, user will have the user object and error will be None; if
    there is something wrong with the token, the user will be None and the
    error will have a Response created with :py:func:`JSONError`.

    :param token: The token received
    :type token: str

    :return: Tuple with the user and the error."""
    user = User.query.filter_by(token=token).first()
    if not user:
        raise UserNotFoundException()

    if not user.valid_token(token):
        raise InvalidTokenException()

    return user
