from karp5.dbhandler.dbhandler import SQLNull


def test_sql_null_w_lexicon():
    sql_null = SQLNull("LEXICON")
    assert str(sql_null) == "SQLNull: No SQL db available for LEXICON"
    assert sql_null.message == "No SQL db available for LEXICON"
