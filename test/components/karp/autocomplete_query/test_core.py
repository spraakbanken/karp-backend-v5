import pytest

from karp.autocomplete_query.core import (
    AutoCompleteInputDto,
    AutoCompleteQueryV4,
    AutoCompleteQueryV5,
)
from karp.config import ConfigManager
from karp.user.core import User


@pytest.fixture()
def user1() -> User:
    return User(
        username="user1",
        is_authenticated=True,
        permitted=["saldo"]
    )

@pytest.fixture()
def input_dto(user1: User) -> AutoCompleteInputDto:
    return AutoCompleteInputDto(
        mode="karp",
        user=user1,
        qs=["ko"]
    )


@pytest.fixture()
def config_manager() -> ConfigManager:
    from karp5.config import conf_mgr
    return conf_mgr

    
@pytest.fixture()
def v4_query(config_manager: ConfigManager) -> AutoCompleteQueryV4:
    return AutoCompleteQueryV4(config_manager)
    

@pytest.fixture()
def v5_query(config_manager: ConfigManager) -> AutoCompleteQueryV5:
    return AutoCompleteQueryV5(config_manager)
    

def test_compare(input_dto, v4_query, v5_query):

    assert v4_query.query(input_dto) == v5_query.query(input_dto)
