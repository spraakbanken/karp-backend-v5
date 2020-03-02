import attr
import typing

@attr.s(auto_attribs=True)
class User:
    name: str = ""
    is_authenticated: bool = False
    allowed_lexicons: typing.List[str] = attr.Factory(list)

    def is_not_authenticated(self) -> bool:
        return not self.is_authenticated
