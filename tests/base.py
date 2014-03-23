#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest
import json

from luncho import server


class LunchoTests(unittest.TestCase):
    """Base testing for all Lunch-o tests."""

    # ------------------------------------------------------------
    #  Test set up and tear down
    # ------------------------------------------------------------
    def setUp(self):
        # leave the database blank to make it in memory
        server.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        server.app.config['TESTING'] = True

        self.app = server.app.test_client()
        server.db.create_all()

    def tearDown(self):
        server.db.drop_all(bind=None)

    # ------------------------------------------------------------
    #  Common assertions for lunch-o
    # ------------------------------------------------------------

    def assertJson(self, expected, response):
        """Compare JSONs."""
        if not isinstance(response, dict):
            response = json.loads(response)

        for key in expected:
            if not key in response:
                self.fail('Key {key} missing in response'.format(
                    key=key))

            if response[key] != expected[key]:
                self.fail('Key "{key}" differs: Expected "{expected}", '
                          'response "{response}"'.format(
                              key=key,
                              expected=expected[key],
                              response=response[key]))

    def assertStatusCode(self, response, status):
        """Check the status code of the response."""
        self.assertEqual(response.status_code, status)

    # ------------------------------------------------------------
    #  Easy way to convert the data to JSON and do requests
    # ------------------------------------------------------------

    def post(self, url, data):
        """Send a POST request to the URL."""
        return self.app.post(url,
                             data=json.dumps(data),
                             content_type='application/json')

    def put(self, url, data):
        """Send a PUT request to the URL."""
        return self.app.put(url,
                            data=json.dumps(data),
                            content_type='application/json')

    def delete(self, url):
        """Send a DELETE request to the URL. There is no data to be send."""
        return self.app.delete(url)

    def get(self, url):
        """Send a GET request to the URL. There is no data to be send."""
        return self.app.get(url)
