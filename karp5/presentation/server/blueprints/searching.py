from flask import Blueprint, Response, abort, jsonify, make_response, request

from karp5.infrastructure.searching.queries.autocomplete_v4 import (
    AutocompleteV4Request,
    GetAutocompleteV4,
)
from karp5.infrastructure.kernel.config import conf_mgr
from karp5.context import auth
from karp5.server.translator import parser


searching_blueprint = Blueprint("searching_blueprint", __name__)


@searching_blueprint.route("/autocomplete_v4")
def get_autocomplete_v4() -> Response:
    """Returns lemgrams matching the query text.
    Each mode specifies in the configs which fields that should be
    considered.
    The parameter 'q' or 'query' is used when only one word form is to be
    processed.
    The parameter 'multi' is used when multiple word forms should be
    processed.
    The format of result depends on which flag that is set.
    """
    query = GetAutocompleteV4(configM=conf_mgr)

    user_is_authorized, permitted = auth.validate_user(mode="read")
    settings = parser.make_settings(
        permitted,
        {"size": 1000, "mode": "external"},
        user_is_authorized=user_is_authorized,
    )
    query = request.query_string
    autocomplete_request = AutocompleteV4Request(settings=settings, query=query)

    result = query.query(autocomplete_request)
    if not result:
        abort(404)
    return make_response(jsonify(result))
