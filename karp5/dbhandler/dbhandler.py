# -*- coding=UTF-8 -*-
"""
Connect to the sql data base and interact with it.
Emails the admins (config/config.json) if an error occurs.
"""

import datetime
import json
import logging
from typing import List, Union

import sqlalchemy as sql
from sqlalchemy.ext.compiler import compiles

from karp5.config import mgr as conf_mgr


_logger = logging.getLogger("karp5")


@compiles(sql.VARCHAR, "mysql")
@compiles(sql.String, "mysql")
def compile_varchar(element, compiler, **kw):
    """ Forces mysql to use case sensitiveness for strings types """
    return "VARCHAR(%s) COLLATE utf8_bin" % (element.length)


STATUS_CHANGE = sql.types.Enum("added", "changed", "removed", "imported")
STATUS_SUGG = sql.types.Enum("waiting", "accepted", "rejected", "accepted_modified")


def get_engine(lexicon, mode=None, suggestion=False, echo=True):
    if mode:
        dburl = conf_mgr.get_mode_sql(mode)
    else:
        dburl = conf_mgr.get_lexicon_sql(lexicon)
    print("dburl = {}".format(dburl))
    if not dburl:
        raise SQLNull("%s/%s" % (lexicon, mode))

    metadata = sql.MetaData()
    if not suggestion:
        db_entry = create_table(metadata)
    else:
        db_entry = create_suggestion_table(metadata)

    engine = sql.create_engine(dburl, encoding="utf-8", echo=echo)
    metadata.create_all(engine)
    return engine, db_entry


def create_table(metadata):
    db_entry = sql.Table(
        "karpentry",
        metadata,
        sql.Column("id", sql.String(50), index=True),
        sql.Column("date", sql.types.DateTime, index=True),
        sql.Column("user", sql.String(320), index=True),
        # Text(2**24-1) corresponds to MediumText in MySQL
        # avoid using the type MediumText (specific to MySQL)
        sql.Column("source", sql.types.Text(2 ** 24 - 1)),
        sql.Column("msg", sql.String(160)),
        sql.Column("lexicon", sql.String(50), index=True),
        sql.Column("status", STATUS_CHANGE),
        sql.Column("version", sql.Integer),
    )
    sql.Index("historyindex", db_entry.c.lexicon, db_entry.c.status, db_entry.c.date)
    return db_entry


def create_suggestion_table(metadata):
    db_entry = sql.Table(
        "karpsuggestions",
        metadata,
        sql.Column("id", sql.String(50), index=True),
        sql.Column("date", sql.types.DateTime, index=True),
        sql.Column("user", sql.String(320), index=True),
        # Text(2**24-1) corresponds to MediumText in MySQL
        # avoid using the type MediumText (specific to MySQL)
        sql.Column("source", sql.types.Text(2 ** 24 - 1)),
        sql.Column("msg", sql.String(160)),
        sql.Column("lexicon", sql.String(50), index=True),
        # For suggestions
        sql.Column("status", STATUS_SUGG, index=True),
        sql.Column("origid", sql.String(22), index=True),
        # Remember which version this is a copy of
        sql.Column("version", sql.Integer),
        sql.Column("acceptmsg", sql.String(160)),
    )
    return db_entry


def update_test(_id, lexicon, doc, user, msg):
    try:
        engine, db_entry = get_engine(lexicon)
        ins = db_entry.insert().values(
            id=_id, date=datetime.datetime.now(), user=user, msg=msg, source=doc
        )
        conn = engine.connect()
        conn.execute(ins)
        return 1, ""
    except SQLNull(lexicon):
        return 0, ("Lexicon %s has no SQL instance" % lexicon)
    except Exception as e:
        return 0, handle_error(e, user, msg, doc)


