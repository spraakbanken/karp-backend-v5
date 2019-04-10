
# Calls to the backend
*Version: [SBVERSION]*

|        |                            |
|:-------|:---------------------------|
|**Public calls (may require password for protected lexicons):**||

|        |                            |
|:-------|:---------------------------|
|[modes](#modes)                      |see the hierarchy of the modes |
|[groups](#groups)                    |see the available index modes and their components |
|[modeinfo](#modeinfo)                |see the available search fields of a mode |
|[lexiconinfo](#lexiconinfo)          |see the available search fields of a lexicon |
|[lexiconorder](#lexiconorder)        |for retrieving the lexicon order |
|[query](#query)                      |for normal querying |
|[querycount](#querycount)            |for querying with some statistics |
|[minientry](#minientry)              |for getting minientries |
|[statistics](#statistics)            |for getting statistics, aggregation |
|[statlist](#statlist)                |for getting statistics, table view |
|[autocomplete](#autocomplete)        |for autocompletion of lemgrams |
|[saldopath](#saldopath)              |for showing the path from a saldo sense to PRIM |
|[getcontext](#getcontext)            |for showing the (alphabetical) neighbours of an entry |
|[explain](#explain)                  |for normal querying |
|[random](#random)                    |for retrieving a random lexical entry |
|[suggest](#suggest)                  |make an update suggestion |
|[suggestnew](#suggest)               |suggest a new entry |
|[checksuggestion](#checksuggestion)  |see the status of a suggestion |
| <br/> ||
|**Password protected calls:**||
|[delete](#delete)                           |delete an entry by \#ID |
|[mkupdate](#update)                         |update a lexical entry |
|[add](#add)                                 |add a lexical entry |
|[readd](#add)                               |add an entry which already has an id (one that has been deleted) |
|[addbulk](#addbulk)                         |add multiple entries |
|[add\_child](#add_child)                    |add an entry and link it to its parent |
|[checksuggestions](#checksuggestions)       |view suggestions |
|[acceptsuggestion](#acceptsuggestion)       |accept a suggestion |
|[acceptandmodify](#acceptandmodify)         |accept a suggestion after modifications have been made to it |
|[rejectsuggestion](#rejectsuggestion)       |reject a suggestion |
|[checkuser](#checkuser)                     |for checking whether the user is ok |
|[checkuserhistory](#checkuserhistory)       |for retrieving the edit history of a user |
|[checkhistory](#checkhistory)               |for retrieving the edit history of an entry |
|[checklexiconhistory](#checklexiconhistory) |for retrieving the edit history of one or more lexicon |
|[checkdifference](#checkdifference)         |see the difference between two versions |
|[export](#export)                           |export a lexicon |


# Query language

The query language is simple and based on the language used in Karp's
frontend.

**simple:** free text search. Searches all fields.

* `q=simple||satt och`

**extended:** search a specific field

* `q=extended||and|field|operator|value`   (positive)
* `q=extended||not|field|operator|value`   (negative)

**Example:** search all entries with a word form that is "blomma" or
"äpple" and that has no part of speech tag:

* `q=extended||and|pos|missing||and|wf|equals|blomma|äpple`


# Operators

* `equals`
* `exists`
* `missing` (may not be available for lexicons with nested document structure)
* `regexp`
* `startswith`
* `endswith`
* `lte` (less than)
* `gte` (greater than)
* `range` (syntax: `fieldX|range|0|5`)


# Modes

The lexicons in Karp are divided into groups. A group consists of
lexicons that have a similar document structure. Each group has it's own
set of search fields, ordering functions etc. Groups that are sometimes
queried together are gathered into modes. The modes often, but not
always, correspond to the frontend modes. Every group is also a mode.
You can find more information about the available groups
[here]([SBURL]/groups) and modes [here]([SBURL]/modes).


# Search fields

Which search fields that are available depends on which mode you are
using. To see all fields for SB's default lexicons, go to
[[SBURL]/modeinfo/karp]([SBURL]/modeinfo/karp)


# Calls in detail

## query<a name="query"></a>

Login may be required for some lexicons.

|Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`q`        |the query|
|`mode`     |which mode to search in. default: karp|
|`resource` |one or more comma separated lexicon to search. default: all|
|`size`     |number of hits to show on each page. default: 25|
|`start`    |the index of the first hit to show. default: 0|
|`sort`     |one or more comma separated fields to sort on. default: depends on mode, usually lexiconOrder, score, baseform, lemgram|
|`export`   |get the result in another format. which options that are available depends on lexicon and mode. examples: xml, lmf, tsb, tab, csv.|
|`format`   |get each hit in the json structure in another format. which options that are available depends on lexicon and mode. examples: app, tryck.|


### Formatting and exports

Asking for **export** will not return the json objects (the hits). The
result will look like:

     {
         "formatted": a string in the current format
         ...
     }

Asking for another **format**, will give the following result

    {
        "hits": {
            "hits":[{
                "_source": ...,
                "formatted": "...xml string...",
                ...
            }]
        }
    }

**Examples:**

- [`[SBURL]/query?q=simple||stort hus&mode=stablekarp`]([SBURL]/query?q=simple%7C%7Cstort%20hus&mode=stablekarp)
- [`[SBURL]/query?q=simple||flicka&mode=saldogroup&resource=saldo,saldom,saldoe`]([SBURL]/query?q=simple%7C%7Cflicka&mode=saldogroup&resource=saldo,saldom,saldoe)
- [`[SBURL]/query?q=extended||and|lemgram|startswith|dalinm--`]([SBURL]/query?q=extended%7C%7Cand%7Clemgram%7Cstartswith%7Cdalinm--)
- [`[SBURL]/query?q=extended||and|wf|equals|äta||and|pos|missing&resource=kelly,lwt&mode=stablekarp`]([SBURL]/query?q=extended%7C%7Cand%7Cwf%7Cequals%7Cäta%7C%7Cand%7Cpos%7Cmissing&resource=kelly,lwt&mode=stablekarp)
- [`[SBURL]/query?q=extended||and|wf|regexp|.*o.*a&mode=bliss`]([SBURL]/query?q=extended%7C%7Cand%7Cwf%7Cregexp%7C.*o.*a&mode=bliss)
- [`[SBURL]/query?q=extended||and|wf|regexp|.*o.*a&start=25&mode=bliss`]([SBURL]/query?q=extended%7C%7Cand%7Cwf%7Cregexp%7C.*o.*a&start=25&mode=bliss)
- [`[SBURL]/query?q=extended||and|sense|exists&mode=historic_ii`]([SBURL]/query?q=extended%7C%7Cand%7Csense%7Cexists&mode=historic_ii)
- [`[SBURL]/query?q=extended||and|wf|equals|sitta||not|wf|equals|satt&mode=external`]([SBURL]/query?q=extended%7C%7Cand%7Cwf%7Cequals%7Csitta%7C%7Cnot%7Cwf%7Cequals%7Csatt&mode=external)
- [`[SBURL]/query?q=simple||muminfigurer&mode=term-swefin&format=csv`]([SBURL]/query?q=simple||muminfigurer&mode=term-swefin&format=csv)

**Result:**

    hits{
      total: number of hits
      hits:  a list with information about the hits
         hits[n]._source:      all information in hit n
         hits[n]._source._id   Elasticsearch's identifier for the entry
         hits[n]._version:     the current version of this entry
         hits[n]._source.lexiconName
         hits[n]._source.lexiconOrder
         hits[n]._source.FormRepresentations
         hits[n]._source.Sense
         hits[n]._source.WordForms

         hits[n]._source.ListOfComponents
         hits[n]._source.RelatedForm
         hits[n]._source.compareWith
         hits[n]._source.entryType
         hits[n]._source.saldoLinks
         hits[n]._source.see
         hits[n]._source.symbolCenter
         hits[n]._source.symbolHeight
         hits[n]._source.symbolPath
         hits[n]._source.symbolWidth

         For freetext search (simple||...) only:
         hits[n].highlight       information and paths about the matching part of the entry
    }


## querycount<a name="querycount"></a>

As a normal [*query*](#query), but also shows the distribution over
lexicons. Is a mix of [*query*](#query) and [*statistics*](#statistics).
The distribution results are sorted in lexicon order.

**Example:**

- [`[SBURL]/querycount?q=simple||stort hus&mode=stablekarp`]([SBURL]/querycount?q=simple%7C%7Cstort%20hus&mode=stablekarp)


**Result:**

    hits{...}                                          as above
    distribution                                       a list of counts for each lexicon that contains at least one match
    distribution[n].key                                the order for the n:th lexicon
    distribution[n].doc_count                          the count for the n:th lexicon
    distribution[n].lexiconName.buckets.[0].doc_count  the count for the n:th lexicon (again)
    distribution[n].lexiconName.buckets.[0].key        the name of the n:th lexicon


## minientry<a name="minientry"></a>

Returns a mini variant of the normal query result. Only shows the fields
specified in "show", but otherwise works the same way as
[*query*](#query).

|Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`q`        |the query |
|`mode`     |which mode to search in. default: karp |
|`resource` |one or more comma separated lexica to search. default: all |
|`show`     |one or more comma separated fields to show. default: depends on mode, usually lexiconName, lemgram, baseform |
|`size`     |number of hits to show on each page. default: 25 |

**Examples:**

- [`[SBURL]/minientry?q=extended||and|wf|equals|sitta|ligga`]([SBURL]/minientry?q=extended%7C%7Cand%7Cwf%7Cequals%7Csitta%7Cligga)
- [`[SBURL]/minientry?q=extended||and|writtenForm|equals|får||and|writtenForm|equals|fick&show=pos`]([SBURL]/minientry?q=extended%7C%7Cand%7CwrittenForm%7Cequals%7Cfår%7C%7Cand%7CwrittenForm%7Cequals%7Cfick&show=pos)

**Result:**

See [query](#query).


## statistics<a name="statistics"></a>

Aggregation, as provided by Elasticsearch. Shows the number of hits,
group by the requested fields. Defaults to show the distribution grouped
by lexicon and pos tags.

|Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`q`        |  the query |
|`mode`     |  which mode to search in. default: karp |
|`resource` |  one or more comma separated lexica to search. default: all |
|`size`     |  number of hits to show in each bucket. default: 100 |
|`buckets`  |  one or more comma separated fields to group the results by. default: lexiconName, pos |
|`cardinality`|  shows the cardinality number of values for the innermost of the requested buckets, instead of showing the actual values. Not compatible with `q`. `size` will be ignored. |


**Examples:**

- [`[SBURL]/statistics`]([SBURL]/statistics)
- [`[SBURL]/statistics?q=simple||kasusformer&mode=karp`]([SBURL]/statistics?q=simple%7C%7Ckasusformer&mode=karp)
- [`[SBURL]/statistics?resource=hellqvist&mode=historic_ii`]([SBURL]/statistics?resource=hellqvist&mode=historic_ii)
- [`[SBURL]/statistics?buckets=pos.bucket,sense.bucket&size=200&mode=stablekarp`]([SBURL]/statistics?buckets=pos.bucket,sense.bucket&size=200&mode=stablekarp)

The result is not sorted.

**Result:** X is the name of the first bucket (default: lexiconName), Y
(defaults to pos) the second and so on. For a search where a query or a
resource is specified:

    aggregations {
        q_statistics.doc_count : total number of hits

        q_satistics.X: information about the data grouped by X (the first bucket)
        q_satistics.X_missing: information about the data missing X

          q_satistics.X.buckets[n].key: X value
          q_satistics.X.buckets[n].doc_count: number of hits within the X value

          q_satistics.X.buckets[n].Y: information grouped by X and then Y
          q_satistics.X.buckets[n].Y.doc_count: number of hits within the Y value in X


          q_satistics.X_missing.buckets[n]: information about entries which do not have any X value
          q_satistics.X_missing.buckets[n].doc_count: number of hits that do not have any X value

          q_satistics.X.buckets[n].Y_missing: information grouped by X and then Y, showing cases without any value for Y
          q_satistics.X.buckets[n].Y.doc_count: number of hits within the Y value in X

          ....
    }


## statlist<a name="statlist"></a>

Gives a table view based on the bucketed aggregations (see
[statistics](#statistics)). Shows the number of hits, group by the
requested fields. Defaults to show the distribution grouped by lexicon
and pos tags.

|Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`q`        |the query|
|`mode`     |which mode to search in. default: karp|
|`resource` |one or more comma separated lexica to search. default: all|
|`buckets`  |one or more comma separated fields to group the results by. default: lexiconName, pos|
|`size`     |number of hits to show in each bucket. Does hence not correspond to the number of table rows. default: 100.|

**Examples:**

-   [`[SBURL]/statlist`]([SBURL]/statlist)
-   [`[SBURL]/statlist?q=simple||ärt&buckets=resource,lemgram.bucket`]([SBURL]/statlist?q=simple%7C%7Cärt&buckets=resource,lemgram.bucket)
-   [`[SBURL]/statlist?resource=hellqvist`]([SBURL]/statlist?resource=hellqvist)
-   [`[SBURL]/statlist?mode=historic_i&buckets=pos.bucket`]([SBURL]/statlist?mode=historic_i&buckets=pos.bucket)
-   [`[SBURL]/statlist?buckets=pos.bucket&size=200&mode=stablekarp`]([SBURL]/statlist?buckets.bucket=pos&size=200&mode=stablekarp)

**Result:**

    {
      "stat_table": [
        [
          "konstruktikon",
          "",
          88
        ],
        [
          "saldom",
          "nn",
          3
        ],
        ...
      ]
    }


## autocomplete<a name="autocomplete"></a>

Gives suggestions for lemgrams (or other fields, as specified for each
mode) which have a word form (or other field, as specified for each
mode) matching the given one.

It does not match prefixes. Searching for "sig" does hence not give
suggestions like "sigill" or "signatur".

Provides lemgram suggestions to Korp, by looking in mode `external`.

**Examples:**

- [`[SBURL]/autocomplete?mode=external&q=sig`]([SBURL]/autocomplete?mode=external&q=sig)
- [`[SBURL]/autocomplete?multi=kasta,docka&resource=saldom&mode=external`]([SBURL]/autocomplete?multi=kasta,docka&resource=saldom&mode=external)
- [`[SBURL]/autocomplete?q=kasus&resource=saldom,dalin,hellqvist`]([SBURL]/autocomplete?q=kasus&resource=saldom,dalin,hellqvist)
- [`[SBURL]/autocomplete?q=kasta&resource=saldom`]([SBURL]/autocomplete?q=kasta&resource=saldom)

|Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`q`        | the query, a word form|
|`multi`    | a comma separated list of queries (word forms). do not use together with q|
|`resource` | one or more comma separated lexica to search. default: all|
|`mode`     | which mode to search in. default: karp|

The result is not sorted and one lemgram may occur multiple times

**Result:**

    hits{
      total: number of hits
      hits:  information about the hits
      hits[n]._source: information about hit n
      hits[n]._source.FormRepresentations.lemgram: lemgram
    }

If `multi` parameter is used, the output will be a dictionary with one
key corresponding to every input word. The values will be the same
format as for q:

    {
        "kasta": {"hits": ...  },
        "docka": {"hits": ...  }
    }


## saldopath<a name="saldopath"></a>

Shows the path from a saldo sense to PRIM. Only works for saldo senses.

**Example:**

- [`[SBURL]/saldopath?q=bandy..1`]([SBURL]/saldopath?q=bandy..1)

**Result:**

    {
        "path": [input_sense..1, ..., PRIM..1]
    }


## getcontext<a name="getcontext"></a>

Shows the (alphabetical) neighbours of an entry

The sorting order is based on the mode configs. (The order must be
strict, eg. no two words may have the same score. If they do, getcontext
will not work properly.)

**Examples:**

- [`[SBURL]/getcontext/#lexicon?center=#ID`]([SBURL]/getcontext/#lexicon?center=#ID)
- [`[SBURL]/getcontext/saldo?q=extended||and|pos|equals|nn&size=2`]([SBURL]/getcontext/saldo?q=extended%7C%7Cand%7Cpos%7Cequals%7Cnn&size=2)
- [`[SBURL]/getcontext/saol?q=extended||not|ptv|equals|true&size=2`]([SBURL]/getcontext/saol?q=extended||not|ptv|equals|true&size=2)

|Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`center`   |the Elasticsearch-ID of the entry to center the search around. default: the first entry|
|`q`        |an optional query to restrict entries that appear in the result|
|`size`     |number of hits to show on each side of the center word. default: 10|

**Result:**

    {
        "center": {}, // the centered entry
        "pre": [],    // a list of hits (that match the query) occurring immediately before the centered
        "post": [],   // a list of hits (that match the query) occurring immediately after the centered entry
    }


## explain<a name="explain"></a>

A tool for debugging. Shows the result of the given query, the json
formatted query as sent to Elasticsearch and the information given by a
[\_validate/query?explain](https://www.elastic.co/guide/en/elasticsearch/guide/current/_validating_queries.html#_understanding_queries)
call to Elasticsearch.

**Example:**

- [`[SBURL]/explain?q=simple||mastodont`]([SBURL]/explain?q=simple%7C%7Cmastodont)

**Result:**

    {
        "ans": {},                // the normal query result
        "elastic_json_query": {}, // the query translated to Elastic's api
        "explain": {}             // Elastic's result to a `_validate/query?explain` query.
    }

## modes<a name="modes"></a>

Shows the hierarchy of the modes.

- [`[SBURL]/modes`]([SBURL]/modes)


## groups<a name="groups"></a>

Shows the available groups (modes to which updates can be made).

- [`[SBURL]/groups`]([SBURL]/groups)


## modeinfo<a name="modeinfo"></a>

Shows the search fields that are available in a mode.

- [`[SBURL]/modeinfo/bliss`]([SBURL]/modeinfo/bliss)


## lexiconinfo<a name="lexiconinfo"></a>

Shows the search fields that are available in a lexicon. Note that the
fields are set on the level of lexicon groups - some fields in the
listing might be unused by the specified lexicon.

- [`[SBURL]/lexiconinfo/blissword`]([SBURL]/lexiconinfo/blissword)


## lexiconorder<a name="lexiconorder"></a>

Shows the lexicons and their order. The [query](#query) results are also
ordered in this way.

- [`[SBURL]/lexiconorder`]([SBURL]/lexiconorder)


**Result:**

    {
      "lexiconA": 1,
      "lexiconB": 3,
      "lexiconC": 8,
      ...
    }


## random<a name="random"></a>

Shows a randomly selected lexical entry.

|Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`resource` |  one or more comma separated lexica to search. default: all|
|`mode`     |  which mode to search in. default: karp|
|`show`     |  one or more comma separated fields to show. default: depends on mode, usually lexiconName, lemgram, baseform|
|`show_all` |  all fields of the entries will be shown if this flag is set to true (or any value). Overrides show|
|`size`     |  number of hits to show on each page. default: 1|

**Examples:**

- [`[SBURL]/random`]([SBURL]/random)
- [`[SBURL]/random?resource=saldo`]([SBURL]/random?resource=saldo)


## suggest, suggestnew<a name="suggest"></a>

Works like [update](update), but requires no log in. The suggestion is
stored in a separate system until it has been accepted by a logged in
user.

The field `version` is optional, but will prevent an old version to
later override a newer one.

**Examples:**

- `[SBURL]/suggest/#lexicon/#ID -d {"message" : ..., "user": ..., "version": ... }`
- `[SBURL]/suggestnew/#lexicon -d {"message" : ..., "user": ..., "version": ... }`

**Result:**

    {
        "es_ans": {},        // output from Elasticsearch
        "es_loaded": 1,      // 1 if the suggestion is stored in Elasticsearch
        "id":                // the #ID of the suggestion. Can be used to see the current status, accept or reject the suggestion.
        "sql_loaded": 1,     // 1 if the suggestion is stored in SQL
        "suggestion": true,
        "sql_error": ""      // present if there were errors storing the suggestion
    }


## delete<a name="delete"></a>

Deletes one entry, identified by its lexicon and \#ID. Requires a valid
username and password.

**Example:**

-   [`[SBURL]/delete/#lexicon/#ID`]([SBURL]/delete/#lexicon/#ID)

**Result:**

    {
        "sql_loaded": 1, // 1 if successfully marked as deleted in the SQL database
        "es_loaded": 1,  // 1 if successfully deleted from Elasticsearch (is no longer searchable)
        "es_ans": "",    // the answer from Elasticsearch
    }


## mkupdate<a name="update"></a>

Updates a lexicalentry identified by its lexicon and Elasticsearch's id
(\#ID). Requires a valid username and password. The IDs are found in any
query results. To avoid conflicts, the last known version number of the
entry can be provided as a query string. If a version number is provided
and the database entry has been updated since the our last read, a
version conflict error message will be returned.

**Examples:**

- `XPOST [SBURL]/mkupdate/#lexicon/#ID -d '{'doc' : updated entry, 'version' : (last) version, 'message' : update message}'`
- `XPOST [SBURL]/mkupdate/#lexicon/#ID -d '{'doc' : updated entry, 'version' : (last) version, 'message' : update message}'`

**Result:**

    {
        "sql_loaded": 1,  // 1 if successfully saved in the SQL database
        "es_loaded": 1,   // 1 if successfully stored in Elasticsearch (is searchable)
        "es_ans": {"_id":..., "_index":..., "_type":..., "_version": ...}   // the answer from Elasticsearch
    }

**Error messages:**

Version conflict:

    {"message": "Database exception: Error during update. Message: TransportError(409, u`RemoteTransportException[...]; nested: VersionConflictEngineException[...]: version conflict, current [3], provided [1]]; `)."}

ID could not be found:

    {"message": "Database exception: Error during update. Message: TransportError(404, u`RemoteTransportException[...]; nested: DocumentMissingException[...]: document missing]; `)"}


## add, readd<a name="add"></a>

Adds a lexicalentry. Requires a valid username and password. The given
ID is found in the returned object and is associated with the entry in
Elasticsearch and in the SQL database.

**Examples:**

- `XPOST [SBURL]/add/#lexicon -d '{'doc' : {...,'lexiconName': 'saldo', lexiconOrder': 0, ...} 'version': (last) version, 'message': update message}'`

If an entry has existed in the data base before and has got an ID, it
can be readded to get the same ID:

- `XPOST [SBURL]/readd/#lexicon/#ID -d '{'doc': {...,'lexiconName': 'saldo', lexiconOrder': 0, ...} 'version': (last) version, 'message': update message}'`

**Result:**

    {
        "sql_loaded": 1,     // 1 if successfully saved in the SQL database
        "es_loaded": 1,      // 1 if successfully stored in Elasticsearch (is searchable)
        "suggestion": false, // true if the update has been treated as suggestion
        "es_ans": {"_id": ..., "_index": ..., "_type": ..., "_version": ..., "created": true}  // the answer from Elasticsearch
    }


## addbulk<a name="addbulk"></a>

Adds a list of entries to a lexicon. Requires a valid username and
password.

**Example:**

- `XPOST [SBURL]/addbulk/#lexicon -d '{'doc': [{...entry1...}, {...entry2...}, ...], 'message': update message}'`

**Result:**

    {
        "sql_loaded": 30, // number of entries successfully saved in the SQL database,
        "es_loaded": 30,  // number of entries successfully stored in Elasticsearch,
        "ids": [],        // a list of the new entries IDs,
        "suggestion": false
    }


## add\_child<a name="add_child"></a>

Adds a lexical entry and link it to its parent. Requires a valid
username and password. The given ID is found in the returned object and
is associated with the entry in Elasticsearch and in the SQL database.

**Example:**

- `XPOST [SBURL]/addchild/#lexicon/#parentid -d '{'doc': {..., 'lexiconName': 'saldo', lexiconOrder' : 0, ...} 'version': (last) version, 'message': update message}' `

**Result:**

    {
        "parent": // the result of adding the link to the parent (see mkupdate),
        "child":  // the result of adding the child (see add)
    }


## checksuggestions<a name="checksuggestions"></a>

Requires log in. Show the suggestions for the chosen lexicons.


|Required parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`resource` | one or more comma separated lexicons to search. default: all|

|Available Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`size`     |the number of suggestions to view (order by decreasing date). default: 50|
|`status`   |waiting, rejected, accepted. default: all|

**Example:**

- [[`SBURL]/checksuggestions?resource=konstruktikon&size=2&status=waiting`]([SBURL]/checksuggestions?resource=konstruktikon&size=2&status=waiting)

**Result:**

    {
      "updates": [
        {
          "acceptmessage":, // is set when the suggestion is accepted or rejected
          "date":,          // the date of suggestion
          "doc":,           // the suggested lexical entry
          "id":,            // the #ID of the suggestion
          "lexicon":,       // the lexicon it belongs to
          "message":,       // message from the suggester
          "origid":,        // the #ID of the entry the suggestion concerns
          "status":,        // the status of the suggestion (waiting, accepted or rejected)
          "user":,          // the name or email adress of the suggester
          "version":        // the version of the entry that the suggestion concerns
        }
      ]


## checksuggestion<a name="checksuggestion"></a>

Checks the status of a given suggestion. Does not require log in.

**Example:**

- [`[SBURL]/checksuggestion/#lexicon/#ID`]([SBURL]/checksuggestion/#lexicon/#ID)

    The \#ID refers to the suggestion, not the original entry.

**Result:**

    {
      "updates": [
        {
          "acceptmessage":, // is set when the suggestion is accepted or rejected
          "date":,          // the date of suggestion
          "doc":,           // the suggested lexical entry
          "id":,            // the #ID of the suggestion
          "lexicon":,       // the lexicon it belongs to
          "message":,       // message from the suggester
          "origid":,        // the #ID of the entry the suggestion concerns
          "status":,        // the status of the suggestion (waiting, accepted or rejected)
          "user":,          // the name or email adress of the suggester
          "version":        // the version of the entry that the suggestion concerns
        }
      ]


## acceptsuggestion<a name="acceptsuggestion"></a>

Requires log in. Changes the status of a suggestion to "accepted" and
moves it to the live data base. Accepted suggestions are still present
in the sql data base (but not searchable through the suggestion Elasticsearch).

**Example:**

- `[SBURL]/acceptsuggestion/#lexicon/#ID -d {"message" : ...}`

    The \#ID refers to the suggestion, not the original entry. The
    message will be stored in the suggestion data base and in the live
    data base.

**Result:**

    {
        "es_ans": {
            "_id":,           // #ID of the updated entry
            "_index":,
            "_type":,
            "_version":
        },
        "es_loaded": 1,       // 1 if successfully loaded to Elasticsearch
        "sql_loaded": 1,      // 1 if successfully loaded to the live SQL
        "sugg_db_error": "",  // present if there were errors storing the suggestion
        "sugg_db_loaded": 1,  // 1 if successfully loaded to suggestion SQL
        "sugg_es_ans": {
            "es_ans" : {...}, // answer from Elasticsearch
            "es_loaded": 1,   // 1 if removed from the suggestion Elasticsearch
            "sql_loaded": 1,  // 1 if the suggestion was marked as accepted
        }
    }


## acceptandmodify<a name="acceptandmodify"></a>

Requires log in. Changes the status of a suggestion to
"accepted\_modified" and adds the new, modified, version to the live
data base. Accepted suggestions are still present in the sql data base
(but not searchable through the suggestion Elasticsearch).

**Example:**

- `[SBURL]/acceptandmodify/#lexicon/#ID -d {"doc": {...} "message" : ...}`

    The \#ID refers to the suggestion, not the original entry. The data
    is the new version that should be kept. The message will be stored
    in the suggestion data base and in the live data base.

**Result:**

    {
        "es_ans": {
            "_id":,           // #ID of the updated entry
            "_index":,
            "_type":,
            "_version":
        },
        "es_loaded": 1,       // 1 if successfully loaded to Elasticsearch
        "sql_loaded": 1,      // 1 if successfully loaded to the live SQL
        "sugg_db_error": "",  // present if there were errors storing the suggestion
        "sugg_db_loaded": 1,  // 1 if successfully loaded to suggestion SQL
        "sugg_es_ans": {
            "es_ans" : {...}, // answer from Elasticsearch
            "es_loaded": 1,   // 1 if removed from the suggestion Elasticsearch
            "sql_loaded": 1,  // 1 if the suggestion was marked as accepted
        }
    }



## rejectsuggestion<a name="rejectsuggestion"></a>

Requires log in. Changes the status of a suggestion to "rejected".
Rejected suggestions are still present in the sql data base (but not
searchable through the suggestion Elasticsearch).

**Example:**

- `[SBURL]/rejectsuggestion/#lexicon/#ID -d {"message" : ...}`

    The \#ID refers to the suggestion, not the original entry. The
    message will be stored in the suggestion data base.

**Result:**

    {
        "es_ans": {},       // output from the deletion from the suggestion Elasticsearch
        "es_loaded": 1,     // 1 if successfully removed to the suggestion Elasticsearch
        "sugg_db_error":,   // present if there were errors storing the suggestion
        "sugg_db_loaded": 1 // 1 if successfully loaded to suggestion SQL
    }


## checkuser<a name="checkuser"></a>

Checks whether the provided user log-in details are ok.

**Result:**

    {
      "authenticated": "",              // is the user name and password ok
      "permitted_resources.lexica": ""  // lexicons that the user may see or edit
    }


## checkuserhistory<a name="checkuserhistory"></a>

Shows the edit history of the user, ordered from newest to oldest.

|Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`size`     |number of hits to show on each page. default: 10|

**Result:**

    {
        "updates": [
            {
                "date",
                "doc",     //the entry that has been edited
                "id",
                "message",
                "user"
            },
            ...
        ]
    }


## checkhistory<a name="checkhistory"></a>

Shows the edit history of an entry, selected by its identifier and
ordered from newest to oldest.

|Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`size`     |number of hits to show on each page. default: 10|

**Example:**

- [`[SBURL]/checkhistory/\#lexicon/\#ID`]([SBURL]/checkhistory/\#lexicon/\#ID)

**Result:**

{
    "updates": [
        {
            "date",
            "doc",     //the entry that has been edited
            "id",
            "message",
            "user"
        },
        ...
    ]
}


## checklexiconhistory<a name="checklexiconhistory"></a>

Shows the edit history of one lexicon, ordered from newest to oldest. If
no lexicon is specified, all is picked.

|Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`size`     |number of hits to show on each page. default: 10  |

**Examples:**

If a date is provided (in the correct format) only updates
done later than this is shown.

- [`[SBURL]/checklexiconhistory/#lexicon`]([SBURL]/checklexiconhistory/#lexicon])
- [`[SBURL]/checklexiconhistory/blissword/20150922`]([SBURL]/checklexiconhistory/blissword/20150922])

**Result:**

    {
        "updates": [
            {
                "date",
                "doc",     //the entry that has been edited
                "id",
                "message",
                "user",
                "type"     // CHANGED, ADDED or REMOVED, only present if checklexiconhistory is called
            },
            ...
        ]
    }


## checkdifference<a name="checkdifference"></a>

Shows the diff of a chosen \#ID.

**Examples:**

- [`[SBURL]/checkdifference/#lexicon/#ID/latest`]([SBURL]/checkdifference/#lexicon/#ID/latest)
- [`[SBURL]/checkdifference/#lexicon/#ID/latest/#fromdate`]([SBURL]/checkdifference/#lexicon/#ID/latest)
- [`[SBURL]/checkdifference/#lexicon/#ID/#fromdate/#todate`]([SBURL]/checkdifference/#lexicon/#ID/latest)

**Result:**

    {"diff": [
        {
            "field",  // a field that has been changed between the two versions
            "after",  // the content of the field in the later of the two versions
            "before", // the content of the field in the older of the two versions (not present if the field is added)
            "type"    // added, changed or removed
        }
    ]}


## export<a name="export"></a>

Exports a lexicon. Requires a valid username and password.

|Parameters:|                                                  |
|:----------|:-------------------------------------------------|
|`date`     |export the entries as they were a given date. default: latest|
|`export`   |export to another format than json, eg csv, tsv, xml. Not available for all lexicons! default: json|
|`size`     |number of hits to show. default: all entries|

**Examples:**

- [`[SBURL]/export/#lexicon`]([SBURL]/export/#lexicon)
- [`[SBURL]/export/#lexicon?date=20170901`]([SBURL]/export/#lexicon?date=20170901])
- [`[SBURL]/export/#lexicon?format=lmf&size=2`]([SBURL]/export/#lexicon?format=lmf&size=2)

**Result (if json):**

    {
        "lexicon": [
            ... the lexicon ...
         ]
    }
