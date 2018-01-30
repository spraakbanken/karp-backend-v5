# Adapt your Karp


Add extra urls
=======
If you would like your Karp to handle mor requests than the standard
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
as the name of the function.
The first argument of the decorator should be a list. 
Each decorated function will add an url to this list.

There are four keyword arguments to the decorator; `url`, `methods`, `crossdomain` and `name`.

|             |      |
|-------------|------|
|`url`        | adds a suffix  to the url. This might be used for variable parts of the url.|
|`methods`    | sets what [http methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods) that can be used for this url. Default: `GET`.|
|`name`       | changes the url name. Should be used when the name of the function is not wanted.|
|`crossdomain`| defines whether this url should accept [cross domain calls](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS). Default: `true`.|


```python
# mykarp.py
# import the route decorator
from src.server.helper.utils import route

# the function init will be called when karp starts
def init():
    # the list of urls to export
    urls = []

    # add the first one: 'infoabout/<lexicon>'
    @route(urls, '<lexicon>')
    def infoabout():
        return getinfo()


    # add another: '/addinfo'
    @route(urls, methods=["POST"])
    def addinfo():
        return postinfo()

    return urls
```

Finally, update Karp's `main.py` to make it load your urls:

```python
import backend as karpbackend  # the standard karp
# add this line:
import mykarp  # your karp


def load_urls():
    flaskhelper.register(karpbackend.init())
    # add this line:
    flaskhelper.register(mykarp.init())

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
that uses this automatical update.

Create a file where you define how the updates work.



```python
# my_autoupdates.py

# import the decorator
from src.server.autoupdates import auto_update

# this function will be applied to all objects that are saved in the lexicon 'mylexicon'
@auto_update('mylexicon')
def add_computed_field(obj, lexicon, actiontype, user, date):
    if actiontype == 'add':
        obj['whathapppend'] = "I was added"
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
TODO
Some functions in Karp relies on information specific to each lexicon.
For example, the `export` function only works if every resource defines
how it should be converted to other formats.
Currently, there are five points in Karp's source code where you may define
your own functionality:

| Function       | arguments                        |  |
|----------------|----------------------------------|---------|
| `exportformat` | (ans, lexicon, mode, toformat)   | is run for `export`,  which extracts data from sql |
| `format`       | (ans, es, mode, index, toformat) | is run for normal search (`query`). Adds data. |
| `export`       | (ans, es, mode, index, toformat) |  is run for normal search (`query`).  Replaces the json data. |
| `format_query` | (field, query)                   | alters the user's query string (eg by lowercasing it) |
| `autocomplete` | (mode, boost, q)                 | is run for autocomplete query |


It might be a good idea to call the same function for the three first
calls (although they accept different arguments, for pratical reasons).

It is also possible to change how the `autocomplete` call behaves for
different modes.


Add the path to your config file `modes.json`.
```json
"mymode": {
    ...
   "src": "skbl.searching"
}
```



Add extra stuff (skbl, match)
