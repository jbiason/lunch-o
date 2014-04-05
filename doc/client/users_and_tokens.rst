Users and Tokens
=================

Token
------

All requests require an access token to be valid. The token is valid for a
whole day and, unless you don't have the access token or it expired, you
should use this request to get a valid token:

.. autoflask:: luncho.server:app
   :blueprints: token
   :undoc-endpoints: static,show_api


Users
------

.. autoflask:: luncho.server:app
   :blueprints: users
   :undoc-endpoints: static,show_api
