#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest

from luncho import server

from base import LunchoTests
from luncho.server import Group
from luncho.server import Place


class TestVote(LunchoTests):
    def setUp(self):
        super(TestVote, self).setUp()
        self.default_user()

    def tearDown(self):
        super(TestVote, self).tearDown()

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

    def test_cast_vote(self):
        """Try to cast a vote."""
        group = self._group()
        place = self._place()
        group.places.append(place)
        self.user.groups.append(group)
        server.db.session.commit()

        request = {'choices': [place.id]}
        rv = self.post('/vote/{group_id}/'.format(group_id=group.id),
                       request,
                       token=self.user.token)
        print rv.data
        self.assertJsonOk(rv)

if __name__ == '__main__':
    unittest.main()
