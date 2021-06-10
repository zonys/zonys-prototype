import pathlib
import collections
import typing

from ruamel import yaml

# pylint: disable=too-many-ancestors
class Base(collections.UserDict):
    def __init__(self, path: typing.Union[str, pathlib.Path]):
        super().__init__(None)

        self.__path = pathlib.Path(path)

        data = None

        if self.path.exists():
            data = yaml.YAML().load(self.path)

        if data is None:
            data = collections.OrderedDict()

        self.data = data

    @property
    def path(self) -> "pathlib.Path":
        return self.__path

    @property
    def data(self) -> dict:  # typing.Mapping[str, typing.Any]:
        return self.__data

    @data.setter
    def data(self, data: typing.Mapping[str, typing.Any]):
        self.__data = data

    def destroy(self):
        if self.path.exists():
            self.path.unlink()

    def flush(self):
        yaml.YAML().dump(self.data, self.path)
