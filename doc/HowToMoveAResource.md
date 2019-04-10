### Moving a resource from one Karp to another

- Make sure the lexicon configs in `config/mappings/` are updated in the version you are moving to.

- Add the mode to `config/modes.json` and `config/lexiconconf.json`.
- If you're moving a lexicon from one Karp version to another, set

    `"sql": false`

    in `config/modes.json` for the new version.

- Extract the lastest version of the lexicon from the old Karp:

    For <=v4:

    `python upload_offline.py --exportlatestversion lexiconname > out.json`

- Put the lexicon data file to `data/karplex` (or other suitable directory).

- Remember to switch virtualenvironment when you move between v4 and v5!

- Import the lexicon into your new Karp:

    For v5:

    `python cli.py import_mode lexiconname 20180521`

- If everything goes well, publish it:

    `python cli.py publish_mode lexiconname 20180521`

- Set

    `"sql": "karp"`
    in `config/modes.json` if you want the lexicon to be editable.

- Update Karp's configs:

    ~~`python cli.py create_metadata`~~ (Not needed since version *5.8.0*)

- Restart Karp:

    For v5:

    `supervisorctl -c /etc/supervisord.d/fkkarp.conf restart karpv5`
