#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest
import json

from luncho import server

from luncho.server import User


class TestUsers(unittest.TestCase):
    """Test users request."""

    def setUp(self):
        # leave the database blank to make it in memory
        server.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        server.app.config['TESTING'] = True

        self.app = server.app.test_client()
        server.db.create_all()

    def tearDown(self):
        server.db.drop_all(bind=None)

    def test_create_user(self):
        """Simple user creation."""
        request = {'username': 'username',
                   'full_name': 'full name',
                   'password': 'hash'}
        rv = self.app.put('/user/',
                          data=json.dumps(request),
                          content_type='application/json')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(json.loads(rv.data), {'status': 'OK'})

        # db check
        self.assertIsNotNone(User.query.filter_by(username='username').first())

    def test_duplicate_user(self):
        """Check the status for trying to create a user that it is already
        in the database."""
        self.test_create_user()     # create the first user

        # now duplicate
        request = {'username': 'username',
                   'full_name': 'full name',
                   'password': 'hash'}
        rv = self.app.put('/user/',
                          data=json.dumps(request),
                          content_type='application/json')

        expected = {"status": "ERROR",
                    "error": "username already exists"}

        self.assertEqual(rv.status_code, 409)
        self.assertEqual(json.loads(rv.data), expected)

    def test_no_json(self):
        """Check the status when doing a request that it's not JSON."""
        rv = self.app.put('/user/',
                          data='',
                          content_type='text/html')

        expected = {"error": "Request MUST be in JSON format",
                    "status": "ERROR"}
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(json.loads(rv.data), expected)

    def test_missing_fields(self):
        request = {'password': 'hash'}
        rv = self.app.put('/user/',
                          data=json.dumps(request),
                          content_type='application/json')

        resp = {'error': 'Missing fields: username, full_name',
                'status': 'ERROR'}
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(json.loads(rv.data), resp)

if __name__ == '__main__':
    unittest.main()
