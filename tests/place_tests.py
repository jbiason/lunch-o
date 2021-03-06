#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest

from json import loads

from luncho import server

from luncho.server import Place
from luncho.server import Group

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
        return

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
        return

    def test_create_place_not_verified(self):
        """Try to create a place with an unverified account."""
        request = {'name': 'New place'}
        new_user = self.create_user(name='new_user',
                                    fullname='new user',
                                    passhash='passhash',
                                    verified=False,
                                    create_token=True)
        rv = self.post('/place/',
                       request,
                       token=new_user.token)
        self.assertJsonError(rv, 412, 'Account not verified')
        return


class TestExistingPlaces(LunchoTests):
    """Tests for existing places."""
    def setUp(self):
        super(TestExistingPlaces, self).setUp()
        self.default_user()
        self.place = Place(name='Place',
                           owner=self.user)
        server.db.session.add(self.place)
        server.db.session.commit()
        return

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
        return

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
        return

    def test_update_unknown_place(self):
        """Try to update a place that doesn't exist."""
        placeId = self.place.id + 10
        request = {'name': 'new name'}
        rv = self.put('/place/{placeId}/'.format(placeId=placeId),
                      request,
                      token=self.user.token)
        self.assertJsonError(rv, 404, 'Place not found')
        return

    def test_update_non_admin(self):
        """A non-admin user tries to update the place."""
        new_user = self.create_user(name='newUser',
                                    fullname='New user',
                                    passhash='hash',
                                    verified=True,
                                    create_token=True)
        placeId = self.place.id
        request = {'name': 'new name'}
        rv = self.put('/place/{placeId}/'.format(placeId=placeId),
                      request,
                      token=new_user.token)
        self.assertJsonError(rv, 403, 'User is not admin')
        return

    def test_change_non_existent_admin(self):
        """Try to transfer the admin to a user that doesn't exist."""
        request = {'admin': 'unknown'}
        rv = self.put('/place/{placeId}/'.format(placeId=self.place.id),
                      request,
                      token=self.user.token)
        self.assertJsonError(rv, 404, 'New admin not found')
        return

    def test_delete_place(self):
        """Delete a place."""
        rv = self.delete('/place/{placeId}/'.format(placeId=self.place.id),
                         token=self.user.token)
        self.assertJsonOk(rv)
        return

    def test_delete_non_existent_place(self):
        """Try to delete a place that doesn't exist."""
        placeId = self.place.id + 10
        rv = self.delete('/place/{placeId}/'.format(placeId=placeId),
                         token=self.user.token)
        self.assertJsonError(rv, 404, 'Place not found')
        return

    def test_delete_non_admin(self):
        """Try to delete the place by a non-admin user."""
        new_user = self.create_user(name='newUser',
                                    fullname='New user',
                                    passhash='hash',
                                    verified=True,
                                    create_token=True)
        rv = self.delete('/place/{placeId}/'.format(placeId=self.place.id),
                         token=new_user.token)
        self.assertJsonError(rv, 403, 'User is not admin')
        return


class TestGroupPlaces(LunchoTests):
    """Test the group+places integration, but from places perspective."""

    def setUp(self):
        super(TestGroupPlaces, self).setUp()
        self.default_user()
        self.place = Place(name='Place',
                           owner=self.user)
        server.db.session.add(self.place)
        server.db.session.commit()

    def tearDown(self):
        super(TestGroupPlaces, self).tearDown()

    def test_get_places_from_groups(self):
        """Test getting places linked to the user groups."""
        # user1 owns a place and the group.
        user1 = self.create_user(name='testUser',
                                 fullname='Test User',
                                 verified=True,
                                 create_token=True)
        place = Place(name='Place', owner=user1)
        group = Group(name='Test group', owner=user1)

        user1.groups.append(group)
        group.places.append(place)      # the group now uses that place
        server.db.session.add(user1)
        server.db.session.add(place)
        server.db.session.add(group)

        # user2 is just a member of the group
        user2 = self.create_user(name='anotherUser',
                                 fullname='Another user',
                                 verified=True,
                                 create_token=True)
        user2.groups.append(group)
        server.db.session.add(user2)
        server.db.session.commit()

        # now user2 should get the place in their results.
        rv = self.get('/place/',
                      token=user2.token)
        self.assertJsonOk(rv)
        json = loads(rv.data)
        self.assertTrue('places' in json)
        self.assertEqual(len(json['places']), 1)    # just the new place

if __name__ == '__main__':
    unittest.main()
