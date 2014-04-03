#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest

from luncho import server

from luncho.server import User

from base import LunchoTests


class TestUsers(LunchoTests):
    """Test users request."""

    def test_create_user(self):
        """Simple user creation."""
        request = {'username': 'username',
                   'full_name': 'full name',
                   'password': 'hash'}
        rv = self.put('/user/', request)
        self.assertJsonOk(rv)

        # db check
        self.assertIsNotNone(User.query.filter_by(username='username').first())

    def test_duplicate_user(self):
        """Create a user that it is already in the database."""
        self.test_create_user()     # create the first user

        # now duplicate
        request = {'username': 'username',
                   'full_name': 'full name',
                   'password': 'hash'}
        rv = self.put('/user/', data=request)
        self.assertJsonError(rv, 409, 'Username already exists')

    def test_no_json(self):
        """Do a request that it's not JSON."""
        rv = self.put('/user/', '')
        self.assertJsonError(rv, 400, 'Request MUST be in JSON format')

    def test_missing_fields(self):
        """Send a request with missing fields."""
        request = {'password': 'hash'}
        rv = self.put('/user/', request)
        self.assertJsonError(rv, 400, 'Missing fields', fields=['username',
                                                                'full_name'])


class TestExistingUsers(LunchoTests):
    """Tests for existing users."""
    def setUp(self):
        super(TestExistingUsers, self).setUp()
        self.user = User(username='test',
                         fullname='Test User',
                         passhash='hash')
        server.db.session.add(self.user)
        server.db.session.commit()
        self.user.get_token()

    def tearDown(self):
        super(TestExistingUsers, self).tearDown()

    def test_update_details(self):
        """Update user details."""
        request = {'full_name': 'New User Name',
                   'password': 'newhash'}
        rv = self.post('/user/',
                       request,
                       self.user.token)

        self.assertJsonOk(rv)

        # check in the database
        user = User.query.filter_by(username='test').first()
        self.assertEqual(user.fullname, request['full_name'])
        self.assertEqual(user.passhash, request['password'])

    def test_wrong_token(self):
        """Send a request with an unexisting token."""
        request = {'full_name': 'New User Name',
                   'password': 'newhash'}
        rv = self.post('/user/',
                       request,
                       'no-token')

        self.assertJsonError(rv, 404, 'User not found (via token)')

    def test_expired_token(self):
        """Send a token that exists but it's not valid for today."""
        # the token is not valid by our standards, but it will be found and
        # and the token for today will not be valid
        self.user.token = 'expired'
        server.db.session.commit()

        request = {'full_name': 'New User Name',
                   'password': 'newhash'}
        rv = self.post('/user/',
                       request,
                       self.user.token)

        self.assertJsonError(rv, 400, 'Invalid token')

    def test_delete_user(self):
        """Delete a user."""
        rv = self.delete('/user/', token=self.user.token)
        self.assertJsonOk(rv)

        # check the database
        user = User.query.filter_by(username='test').first()
        self.assertIsNone(user)

    def test_delete_wrong_token(self):
        """Send a delete to a non-existing token."""
        rv = self.delete('/user/', token='no-token')

        self.assertJsonError(rv, 404, 'User not found (via token)')

    def test_delete_expired_token(self):
        """Send a delete to a token for yesterday."""
        # see note on `test_expired_token`
        self.user.token = 'expired'
        server.db.session.commit()

        rv = self.delete('/user/', token=self.user.token)

        self.assertJsonError(rv, 400, 'Invalid token')


if __name__ == '__main__':
    unittest.main()
