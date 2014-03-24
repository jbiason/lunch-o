#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Helper functions."""

from functools import wraps

from flask import request
from flask import jsonify

from luncho.server import User

from luncho.exceptions import RequestMustBeJSONException
from luncho.exceptions import InvalidTokenException
from luncho.exceptions import MissingFieldsException
from luncho.exceptions import UserNotFoundException


class ForceJSON(object):
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


def JSONError(status, message, **kwargs):
    """Generate a JSON error message with the error and extra fields.

    :param status: the HTTP status code for the error
    :type status: int
    :param message: The message in the error
    :type message: str
    :param kwargs: Extra fields to be added in the response. *Note*: `status`
                   and `message` should **NOT** be used.
    :type kwargs: kwargs

    :return: A response with the JSON and the status code."""
    resp = jsonify(status='ERROR',
                   message=message,
                   **kwargs)
    resp.status_code = status
    return resp


def user_or_error(token):
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

    return (user, None)
