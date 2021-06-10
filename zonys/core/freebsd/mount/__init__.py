import re
import subprocess
import pathlib


class NotExistsError(RuntimeError):
    def __init__(self, mountpoint):
        super().__init__(
            "Mountpoint with destination {} does not exist".format(
                mountpoint.destination
            ),
        )


class AlreadyExistsError(RuntimeError):
    def __init__(self, mountpoint):
        super().__init__(
            "Mountpoint with destination {} already exists".format(
                mountpoint.destination
            ),
        )


class Mountpoint:
    def __init__(self, destination):
        if isinstance(destination, str):
            destination = pathlib.Path(destination)
        elif not isinstance(destination, pathlib.Path):
            raise ValueError("destination must be instance of type string or Path")

        self.__destination = destination

    def _list(self):
        result = subprocess.run(
            "mount",
            check=True,
            text=True,
            capture_output=True,
        )

        results = []

        for line in result.stdout.split("\n")[:-1]:
            groups = re.search("(\S+) on (\S+) \((.*)\)", line).groups()
            flags = set(groups[2].split(", "))

            results.append(
                (
                    groups[0],
                    groups[1],
                    flags,
                )
            )

        return results

    @property
    def destination(self):
        return self.__destination

    def exists(self):
        try:
            self.open()
            return True
        except NotExistsError:
            return False

    def open(self):
        raise NotImplementedError()


class Handle:
    def __init__(self, destination):
        if isinstance(destination, str):
            destination = pathlib.Path(destination)
        elif not isinstance(destination, pathlib.Path):
            raise ValueError("destination must be an instance of type string or Path")

        self.__destination = destination
        self.__options = Options(self)

    @property
    def destination(self):
        return self.__destination

    @property
    def options(self):
        return self.__options

    def unmount(self):
        command = [
            "umount",
            str(self.destination),
        ]

        subprocess.run(command, check=True)

    def umount(self):
        self.unmount()


class Options:
    def __init__(self, handle):
        if not isinstance(handle, Handle):
            raise ValueError("handle must be instance of Handle")

        self.__handle = handle

    def __contains__(self, key):
        return key in self.__data
