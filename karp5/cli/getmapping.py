import json

# import logging
import os

from karp5.config import mgr as conf_mgr
from . import upload_offline as upload

_mapping = "kastmapp.json"


def getmapping(alias, outfile=""):

    es = conf_mgr.elastic(alias)
    if conf_mgr.modes.get(alias)["is_index"]:
        to_create = [alias]
    else:
        to_create = conf_mgr.modes.get(alias)["groups"]

    typ = conf_mgr.modes.get(alias)["type"]
    testindex = "testmapping"
    try:
        mapp = open(_mapping, "r").read()
    except Exception:
        mapp = None
    added = []
    for index in to_create:
        print("create", index)
        try:
            print("create")
            es.indices.create(index=testindex, body=mapp)
            print("created")
        except Exception:
            es.indices.delete(index=testindex)
            es.indices.create(index=testindex, body=mapp)
            raise

        for name, info in conf_mgr.lexicons.items():
            if name == index:
                default = conf_mgr.lexicons.get("default", {})
                path = info.get("path", default.get("path", ""))
                fformat = info.get("format", default.get("format", "json"))
                data = open("%s.%s" % (os.path.join(path, name), fformat), "r").read()
                print("read", "%s.%s" % (os.path.join(path, name), fformat))
                upload.upload(
                    fformat,
                    info["mode"],
                    info["order"],
                    data,
                    es,
                    testindex,
                    typ,
                    sql=False,
                    with_id=False,
                )
                print(name, "finished")

    ans = es.indices.get_mapping(index=testindex)
    # pretty print(with json dumps)
    res = json.dumps(ans, indent=4, separators=(",", ": "))
    if outfile:
        open(outfile, "w").write("Lexicons %s" % added)
        open(outfile, "a").write(res)
    else:
        print(res)
    es.indices.delete(index=testindex)