def update(
    _id,
    doc,
    user,
    msg,
    lexicon,
    version=0,
    status="waiting",
    engine=None,
    db_entry=None,
    suggestion_id="",
    date="",
):
    """ Puts an update in the database. If several updates are to be done, an
        engine should be created beforehand in order to avoid errors due to too
        many connections (1040). If no engine is provided, a new one is created
        If suggestion_id is set, this is added to the suggestion table, with
        _id used as orginid.
    """
    try:
        if engine is None:
            engine, db_entry = get_engine(lexicon, suggestion=bool(suggestion_id))

        try:
            version = int(version)
        except ValueError as e:
            version = -1
        if suggestion_id:
            # If the suggestion_id is a bool, set it to be empty
            # A string here means that the suggestion is a modification,
            # while True means that it is a suggested addition.
            # No suggestion_id at all (empty string or False) would mean that
            # it is not a suggestion but a real update.
            if isinstance(suggestion_id, bool):
                suggestion_id = ""
            ins = db_entry.insert().values(
                id=_id,
                origid=suggestion_id,
                date=date or datetime.datetime.now(),
                user=user,
                source=doc,
                version=version,
                msg=msg,
                acceptmsg="",
                status="waiting",
                lexicon=lexicon,
            )
        else:
            ins = db_entry.insert().values(
                id=_id,
                lexicon=lexicon,
                date=date or datetime.datetime.now(),
                user=user,
                msg=msg,
                source=doc,
                status=status,
                version=version,
            )
        conn = engine.connect()
        conn.execute(ins)
        conn.close()
        return 1, ""
    except SQLNull(lexicon):
        return 0, ("Lexicon %s has no SQL instance" % lexicon)
    except Exception as e:
        return 0, handle_error(e, user, msg, doc)


def update_bulk(lexicon, bulk):
    user = "admin"
    try:
        engine, db_entry = get_engine(lexicon, echo=False)
        gen_bulk = []
        for (_id, data, user, msg, lex, status) in bulk:
            user = user
            gen_bulk.append(
                {
                    "id": _id,
                    "date": datetime.datetime.now(),
                    "user": user,
                    "source": data,
                    "msg": msg,
                    "lexicon": lex,
                    "status": status,
                }
            )

        # if outputfile:
        #     with open(outputfile,'w') as f:
        #        for ins in gen_bulk:
        #            s = db_entry.insert(ins).compile(engine,
        #                             compile_kwargs={"literal_binds" : True})
        #            f.write(str(s))
        # else:
        engine.execute(db_entry.insert(), gen_bulk)
        return len(bulk), ""

    except SQLNull(lexicon):
        return 0, ("Lexicon %s has no SQL instance" % lexicon)
    except Exception as e:
        return 0, handle_error(e, user, "bulk update: %s" % e, "")


def dbselect(
    lexicon,
    user="",
    _id="",
    from_date="",
    to_date="",
    exact_date="",
    status=None,
    max_hits=10,
    engine=None,
    db_entry=None,
    suggestion=False,
    mode="",
):
    # does not accept a list of lexicons anymore
    if status is None:
        status = []
    try:
        if engine is None or db_entry is None:
            engine, db_entry = get_engine(lexicon, mode=mode, suggestion=suggestion)

        conn = engine.connect()
        operands = []
        if user:
            operands.append(db_entry.c.user == user)
        if _id:
            operands.append(db_entry.c.id == _id)
        if from_date:
            operands.append(db_entry.c.date >= from_date)
        if to_date:
            operands.append(db_entry.c.date <= to_date)
        if exact_date:
            operands.append(db_entry.c.date == exact_date)
        if lexicon:
            operands.append(db_entry.c.lexicon == lexicon)
        add_list_operands([(status, db_entry.c.status)], operands)
        selects = sql.select([db_entry]).where(sql.and_(*operands))
        if max_hits > 0:
            selects = selects.limit(max_hits)  # only get the first hits
        selects = selects.order_by(db_entry.c.date.desc())  # sort by date
        _logger.info("selects = %s", selects)
        res = []
        for entry in conn.execute(selects):
            # transform the date into a string now to enforce isoformat
            version = 8 if suggestion else 7
            obj = {
                "id": entry[0],
                "date": str(entry[1]),
                "user": entry[2],
                "doc": json.loads(entry[3]),
                "lexicon": entry[5],
                "message": entry[4],
                "status": entry[6],
                "version": entry[version],
            }
            if suggestion:
                obj["acceptmessage"] = entry[9]
                obj["origid"] = entry[7]
            res.append(obj)
        conn.close()
        return res

    except SQLNull(lexicon):
        _logger.warning("Attempt to search for %s in SQL, no db available", lexicon)
        return []


