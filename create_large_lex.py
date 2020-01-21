from sb_json_tools import json_iter


def create_entry(value: int):
    return {"lexiconName": "large_lex", "lexiconOrder": 4, "foo": str(value)}


def main():
    json_iter.dump_to_file(
        (create_entry(value) for value in range(20000)),
        "karp5/tests/data/data/large_lex/large_lex.json",
    )


if __name__ == "__main__":
    main()
