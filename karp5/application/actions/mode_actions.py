from typing import List, Optional

from karp5.config import conf_mgr


def recover(mode: str, *, suffix: Optional[str], lexicons: Optional[List[str]]):
    if not lexicons:
        lexicons = conf_mgr.le
    return "Ok"
