#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from flask import jsonify


class LunchoException(Exception):
    """Generic exception."""
    def __init__(self):
        self.status = 500
        self.message = 'Unknown error'
        self.extra_fields = None

    def response(self):
        """Return a JSON representation of the exception."""
        json = {'status': 'ERROR',
                'message': self.message}
        if self.extra_fields:
            json.update(self.extra_fields)
        response = jsonify(json)
        response.status_code = self.status
        return response


class RequestMustBeJSONException(LunchoException):
    """The request is not a valid JSON."""
    def __init__(self):
        super(RequestMustBeJSONException, self).__init__()
        self.status = 400
        self.message = 'Request MUST be in JSON format'


class MissingFieldsException(LunchoException):
    """There are missing fields in the request."""
    def __init__(self, fields):
        super(MissingFieldsException, self).__init__()
        self.status = 400
        self.message = 'Missing fields'
        self.extra_fields = {'fields': fields}


class InvalidTokenException(LunchoException):
    """The passed token is invalid."""
    def __init__(self):
        super(InvalidTokenException, self).__init__()
        self.status = 400
        self.message = 'Invalid token'


class UserNotFoundException(LunchoException):
    """There is no user with the token."""
    def __init__(self):
        super(UserNotFoundException, self).__init__()
        self.status = 404
        self.message = 'User not found (via token)'


class ElementNotFoundException(LunchoException):
    """The requested element does not exist."""
    def __init__(self, element_name):
        super(ElementNotFoundException, self).__init__()
        self.status = 404
        self.message = '{element} not found'.format(element=element_name)
