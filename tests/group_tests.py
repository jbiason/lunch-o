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


if __name__ == '__main__':
    unittest.main()
