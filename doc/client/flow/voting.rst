Voting
=======

A typical voting/check results flow would be:

1. Get the token:

   .. sourcecode:: http

      POST /token/
      { "user": "username", "password": "userPassword" }

   Remember: the token is valid for a whole day. You can still request the
   token, but the response will always be the same for the whole day.

   We suggest keeping the user credentials and token stored somewhere. If any
   request you receive a 

   .. sourcecode:: http

      HTTP/1.1 404 Not Found
      Content-Type: text/json

      { "status": "ERROR",
        "code": "UserNotFound",
        "User not found (via token)" }

   then request a new token.

2. Once you have the token, you can request the user groups (or store then and
   offer a "Refresh" button somewhere):

   .. sourcecode:: http

      GET /group/

   This will return all groups in which the user is a member.

3. For each group, you can request the current voting results:

   .. sourcecode:: http

      GET /vote/{group_id}/

4. The first result with *always* be the place with more points. The avoid
   requesting the places just to show the name, the name for each place will
   be returned in the results.

   Keep in mind that once every member of a group voted, the voting will have
   a `closed` property set to `true`. In this case, it means there will be no
   change in the results and the place has been picked.

5. To vote, you'll need to display the current places for the group. For that,
   request the places for the group:

   .. sourcecode:: http

      GET /group/{group_id}/places/

   Then let the user pick up to 3 places, with ordering.

6. Once the user picks the places, cast the vote:

   .. sourcecode:: http

      POST /vote/{group_id}/

      { "choices": [ <first place id>, <second place id>, ... ] }

7. Once you get a success response, return to the list of groups. You can even
   re-request the current results, just to be sure.
