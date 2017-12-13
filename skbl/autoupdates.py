import base64
from dateutil.parser import parse as dateparse
from dateutil.relativedelta import relativedelta
from flask import request
import logging
from src.server.autoupdates import auto_update
from urllib2 import urlopen, Request

# skbl_server = 'http://localhost:8080/'
skbl_server = 'http://dev.skbl.se/'


@auto_update('skbl')
def get_sortname(obj, lexicon, actiontype, user, date):
    " Add field with the name on which the sorting should be based "
    last = obj['name'].get('lastname', '')
    if last:
        obj['name']['sortname'] = last
    else:
        obj['name']['sortname'] = obj['name']['firstname']
    for author in obj.get('article_auth', []):
        author['fullname'] = '%s, %s' % (author.get('lastname'), author.get('firstname'))
    return obj


@auto_update('skbl')
def calculate_age(obj, lexicon, actiontype, user, date):
    born = obj.get('lifespan', {}).get('from', {}).get('date', {}).get('date', 0)
    dead = obj.get('lifespan', {}).get('to', {}).get('date', {}).get('date', 0)
    prev_age = obj.get('lifespan', {}).get('age')
    if born and dead:
        born = dateparse(born, default=dateparse('19000101'))
        dead = dateparse(dead, default=dateparse('19000101'))
        year = relativedelta(dead, born).years
        if year != prev_age:
            obj['lifespan']['age'] = year
    return obj


@auto_update('skbl')
def count_children(obj, lexicon, actiontype, user, date):
    kids = 0
    for rel in obj.get('relation', []):
        if rel.get('type') in ['Dotter', 'Son']:
            kids += 1
    obj['num_children'] = kids
    return obj


def clean_cache(obj, actiontype='', user='', date='', auth_str=''):
    # call the skbl-portal for a cache cleaning
    ans = 'error before connecting to server'
    try:
        url = skbl_server+'/emptycache'
        logging.debug("Clean skbl cache %s" % url)
        req = authorize_req(url, auth_str=auth_str)
        ans = urlopen(req).read()
        logging.debug('Cache cleaning: %s' % ans)

    except Exception as e:
        # log errors, but do not fail
        logging.error('Cache cleaning not ok: %s' % ans)
        logging.exception(e)
    return obj


@auto_update('skbl')
def refillcache(obj, lexicon, actiontype='', user='', date=''):
    """ Empty and refill the cache. """
    from threading import Thread
    auth_str = auth_encode()
    clean_cache(obj, actiontype, user, date, auth_str=auth_str)

    # Run the refill call in a subprocess, since this may take a while
    def call(url):
        logging.debug("cache auth %s" % url)
        req = authorize_req(url, auth_str=auth_str)
        logging.debug('cache %s' % urlopen(req).read())
        logging.debug("fill cache")
    t1 = Thread(target=call, args=[skbl_server+'/en/fillcache'])
    t2 = Thread(target=call, args=[skbl_server+'/sv/fillcache'])
    t1.daemon = True  # do not wait for the request to finish
    t1.start()
    t2.daemon = True  # do not wait for the request to finish
    t2.start()
    # Wait for the urlopen have a chance to send the request, but we do not
    # wait for the answer. We want to keep to waiting time low, since it will
    # effect respond time to the save-call to the karp backend. If the server
    # is under heavy load, this might not be enough time. In that case, the
    # cache will remain empty.
    import time
    time.sleep(0.5)
    return obj


def authorize_req(url, auth_str=''):
    req = Request(url)
    if not auth_str:
        auth = request.authorization
        user = '%s:%s' % (auth.username, auth.password)
        # encode to be accepted by base64
        auth_str = base64.b64encode(user.encode())
    req.add_header("Authorization", "Basic %s" % auth_str)
    return req


def auth_encode():
    auth = request.authorization
    user = '%s:%s' % (auth.username, auth.password)
    # encode to be accepted by base64
    return base64.b64encode(user.encode())
