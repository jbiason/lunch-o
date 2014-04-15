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
        self.assertJsonOk(rv)
        return

    def test_cast_less_votes(self):
        """Try to cast a vote with not enough places."""
        group = self._group()
        place1 = self._place()
        place2 = self._place()
        group.places.append(place1)
        group.places.append(place2)
        self.user.groups.append(group)
        server.db.session.commit()

        request = {'choices': [place1.id]}
        rv = self.post('/vote/{group_id}/'.format(group_id=group.id),
                       request,
                       token=self.user.token)
        self.assertJsonError(rv, 406, 'The vote must register 2 places')
        return

    def test_already_voted(self):
        """Try to vote when the user already voted."""
        group = self._group()
        place = self._place()
        group.places.append(place)
        self.user.groups.append(group)
        server.db.session.commit()

        group_id = group.id
        token = self.user.token

        request = {'choices': [place.id]}
        rv = self.post('/vote/{group_id}/'.format(group_id=group_id),
                       request,
                       token=token)
        self.assertJsonOk(rv)   # vote in the day

        rv = self.post('/vote/{group_id}/'.format(group_id=group_id),
                       request,
                       token=token)
        self.assertJsonError(rv, 406, 'User already voted today')
        return

    def test_already_vote_other_group(self):
        """Try to vote in two different groups in the same day."""
        group1 = self._group()
        place1 = self._place()
        group1.places.append(place1)
        self.user.groups.append(group1)

        group2 = self._group()
        place2 = self._place()
        group2.places.append(place2)
        self.user.groups.append(group2)
        server.db.session.commit()

        group1_id = group1.id
        group2_id = group2.id
        place1_id = place1.id
        place2_id = place2.id
        token = self.user.token

        request = {'choices': [place1_id]}
        rv = self.post('/vote/{group_id}/'.format(group_id=group1_id),
                       request,
                       token=token)
        self.assertJsonOk(rv)   # first vote for the day

        request = {'choices': [place2_id]}
        rv = self.post('/vote/{group_id}/'.format(group_id=group2_id),
                       request,
                       token=token)
        self.assertJsonError(rv, 406, 'User already voted today')
        return

    def test_vote_place_not_in_group(self):
        """Vote for a place that doesn't belong to the group."""
        group = self._group()
        place1 = self._place()
        place2 = self._place()
        group.places.append(place2)
        self.user.groups.append(group)
        server.db.session.commit()

        request = {'choices': [place1.id]}
        rv = self.post('/vote/{group_id}/'.format(group_id=group.id),
                       request,
                       token=self.user.token)
        self.assertJsonError(rv, 404, 'Places are not part of this group')
        return

    def test_vote_for_same_place_twice(self):
        """Vote for a place more than once."""
        group = self._group()
        place = self._place()
        group.places.append(place)
        self.user.groups.append(group)
        server.db.session.commit()

        request = {'choices': [place.id, place.id]}
        rv = self.post('/vote/{group_id}/'.format(group_id=group.id),
                       request,
                       token=self.user.token)
        self.assertJsonError(rv, 409, 'Places voted more than once')
        return

    def test_unknown_group(self):
        """Try to vote in a group that doesn't exist."""
        request = {'choices': [100]}
        rv = self.post('/vote/{group_id}/'.format(group_id=100),
                       request,
                       token=self.user.token)
        self.assertJsonError(rv, 404, 'Group not found')
        return

    def test_vote_in_group_not_member(self):
        """Try to vote for a group that the user is not a member."""
        group = self._group()
        place = self._place()
        group.places.append(place)
        server.db.session.commit()

        user2 = self.create_user(name='newUser',
                                 fullname='new user',
                                 verified=True,
                                 create_token=True)

        request = {'choices': [place.id]}
        rv = self.post('/vote/{group_id}/'.format(group_id=group.id),
                       request,
                       token=user2.token)
        self.assertJsonError(rv, 403, 'User is not member of this group')
        return

    def test_vote_place_doesnt_exist(self):
        """Vote for a place that doesnt exist."""
        group = self._group()
        place = self._place()
        group.places.append(place)
        server.db.session.commit()

        request = {'choices': [place.id + 10]}
        rv = self.post('/vote/{group_id}/'.format(group_id=group.id),
                       request,
                       token=self.user.token)
        self.assertJsonError(rv, 404, 'Place not found')
        return

if __name__ == '__main__':
    unittest.main()
