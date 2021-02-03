#!/usr/bin/env python3


def list_names(names):
    if len(names) == 1:
        return names[0]
    else:
        return ', '.join(names[:-1]) + ' en ' + names[-1]
