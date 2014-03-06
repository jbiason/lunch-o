#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""The index blueprint. There is nothing here, we just show a summary of
the current API requests."""

from operator import itemgetter

from flask import Blueprint
from flask import jsonify
from flask import current_app

index = Blueprint('index', __name__)

@index.route('')
def show_routes():
    """List the current API"""
    routes = []
    for rule in current_app.url_map.iter_rules():
        endpoint = rule.endpoint
        if endpoint == 'static':
            # the server does not have a static path, but  Flask automatically
            # registers it. so we just ignore it.
            continue

        path = str(rule)
        methods = rule.methods
        doc = current_app.view_functions[endpoint].__doc__

        routes.append([
            path,
            doc
        ])

    routes.sort(key=itemgetter(0))
    return jsonify(routes)
