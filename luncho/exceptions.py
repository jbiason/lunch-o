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
    """The request is not a valid JSON.

    ..sourcecode:: http

       HTTP/1.1 400 Bad Request
       Content-Type: text/json

       { "status": "ERROR", "message": "Request MUST be in JSON format" }
    """
    def __init__(self):
        super(RequestMustBeJSONException, self).__init__()
        self.status = 400
        self.message = 'Request MUST be in JSON format'


class MissingFieldsException(LunchoException):
    """There are missing fields in the request.

    ..sourcecode:: http

       HTTP/1.1 400 Bad Request
       Content-Type: text/json

       { "status": "ERROR",
         "message": "Missing fields",
         "fields": [<list of missing fields>] }
    """
    def __init__(self, fields):
        super(MissingFieldsException, self).__init__()
        self.status = 400
        self.message = 'Missing fields'
        self.extra_fields = {'fields': fields}


class InvalidTokenException(LunchoException):
    """The passed token is invalid.

    ..sourcecode:: http

       HTTP/1.1 400 Bad REquest
       Content-Type: text/json

       { "status": "ERROR", "message": "Invalid token" }
    """
    def __init__(self):
        super(InvalidTokenException, self).__init__()
        self.status = 400
        self.message = 'Invalid token'


class UserNotFoundException(LunchoException):
    """There is no user with the token.

    ..sourccode:: http

       HTTP/1.1 404 Not Found
       Content-Type: text/json


       { "status": "ERROR", "message": "User not found (via token)" }
    """
    def __init__(self):
        super(UserNotFoundException, self).__init__()
        self.status = 404
        self.message = 'User not found (via token)'


class ElementNotFoundException(LunchoException):
    """The requested element does not exist.

    ..sourcecode:: http

       HTTP/1.1 404 Not Found
       Content-Type: text/json

       { "status": "ERROR", "message": "{element} not found" }

    **Note** {element} will change based on the type of request.
    """
    def __init__(self, element_name):
        super(ElementNotFoundException, self).__init__()
        self.status = 404
        self.message = '{element} not found'.format(element=element_name)


class AuthorizationRequiredException(LunchoException):
    """The request requires auhtorization.

    ..sourcecode:: http

       HTTP/1.1 401 Unauthorized
       Content-Type: text/json

       { "status": "ERROR": "message": "Request requires authorization" }
    """
    def __init__(self):
        super(AuthorizationRequiredException, self).__init__()
        self.status = 401
        self.message = 'Request requires authorization'


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
