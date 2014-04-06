#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest

from json import loads

from luncho import server

from luncho.server import User

from base import LunchoTests


class TestPlaces(LunchoTests):
    """Test places."""

    def setUp(self):
        super(TestPlaces, self).setUp()
        self.user = User(username='test',
                         fullname='Test User',
                         passhash='hash')
        self.user.verified = True
        server.db.session.add(self.user)
        server.db.session.commit()
        self.user.get_token()

    def test_create_place(self):
        """Try to create a place."""
        request = {'name': 'New Place'}
        rv = self.post('/place/',
                       request,
                       token=self.user.token)
        self.assertJsonOk(rv)
        json = loads(rv.data)
        self.assertTrue('id' in json)

    def test_get_places(self):
        """Try to get the user places."""
        token = self.user.token
        self.test_create_place()    # create a place
        rv = self.get('/place/',
                      token=token)
        self.assertJsonOk(rv)
        json = loads(rv.data)
        self.assertTrue('places' in json)
        self.assertEqual(len(json['places']), 1)    # just the new place


if __name__ == '__main__':
    unittest.main()
