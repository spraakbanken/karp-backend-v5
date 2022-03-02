# karp-backend-5

**This package is the legacy version of Karp, [go here for the current version(https://github.com/spraakbanken/karp-backend)]**

## master

[![codecov](https://codecov.io/gh/spraakbanken/karp-backend-v5/branch/master/graph/badge.svg)](https://codecov.io/gh/spraakbanken/karp-backend-v5)
[![](https://github.com/spraakbanken/karp-backend-v5/workflows/Build/badge.svg)](https://github.com/spraakbanken/karp-backend-v5/actions)

Karp is the lexical platform of Språkbanken.
Now migrated to Python 3.6+.

# Karp in Docker

For easy testing, use [Docker](https://docs.docker.com/engine/installation/) to run Karp-b.

- Follow the steps given [here](https://github.com/spraakbanken/karp-docker)

- Run `docker-compose up -d`
- Test it by running `curl localhost:8081/app/test`

**If you want to use Karp without Docker, keep on reading.**

# Prerequisites

- [ElasticSearch6](https://www.elastic.co/downloads/past-releases/elasticsearch-6-3-0)
- SQL, preferrably [MariaDB](https://mariadb.org/)
- a WSGI server
  for example [mod_wsgi](http://modwsgi.readthedocs.io/en/develop/) with [Apache](http://httpd.apache.org/), Waitress, Gunicorn, uWSGI. . .
- an authentication server. Read more about this [here](https://github.com/spraakbanken/karp-docker/blob/master/dummyauth/README.md)
- [Python >= 3.6](https://www.python.org/downloads/) with [pip](http://pip.readthedocs.org/en/stable/installing/)

# Installation

Karp uses virtuals envs for python. To get running:

- run `make install`
- or:
  1. Create the virtual environment using `python3 -m venv venv`.
  2. Activate the virtual environment with `source venv/bin/activate`.
  3. `pip install -r requirements.txt`

# Configuration

Set the environment varibles `KARP5_INSTANCE_PATH` and `KARP5_ELASTICSEARCH_URL`:

1. using `export VAR=value`
2. or creating a file `.env` in the root of your cloned path with `VAR=value`
3. `KARP5_INSTANCE_PATH` - the path where your configs are. If you have cloned this repo you can use `/path/to/karp-backend/`.
4. `KARP5_ELASTICSEARCH_URL` - the url to elasticsearch. Typically `localhost:9200`

Copy `config.json.example` to `config.json` and make your changes.
You will also need to make configurations for your lexicons.
Read more [here](doc/manual.md).

# Tests

TODO: DO MORE TESTS!
Run the tests by typing: `make test`

Test that `karp-backend` is working by starting it
`make run` or `python run.py`

# Known bugs

Counts from the `statistics` call may not be accurate when performing
subaggregations (multiple buckets) on big indices unless the query
restricts the search space. Using
[`breadth_first`](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-terms-aggregation.html#_collect_mode) mode does not (always) help.

Possible workarounds:

- use [composite aggregation](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-composite-aggregation.html) instead, but this does not work with filtering.
- set a bigger shard_size (27 000 works for saldo), but this might break your ES cluster.
- have smaller indices (one lexicon per index) but this does not help for big lexicons or statistics over many lexicons.
- don't allow deeper subaggregations than 2. Chaning the `size` won't help.

# Elasticsearch

If saving stops working because of `Database Exception: Error during update. Message: TransportError(403, u'cluster_block_exception', u'blocked by: [FORBIDDEN/12/index read-only / allow delete (api)];').`, you need to unlock the relevant ES index.

### This is how you do it:

Repeat for every combination of `host` and `port` that is relevant for you. But you only need to do it once per cluster.

- Check if any index is locked: `curl <host>:<port>/_all/_settings/index.blocks*`
  - If all is open, Elasticsearch answers with `{}`
  - else it answers with `{<index>: { "settings": { "index": { "blocks": {"read_only_allow_delete": "true"} } } }, ... }`
- To unlock all locked indices on a `host` and `port`:
  - `curl -X PUT <host>:<port>/_all/_settings -H 'Content-Type: application' -d '{"index.blocks.read_only_allow_delete": null}'`
