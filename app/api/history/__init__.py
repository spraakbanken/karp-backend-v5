from __future__ import unicode_literals
from flask import Blueprint

bp = Blueprint('search', __name__)

from app.search import routes
