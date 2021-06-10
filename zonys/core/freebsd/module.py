import subprocess


class Identifier:
    def __init__(self, name):
        self.__name = name

    @property
    def name(self):
        return self.__name

    def is_loaded(self):
        pass

    def load(self):
        pass

    def open(self):
        pass


class Handle:
    def __init__(self, identifier):
        self.__identifier = identifier

    def unload(self):
        pass
