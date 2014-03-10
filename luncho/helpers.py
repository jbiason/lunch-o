#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""Helper functions."""

from functools import wraps

from flask import request
from flask import jsonify

class ForceJSON(object):
    def __init__(self, required=None):
        self.required = required or []

    def __call__(self, func):
        @wraps(func)
        def check_json(*args, **kwargs):
            json = request.get_json(force=True, silent=True)
            if not json:
                return jsonify(status='ERROR',
                            error='Request MUST be in JSON format'), 400

            # now we have the JSON, let's check if all the fields are here.
            missing = []
            for field in required or []:
                if not field in json:
                    missing.append(field)

            if missing:
                return jsonify(status='ERROR',
                            error='Missing fields: {fields}'.format(
                                fields=', '.join(missing)))

            return func(*args, **kwargs)
        return check_json
