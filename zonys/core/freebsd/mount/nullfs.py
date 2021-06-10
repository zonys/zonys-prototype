import pathlib
import subprocess

import zonys
import zonys.core
import zonys.core.freebsd
import zonys.core.freebsd.mount


class Mountpoint(zonys.core.freebsd.mount.Mountpoint):
    def __init__(self, source, destination, read_only=True):
        super().__init__(destination)

        if isinstance(source, str):
            source = pathlib.Path(source)
        elif not isinstance(source, pathlib.Path):
            raise ValueError("source must be instance of type string or Path")

        if not isinstance(read_only, bool):
            raise ValueError("read_only must be instance of bool")

        self.__source = source
        self.__read_only = read_only

    @property
    def source(self):
        return self.__source

    @property
    def read_only(self):
        return self.__read_only

    def mount(self):
        if self.exists():
            raise zonys.core.freebsd.mount.AlreadyExistsError(self)

        command = ["mount", "-t", "nullfs"]

        if self.read_only:
            command.append("-r")
        else:
            command.append("-w")

        command.extend([str(self.source), str(self.destination)])

        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return Handle(
            self.source,
            self.destination,
        )

    def open(self):
        for entry in self._list():
            if entry[1] == str(self.destination) and "nullfs" in entry[2]:
                return Handle(entry[0], entry[1])

        raise zonys.core.freebsd.mount.NotExistsError(self)


class Handle(zonys.core.freebsd.mount.Handle):
    def __init__(self, source, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if isinstance(source, str):
            destination = pathlib.Path(source)
        elif not isinstance(source, pathlib.Path):
            raise ValueError("source must be an instance of type string or Path")

        self.__source = source

    @property
    def source(self):
        return self.__source
