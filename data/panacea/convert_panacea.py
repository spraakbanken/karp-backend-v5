from __future__ import unicode_literals
import codecs
import json

"""
Module to make json from PANACEA bilingual glossary (source: http://repositori.upf.edu/handle/10230/19966)
"""

first_version = []
# posset = set()

with codecs.open("WP52-LtXfr-ProbLex-deen.txt", "r", encoding="UTF-8-sig") as f:
    for n, line in enumerate(f):
        fields = line.split("\t")
        de = fields[0].strip()
        pos_de = fields[1]
        en = fields[2]
        pos_en = fields[3]
        package_prob = float(fields[6])
        target_prob = float(fields[7])
        corpus_prob = float(fields[8].strip())

        # if pos_de not in posset:
        #     posset.add(pos_de)
        # if pos_en not in posset:
        #     posset.add(pos_en)

        if pos_de == "No":
            de = de[0].upper() + de[1:]

        entry = {"lexiconName": 'panacea',
                 "lexiconOrder": 0,
                 "lemma_german": de,
                 "english": [{"lemma_english": en,
                              "pos_english": pos_en,
                              "package_prob": package_prob,
                              "target_prob": target_prob,
                              "corpus_prob": corpus_prob,
                              }],
                 "pos_german": pos_de
                 }

        first_version.append(entry)

# for pos in posset:
#     print pos

# Collect German Lemmas with identical name and POS into single entry
second_version = {}
for entry in first_version:
    lemma = entry["lemma_german"]
    add = False
    if lemma in second_version:
        if entry["pos_german"] == second_version[lemma]["pos_german"]:
            second_version[lemma]["english"].extend(entry["english"])
        else:
            add = True
    else:
        add = True
    if add:
        second_version[lemma] = entry

panacea = [i for i in list(second_version.values())]

# Dump json to file
with codecs.open("panacea.json", "w", encoding="UTF-8") as f:
    f.write(json.dumps(panacea, sort_keys=False, indent=4, separators=(',', ': '), encoding="UTF-8"))
