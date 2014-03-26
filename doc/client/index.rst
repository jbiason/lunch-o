About the API
==============

A few things you must know before diving into the API:

Everything is JSON
-------------------

Every request should have a JSON payload; anything else will be refused and
return a 400 status. For example:

.. sourcecode:: http

   POST /randomendpoint
   Host: example.com
   Accept: text/html
   Content-Type: application/x-www-form-urlencoded

   field1=value&field2=value

The response will always be:

.. sourcecode:: http

   HTTP/1.1 400 Bad Request
   Content-Type: text/json

   { "status": "ERROR", "message": "Request MUST be in JSON format" }

If instead you do a proper JSON request with:

.. sourcecode:: http

   POST /randomendpoint
   Host: example.com
   Content-type: text/json

   { "field1": "value", "field2": "value" }

Then everything would go fine.

Standard responses
-------------------

Responses will always have a ``status`` parameter with the result of the
operation -- more fields may be also returned, depending on the request.

Successful requests with have the value ``OK`` for ``status`` -- and, again,
more fields may be returned in most cases. Also, the HTTP status code will
**always** be 200.

In case of failure, ``status`` will have the text ``ERROR`` (in all caps) and
a ``message`` field will have the reason for the error -- and, as success, it
may contain more fields with information about the error. For different errors
in the operation there will be a different HTTP status. We tried as hard as
possible to give each error a meaningful HTTP status, even if this sometimes
wouldn't make much sense -- for example, if you try to change the ownership of
a group and the group doesn't exist, you'll get a 404 status; if the new owner
doesn't exist, instead of a proper 404, we will return a 412 status, not
because there is a precondition error in the headers, but because we need 
a different code to point that the new user does not exist.

Redirects
----------

All URLs must end with "/"; if you forget to add them in the URL, you'll
receive a redirect to the path with "/".

API
----

.. toctree::
   :maxdepth: 2

   users_and_tokens
