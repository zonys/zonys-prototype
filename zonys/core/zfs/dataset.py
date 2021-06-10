import toolz

import zonys
import zonys.core
import zonys.core.zfs


class Handle(zonys.core.zfs.Handle):
    def __init__(self, descriptor):
        super().__init__(descriptor)
        self.__properties = Properties(self._descriptor)

    @property
    def properties(self):
        return self.__properties


class Properties:
    def __init__(self, descriptor):
        self.__descriptor = descriptor
        self.__data = toolz.valmap(
            lambda x: zonys.core.zfs.property.Handle(x), self.__descriptor.properties
        )

    def __contains__(self, key):
        return key in self.data

    def __getitem__(self, key):
        return self.data[key]

    @property
    def data(self):
        return self.__data
