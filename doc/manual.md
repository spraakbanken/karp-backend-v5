<!--

OBS!

Gör inga ändringar direkt i HTML-dokumentet, då dessa kommer skrivas över och
gå förlorade. Ändringar ska göras i motsvarande Markdown-fil (samma filnamn
fast med filändelsen ".md").

-->

<script type="text/javascript">
  function loadCSS(filename){

    var file = document.createElement("link")
    file.setAttribute("rel", "stylesheet")
    file.setAttribute("type", "text/css")
    file.setAttribute("href", filename)

    if (typeof file !== "undefined")
      document.getElementsByTagName("head")[0].appendChild(file)
  }

  loadCSS("https://svn.spraakdata.gu.se/repos/lb/trunk/sbkhs/pub/korp.css")
</script>
# Karp's backend
## Technical report and installation guide


## About Karp
Karp is Språkbanken’s lexical infrastructure which is used for publishing and editing
lexical resources. Karp’s backend allows you to make your lexicons searchable and
editable. The lexicons must be in json format, but it is possible to have for example
xml blocks in the json objects, which can still be made searchable.
There are two main types of searches available, simple (free text search) and
extended (field search). In the free text search, the content of a predefined
set of fields is used, as defined when you set the configuration files. In the
extended search, the
user can choose which specific fields to search, eg. baseform or part of speech. Which
fields are searchable and how the text in them is analyzed is also defined during the
configuration.
The backend is a WSGI application written in Python. The main components of the
system are ElasticSearch and SQL. ElasticSearch (ES) provides fast searching and an
easy way of indexing and analyzing your data. The SQL database is used only as a
back-up and for keeping the revision history of edited resources.
The code base for Karp’s backend contains one example resource, the Bilingual
Glossary German-English with Probabilities (PANACEA) created by Linguatec GmbH,
which can be used for testing your Karp installation.


## Input Format

Each lexical entry must be represented as one json object, and contain the name of
the lexicon (`lexiconName`). It should also contain the order of the lexicons
(`lexiconOrder`), which regulates in which order the search results are shown<sup><a href="#footnote1">1</a></sup> .
This should be an integer, starting from 0 . A lexicon is a list of objects. A simple example:

``` json
[
 {
     "lexiconName": "saldo",
     "lexiconOrder": 0,
     "baseform": "katt",
     "partOfSpeech": "nn",
      "xml": "<definition>Some <b>dumped</b> data</definition>"
   },
  {
    "lexiconName": "saldo",
    "lexiconOrder": 0,
    "baseform": "hund",
    "partOfSpeech": "nn"
  },
  {
    "lexiconName": "lexin",
    "lexiconOrder": 1,
    "baseform": "hund",
    "partOfSpeech": ["nn","vb"],
    "lexinID": "lx500"
  }
]
```

The entries may of course have a much more complex structure, and contain lists,
other objects etc. ES will allow the type of a field to vary between lists and single
objects, but not between other any two types. The above example is thus ok, even
though `partOfSpeech` varies in type, but the below is not:
```json
[
 {
   "lexiconName": "saldo",
   "lexiconOrder": 0,
   "baseform": "katt",
   "partOfSpeech": "nn"
 },
 {
   "lexiconName": "lexin",
   "lexiconOrder": 1,
   "baseform": "hund",
   "partOfSpeech": {"swe": "nn", "eng": "vb"}
 }
]
```
Your work will be simplified if all entries are similarly structured, but it is not
required.

<span id="footnote1">[1]</span>
A standard use case of the Karp backend is to group all search results by
lexicon. This also corresponds to the set-up in the frontend. You will also
have to specify the order of your lexicons later in the configuration part


