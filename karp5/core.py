class UserRepository:
    pass


class ModeRepository:
    pass


class LexiconRepository:
    pass


class GroupRepository:
    pass


class EntryRepository:
    pass


class Context:
    def __init__(self):
        self.mode_repository = ModeRepository()
        self.lexicon_repository = LexiconRepository()
        self.group_repository = GroupRepository()
        self.entry_repository = EntryRepository()



context = Context()
