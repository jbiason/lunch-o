#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest

from json import loads

from luncho import server

from luncho.server import User
from luncho.server import Group
from luncho.server import Place

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
        rv = self.get('/group/', token=self.user.token)
        self.assertJsonOk(rv, groups=[])
        return

    def test_create_group(self):
        """Test creating a group."""
        request = {'name': 'Test group'}
        rv = self.post('/group/',
                       request,
                       token=self.user.token)
        self.assertJsonOk(rv, id=1)
        return

    def test_create_group_unverified_account(self):
        """Try creating a group with an account that's not verified yet."""
        self.user.verified = False
        server.db.session.commit()

        request = {'name': 'Test group'}
        rv = self.post('/group/',
                       request,
                       token=self.user.token)
        self.assertJsonError(rv, 412, 'Account not verified')
        return

    def test_user_in_own_group(self):
        """The user must belong to a group it owns."""
        token = self.user.token
        self.test_create_group()
        rv = self.get('/group/', token=token)
        self.assertJsonOk(rv, groups=[{'id': 1,
                                       'name': 'Test group',
                                       'admin': True}])
        return

    def test_get_groups_unknown_token(self):
        """Request groups with an unknown token."""
        rv = self.get('/group/', token='invalid')
        self.assertJsonError(rv, 404, 'User not found (via token)')
        return

    def test_get_groups_expired_token(self):
        """Request groups with an expired token."""
        self.user.token = 'expired'
        server.db.session.commit()

        rv = self.get('/group/', token=self.user.token)
        self.assertJsonError(rv, 400, 'Invalid token')
        return

    def test_create_group_unknown_token(self):
        """Try to create a group with an invalid token."""
        request = {'name': 'Test group'}
        rv = self.post('/group/',
                       request,
                       token='invalid')
        self.assertJsonError(rv, 404, 'User not found (via token)')
        return

    def test_create_group_expired_token(self):
        self.user.token = 'expired'
        server.db.session.commit()

        request = {'name': 'Test group'}
        rv = self.post('/group/',
                       request,
                       token=self.user.token)
        self.assertJsonError(rv, 400, 'Invalid token')
        return


