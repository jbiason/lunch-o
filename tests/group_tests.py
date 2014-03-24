#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest

from luncho import server

from luncho.server import User

from base import LunchoTests


class TestGroups(LunchoTests):
    """Test groups requests."""

    def setUp(self):
        super(TestGroups, self).setUp()
        # create a user to have a token
        self.user = User(username='test',
                         fullname='Test User',
                         passhash='hash')
        self.user.verified = True
        server.db.session.add(self.user)
        server.db.session.commit()
        self.user.get_token()
        return

    def test_empty_list(self):
        """Get an empty list from a user without groups."""
        rv = self.get('/group/{token}/'.format(token=self.user.token))
        expected = {'status': 'OK',
                    'groups': []}
        self.assertStatusCode(rv, 200)
        self.assertJson(expected, rv.data)

    def test_create_group(self):
        """Test creating a group."""
        request = {'name': 'Test group'}
        rv = self.put('/group/{token}/'.format(token=self.user.token),
                      request)

        expected = {'status': 'OK', 'id': 1}    # always 1 'cause the database
                                                # is erased on every test
        self.assertStatusCode(rv, 200)
        self.assertJson(expected, rv.data)

    def test_create_group_unverified_account(self):
        """Try creating a group with an account that's not verified yet."""
        self.user.verified = False
        server.db.session.commit()

        request = {'name': 'Test group'}
        rv = self.put('/group/{token}/'.format(token=self.user.token),
                      request)

        expected = {'status': 'ERROR',
                    'error': 'Account not verified'}
        self.assertStatusCode(rv, 412)
        self.assertJson(expected, rv.data)

if __name__ == '__main__':
    unittest.main()
