import typing

import zonys
import zonys.core


class Manager:
    def __init__(self, _namespace: "zonys.core.namespace.Handle"):
        self.__namespace = _namespace

        file_system = None
        if "storage" not in self.namespace.file_system.children:
            file_system = self.namespace.file_system.children.create("storage")
        else:
            file_system = self.namespace.file_system.children.open("storage")

        self.__file_system = file_system
        self.__volumes = _Volumes(self, self.__file_system)

    @property
    def namespace(self) -> "zonys.core.namespace.Handle":
        return self.__namespace

    @property
    def volumes(self) -> "_Volumes":
        return self.__volumes


class _Volumes:
    def __init__(
        self,
        manager: "Manager",
        file_system: "zonys.core.zfs.file_system.Handle",
    ):
        self.__manager = manager
        self.__file_system = file_system

    def __iter__(self) -> typing.Iterator["_Handle"]:
        return iter([])

    def __contains__(self, key: str) -> bool:
        return False
