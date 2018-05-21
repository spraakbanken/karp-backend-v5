### Moving a resource from one Karp to another

- Make sure the lexicon configs in `config/mappings/` are updated.
- Add the mode to `config/modes.json` and `config/lexiconconf.json`.
- If you're moving a lexicon from one Karp version to another, set

    `"sql": false`

    in `config/modes.json`.
- Extract the lastest version of the lexicon from the old Karp:

    For <=v4:

    `python upload_offline.py --exportlatestversion lexiconname > out.json`
- Put the lexicon data file to `data/karplex` (or other suitable directory).
- Import the lexicon into your new Karp:

    For v5:

    `python offline.py --import_mode lexiconname 20180521`
- If everything goes well, publish it:

    `python offline.py --publish_mode lexiconname 20180521`

- Set

    `"sql": "karp"`
    in `config/modes.json` if you want the lexicon to be editable.

- Update Karp's configs:

    `python offline.py --create_metadata`
- Restart Karp:

    For v5:

    `supervisorctl -c /etc/supervisord.d/fkkarp.conf restart karpv5`

