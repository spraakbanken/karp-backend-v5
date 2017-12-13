import json


class Baselang:
    def __init__(self, lang):
        self.forms = []
        self.lang = lang
        self.source = ''
        self.example = ''
        self.definition = ''
        self.compound = []

    def __unicode__(self):
        return '"baselang":' + json.dumps(self.__dict__, ensure_ascii=False)


class Targetlangs:
    def __init__(self):
        self.targets = []

    def add_target(self, target):
        self.targets.append(target)

    def __unicode__(self):
        return '"targetlang": [%s]' % ','.join([unicode(t) for t in self.targets])


class Targetlang:
    def __init__(self, lang):
        self.forms = []
        self.lang = lang
        self.source = ''
        self.example = ''
        self.compound = []

    def __unicode__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)
