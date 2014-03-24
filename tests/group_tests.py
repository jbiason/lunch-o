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

    def test_user_in_own_group(self):
        """The user must belong to a group it owns."""
        token = self.user.token
        self.test_create_group()
        rv = self.get('/group/{token}/'.format(token=token))
        expected = {'status': 'OK',
                    'groups': [{'id': 1,
                                'name': 'Test group',
                                'admin': True}]}
        self.assertStatusCode(rv, 200)
        self.assertJson(expected, rv.data)


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
        expected = {'status': 'OK'}
        self.assertStatusCode(rv, 200)
        self.assertJson(expected, rv.data)

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
        rv = self.post('/group/{token}/{groupId}/'.format(token=self.user.token,
                                                          groupId=self.group.id),
                       request)
        expected = {'status': 'OK'}
        self.assertStatusCode(rv, 200)
        self.assertJson(expected, rv.data)

        # check the database
        group = Group.query.get(groupId)
        self.assertEqual(group.owner, new_username)

if __name__ == '__main__':
    unittest.main()
