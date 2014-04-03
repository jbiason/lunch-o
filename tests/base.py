#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest
import json
import base64

from luncho import server


def _token_header(token=None):
    """Generate the headers required for using the token as an auth."""
    if not token:
        return None

    message = '{token}:Ignored'.format(token=token)
    headers = {'Authorization': 'Basic {code}'.format(
        code=base64.b64encode(message))}
    return headers


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

    def assertJson(self, response, expected):
        """Compare JSONs.

        :param response: a test_client response
        :param expected: expected response
        :type expected: dict"""
        response = json.loads(response.data)

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

    def assertJsonOk(self, response, **extras):
        """Assert the the response is an OK. Extra fields can be expected
        in the `extras` parameter."""
        expected = {'status': 'OK'}
        if extras:
            expected.update(extras)
        self.assertStatusCode(response, 200)
        self.assertJson(response, expected)

    def assertJsonError(self, response, status, message, **extras):
        """Assert that the response is an error. Extra fields returned in
        the JSON can be expected in the `extras` parameter."""
        expected = {'status': 'ERROR', 'message': message}
        if extras:
            expected.update(extras)

        self.assertStatusCode(response, status)
        self.assertJson(response, expected)

    # ------------------------------------------------------------
    #  Easy way to convert the data to JSON and do requests
    # ------------------------------------------------------------

    def post(self, url, data, token=None):
        """Send a POST request to the URL."""
        return self.app.post(url,
                             data=json.dumps(data),
                             headers=_token_header(token),
                             content_type='application/json')

    def put(self, url, data, token=None):
        """Send a PUT request to the URL."""
        return self.app.put(url,
                            data=json.dumps(data),
                            headers=_token_header(token),
                            content_type='application/json')

    def delete(self, url, token=None):
        """Send a DELETE request to the URL. There is no data to be send."""
        return self.app.delete(url,
                               headers=_token_header(token))

    def get(self, url, token=None):
        """Send a GET request to the URL. There is no data to be send."""
        return self.app.get(url,
                            headers=_token_header(token))
