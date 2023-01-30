import pydantic


class User(pydantic.BaseModel):
    username: str
    is_authenticated: bool
    permitted: list[str]
    
    # def __init__(
    #     self,
    #     username: str,
    #     is_authenticated: bool,
    #     permitted: list[str],
    # ):
    #     self.username = username
    #     self.is_authenticated = is_authenticated
    #     self.permitted = permitted