class TestExistingGroups(LunchoTests):
    """Test for existing groups."""
    def setUp(self):
        super(TestExistingGroups, self).setUp()
        # create a user to have a token
        self.user = User(username='test',
                         fullname='Test User',
                         passhash='hash')
        self.user.verified = True
        server.db.session.add(self.user)

        # create a group for the user
        self.group = Group(name='Test group',
                           owner=self.user)
        server.db.session.add(self.group)
        server.db.session.commit()
        self.user.get_token()
        return

    def tearDown(self):
        super(TestExistingGroups, self).tearDown()
        return

    def test_update_name(self):
        """Change the group name."""
        group_id = self.group.id
        request = {'name': 'New test group'}
        rv = self.put('/group/{group_id}/'.format(group_id=self.group.id),
                      request,
                      token=self.user.token)
        self.assertJsonOk(rv)

        # check the database
        group = Group.query.get(group_id)
        self.assertEqual(group.name, request['name'])
        return

    def test_update_name_invalid_token(self):
        """Try to change the name with an unknown token."""
        request = {'name': 'New test group'}
        rv = self.put('/group/{group_id}/'.format(group_id=self.group.id),
                      request,
                      token='invalid')
        self.assertJsonError(rv, 404, 'User not found (via token)')
        return

    def test_update_name_expired_token(self):
        """Try to change the name with an expired token."""
        self.user.token = 'expired'
        server.db.session.commit()

        request = {'name': 'New test group'}
        rv = self.put('/group/{group_id}/'.format(group_id=self.group.id),
                      request,
                      token=self.user.token)
        self.assertJsonError(rv, 400, 'Invalid token')
        return

    def test_update_owner(self):
        """Change the group owner."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()

        group_id = self.group.id
        new_username = new_user.username

        request = {'admin': new_user.username}
        rv = self.put('/group/{group_id}/'.format(group_id=group_id),
                      request,
                      token=self.user.token)
        self.assertJsonOk(rv)

        # check the database
        group = Group.query.get(group_id)
        self.assertEqual(group.owner, new_username)
        return

    def test_update_owner_invalid(self):
        """Try to change the owner to a user that doesn't exist."""
        request = {'admin': 'unknown'}
        rv = self.put('/group/{group_id}/'.format(group_id=self.group.id),
                      request,
                      token=self.user.token)
        self.assertJsonError(rv, 404, 'New admin not found')
        return

    def test_update_unknown_group(self):
        """Try to update a group that doesn't exist."""
        group_id = self.group.id + 10
        request = {'name': 'New test group'}
        rv = self.put('/group/{group_id}/'.format(group_id=group_id),
                      request,
                      token=self.user.token)
        self.assertJsonError(rv, 404, 'Group not found')
        return

    def test_not_admin(self):
        """Try to update with a user that it is not the group admin."""
        new_user = self.create_user(name='another_user',
                                    fullname='Another user',
                                    passhash='hash',
                                    verified=True,
                                    create_token=True)
        request = {'name': 'A new name'}
        rv = self.put('/group/{group_id}/'.format(group_id=self.group.id),
                      request,
                      token=new_user.token)
        self.assertJsonError(rv, 403, 'User is not admin')
        return

    def test_delete_group(self):
        """Delete a group."""
        group_id = self.group.id
        rv = self.delete('/group/{group_id}/'.format(group_id=group_id),
                         token=self.user.token)
        self.assertJsonOk(rv)
        return

    def test_delete_unknown_group(self):
        """Delete a group that doesn't exist."""
        group_id = self.group.id + 10
        rv = self.delete('/group/{group_id}/'.format(group_id=group_id),
                         token=self.user.token)
        self.assertJsonError(rv, 404, 'Group not found')
        return

    def test_delete_not_admin(self):
        """Try to delete a group when the user is not the admin."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()
        new_user.get_token()

        rv = self.delete('/group/{group_id}/'.format(group_id=self.group.id),
                         token=new_user.token)
        self.assertJsonError(rv, 403, 'User is not admin')
        return

    def test_delete_invalid_token(self):
        """Try to delete a group with an unknown token."""
        rv = self.delete('/group/{group_id}/'.format(group_id=self.group.id),
                         token='invalid')
        self.assertJsonError(rv, 404, 'User not found (via token)')
        return


class TestUsersInGroup(LunchoTests):
    """Tests for managing users in the group."""
    def setUp(self):
        super(TestUsersInGroup, self).setUp()
        # create a user to have a token
        self.user = User(username='test',
                         fullname='Test User',
                         passhash='hash')
        self.user.verified = True
        server.db.session.add(self.user)

        # create a group for the user
        self.group = Group(name='Test group',
                           owner=self.user)
        server.db.session.add(self.group)

        self.user.groups.append(self.group)
        server.db.session.commit()
        self.user.get_token()
        return

    def tearDown(self):
        super(TestUsersInGroup, self).tearDown()
        return

    def test_add_user(self):
        """Try to add another user in the group."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()

        request = {'usernames': [new_user.username]}

        url = '/group/{group_id}/users/'.format(group_id=self.group.id)
        rv = self.post(url,
                       request,
                       token=self.user.token)
        self.assertJsonOk(rv)
        return

    def test_add_no_owner(self):
        """Try to add users without being the group admin."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()
        new_user.get_token()

        request = {'usernames': [new_user.username]}

        url = '/group/{group_id}/users/'.format(group_id=self.group.id)
        rv = self.post(url,
                       request,
                       token=new_user.token)
        self.assertJsonError(rv, 403, 'User is not admin')
        return

    def test_add_no_such_user(self):
        """Try to add an unknown user to the group."""
        request = {'usernames': ['unknown']}
        url = '/group/{group_id}/users/'.format(group_id=self.group.id)
        rv = self.post(url,
                       request,
                       token=self.user.token)

        # not finding users still returns a 200, but with the users in the
        # "not_found" field
        self.assertJsonOk(rv)
        json = loads(rv.data)
        self.assertTrue('not_found' in json)
        self.assertTrue('unknown' in json['not_found'])
        return

    def test_add_unknown_group(self):
        """Try to add users to some unknown group."""
        # the usernames are worthless, group not found should kick first
        request = {'usernames': ['unkonwn']}
        group_id = self.group.id + 10
        rv = self.post('/group/{group_id}/users/'.format(group_id=group_id),
                       request,
                       token=self.user.token)
        self.assertJsonError(rv, 404, 'Group not found')
        return

    def test_get_members(self):
        """Try to get a list of group members."""
        username = self.user.username
        fullname = self.user.fullname
        url = '/group/{group_id}/users/'.format(group_id=self.group.id)
        rv = self.get(url,
                      token=self.user.token)
        self.assertJsonOk(rv)
        json = loads(rv.data)
        self.assertTrue('users' in json)
        self.assertEqual(len(json['users']), 1)     # just the owner
        self.assertEqual(json['users'][0]['username'], username)
        self.assertEqual(json['users'][0]['full_name'], fullname)
        return

    def test_get_members_by_member(self):
        """Non admin user requests the list of group members."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        new_user.groups.append(self.group)
        server.db.session.commit()
        new_user.get_token()

        url = '/group/{group_id}/users/'.format(group_id=self.group.id)
        rv = self.get(url,
                      token=new_user.token)
        self.assertJsonOk(rv)

        json = loads(rv.data)
        self.assertTrue('users' in json)
        self.assertEqual(len(json['users']), 2)     # owner and new user
        return

    def test_get_members_by_non_member(self):
        """A user that is not part of the group ask for members."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()
        new_user.get_token()

        url = '/group/{group_id}/users/'.format(group_id=self.group.id)
        rv = self.get(url,
                      token=new_user.token)
        self.assertJsonError(rv, 403, 'User is not member of this group')
        return

    def test_unknown_group(self):
        """Test trying to get members of a group that doesn't exist."""
        group_id = self.group.id + 10
        rv = self.get('/group/{group_id}/users/'.format(group_id=group_id),
                      token=self.user.token)
        self.assertJsonError(rv, 404, 'Group not found')
        return


