#!/usr/bin/env python3


class Dir:
    """
    kwargs:
        parent  parent node DirEnt ref
        url     node list api url
    """
    def __init__(self, **kwargs):
        self._parent = kwargs.get('parent', False)
        self._url = kwargs.get('url', False)

    @staticmethod
    def printlist(filelist):
        pass

    @property
    def files(self):
        pass
