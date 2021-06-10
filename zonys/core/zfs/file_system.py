import pathlib
import subprocess
import typing

import libzfs

import zonys
import zonys.core
import zonys.core.zfs
import zonys.core.zfs.dataset
import zonys.core.zfs.snapshot
import zonys.core.zfs.property


class AlreadyExistsError(RuntimeError):
    def __init__(self, name):
        super().__init__("File system {} already exists".format(name))


class NotExistError(RuntimeError):
    def __init__(self, name):
        super().__init__("File system {} does not exist".format(name))


class ReadingPropertiesError(RuntimeError):
    def __init__(self, handle):
        super().__init("")


class DescriptorIdentifierNotMatch(RuntimeError):
    pass


class InvalidDescriptorError(RuntimeError):
    pass


class InvalidIdentifierError(RuntimeError):
    pass


class Identifier:
    def __init__(self, *args):
        segments = None

        if len(args) == 1:
            if isinstance(args[0], str):
                segments = args[0].split(zonys.core.zfs.SEPARATOR)
            elif isinstance(args[0], list) and all(
                map(lambda x: isinstance(x, str), args[0])
            ):
                segments = args[0]
        elif all(map(lambda x: isinstance(x, str), args)):
            segments = args

        if segments is None:
            raise InvalidIdentifierError(args)

        self.__segments = segments

    def __str__(self):
        return zonys.core.zfs.SEPARATOR.join(self.segments)

    @property
    def segments(self):
        return self.__segments

    @property
    def first(self):
        return self.segments[0]

    @property
    def last(self):
        return self.segments[-1]

    @property
    def parent(self):
        return Identifier(self.segments[0:-1])

    @property
    def path(self):
        return pathlib.Path("/", *self.segments)

    def child(self, *args):
        return Identifier([*self.segments, *args])

    def exists(self):
        try:
            self.open()
            return True
        except:
            return False

    def create(self, create_ancestors=True):
        if self.exists():
            raise AlreadyExistsError(self)

        libzfs.ZFS().get(self.first).create(
            str(self),
            {},
            libzfs.DatasetType.FILESYSTEM,
            create_ancestors=create_ancestors,
        )

        return Handle(libzfs.ZFS().get_dataset(str(self)), self)

    def open(self):
        try:
            return Handle(libzfs.ZFS().get_dataset(str(self)), self)
        except:
            raise NotExistError(self)

    def receive(self, descriptor: int) -> "zonys.zfs.snapshot.Handle":
        if self.exists():
            raise AlreadyExistsError(self)

        name = str(self)

        libzfs.ZFS().receive(
            name,
            descriptor,
        )

        return list(self.open().snapshots)[0]


class Handle(zonys.core.zfs.dataset.Handle):
    def __init__(self, descriptor, identifier=None):
        super().__init__(descriptor)

        if identifier is None:
            identifier = Identifier(self._descriptor.name)
        elif self._descriptor.name != str(identifier):
            raise DescriptorIdentifierNotMatch(self)

        self.__children = Children(self._descriptor)
        self.__identifier = identifier
        self.__path = pathlib.Path("/", str(self.identifier))
        self.__snapshots = Snapshots(self._descriptor)

    @property
    def children(self):
        return self.__children

    @property
    def identifier(self):
        return self.__identifier

    @property
    def path(self):
        return self.__path

    @property
    def snapshots(self):
        return self.__snapshots

    @property
    def parent(self):
        return Handle(self.identifier.parent.open())

    def is_mounted(self):
        return self._descriptor.mountpoint != None

    def mount(self):
        self._descriptor.mount()

    def unmount(self):
        self._descriptor.umount()

    def destroy(self):
        if self.is_mounted():
            self.unmount()

        self.snapshots.destroy_all()
        self._descriptor.delete()

    def jail(self, jail):
        command = [
            "zfs",
            "jail",
            jail.name,
            str(self.identifier),
        ]

        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def unjail(self, jail):
        command = [
            "zfs",
            "unjail",
            jail.name,
            str(self.identifier),
        ]

        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


class Children:
    def __init__(self, descriptor):
        self.__descriptor = descriptor
        self.__identifier = Identifier(self.__descriptor.name)

    def __iter__(self):
        return map(
            lambda x: Handle(x, Identifier(x.name)),
            self.__descriptor.children,
        )

    def __contains__(self, name):
        return self.__identifier.child(name).exists()

    def __getitem__(self, name):
        return self.__identifier.child(name).open()

    def create(self, name):
        return self.__identifier.child(name).create()

    def open(self, name):
        return self.__identifier.child(name).open()


class Snapshots:
    def __init__(self, descriptor):
        self.__descriptor = descriptor

    def __iter__(self):
        return map(
            lambda x: zonys.core.zfs.snapshot.Handle(
                x, zonys.core.zfs.snapshot.Identifier(x.name)
            ),
            self.__descriptor.snapshots,
        )

    def __getitem__(self, name):
        return zonys.core.zfs.snapshot.Identifier(self.__descriptor.name, name).open()

    def __contains__(self, name):
        return zonys.core.zfs.snapshot.Identifier(self.__descriptor.name, name).exists()

    def create(self, name):
        return zonys.core.zfs.snapshot.Identifier(self.__descriptor.name, name).create()

    def destroy(self, name):
        return (
            zonys.core.zfs.snapshot.Identifier(self.__descriptor.name, name)
            .open()
            .destroy()
        )

    def destroy_all(self):
        for snapshot in self:
            snapshot.destroy()
