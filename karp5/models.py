"""Domain models use by Karp5.
"""
from typing import List, Optional, Union


class User:
    """Model of a User.
    """

    pass


class Lexicon:
    """Model of a Lexicon.
    """

    def __init__(self, name: str = None, mode=None):
        self.name = name
        self.mode = mode


class Mode:
    """Model of a Mode.
    """

    def __init__(
        self,
        name: str,
        *,
        elastic_url: List[str] = None,
        sql: Union[str, bool] = None,
        doc_type: str,
        secret_fields: List[str] = None,
        src: Optional[str] = None,
        suggestionalias: str,
        sort_by: List[str],
        head_sort_field: List[str],
        autocomplete_field: List[str],
        minientry_fields: List[str],
        statistics_buckets: List[str],
        boosts: List[str],
        is_index: bool = True,
        indexalias: str = None,
        groups: List[str] = None,
    ):
        self.name = name
        self.elastic_url = elastic_url
        self.sql = sql
        self.doc_type = doc_type
        self.secret_fields = secret_fields
        self.src = src
        self.suggestionalias = suggestionalias
        self.sort_by = sort_by
        self.head_sort_field = head_sort_field
        self.autocomplete_field = autocomplete_field
        self.minientry_fields = minientry_fields
        self.statistics_buckets = statistics_buckets
        self.boosts = boosts
        self.is_index = is_index
        if indexalias is None:
            self.indexalias = name
        else:
            self.indexalias = indexalias
        self.groups = groups


class Group:
    pass


class Entry:
    pass
