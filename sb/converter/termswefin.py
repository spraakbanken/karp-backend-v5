import logging
from src.server.autoupdates import auto_update_child
import src.server.errorhandler as Err


@auto_update_child('term-swefin')
def add_child(parent, child):
    # add the child baselanguage form as a compound form of the parent
    try:
        wf = child['baselang']['wordform']
        parentbase = parent.get('baselang')
        if 'compound' not in parentbase:
             parentbase['compound'] = []
        parentbase['compound'].append(wf)

        # Set the translation for each language listed in the parent
        for ptarget in parent.get('targetlang', []):
            form = '' # default form
            # double for loop, ok since the length of each list is maximum 3
            for ctarget in child.get('targetlang', []):
                if ptarget.get('lang', '') == ctarget.get('lang', ''):
                    form = ctarget.get('wordform', '')
            if 'compound' not in ptarget:
                 ptarget['compound'] = []
            ptarget['compound'].append(form)

        return parent
    except Exception as e:
        logging.error(e)
        msg = ("Could not find all necessary fields (baselang.wordform) in  %s"
               % child)
        raise Err.KarpGeneralError(msg, user_msg=msg)
