import io
import multiprocessing
import pathlib
import os
import typing

import libzfs

import zonys
import zonys.core
import zonys.core.zfs
import zonys.core.zfs.dataset
import zonys.core.zfs.file_system


class AlreadyExistsError(RuntimeError):
    def __init__(self, file_system, name):
        handle = Handle(file_system, name)
        super().__init__("Snapshot {} already exists".format(str(handle)))


class NotExistError(RuntimeError):
    def __init__(self, handle):
        super().__init__("Snapshot {} does not exist".format(str(handle)))


class DescriptorIdentifierNotMatch(RuntimeError):
    pass


class InvalidDescriptorError(RuntimeError):
    pass


class InvalidIdentifierError(RuntimeError):
    pass


class Identifier:
    def __init__(self, *args):
        file_system_identifier = None
        name = None

        if len(args) == 1:
            if isinstance(args[0], str):
                values = args[0].split("@")
                if len(values) != 2:
                    raise InvalidIdentifierError()

                file_system_identifier = zonys.core.zfs.file_system.Identifier(
                    values[0]
                )
                name = values[1]
        elif len(args) == 2:
            if isinstance(args[0], str) and isinstance(args[1], str):
                file_system_identifier = zonys.core.zfs.file_system.Identifier(args[0])
                name = args[1]
            elif isinstance(args[0], list) and isinstance(args[1], str):
                file_system_identifier = zonys.core.zfs.file_system.Identifier(args[0])
                name = args[1]
            elif isinstance(
                args[0], zonys.core.zfs.file_system.Identifier
            ) and isinstance(args[1], str):
                file_system_identifier = args[0]
                name = args[1]

        if file_system_identifier is None or name is None:
            raise InvalidIdentifierError()

        self.__file_system_identifier = file_system_identifier
        self.__name = name

    def __str__(self):
        return "{}@{}".format(str(self.file_system_identifier), self.name)

    @property
    def file_system_identifier(self):
        return self.__file_system_identifier

    @property
    def name(self):
        return self.__name

    @property
    def first(self):
        return self.file_system_identifier.first

    def exists(self):
        try:
            handle = self.open()
            return True
        except:
            return False

    def create(self):
        if self.exists():
            raise AlreadyExistsError(self)

        libzfs.ZFS().get_dataset(str(self.file_system_identifier)).snapshot(str(self))

        return Handle(
            libzfs.ZFS().get_snapshot(str(self)),
            self,
        )

    def open(self):
        try:
            return Handle(libzfs.ZFS().get_snapshot(str(self)), self)
        except:
            raise NotExistError(self)


class Handle(zonys.core.zfs.dataset.Handle):
    def __init__(self, descriptor, identifier=None):
        super().__init__(descriptor)

        if identifier is None:
            identifier = Identifier(self._descriptor.name)
        elif self._descriptor.name != str(identifier):
            raise DescriptorIdentifierNotMatch(self)

        self.__identifier = identifier

    @property
    def identifier(self):
        return self.__identifier

    @property
    def file_system(self):
        return self.identifier.file_system_identifier.open()

    @property
    def path(self) -> pathlib.Path:
        return self.file_system.path.joinpath(
            ".zfs",
            "snapshot",
            self.identifier.name,
        )

    def destroy(self):
        self._descriptor.delete()

    def clone(self, identifier):
        self._descriptor.clone(str(identifier))
        return identifier.open()

    def rename(self, name: str):
        self._descriptor.rename(name)
        self.__identifier = Identifier(
            self.__identifier.file_system_identifier,
            name,
        )

    def send(
        self,
        target: typing.Any,
        compress: bool = False,
    ):
        flags = set()

        if compress:
            flags.add(
                libzfs.SendFlag.COMPRESS,
            )

        send = lambda x: self.__descriptor.send(x, flags=flags)

        if isinstance(target, int):
            send(target)
        else:
            (destination, source) = os.pipe()
            child_process = multiprocessing.Process(
                target=Handle.__send_child, args=(send, destination, source)
            )
            child_process.start()

            Handle.__send_parent(target, destination, source)
            child_process.join()

    @staticmethod
    def __send_parent(
        target: typing.Any,
        destination: int,
        source: int,
    ):
        write = None

        if isinstance(target, io.TextIOBase):
            write = lambda x: target.write(str(x))
        elif isinstance(target, io.RawIOBase):
            write = target.write
        else:
            write = target.write

        os.close(source)

        while True:
            data = os.read(destination, 8192)
            if len(data) == 0:
                break

            write(data)

        os.close(destination)

    @staticmethod
    def __send_child(
        send: typing.Callable,
        destination: int,
        source: int,
    ):
        os.close(destination)
        send(source)
        os.close(source)
