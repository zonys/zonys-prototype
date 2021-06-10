SEPARATOR = "/"


class Error(RuntimeError):
    pass


class Object:
    pass


class Handle(Object):
    def __init__(self, descriptor):
        super().__init__()
        self.__descriptor = descriptor

    @property
    def _descriptor(self):
        return self.__descriptor
