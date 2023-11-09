from dataclasses import dataclass
from json import loads
from typing import Any
import logging
import re
from karp5 import errors

from karp5.server.translator import parser
from karp5.server.translator.errors import AuthenticationError

logger = logging.getLogger(__name__)


@dataclass
class AutocompleteV4Request:
    settings: dict[str, Any]
    query: str


class GetAutocompleteV4:
    def __init__(self, configM) -> None:
        self.configM = configM

    def query(self, request: AutocompleteV4Request):
        """Returns lemgrams matching the query text.
        Each mode specifies in the configs which fields that should be
        considered.
        The parameter 'q' or 'query' is used when only one word form is to be
        processed.
        The parameter 'multi' is used when multiple word forms should be
        processed.
        The format of result depends on which flag that is set.
        """
        query = request.query
        settings = request.settings
        configM = self.configM
        try:
            parsed = parser.parse_qs(query)
            mode = parser.get_mode(query)
            p_extra = parser.parse_extra(parsed, settings)
            qs = parsed.get("q", []) or parsed.get("query", [])
            multi = False
            if not qs:
                # check if there are multiple words forms to complete
                qs = settings.get("multi", [])
                logger.debug("qs %s" % qs)
                multi = True

            # use utf8, escape '"'
            qs = [re.sub('"', '\\"', q.decode("utf8")) for q in qs]

            headboost = configM.searchfield(mode, "boosts")[0]
            res = {}
            ans = {}
            # if multi is not true, only one iteration of this loop will be done
            for q in qs:
                boost = """"functions": [{"boost_factor" : "500",
                            "filter":{"term":{"%s":"%s"}}}]""" % (
                    headboost,
                    q,
                )

                if mode == "external":
                    exp = self.external_autocompletequery(mode, boost, q)
                else:
                    exp = self.autocompletequery(mode, boost, q)
                autocomplete_field = configM.searchonefield(mode, "autocomplete_field")
                fields = ['"exists": {"field" : "%s"}' % autocomplete_field]
                # last argument is the 'fields' used for highlightning
                elasticq = parser.search([exp] + p_extra, fields, "")

                es = configM.elastic(mode=mode)
                logger.debug("_source: %s" % autocomplete_field)
                logger.debug(elasticq)
                index, typ = configM.get_mode_index(mode)
                ans = parser.adapt_query(
                    settings["size"],
                    0,
                    es,
                    loads(elasticq),
                    {
                        "size": settings["size"],
                        "index": index,
                        "_source": autocomplete_field,
                    },
                )
                # save the results for multi
                res[q] = ans
            if multi:
                return res
            else:
                # single querys: only return the latest answer
                return ans
        except AuthenticationError as e:
            logger.exception(e)
            msg = e.message
            raise errors.KarpAuthenticationError(msg)
        except errors.KarpException as e:  # pass on karp exceptions
            logger.exception(e)
            raise
        except Exception as e:  # catch *all* exceptions
            logger.exception(e)
            raise errors.KarpGeneralError("Unknown error", debug_msg=e, query=query)

    def autocompletequery(self, mode, boost, q):
        """Constructs an autocompletion query, searching for lemgrams starting
        with 'text'
        Returns a query object to be sent to elastic search
        """
        # other modes: don't care about msd
        look_in = []
        for boost_field in self.configM.searchfield(mode, "boosts"):
            look_in.append('{"match_phrase" : {"%s" : "%s"}}' % (boost_field, q))

        exp = """"query" : {"function_score": {%s,
                "query" : { "bool" : {"should" :
                [%s]}}}}""" % (
            boost,
            ",".join(look_in),
        )

        return exp

    def external_autocompletequery(self, mode, boost, q):
        """Constructs an autocompletion query, searching for lemgrams starting
        with 'text'
        Returns a query object to be sent to elastic search
        """
        # external mode: exclude msd tags that mark compounds
        # q should be equal to baseform or be equal to an inflected form which does
        # not have the msd tag ci, cm och sms
        exp = """"nested" : {"path" :"WordForms", "query" : {"function_score": {%s,
                "query" : { "bool" : {"should" :
                [{"match_phrase" : {"%s" : "%s"}}, {"bool" :
                {"must" : [{"match_phrase" : {"%s" : "%s"}},
                {"bool" : {"must_not" : [{"regexp" : {"WordForms.msd" :
                    "c|ci|cm|sms"}}]}}]}}]}}}}}"""
        return exp % (
            boost,
            self.configM.lookup("baseform", mode),
            q,
            self.configM.lookup("wf_inflected", mode),
            q,
        )
