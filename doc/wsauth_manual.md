Karp requires an authentication system that tells which lexicon a user may read
and edit.
If you don't care so much about security, try out the
[dummy system](https://github.com/spraakbanken/karp-docker/dummyauth).
Notice that this will let anyone both read and write to your databases, so
don't use this outside test environments.

If you want to setup your own system, all you need to make sure is that it is able to:

1. List all resources that are open to read for everyone
2. Say whether a the user's log in details are ok
3. Tell wich resources this user have been given read and write permissions to


The system should answer to these two calls:

* `<url>/authenticate`

   This is a POST request. Data:

    * `"include_open_resources":` `true` if the list of open resources should be sent along with the answer
    * `"username"`: the name of the user
    * `"password"`: the user's password (base64 encoded)
    * `"checksum"`: `md5(user + password + secretkey).hexdigest()` where the secret key for you authentication system is set in karp's configuration file.
    This is to protect your authorization system from being spammed. You can either ignore this parameter, or verify that the checksum is ok.

* `<url>/resources`

   This is a POST request. Data:
    * `"include_open_resources":` `true`

Answer to both calls:
```json
 {
   "permitted_resources": {
     "lexica": [{"lexicon1": {"write": true, "read": true}, "lexicon2": {"write": false, "read": true}}]
   },
   "username": user,
   "authenticated": true/false
 }
```
