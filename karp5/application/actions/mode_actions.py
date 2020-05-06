from typing import List, Optional

from karp5.config import conf_mgr
from karp5.cli import upload_offline


def recover(mode: str, *, suffix: Optional[str] = None, lexicons: Optional[List[str]] = None):
    if not lexicons:
        lexicons = conf_mgr.get_lexiconlist(mode)

    index_name = upload_offline.make_indexname(mode, suffix)

    return "Ok"
