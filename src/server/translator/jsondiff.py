import json
import sys

# Borrow from http://djangosnippets.org/snippets/2247/
# and inspired by https://github.com/jclulow/jsondiff
# Modified to return information more useful to us


TYPE = 'TYPE'
PATH = 'PATH'
VALUE = 'VALUE'


class Diff(object):
    def __init__(self, first, second, with_values=False):
        self.difference = []
        self.seen = []
        self.check(first, second, with_values=with_values)

    def check(self, first, second, path='', with_values=False):
        if with_values and second is not None:
            if not isinstance(first, type(second)):
                # Type and hence value change:
                self.save_diff(path, type(first).__name__,
                               type(second).__name__, TYPE)
                self.save_diff(path, first, second, PATH)

        if isinstance(first, dict):
            for key in first:
                # the first part of path must not have trailing dot.
                if len(path) == 0:
                    new_path = key
                else:
                    new_path = "%s.%s" % (path, key)

                if isinstance(second, dict):
                    if key in second:
                        sec = second[key]
                    else:
                        #  Add or remove:
                        #  there are key in the first,
                        # that is not presented in the second
                        self.save_diff(new_path, first.get(key), '', PATH)

                        # prevent further values checking.
                        sec = None

                    # recursive call
                    if sec is not None:
                        self.check(first[key], sec, path=new_path,
                                   with_values=with_values)

        # if object is list, loop over it and check.
        elif isinstance(first, list):
            for (index, item) in enumerate(first):
                new_path = "%s[%s]" % (path, index)
                # try to get the same index from second
                sec = None
                if second is not None:
                    try:
                        sec = second[index]
                    except (IndexError, KeyError):
                        # List with new member
                        self.save_diff(new_path, item, '', TYPE)

                # recursive call
                self.check(first[index], sec, path=new_path,
                           with_values=with_values)

        # not list, not dict. Check for equality (only if with_values is True)
        # and return.
        else:
            if with_values and second is not None:
                if first != second:
                    # Value change
                    self.save_diff(path, first, second, VALUE)
            return

    def save_diff(self, path, diff_before, diff_after, type_):
        long_message = '%s - %s | %s' % (path, diff_before, diff_after)
        if long_message not in self.seen:
            self.seen.append(long_message)
            self.difference.append((type_, path, diff_before, diff_after))


def getContent(location):
    content = None
    if isinstance(location, dict):  # compatability with python3
        return location
    else:
        content = open(location, 'r').read()
    if content is None:
        raise Exception("Could not load content for " + location)
    return json.loads(content)


def compare(location1, location2, print_all=False):
    json1 = getContent(location1)
    json2 = getContent(location2)
    diff1 = Diff(json1, json2, True).difference
    diff2 = Diff(json2, json1, False).difference
    diffs = []
    for type_, path, before, after in diff1:
        if before and after:
            action = "TYPECHANGE" if type_ == "TYPE" else "CHANGE"
            diffs.append({'type': action, 'field': path,
                          'before': before, 'after': after})
        elif before:
            diffs.append({'type': 'REMOVED', 'field': path, 'before': before})
        elif print_all:
            # changes should be caught in the first if clause, additions below
            diffs.append({'type': 'CHANGE', 'field': path,
                          'after': after, 'before': before})
    for type_, path, after, before in diff2:
        diffs.append({'type': 'ADDED', 'field': path, 'after': after})
    return diffs

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('Error')
    location1 = sys.argv[1]
    location2 = sys.argv[2]
    diffs = compare(location1, location2)
    if len(diffs) > 0:
        print('\r\nFound differences comparing '+location1+' and '+location2)
    for diff in diffs:
        print(diff)