def dbselect_gen(
    lexicon,
    user="",
    _id="",
    from_date="",
    to_date="",
    exact_date="",
    status=None,
    max_hits=10,
    engine=None,
    db_entry=None,
    suggestion=False,
    mode="",
):
    # does not accept a list of lexicons anymore
    if status is None:
        status = []
    try:
        if engine is None or db_entry is None:
            engine, db_entry = get_engine(lexicon, mode=mode, suggestion=suggestion)

        conn = engine.connect()
        operands = []
        if user:
            operands.append(db_entry.c.user == user)
        if _id:
            operands.append(db_entry.c.id == _id)
        if from_date:
            operands.append(db_entry.c.date >= from_date)
        if to_date:
            operands.append(db_entry.c.date <= to_date)
        if exact_date:
            operands.append(db_entry.c.date == exact_date)
        if lexicon:
            operands.append(db_entry.c.lexicon == lexicon)
        add_list_operands([(status, db_entry.c.status)], operands)
        selects = sql.select([db_entry]).where(sql.and_(*operands))
        if max_hits > 0:
            selects = selects.limit(max_hits)  # only get the first hits
        selects = selects.order_by(db_entry.c.date.desc())  # sort by date
        _logger.info("selects = %s", selects)
        for entry in conn.execute(selects):
            # transform the date into a string now to enforce isoformat
            version = 8 if suggestion else 7
            obj = {
                "id": entry[0],
                "date": str(entry[1]),
                "user": entry[2],
                "doc": json.loads(entry[3]),
                "lexicon": entry[5],
                "message": entry[4],
                "status": entry[6],
                "version": entry[version],
            }
            if suggestion:
                obj["acceptmessage"] = entry[9]
                obj["origid"] = entry[7]
            yield obj
        conn.close()
        # return res

    except SQLNull(lexicon):
        _logger.warning("Attempt to search for %s in SQL, no db available", lexicon)
        return


def add_list_operands(to_add, operands):
    for vals, row_val in to_add:
        disjunct_operands = []
        if isinstance(vals, str):
            vals = [vals]
        for val in vals:
            disjunct_operands.append(row_val == val)

        operands.append(sql.or_(*disjunct_operands))


def get_entries_to_keep_gen(lexicon, *, to_date=None):
    engine, db_entry = get_engine(lexicon, echo=False)

    _logger.debug("exporting entries from %s ", lexicon)

    dbselect_kwargs = {"engine": engine, "db_entry": db_entry, "max_hits": -1}
    if to_date is not None:
        dbselect_kwargs["to_date"] = to_date

    old_id = None
    for entry in dbselect_gen(lexicon, **dbselect_kwargs):
        if entry["id"] == old_id:
            print(f"skipping entry = {entry}")
            continue
        elif entry["status"] == "removed":
            print(f"skipping entry = {entry}")
            old_id = entry["id"]
            continue
        else:
            old_id = entry["id"]
            yield entry


