#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest

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
        rv = self.get('/group/{token}/'.format(token=self.user.token))
        self.assertJsonOk(rv, groups=[])

    def test_create_group(self):
        """Test creating a group."""
        request = {'name': 'Test group'}
        rv = self.put('/group/{token}/'.format(token=self.user.token),
                      request)
        self.assertJsonOk(rv, id=1)

    def test_create_group_unverified_account(self):
        """Try creating a group with an account that's not verified yet."""
        self.user.verified = False
        server.db.session.commit()

        request = {'name': 'Test group'}
        rv = self.put('/group/{token}/'.format(token=self.user.token),
                      request)
        self.assertJsonError(rv, 412, 'Account not verified')

    def test_user_in_own_group(self):
        """The user must belong to a group it owns."""
        token = self.user.token
        self.test_create_group()
        rv = self.get('/group/{token}/'.format(token=token))
        self.assertJsonOk(rv, groups=[{'id': 1,
                                       'name': 'Test group',
                                       'admin': True}])


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
                           owner=self.user.username)
        server.db.session.add(self.group)
        server.db.session.commit()
        self.user.get_token()

    def tearDown(self):
        super(TestExistingGroups, self).tearDown()

    def test_update_name(self):
        """Change the group name."""
        groupId = self.group.id
        request = {'name': 'New test group'}
        rv = self.post('/group/{token}/{groupId}/'.format(token=self.user.token,
                                                          groupId=self.group.id),
                       request)
        self.assertJsonOk(rv)

        # check the database
        group = Group.query.get(groupId)
        self.assertEqual(group.name, request['name'])

    def test_update_owner(self):
        """Change the group owner."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()

        groupId = self.group.id
        new_username = new_user.username

        request = {'maintainer': new_user.username}
        rv = self.post('/group/{token}/{groupId}/'.format(
            token=self.user.token,
            groupId=self.group.id),
            request)
        self.assertJsonOk(rv)

        # check the database
        group = Group.query.get(groupId)
        self.assertEqual(group.owner, new_username)

    def test_update_unknown_group(self):
        """Try to update a group that doesn't exist."""
        groupId = self.group.id + 10
        request = {'name': 'New test group'}
        rv = self.post('/group/{token}/{groupId}/'.format(
            token=self.user.token,
            groupId=groupId),
            request)
        self.assertJsonError(rv, 404, 'Group not found')

    def test_delete_group(self):
        """Delete a group."""
        groupId = self.group.id
        rv = self.delete('/group/{token}/{groupId}/'.format(
            token=self.user.token,
            groupId=groupId))
        self.assertJsonOk(rv)

    def test_delete_unknown_group(self):
        """Delete a group that doesn't exist."""
        groupId = self.group.id + 10
        rv = self.delete('/group/{token}/{groupId}/'.format(
            token=self.user.token,
            groupId=groupId))
        self.assertJsonError(rv, 404, 'Group not found')

    def test_delete_not_admin(self):
        """Try to delete a group when the user is not the admin."""
        new_user = User(username='another_user',
                        fullname='Another user',
                        passhash='hash')
        server.db.session.add(new_user)
        server.db.session.commit()
        new_user.get_token()

        rv = self.delete('/group/{token}/{groupId}/'.format(
            token=new_user.token,
            groupId=self.group.id))
        self.assertJsonError(rv, 401, 'User is not admin')

if __name__ == '__main__':
    unittest.main()
