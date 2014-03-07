#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""User management."""

from flask import Blueprint
from flask import request
# from flask import jsonify
# from flask import current_app

users = Blueprint('users', __name__)


@users.route('', methods=['PUT'])
def create_user():
    """Create a new user. Request must be:
    { "username": "username", "full_name": "Full Name", "password": "hash" }"""
    