#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import tempfile
import unittest
import json

from luncho import server


class TestUsers(unittest.TestCase):
    """Test users request."""

    def setUp(self):
        (_, server.app.config['SQLITE_FILENAME']) = tempfile.mkstemp()
        self.app = server.app.test_client()

    def tearDown(self):
        os.unlick(server.app.config['SQLITE_FILENAME'])

    def test_create_user(self):
        request = {'username': 'username',
                   'full_name': 'full name',
                   'password': 'hash'}
        rv = self.app.put('/users/',
                          data=json.dumps(request),
                          content_type='application/json')
        print rv.data

if __name__ == '__main__':
    unittest.main()
