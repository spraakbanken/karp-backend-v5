"""Mode"""
from abc import ABCMeta, abstractmethod
import copy
from typing import Dict, List, Optional

import attr


def falsly_values_to_none(x):
    if not x:
        return None
    return x


@attr.s(auto_attribs=True)
class Mode:
    id: str = attr.ib()
    type: str = attr.ib()
    indexalias: str = attr.ib()
    suggestionalias: str = attr.ib()
    elastic_url: List[str] = attr.Factory(list)
    sql: Optional[str] = None
    secret_fields: List[str] = attr.Factory(list)
    src: Optional[str] = attr.ib(default=None, converter=falsly_values_to_none)
    sort_by: List[str] = attr.Factory(list)
    head_sort_field: List[str] = attr.Factory(list)
    autocomplete_field: List[str] = attr.Factory(list)
    minientry_fields: List[str] = attr.Factory(list)
    statistics_buckets: List[str] = attr.Factory(list)
    boosts: List[str] = attr.Factory(list)
    groups: List[str] = attr.Factory(list)
    is_index: bool = False
    filter_for_unauth_user: Optional[Dict] = None

    @classmethod
    def from_mapping(cls, id: str, mapping: Dict, defaults: Optional[Dict] = None):
        if defaults:
            kwargs = copy.deepcopy(defaults)
            kwargs.update(mapping)
        else:
            kwargs = dict(mapping)

        return cls(id=id, **kwargs)


class ModeRepository(metaclass=ABCMeta):
    @abstractmethod
    def mode_by_id(self, mode_id: str) -> Mode:
        raise NotImplementedError()

    @abstractmethod
    def mode_ids(self) -> List[str]:
        raise NotImplementedError()

    def modes_that_include_mode(self, mode_id: str) -> List[Mode]:
        modes = dict()
        modes[mode_id] = self.mode_by_id(mode_id)
        for m_id in self.mode_ids():
            if m_id == mode_id:
                continue
            mode = self.mode_by_id(m_id)
            if mode_id in mode.groups:
                modes[m_id] = mode

        return list(modes.values())
