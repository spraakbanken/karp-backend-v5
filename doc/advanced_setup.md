# Adapt your Karp


Add extra urls
=======
If you would like your Karp to handle more requests than the standard
Karp, you can add an extra file where you define more url calls.
For example, say that you want to make it possible to call
`/infoabout/<lexicon>`
and
`/addinfo`.
The first one should return a dictionary with information about your
resources.
The last one should be a POST call, adding things to the dictionary.
For some reason, you don't want this information to be in ElasticSearch,
but in a simple .json file on your server.

To do this, we first define how the functions should work.

```python
# mykarp.py
import flask
import urlparse

def postinfo():
    query = flask.request.query_string
    parsed = urlparse.parse_qs(query)
    for key, val in parsed():
        # write to your file
        update_info_file(key, val)
    return flask.jsonify({"saved": "ok"})


def getinfo(lexicon):
    # read from your file
    info = read_info_file()
    return flask.jsonify(info.get(lexicon, {}))
```

Now, use the Karp `@route` decorator to add these to
the ones known by Karp. The `@route` decorator is similar to the one
in [Flask](http://flask.pocoo.org/docs/0.12/quickstart/), but will assume that the wanted url is the same
as the name of the function. By default it also allow cross domain calls to this url.

Each decorated function will add an url to Karp.

There are four keyword arguments to the decorator; `url`, `methods`, `crossdomain` and `name`.

|             |      |
|-------------|------|
|`url`        | adds a suffix  to the url. This might be used for variable parts of the url.|
|`methods`    | sets what [http methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) that can be used for this url. Default: `GET`.|
|`name`       | changes the url name. Should be used when the name of the function is not wanted.|
|`crossdomain`| defines whether this url should accept [cross domain calls](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS). Default: `true`.|


```python
# mykarp.py

# the function init will be called when karp starts
def init(route):

    # add the first one: 'infoabout/<lexicon>'
    @route('<lexicon>')
    def infoabout():
        return getinfo()


    # add another: '/addinfo'
    @route(methods=["POST"])
    def addinfo():
        return postinfo()

```

Finally, update Karp's `main.py` to register your urls:

```python
import backend as karpbackend  # the standard karp
# add this line:
import mykarp  # your karp


def load_urls():
    flaskhelper.register(karpbackend.init)
    # add this line:
    flaskhelper.register(mykarp.init)

app = flaskhelper.app

if __name__ == '__main__':
    load_urls()
    flaskhelper.app.run()
```


Add autoupdates
===============
Each time a document is saved (created or updated) in Karp,
automatic changes may be made to it. For example, you might want
to add a `lastmodified` field to it, containing the current date
and time, or you might want to set the lexicon order so that
the user does not have to do that.

To do this, we use Karp's `@auto_update` decorator.
```python
@auto_update('mylexicon')
def update_function(obj, lexicon, actiontype, user, date):
    ...
```
The function that are decorated should take five arguments:

|      |                     |
|------|-------------------- |
|`obj` |  the current object |
|`lexicon`|  the name of the current lexicon |
|`actiontype` | 'add' or 'update' |
|`user` |  the name of the user that made the update |
|`date` |  the current date and time |

The decorator `@auto_update` takes any number of arguments, each of them stating a lexicon
that uses this automatic update.

Create a file where you define how the updates work.



```python
# my_autoupdates.py

# import the decorator
from karp5.document import auto_update

# this function will be applied to all objects that are saved in the lexicon 'mylexicon'
@auto_update('mylexicon')
def add_computed_field(obj, lexicon, actiontype, user, date):
    if actiontype == 'add':
        obj['whathapppend'] = "I was added"
        obj['auto_id'] = generate_id(lexicon)
    else:
        obj['whathapppend'] = "I've been around for a while"
    return

# this function will apply to all objects saved in the lexicons
# 'mylexicon' and 'myotherlexicon'
@auto_update('mylexicon', 'myotherlexicon')
def add_more_data(obj, lexicon, actiontype, user, date):
    stats = get_lexicon_stats(lexicon)
    obj['stats'] = stats
```

Finally, make sure that the file `my_autoupdates.py` is be read when karp
is loaded. You can achieve this by importing it somewhere, for example
in your new file `mykarp.py` from the section above.



Add extra src
=============
Some functions in Karp relies on information specific to each lexicon.
For example, the `export` function only works if every resource defines
how it should be converted to other formats.
For these functions, it is possible to inject your own source code in to Karp.
Karp will look then for user defined code for the current mode and run it. If
no user defined code is available, the default code will be used instead.

Currently, there are five points in Karp's source code where you may define
your own functionality:

| Function       | arguments                        |  |
|----------------|----------------------------------|---------|
| `exportformat` | (ans, lexicon, mode, toformat)   | is run for `export`,  which extracts data from sql |
| `format`       | (ans, es, mode, index, toformat) | is run for normal search (`query`). Adds data. |
| `export`       | (ans, es, mode, index, toformat) |  is run for normal search (`query`).  Replaces the json data. |
| `format_query` | (field, query)                   | alters the user's query string (eg by lowercasing it) |
| `autocomplete` | (mode, boost, query)             | is run for autocomplete query |


It might be a good idea to call the same function for the three first
calls (although they accept different arguments, for practical reasons).

| Argument |     |
|----------|-----|
| ans      | the result from ES (a json object) |
| lexicon  | the lexicon, eg. "saldo"|
| mode     | the current mode, eg "external" |
| toformat | a string defining the wanted format, eg "csv" |
| index    | the current index in case more data from ES is needed |
| field    | the field the query is matched to, eg "wordform" |
| query    | the querystring, eg "ost" |
| boost    | the fields that the query should preferably be found in |


To add source code, simple create a python file with one or many of the functions above.
Then put the path to this file `modes.json`.
```json
"mymode": {
    ...
   "src": "skbl.searching"
}
```

It is also possible to change how the `autocomplete` call behaves for
different modes. The `autocomplete` will always look for entries that have a value set
for the field defined for `autocomplete` in `config/modes.json` and then show this field.
In the default setup, it will also search for the given query string in the
fields specified as `boost` fields in `config/modes.json` (eg. `wordforms`).
For example, the query `autocomplete?q=ost` will search entries matching

1. the `autocomplete` field exists
2. `ost` is found in the `boost` fields [modifiable part]

and return the `autocomplete` field for these entries.

The extra source code added to this part may modify the part 2 above. For the SB mode
`external`, the query above would search for entries where

1. the `autocomplete` field exists
2. `ost` is found in a word form field which is not a compounding form
