"""Containers and container utilities."""


def merge_dict(adict, bdict):
    " Merges bdict into adict by taking the union of the vaule lists "
    for key, b_val in bdict.items():
        if key in adict:
            a_val = adict[key]
            if isinstance(a_val, list):
                if isinstance(b_val, list):
                    for b in b_val:
                        if b not in a_val:
                            adict[key].append(b)
                elif b_val not in a_val:
                    adict[key].append(b_val)
            elif isinstance(b_val, list):
                a_val = [a_val] if a_val not in b_val else []
                a_val.extend(b_val)
                adict[key] = a_val
            elif a_val != b_val:
                adict[key] = [a_val, b_val]
        else:
            adict[key] = b_val
