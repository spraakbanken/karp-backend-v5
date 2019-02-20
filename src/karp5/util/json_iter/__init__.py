import json


def dump_array_fp(fp, gen):
    """ Dump array to a file object.

    Parameters
    ----------
    fp : file object
        File object to write to. Must be writable.
    gen : Iterable
        Iterable object to write.
    """
    fp.write('[\n')
    it = iter(gen)
    try:
        obj = next(it)
        fp.write(json.dumps(obj))
    except StopIteration:
        pass
    else:
        for v in it:
            fp.write(',\n')
            fp.write(json.dumps(v))
    fp.write('\n]')


def dump_array(filename, gen):
    with open(filename, 'w') as fp:
        return dump_array_fp(fp, gen)
