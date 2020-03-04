import attr
from typing import Dict


@attr.s(auto_attribs=True)
class User:
    name: str = ""
    is_authenticated: bool = False
    lexicon_permissions: Dict[str, Dict[str, bool]] = attr.Factory(dict)

    def is_not_authenticated(self) -> bool:
        return not self.is_authenticated
