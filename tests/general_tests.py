#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from base import LunchoTests


class TestLuncho(LunchoTests):
    """Test things that are in the base system, not the blueprints
    (although the blueprints are required to create the URLs to be used)."""

    def setUp(self):
        super(TestLuncho, self).setUp()
        return

    def tearDown(self):
        super(TestLuncho, self).tearDown()
        return

    def test_auth(self):
        """Try to request an authenticated request without authentication."""
        rv = self.app.get('/place/')    # GET /place/ is authenticated
        self.assertJsonError(rv, 401, 'Request requires authentication')
