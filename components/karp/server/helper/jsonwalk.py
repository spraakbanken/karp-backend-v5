

def walk(d, path):
    step = d.get(path[0])
    if isinstance(step, list):
        nextstep = step[0]
    elif not step or not isinstance(step, dict) or len(path) < 1:
        return step
    else:
        nextstep = step

    return walk(nextstep, path[1:])


def walk_exception(d, path):
    step = d
    for pathstep in path:
        step = step.get(pathstep)
        if isinstance(step, list):
            step = step[0]
    return step


def walk2(d, path):
    try:
        return walk_exception(d, path)
    except AttributeError as IndexError:
        return None