class TestPlacesInGroup(LunchoTests):
    """Test the integration between groups and places."""

    def setUp(self):
        super(TestPlacesInGroup, self).setUp()
        self.default_user()
        return

    def tearDown(self):
        super(TestPlacesInGroup, self).tearDown()
        return

    def _group(self):
        """Add a default group."""
        group = Group(name='Test group',
                      owner=self.user)
        server.db.session.add(group)
        self.user.groups.append(group)
        server.db.session.commit()
        return group

    def _place(self, user=None):
        """Add a default place, linked to the user."""
        if not user:
            user = self.user

        place = Place(name='Place',
                      owner=user)
        server.db.session.add(place)
        server.db.session.commit()
        return place

    def test_add_place(self):
        """Add a place to the group."""
        place = self._place()
        group = self._group()

        request = {'places': [place.id]}
        group_id = group.id
        rv = self.post('/group/{group_id}/places/'.format(group_id=group_id),
                       request,
                       token=self.user.token)
        self.assertJsonOk(rv)
        json = loads(rv.data)
        self.assertTrue('rejected' in json)
        self.assertFalse(json['rejected'])  # the list should be empty (False)

        self.assertTrue('not_found' in json)
        self.assertFalse(json['not_found'])
        return

    def test_add_place_of_member(self):
        """Add a place that belongs to a member of the group."""
        new_user = self.create_user(name='newuser',
                                    fullname='new user',
                                    verified=True)
        group = self._group()           # group belongs to self.user
        group.users.append(new_user)
        place = self._place(new_user)   # place belongs to new_user

        request = {'places': [place.id]}
        group_id = group.id
        rv = self.post('/group/{group_id}/places/'.format(group_id=group_id),
                       request,
                       token=self.user.token)
        self.assertJsonOk(rv)
        json = loads(rv.data)
        self.assertTrue('rejected' in json)
        self.assertFalse(json['rejected'])

    def test_add_place_of_non_member(self):
        """Add a place that belongs to seomeone not in the group."""
        new_user = self.create_user(name='newuser',
                                    fullname='new user',
                                    verified=True)
        group = self._group()           # group belongs to self.user
        place = self._place(new_user)   # place belongs to new_user
        place_id = place.id

        request = {'places': [place.id]}
        group_id = group.id
        rv = self.post('/group/{group_id}/places/'.format(group_id=group_id),
                       request,
                       token=self.user.token)
        self.assertJsonOk(rv)
        json = loads(rv.data)
        self.assertTrue('rejected' in json)
        self.assertTrue(place_id in json['rejected'])
        return

    def test_add_place_unkown_group(self):
        """Add a place to a group that doesn't exist."""
        place = self._place()
        request = {'places': [place.id]}
        rv = self.post('/group/{group_id}/places/'.format(group_id=100),
                       request,
                       token=self.user.token)
        self.assertJsonError(rv, 404, 'Group not found')
        return

    def test_add_place_non_admin(self):
        """Try to add a place with a user that's not the group admin."""
        new_user = self.create_user(name='newUser',
                                    fullname='new user',
                                    verified=True,
                                    create_token=True)
        group = self._group()
        place = self._place(new_user)   # just make sure the user owns it

        request = {'places': [place.id]}
        rv = self.post('/group/{group_id}/places/'.format(group_id=group.id),
                       request,
                       token=new_user.token)
        self.assertJsonError(rv, 403, 'User is not admin')
        return

    def test_add_unknown_place(self):
        """Try to add a place that doesn't exist."""
        group = self._group()

        request = {'places': [100]}
        group_id = group.id
        rv = self.post('/group/{group_id}/places/'.format(group_id=group_id),
                       request,
                       token=self.user.token)
        self.assertJsonOk(rv)
        json = loads(rv.data)
        self.assertTrue('rejected' in json)
        self.assertFalse(json['rejected'])  # can't be rejected

        self.assertTrue('not_found' in json)
        self.assertEquals(len(json['not_found']), 1)     # the place itself
        return

    def test_get_group_places(self):
        """Try to get a list of places in the group."""
        group = self._group()
        place = self._place()
        group.places.append(place)
        server.db.session.commit()

        rv = self.get('/group/{group_id}/places/'.format(group_id=group.id),
                      token=self.user.token)
        self.assertJsonOk(rv)
        json = loads(rv.data)
        self.assertTrue('places' in json)
        self.assertEquals(place.id, json['places'][0]['id'])
        return

    def test_get_places_unknown_group(self):
        """Try to get the places of a group that doesn't exist."""
        rv = self.get('/group/{group_id}/places/'.format(group_id=100),
                      token=self.user.token)
        self.assertJsonError(rv, 404, 'Group not found')
        return

    def test_group_get_places_non_member(self):
        """Non member tries to get the group places."""
        new_user = self.create_user(name='newUser',
                                    fullname='New User',
                                    verified=True,
                                    create_token=True)
        group = self._group()
        place = self._place()
        group.places.append(place)
        server.db.session.commit()

        rv = self.get('/group/{group_id}/places/'.format(group_id=group.id),
                      token=new_user.token)
        self.assertJsonError(rv, 403, 'User is not member of this group')
        return

    def test_delete_place(self):
        """Delete a place from a group."""
        group = self._group()
        place = self._place()
        group.places.append(place)
        server.db.session.commit()

        group_id = group.id
        place_id = place.id

        url = '/group/{group_id}/places/{place_id}/'.format(
            group_id=group_id, place_id=place_id)
        rv = self.delete(url,
                         token=self.user.token)

        self.assertJsonOk(rv)

        # check if it was really removed in the database
        group = Group.query.get(group_id)
        for place in group.places:
            if place.id == place_id:
                self.fail('Place still connected to group')

        return

    def test_delete_unknown_group(self):
        """Try to delete a place of a group that doesn't exist."""
        url = '/group/{group_id}/places/{place_id}/'.format(
            group_id=100, place_id=100)
        rv = self.delete(url, token=self.user.token)
        self.assertJsonError(rv, 404, 'Group not found')
        return

    def test_delete_unknown_place(self):
        """Try to delete a place that doesn't belong to the group."""
        group = self._group()
        url = '/group/{group_id}/places/{place_id}/'.format(
            group_id=group.id, place_id=100)
        rv = self.delete(url, token=self.user.token)
        self.assertJsonError(rv, 404, 'Place not found')
        return

if __name__ == '__main__':
    unittest.main()