def modifysuggestion(_id, lexicon, msg="", status="", origid="", engine=None, db_entry=None):
    try:
        if engine is None or db_entry is None:
            engine, db_entry = get_engine(lexicon, suggestion=True)
        if isinstance(msg, str):
            msg = msg.encode("utf-8")
        conn = engine.connect()
        operands = []
        if status:
            operands.append(db_entry.c.status == status)
        if msg:
            operands.append(db_entry.c.msg == msg)
        if origid:
            operands.append(db_entry.c.origid == origid)
        update = (
            db_entry.update()
            .where(db_entry.c.id == _id)
            .values({"status": status, "acceptmsg": msg})
        )
        conn.execute(update)
        conn.close()
        return 1, ""

    except SQLNull(lexicon):
        return 0, ("Lexicon %s has no SQL instance" % lexicon)
    except Exception as e:
        return 0, handle_error(e, "--modification--", msg, "--modified--")


def handle_error(e, user, msg, doc):
    mail_sent = "No warnings sent by email"
    if conf_mgr.app_config.ADMIN_EMAILS:
        import karp5.dbhandler.emailsender as sender

        report = "User: %s, msg: %s. \nDoc:\n%s" % (user, msg, doc)
        msg = "Karp-b failure, %s.\n%s\n%s" % (datetime.datetime.now(), e, report)
        sender.send_notification(conf_mgr.app_config.ADMIN_EMAILS, "Karp failure", msg)
        mail_sent = "Warning sent to %s" % ", ".join(conf_mgr.app_config.ADMIN_EMAILS)
    return "%s. %s" % (str(e), mail_sent)


def delete(lexicon, _id):
    engine, dbtable = get_engine(lexicon)
    conn = engine.connect()
    conn.execute(dbtable.delete().where(dbtable.c.id == _id))
    conn.close()

    return []


def deletebulk(lexicon="", user=""):
    engine, dbtable = get_engine(lexicon)
    conn = engine.connect()
    operands = []
    if user and lexicon:
        operands = []
        operands.append(dbtable.c.user == user)
        operands.append(dbtable.c.lexicon == lexicon)
        choice = sql.and_(*operands)
    elif user:
        choice = dbtable.c.user == user
    elif lexicon:
        choice = dbtable.c.lexicon == lexicon

    conn.execute(dbtable.delete().where(choice))
    conn.close()


def get_entries_to_keep(lexicons: Union[str, List[str]], *, to_date=None, exclude_states=None):
    """Retrieve entries from one or several lexicons to keep.

    Arguments:
        lexicons {Union[str, List[str]]} -- lexicon or lexicons to export

    Keyword Arguments:
        to_date {[type]} -- Optional date to limit the search (default: {None})

    Returns:
        Iterable -- [descrip
    """
    to_keep = {}
    if isinstance(lexicons, str):
        lexicons = [lexicons]

    for lex in lexicons:
        engine, db_entry = get_engine(lex, echo=False)
        dbselect_kwargs = {"engine": engine, "db_entry": db_entry, "max_hits": -1}
        if to_date:
            dbselect_kwargs["to_date"] = to_date
        for entry in dbselect(lex, **dbselect_kwargs):
            _id = entry["id"]
            if _id:  # don't add things without id, they are errors
                if _id in to_keep:
                    last = to_keep[_id]["date"]
                    if last < entry["date"]:
                        _logger.debug("|get_entries_to_keep_from_sql| Update entry.")
                        to_keep[_id] = entry
                else:
                    to_keep[_id] = entry
            else:
                _logger.warning("|sql no id| Found entry without id:")
                _logger.warning("|sql no id| %s", entry)
    # _logger.debug("to_keep = %s", to_keep)
    if exclude_states:
        if isinstance(exclude_states, str):
            exclude_states = [exclude_states]
        gen_out = ((i, v) for i, v in to_keep.items() if v["status"] not in exclude_states)
    else:
        gen_out = to_keep.items()
    return gen_out


class SQLNull(Exception):
    """ Tells that there is no SQL instance """

    def __init__(self, lex):
        Exception.__init__(self, "No SQL db available for %s" % lex)
