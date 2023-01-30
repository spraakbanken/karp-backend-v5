import abc

import pydantic

from karp.config import ConfigManager
from karp.user.core import User


class AutoCompleteInputDto(pydantic.BaseModel):
    mode: str
    user: User
    qs: list[str]


class AutoCompleteQuery(abc.ABC):
    @abc.abstractmethod
    def query(self, input_dto: AutoCompleteInputDto):
        ...


class AutoCompleteQueryV4(AutoCompleteQuery):
    def __init__(self, conf_mgr: ConfigManager):
        self.conf_mgr = conf_mgr
        
    def query(self, input_dto: AutoCompleteInputDto):
        return input_dto.mode


class AutoCompleteQueryV5(AutoCompleteQuery):
    def __init__(self, conf_mgr: ConfigManager):
        self.conf_mgr = conf_mgr
        
    def query(self, input_dto: AutoCompleteInputDto):
        headboost = self.conf_mgr.searchfield(input_dto.mode, "boosts")[0]
        return {
            "mode": input_dto.mode,
            "headboost": headboost,
        }
