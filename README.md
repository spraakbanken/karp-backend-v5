**This package - code and documentation - is still under construction.**

Karp is the lexical platform of Språkbanken.

Karp in Docker
=============
For easy testing, use [Docker](https://docs.docker.com/engine/installation/) to run Karp-b.

* Follow the steps given [here](https://github.com/spraakbanken/karp-docker)


* Run `docker-compose up -d`
* Test it by running `curl localhost:8081/app/test`


If you want to use Karp without Docker, keep on reading.
Prerequisites
=============

* [ElasticSearch6](https://www.elastic.co/downloads/past-releases/elasticsearch-6-3-0)
* SQL, preferrably [MariaDB](https://mariadb.org/)
* a WSGI server
  for example [mod_wsgi](http://modwsgi.readthedocs.io/en/develop/) with [Apache](http://httpd.apache.org/), Waitress, Gunicorn, uWSGI. . .
http://modwsgi.readthedocs.io/en/develop/
http://httpd.apache.org/
* an authentication server. Read more about this [here](https://github.com/spraakbanken/karp-docker/blob/master/dummyauth/README.md)
* [Python 2.7 - 3.6](https://www.python.org/downloads/) with [pip](http://pip.readthedocs.org/en/stable/installing/)


Installation
============

Karp uses virtuals envs for python. To get running:

1. Install virtualenv using `pip install virtualenv`
2. Create the virtual environment using `virtualenv venv`.
3. Activate the virtual environment with `source venv/bin/activate`.
4. `pip install -r requirements.txt`


Configuration
=============

Copy `config.json.example` to `config.json` and make your changes.
You will also need to make configurations for your lexicons.
Read more [here](TODO manual.md).


Tests
=====
TODO: DO MORE TESTS!
Test that Karp-b is working by starting it
`python src/main.py`


Known bugs
==========
Counts from the `statistics` call may not be accurate when performing
subaggregations (multiple buckets) on big indices unless the query
restricts the search space. Using
[`breadth_first`](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-terms-aggregation.html#_collect_mode)
 mode does not (always) help.


Possible workarounds:

 - use [composite aggregation](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-composite-aggregation.html)
 instead, but this does not work with filtering.
 - set a bigger shard_size (27 000 works for saldo), but this might break your ES cluster.
 - have smaller indices (one lexicon per index) but this does not help for big lexicons or statistics over many lexicons.
 - don't allow deeper subaggregations than 2. Chaning the `size` won't help.
