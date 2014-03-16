#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest
import json

from luncho import server

from luncho.server import User


class TestToken(unittest.TestCase):
    """Test token requests."""

    def setUp(self):
        # leave the database blank to make it in memory
        server.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        server.app.config['TESTING'] = True

        self.app = server.app.test_client()
        server.db.create_all()

        # add a user
        self.test_user = User(username='test',
                              fullname='Testing user',
                              passhash='hash')
        server.db.session.add(self.test_user)
        server.db.session.commit()

    def tearDown(self):
        server.db.drop_all(bind=None)

    def test_create_token(self):
        """Test requesting a token"""
        request = {'username': 'test',
                   'password': 'hash'}
        rv = self.app.post('/token/',
                           data=json.dumps(request),
                           content_type='application/json')

        self.assertEqual(rv.status_code, 200)
        response = json.loads(rv.data)
        self.assertTrue('status' in response)
        self.assertEqual(response['status'], 'OK')
        self.assertTrue('token' in response)
        # we can't check the token itself 'cause it should change every day

    def test_reget_token(self):
        """Check if getting the token twice will produce the same token."""
        request = {'username': 'test',
                   'password': 'hash'}
        rv = self.app.post('/token/',
                           data=json.dumps(request),
                           content_type='application/json')

        self.assertEqual(rv.status_code, 200)
        response = json.loads(rv.data)

        # re-request the token
        rv = self.app.post('/token/',
                           data=json.dumps(request),
                           content_type='application/json')

        self.assertTrue(rv.status_code, 200)
        self.assertEqual(response['token'], json.loads(rv.data)['token'])

    def test_no_such_user(self):
        """Check the result of getting a token for a user that doesn't
        exist."""
        request = {'username': 'username',
                   'password': 'hash'}
        rv = self.app.post('/token/',
                           data=json.dumps(request),
                           content_type='application/json')

        self.assertEqual(rv.status_code, 404)
