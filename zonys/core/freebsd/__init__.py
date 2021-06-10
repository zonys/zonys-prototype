"""
import pathlib
import subprocess
import typing

class Error(RuntimeError):
    pass

# pylint: disable=redefined-builtin
def open(root: pathlib.Path) -> '_Handle':
    return _Handle(root)

class _Handle:
    def __init__(
        self,
        root: pathlib.Path,
        jail_id: typing.Optional[int] = None,
    ):
        self.__root = root
        self.__services = _Services(self)
        self.__jail_id = jail_id

    @property
    def root(self) -> pathlib.Path:
        return self.__root

    @property
    def jail_id(self) -> typing.Optional[int]:
        return self.__jail_id

    @property
    def services(self) -> '_Services':
        return self.__services

class _Services:
    def __init__(self, handle: '_Handle'):
        self.__handle = handle
        self.__all_services = _AllServices(handle)
        self.__enabled_services = _EnabledServices(handle)

    @property
    def all(self) -> '_AllServices':
        return self.__all_services

    @property
    def enabled(self) -> '_EnabledServices':
        return self.__enabled_services

class _AllServices:
    def __init__(self, handle: '_Handle'):
        self.__handle = handle

class _EnabledServices:
    def __init__(self, handle: '_Handle'):
        self.__handle = handle

class _Service:
    def __init__(self, name: str):
        self.__name = name

    def __str__(self):
        return self.__name

    @property
    def name(self):
        return self.__name

class _EnabledService(_Service):
    pass

def existing() -> typing.Iterator['_Handle']:
    return map(
        lambda x: _Handle(x),
        subprocess.run(
            ['service', '-l'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            text=True,
        ).stdout.split("\n")[:-1]
    )

class _Handle:
    def __init__(self, name: str):
        self.__name = name

    @property
    def name(self):
        return self.__name
"""
