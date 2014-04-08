#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest

from json import loads

from luncho import server

from luncho.server import User
from luncho.server import Place

from base import LunchoTests


class TestPlaces(LunchoTests):
    """Test places."""

    def setUp(self):
        super(TestPlaces, self).setUp()
        self.default_user()
        return

    def tearDown(self):
        super(TestPlaces, self).tearDown()
        return

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


class TestExistingPlaces(LunchoTests):
    """Tests for existing places."""
    def setUp(self):
        super(TestExistingPlaces, self).setUp()
        self.default_user()
        self.place = Place(name='Place',
                           owner=self.user)
        server.db.session.add(self.place)
        server.db.session.commit()

    def test_update_name(self):
        """Try to update a place."""
        request = {'name': 'New name'}
        placeId = self.place.id
        rv = self.put('/place/{placeId}/'.format(placeId=placeId),
                      request,
                      token=self.user.token)
        self.assertJsonOk(rv)

        # check the database
        place = Place.query.get(placeId)
        self.assertEqual(place.name, request['name'])

    def test_update_owner(self):
        """Update the owner of the group."""
        new_user = self.create_user(name='newUser',
                                    fullname='New User',
                                    passhash='hash',
                                    verified=True)
        placeId = self.place.id
        request = {'admin': new_user.username}
        rv = self.put('/place/{placeId}/'.format(placeId=placeId),
                      request,
                      token=self.user.token)
        self.assertJsonOk(rv)

        # check the database
        place = Place.query.get(placeId)
        self.assertEqual(place.owner, 'newUser')


if __name__ == '__main__':
    unittest.main()
