#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest
import json

from luncho import server

from luncho.server import User

from base import LunchoTests


class TestToken(LunchoTests):
    """Test token requests."""

    def setUp(self):
        # leave the database blank to make it in memory
        super(TestToken, self).setUp()
        # add a user
        self.test_user = User(username='test',
                              fullname='Testing user',
                              passhash='hash')
        server.db.session.add(self.test_user)
        server.db.session.commit()

    def tearDown(self):
        super(TestToken, self).tearDown()

    def test_create_token(self):
        """Test requesting a token"""
        request = {'username': 'test',
                   'password': 'hash'}
        rv = self.app.post('/token/',
                           data=json.dumps(request),
                           content_type='application/json')

        self.assertJsonOk(rv)
        response = json.loads(rv.data)
        self.assertTrue('token' in response)
        # we can't check the token itself 'cause it should change every day

    def test_reget_token(self):
        """Check if getting the token twice will produce the same token."""
        request = {'username': 'test',
                   'password': 'hash'}
        rv = self.app.post('/token/',
                           data=json.dumps(request),
                           content_type='application/json')
        self.assertJsonOk(rv)
        response = json.loads(rv.data)

        # re-request the token
        rv = self.app.post('/token/',
                           data=json.dumps(request),
                           content_type='application/json')
        self.assertJsonOk(rv)
        self.assertEqual(response['token'], json.loads(rv.data)['token'])

    def test_no_such_user(self):
        """Check the result of getting a token for a user that doesn't
        exist."""
        request = {'username': 'username',
                   'password': 'hash'}
        rv = self.app.post('/token/',
                           data=json.dumps(request),
                           content_type='application/json')
        self.assertJsonError(rv, 404, 'User does not exist')

    def test_wrong_password(self):
        """Try to log with the wrong password."""
        request = {'username': 'test',
                   'password': 'nothing'}
        rv = self.app.post('/token/',
                           data=json.dumps(request),
                           content_type='application/json')
        self.assertJsonError(rv, 401, 'Invalid password')

if __name__ == '__main__':
    unittest.main()