## Prerequisites
* [ElasticSearch6](https://www.elastic.co/downloads/past-releases/elasticsearch-6-3-0)
* SQL, preferrably [MariaDB](https://mariadb.org/)
* a WSGI server
  for example [mod_wsgi](http://modwsgi.readthedocs.io/en/develop/) with [Apache](http://httpd.apache.org/), Waitress, Gunicorn, uWSGI. . .
http://modwsgi.readthedocs.io/en/develop/
http://httpd.apache.org/
* an authentication server. Read more about this [here](https://github.com/spraakbanken/karp-docker/blob/master/dummyauth/README.md)
* [Python >= 2.7](https://www.python.org/downloads/) with [pip](http://pip.readthedocs.org/en/stable/installing/)


## Configurations
### Some notes on virtualenv
Whenever you want to run the code from a fresh terminal, you must
reenter the virtual environment: `source venv/bin/activate`
To deactivate the environment (when done working with the Karp), deactivate it:
`deactivate`


### Basic setup
For `karp-backend`to find the configuration, you first need to set the following
environment variable `KARP5_INSTANCE_PATH`.
Set by either:
- `export KARP5_INSTANCE_PATH=/path/to/karp-backend/`.
- add the line `KARP5_INSTANCE_PATH=/path/to/karp-backend/` to `.env` in the same path as `run.py`.

To configure the elasticsearch url, set the environment variable `KARP5_ELASTICSEARCH_URL`. You can specify several urls by separating them with ','.

The configurations are all done in the directory `config`.

0 = All users, including Dockers user, must set this option

1 = All non-Docker users must set this option

2 = Easy but not necessary

3 = For advanced users

Copy the configuration file `config.json.example` to `config.json` and make
the necessary changes as below.

* "AUTH": 1

    This file keeps the configurations needed to call the authorization system. To read or
    modify a lexicon, this system must permit the user to do so. If you don't have a autherization
    system you can use the dummy setup inculded in [Karp's Docker version]().
    It will let
    anyone read and modify all your lexicons.
    If you want to use another system read [this page](wsauth_manual.html) on how it should work, and then
    enter the configurations in the `config.json` file.
* "DB": 0-1
    * `ADMIN_EMAILS` 0: a list to which emails will be sent upon karp failures.
    * `SENDER_EMAIL` 2: the error emails will appear to be sent from this address
    * `DPASS` 1: the value of this string should be .dbuser:dbpassword@dbserver`
* "DEBUG": 2
    * `DEBUG_LEVEL` 2: set this to one of (DEBUG, INFO, WARNING, ERROR, CRITICAL) **Note** case-insensitive
    * `DEBUG_TO_STDERR` 2: if you want the logs to be written to a file, set this to `false`
    * configure the other parameters as you wish
* "SETUP": 0-3
    * `SECRET_KEY` 0: make up your own key here! Used for flask's [sessions](http://flask.pocoo.org/docs/0.12/quickstart/#sessions). Make it as random as possible.
    * `ABSOLUTE_PATH` 1: ?
    * `BACKEND_URL` 0: The url to `karp-backend` to display in API documentation.
    * `script_path` 1: ?
    * `standardmode` 1: name the mode that is the standard mode. This mode will later be setup in `modes.json`
    * `scan_limit` 3: for ES. Queries asking a large number of results should use scan/scroll instead
    *    of search. Set the limit for when scan should be performed.
    * `max_page` 3: the number of lexicon to appear on querycount results
    * `minientry_page` 3: the standard numbers of hits for a minientry query

This is all configurations you need to the get the (empty) Karp system up and running.


### Lexical configuration
In order to be able to search and upload data, you will also need to
configure how your data is structured. There are lexicon-related
configuration files in the Karp package that will work with the PANACEA lexicon
mentioned in Section 1. This was done in order to provide a working example. If
you want to use these, copy `modes.json.panacea` to `modes.json` and
`lexiconconf.json.panacea` to `lexiconconf.json`. Then skip to section [X](TODO).

If you want to use your own lexicon, keep on reading.

An entry in `lexiconconf.json` looks as follows.
```json
  "testlex": {
    "mode": "testlex",
    "order": 0,
    "path": "data/karplex/",
    "no_escape": false,
    "format": "json",
    "usedtags": []
  }
```
You must define one such object for each lexicon. If many lexicons have a similar setup,
you can use the `default` object.
```
{
  "default": {
    "path": "data/karplex/",
    "no_escape": false,
    "format": "json",
    "usedtags": []
  },
  "testlex1": {
    "mode": "testlex",
    "order": 0
  },
  "testlex2": {
    "mode": "testlex",
    "order": 1
  }
}
```
All items `(key, val)` of this object will be set for any lexicon that does not have any key `key`.

1 = All users with their own lexicon must set this option

2 = Easy but not necessary

3 = For advanced users

* `order` 1: the order (identifier) of the lexicon. The default karp settings will sort search results in this order.
* `mode` 1: the primary mode does this lexicon belong to.
* `path` 1: the path to the directory containing the lexicon
* `format` 1: should be json, unless you provide conversion scripts from your format to json
* `usedtags` 3: xml fields  in a lexicon may, for security reasons, only contain tags form a fixed set. Define this set here
* `no_escape` 3: put to true only if you want this lexicon to have any tags in its xml fields. do this at your own risk.


### Mode configuration
The lexicons in Karp are divided into groups. A group consists of lexicons that
have a similar document structure. Each group has it's own set of search fields,
ordering functions etc. Groups that are sometimes queried together are gathered
into modes. The modes often, but not always, correspond to the frontend modes.
Every group is also a mode and for convenience, they are all referred to as "modes".
In the file `modes.json` you define these modes and
state how they should be queried.

As for `lexiconconf.json`, you may put things that are common for many modes in
the "default" object. These settings will be overriden by explicit settings in the
other modes.
The example mode (`mode.json.example`) contains empty fields for all non-necessary settings.
`testindex1` in the same file contains all necessary settings for the most simple
mode type.

In `config.json` you provided the name of your standard mode. This mode must be implemented here.
In the example files, the mode is called *karp*.

0 = All users, including Dockers user, must set this option

1 = All non-Docker users must set this option

2 = Easy but not necessary

3 = For advanced users


* `indexalias` 0: the name of this mode/group
* `is_index` 0: true if this is a group, i.e. a mode that contains no other modes
* `groups` 0: if this mode contains other modes (`is_index` = true), then this mode is a collection of other modes.
*  `elastic_url` 1: the url to your ElasticSearch cluster.
* `sql` 1: the SQL table to use for this mode
* `suggestionalias` 1: the SQL table for [suggestions](TODO) for this mode
* `type` 1: the ElasticSearch [`type`](TODO) to use
* `sort_by` 2: the fields by which to sort the results for [advanced queries](TODO)
* `boosts` 2: ...
* `statistics_buckets`2: ...
* `minientry_fields` 3: (all fields below may be put to [])...
* `head_sort_field` 3: ...
* `autocomplete_field` 3: ...
* `secret_fields` 3: fields which should not be shown to non-logged in users
* `src` 3: pythonmodules which contain extra source code for this mode, eg `sb.server.formatdata`


### Mapping configuration
Each mode must have a file defining its fields, their data type and how to index them.
This is done in `mappingconf_<yourmode>.json`.
The settings are used by ElasticSearch, and you can read more about the process
[here](https://www.elastic.co/guide/en/elasticsearch/reference/2.4/mapping.html).
You can use this file to define and set tokenizers,
searchable fields etc.

The default `mappingconf_panacea.json.panacea` file contains a simple mapping
for the PANACEA lexicon. A more advanced example of a mapping can be found in
`mappingconf_advanced.json.example`.

#### Easy set-up: Using the default mapping
It it possible to partly ignore this step for the moment and go on to upload your
data. In that case all text in your data will be searchable and tokenized by a standard
[european tokenizer](https://www.elastic.co/guide/en/elasticsearch/reference/2.4/analysis-standard-tokenizer.html).

#### Advanced set-up: Creating a custom mapping
If - or when - you want more control of your data, you can add mapping files for each of your
modes.
If this is done after the data has been uploaded for the first time, you will need to [reload](TODO)
it after finishing the new mapping.
Have a look at the file `mappingconf_advanced.json.example`.
In the first section, `settings`, you can define custom tokenizers, analyzers
and filters etc.
You may also want to set the [result window size](TODO):

`"max_result_window" : 10000`

This will allow [deep pagination](TODO) to work up to 10 000 items (default in
ES2 is 1 000).
Set this to the same value as in `scan_limit` in `config.json`.

ES provides a set of built-in analyzers, and at Språkbanken we have added some
more to fit our data.
The default analyzer in ES will split words on special characters (-,\_,.,"...).
If that’s not what you want, consider the type `keyword`, which treats the
whole string as one token (useful for different types of identifiers, or
possibly multiwords expression that should not be analyzed as separate
tokens).
The analyzer `whitespace` splits only on whitespaces. If you are
interested in other alternatives or defining your own analyzers, please read
the [ES documentation](https://www.elastic.co/guide/en/elasticsearch/reference/2.4/analysis.html).
(TODO all this will change if we upgrade to ES6.)

The second section in the mappings file, `mappings`, is a definition of your data’s structure.
You can control the `_all` fields here:

`"_all" : {"enabled" : false}`  prevents ES from making all fields searchable.
If you do want all text to be searchable, put this to true. Note that this will
enable free text searches to match the text in `lexiconName` and `lexiconOrder`.

`"all_text", "all_xml"` These are used instead of `_all` in Språkbanken’s version.
Each field in the mapping below specifies whether its content should be copied to
one of those. The difference between the two is the analyzers used; text copied to
all_text is tokenized as normal, while the text copied to all_xml is tokenized as
xml. Simply leave out these if you enabled `_all` above.

The rest of the content is only depending on your data’s type structure. If your
data is simple, just write down the types of it yourself. If it is more complex, you
could let ES do the job for you, by inputting all data to ES and then extracting the
automatically generated mapping. To do this, run one of the commands:
without Docker:

`python cli.py getmapping config/newmappingconf.json`

with Docker:

`docker-compose run --rm karp python cli.py getmapping config/newmappingconf.json`

This will give you the file `newmappingconf.json`, which you can use as your `mappingconf_<yourmode>.json`.
Modify the settings mentioned above as needed.
What’s important is to look at the fields `copy_to`, `analyzer`,
`index` and `type` for each of your data fields.
In the below example, we see that `"blissName"` is of type `"text"`, and is copied to `all_text`,
meaning that it will be searchable in free text searches.
Since no analyzer is specified, ES will use its standard text analyzer.
`"category"` is also a `text`, but should be analyzed with our custom analyzer.
`"blissID"` is not indexed at all, meaning that it will not be searchable, neither in simple
nor extended queries.

```json
"blissName": {
  "copy_to" : "all_text",
  "type": "text"
},
"category": {
  "copy_to" : "all_text",
  "type": "text",
  "analyzer" : "full_name"
},
"blissID": {
  "index" : "no"
}
```
TODO check that this works with ES2 (or just update the whole example)

Note that you do not need to specify whether a field contains a list or a single object.
`"blissName"` could contain one string, or a list of strings.

Finally, the possibility of using multiple analyzer on a field is worth mentioning.
This is done by adding the special field called `fields`. In the example mapping,
you’ll see that `FormRepresentations.baseform` has an extra line:

```json
"fields" : {"sortform" : {"type" : "keyword"}}
```

By using this, we can search both `FormRepresentations.baseform` - where multiword
expressions have been tokenized - and `FormRepresentations.baseform.sortform` -
where the whole expression is always treated as one inseparable unit.
The first option
will allow us to to find "car park" by searching for "park", but will also find "car park"
when we search for words starting with "pa".


### Field mappings
Apart for the mappingsconfiguration above, each mode must also have a file defining which
fields to expose to the end user. This is done in `fieldmappings_<yourmode>.json`.

The keys in this object are names which you will later be able to use in an extended
query to Karp backend (and might hence match the field names for extended search in the frontend).
For example, if a lexical entry looks like this
```json
{
  "Form": {"baseform": "...", "partOfSpeech": "...", "example": "..."},
  "Sense": { "example": "..."}}
}
```
and you wish to be able to search for `baseform`, `part of speech` and the text in any of
the examples (but you do not make a distinction between `Form.exmaple` and `Sense.example`) you should add
these lines
```
{
  "baseform": ["Form.baseform"],
  "pos": ["Form.partOfSpeech"],
  "example": ["Sense.example","Form.example"]
}
```
Mappings can be many-to-many; one key can be linked to many fields and many keys
may refer to the same field.
The `anything`-field: ES will keep a copy of all text from the fields of your choice (you
will set this in the `mappingconf_<yourmode>.json`) in one or more designated fields, usually re-
ferred to as `_all`. Within Karp, these field is referred as `anything`,
and used for free text search, so specify here which ES field that should point to.
If you don’t know yet what field names you want to put here, simply put
`"anything" = ["_all"]`.


## Inputting data to the system
### Creating metadata
To generate metadata for the backend, first you must create `config/mappings/fieldmappings_<RESOURCE>.json` (see [config/mappings/fieldmappings_default.json](/config/mappings/fieldmappings_default.json) and [config/mappings/fieldmappings_panacea.json.panacea](../blob/master/config/mappings/fieldmappings_panacea.json.panacea) for examples) as describe in [here](#Field-mappings).
~~Then run in a virtual environment `python cli.py create_metadata` to create `config/fieldmappings.json` with all fieldmappings that a user can use.~~ (Not needed since *version 5.8.0*)

### create_mode & publish_mode
1. Your lexical resource must be in json-format as [above](#Input-Format).
2. Verify that `lexiconName` and `lexiconOrder` is present and correct in every lexical entry.
3. Place your data file `RESOURCE.json` in the directory specified in `lexiconconf.json`.
  * **example:** ```json "testlex": { ... "path": data/testlex/` ... }```
4. Run `source venv/bin/activate`
5. Run `python cli.py create_mode RESOURCE SUFFIX`. This will import all lexical entries from `<path-in-lexiconf.json-for RESOURCE>/RESOURCE.json` to the backend.
  * **example:** `python cli.py create_mode testlex 20181003` imports from `data/testlex/testlex.json`.
6. Run `python cli.py publish_mode RESOURCE SUFFIX`. This will point the alias `RESOURCE` to `RESOURCE_SUFFIX` so that searches with `mode=RESOURCE` will be directed to `RESOURCE_SUFFIX`. Will also update all modes that have `RESOURCE` in their `groups`-list.
  * **example:** `python cli.py publish_mode testlex 20181003`
7. Restart the server.



### TODO touch



## Reloading your data
TODO


## Outputting your data from the system
TODO


## Testing the backend
Once you finished the configuration and uploading, you might want to test how
things are working. Below you'll find some basic examples of how to inspect the
data.
In these examples, we are running a test version locally. Start it by running
`python backend.py`
The web service will now run on `localhost:5000`. If you are using Docker, or if you
have your WSGI server of choice running and set-up already, you should also be able
to access the Karp backend through that, without running the python script manually.
The docker webservice runs on `localhost:8081/app`.

Errors and debug messages will be logged to `std.err` or to a file, according to your setup in `config.json`.
To see the errors and debugs when running Docker, use `docker-compose logs -f`.

If you change the Kapr source code, the WSGI application needs to be reloaded:
`touch backend.wsgi`.

To see a detailed documentation on the API, go to `http://localhost:5000/app` (or to `https://ws.spraakbanken.gu.se/ws/karp`).

#### Aggregation and statistics
To start with, you might want to do an aggregation over the data to see some statistics
and make sure everything is there:

`curl 'localhost:5000/statlist'`

Note: if you have left the field `statistics_buckets` in `modes.json` empty, you will have to manually
choose which fields you want to see statistics for: `localhost:5000/statlist?buckets=pos`.

The result looks something like this:
```json
{
  "stat_table": [
    [
      "nn",
      2
    ],
    [
      "ab",
      1
    ]
  ]
}
```
In this case, our default statistical bucket is set to part of speech and the lexicon in our default mode has two
nouns (nn) and one adverbial (ab).


#### Simple search
If the statistics looked good, you could go on testing a free text search:
`curl 'localhost:5000/query?q=simple||house'`.

Check that the result is what you expected. The search should query all fields you defined as `anything` in `modes.json`.
Also check that the index (`_index`) specified in each `hit` is the one that you last uploaded your data to.

#### Extended search
Now try and see that the configuration in `fieldmappings.py` works. Try searching
different fields (keys from the fieldmappings).

`curl 'localhost:5000/query?q=extended||and|FIELD|equals|house'`

### Random search
The random search will, as the name suggests, let you see random entries. The information
will be displayed the same way as for minientries. It might be useful to test
this function a few times to see that the entries show up and contain the information
you expected.

`curl 'localhost:5000/random'`
