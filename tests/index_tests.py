#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import unittest
import json

from base import LunchoTests


class TestIndex(LunchoTests):
    """Tests for the index."""

    def setUp(self):
        super(TestIndex, self).setUp()

    def tearDown(self):
        super(TestIndex, self).tearDown()

    def test_self(self):
        """The index must be listed in the index."""
        rv = self.get('/')
        self.assertJsonOk(rv)

        response = json.loads(rv.data)
        self.assertEqual(response['api'][0][0], '/')

if __name__ == '__main__':
    unittest.main()
