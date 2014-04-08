#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest

from json import loads

from luncho import server

from luncho.server import User
from luncho.server import Group

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

    def test_create_group(self):
        """Test creating a group."""
        request = {'name': 'Test group'}
        rv = self.post('/group/',
                       request,
                       token=self.user.token)
        self.assertJsonOk(rv, id=1)

    def test_create_group_unverified_account(self):
        """Try creating a group with an account that's not verified yet."""
        self.user.verified = False
        server.db.session.commit()

        request = {'name': 'Test group'}
        rv = self.post('/group/',
                       request,
                       token=self.user.token)
        self.assertJsonError(rv, 412, 'Account not verified')

    def test_user_in_own_group(self):
        """The user must belong to a group it owns."""
        token = self.user.token
        self.test_create_group()
        rv = self.get('/group/', token=token)
        self.assertJsonOk(rv, groups=[{'id': 1,
                                       'name': 'Test group',
                                       'admin': True}])

    def test_get_groups_unknown_token(self):
        """Request groups with an unknown token."""
        rv = self.get('/group/', token='invalid')
        self.assertJsonError(rv, 404, 'User not found (via token)')

    def test_get_groups_expired_token(self):
        """Request groups with an expired token."""
        self.user.token = 'expired'
        server.db.session.commit()

        rv = self.get('/group/', token=self.user.token)
        self.assertJsonError(rv, 400, 'Invalid token')

    def test_create_group_unknown_token(self):
        """Try to create a group with an invalid token."""
        request = {'name': 'Test group'}
        rv = self.post('/group/',
                       request,
                       token='invalid')
        self.assertJsonError(rv, 404, 'User not found (via token)')

    def test_create_group_expired_token(self):
        self.user.token = 'expired'
        server.db.session.commit()

        request = {'name': 'Test group'}
        rv = self.post('/group/',
                       request,
                       token=self.user.token)
        self.assertJsonError(rv, 400, 'Invalid token')


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

    def tearDown(self):
        super(TestExistingGroups, self).tearDown()

    def test_update_name(self):
        """Change the group name."""
        groupId = self.group.id
        request = {'name': 'New test group'}
        rv = self.put('/group/{groupId}/'.format(groupId=self.group.id),
                      request,
                      token=self.user.token)
        self.assertJsonOk(rv)

        # check the database
        group = Group.query.get(groupId)
        self.assertEqual(group.name, request['name'])

    def test_update_name_invalid_token(self):
        """Try to change the name with an unknown token."""
        request = {'name': 'New test group'}
        rv = self.put('/group/{groupId}/'.format(groupId=self.group.id),
                      request,
                      token='invalid')
        self.assertJsonError(rv, 404, 'User not found (via token)')

    def test_update_name_expired_token(self):
        """Try to change the name with an expired token."""
        self.user.token = 'expired'
        server.db.session.commit()

        request = {'name': 'New test group'}
        rv = self.put('/group/{groupId}/'.format(groupId=self.group.id),
                      request,
                      token=self.user.token)
        self.assertJsonError(rv, 400, 'Invalid token')

    def test_update_owner(self):
        """Change the group owner."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()

        groupId = self.group.id
        new_username = new_user.username

        request = {'admin': new_user.username}
        rv = self.put('/group/{groupId}/'.format(groupId=groupId),
                      request,
                      token=self.user.token)
        self.assertJsonOk(rv)

        # check the database
        group = Group.query.get(groupId)
        self.assertEqual(group.owner, new_username)

    def test_update_owner_invalid(self):
        """Try to change the owner to a user that doesn't exist."""
        request = {'admin': 'unknown'}
        rv = self.put('/group/{groupId}/'.format(groupId=self.group.id),
                      request,
                      token=self.user.token)
        self.assertJsonError(rv, 404, 'New admin not found')

    def test_update_unknown_group(self):
        """Try to update a group that doesn't exist."""
        groupId = self.group.id + 10
        request = {'name': 'New test group'}
        rv = self.put('/group/{groupId}/'.format(groupId=groupId),
                      request,
                      token=self.user.token)
        self.assertJsonError(rv, 404, 'Group not found')

    def test_delete_group(self):
        """Delete a group."""
        groupId = self.group.id
        rv = self.delete('/group/{groupId}/'.format(groupId=groupId),
                         token=self.user.token)
        self.assertJsonOk(rv)

    def test_delete_unknown_group(self):
        """Delete a group that doesn't exist."""
        groupId = self.group.id + 10
        rv = self.delete('/group/{groupId}/'.format(groupId=groupId),
                         token=self.user.token)
        self.assertJsonError(rv, 404, 'Group not found')

    def test_delete_not_admin(self):
        """Try to delete a group when the user is not the admin."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()
        new_user.get_token()

        rv = self.delete('/group/{groupId}/'.format(groupId=self.group.id),
                         token=new_user.token)
        self.assertJsonError(rv, 403, 'User is not admin')

    def test_delete_invalid_token(self):
        """Try to delete a group with an unknown token."""
        rv = self.delete('/group/{groupId}/'.format(groupId=self.group.id),
                         token='invalid')
        self.assertJsonError(rv, 404, 'User not found (via token)')


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

    def tearDown(self):
        super(TestUsersInGroup, self).tearDown()

    def test_add_user(self):
        """Try to add another user in the group."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()

        request = {'usernames': [new_user.username]}

        rv = self.put('/group/{groupId}/users/'.format(groupId=self.group.id),
                      request,
                      token=self.user.token)
        self.assertJsonOk(rv)

    def test_add_no_owner(self):
        """Try to add users without being the group admin."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()
        new_user.get_token()

        request = {'usernames': [new_user.username]}

        rv = self.put('/group/{groupId}/users/'.format(groupId=self.group.id),
                      request,
                      token=new_user.token)
        self.assertJsonError(rv, 403, 'User is not admin')

    def test_add_no_such_user(self):
        """Try to add an unknown user to the group."""
        request = {'usernames': ['unknown']}
        rv = self.put('/group/{groupId}/users/'.format(groupId=self.group.id),
                      request,
                      token=self.user.token)
        self.assertJsonError(rv, 404,
                             'Some users in the add list do not exist')

    def test_add_unknown_group(self):
        """Try to add users to some unknown group."""
        # the usernames are worthless, group not found should kick first
        request = {'usernames': ['unkonwn']}
        groupId = self.group.id + 10
        rv = self.put('/group/{groupId}/users/'.format(groupId=groupId),
                      request,
                      token=self.user.token)
        self.assertJsonError(rv, 404, 'Group not found')

    def test_get_members(self):
        """Try to get a list of group members."""
        rv = self.get('/group/{groupId}/users/'.format(groupId=self.group.id),
                      token=self.user.token)
        self.assertJsonOk(rv)
        json = loads(rv.data)
        self.assertTrue('users' in json)
        self.assertEqual(len(json['users']), 1)     # just the owner
        self.assertEqual(json['users'][0]['username'],
                         self.user.username)
        self.assertEqual(json['users'][0]['full_name'],
                         self.user.fullname)

    def test_get_members_by_member(self):
        """Non admin user requests the list of group members."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        new_user.groups.append(self.group)
        server.db.session.commit()
        new_user.get_token()

        rv = self.get('/group/{groupId}/users/'.format(groupId=self.group.id),
                      token=new_user.token)
        self.assertJsonOk(rv)

        json = loads(rv.data)
        self.assertTrue('users' in json)
        self.assertEqual(len(json['users']), 2)     # owner and new user

    def test_get_members_by_non_member(self):
        """A user that is not part of the group ask for members."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()
        new_user.get_token()

        rv = self.get('/group/{groupId}/users/'.format(groupId=self.group.id),
                      token=new_user.token)
        self.assertJsonError(rv, 403, 'User is not member of this group')

if __name__ == '__main__':
    unittest.main()
