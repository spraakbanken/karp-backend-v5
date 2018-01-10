Karp in Docker
=============
For easy testing, use [Docker](TODO) to run Karp-b.

* Follow the steps given [here](TODO github/karp-docker/README)


* Run `docker-compose up -d`
* Test it by running `curl localhost:8081/app/test`


Prerequisites
=============

* [ElasticSearch2](TODO)
* SQL, preferrably [MariaDB](TODO)
* a WSGI server
  for example [mod_wsgi with Apache](TODO), Waitress, Gunicorn, uWSGI. . .
* an authentication server  # TODO more about this somewhere
* [Python >= 2.7](https://www.python.org/downloads/) with [pip](http://pip.readthedocs.org/en/stable/installing/)


Installation
============

Karp uses virtuals envs for python. To get running:

1. Install virtualenv using `pip install virtualenv`
2. Create the virtual environment using `virtualenv venv`.
3. Activate the virtual environment with `source venv/bin/activate`.
4. `pip install -r requirements.txt`


Configuration
=============

Copy config.json.example to config.json and make your changes. (read more in the docs)


Tests
=====
TODO: DO MORE TESTS!
Test that Karp-b is runnig by starting it
`python src/main.py`
