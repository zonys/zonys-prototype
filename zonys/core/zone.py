import pathlib
import shutil
import typing
import uuid

import mergedeep

import zonys
import zonys.core
import zonys.core.collection
import zonys.core.configuration
import zonys.core.freebsd.jail
import zonys.core.handler
import zonys.core.handler.base
import zonys.core.handler.execute
import zonys.core.handler.include
import zonys.core.handler.mount
import zonys.core.handler.name
import zonys.core.handler.network
import zonys.core.handler.provision
import zonys.core.handler.temporary
import zonys.core.handler.variable
import zonys.core.namespace
import zonys.core.persistence
import zonys.core.util

SHARED_SCHEMA = [
    zonys.core.handler.variable.SCHEMA,
    zonys.core.handler.include.SCHEMA,
]

LOCAL_SCHEMA = [
    *SHARED_SCHEMA,
    zonys.core.handler.name.SCHEMA,
    zonys.core.handler.base.SCHEMA,
    zonys.core.handler.provision.SCHEMA,
]

MERGED_SCHEMA = [
    *SHARED_SCHEMA,
    zonys.core.handler.mount.SCHEMA,
    zonys.core.handler.temporary.SCHEMA,
    zonys.core.handler.network.SCHEMA,
    zonys.core.handler.execute.SCHEMA,
]


class Error(RuntimeError):
    pass


class AlreadyExistsError(Error):
    pass


class NotFoundError(Error):
    pass


class AlreadyRunningError(Error):
    pass


class NotRunningError(Error):
    pass


class RunningError(Error):
    pass


class NameAlreadyUsedError(Error):
    pass


class IllegalFileSystemIdentifierError(Error):
    pass


class Manager:
    def __init__(self, _namespace: "zonys.core.namespace.Handle"):
        self.__namespace = _namespace

        file_system = None
        if "zone" not in self.namespace.file_system.children:
            file_system = self.namespace.file_system.children.create("zone")
        else:
            file_system = self.namespace.file_system.children.open("zone")

        if not file_system.is_mounted():
            file_system.mount()

        self.__file_system = file_system

        self.__zones = _Zones(self, self.__file_system)

    @property
    def namespace(self) -> "zonys.core.namespace.Handle":
        return self.__namespace

    @property
    def zones(self) -> "_Zones":
        return self.__zones


class _Zones:
    def __init__(
        self,
        manager: "Manager",
        file_system: "zonys.core.zfs.file_system.Handle",
    ):
        self.__manager = manager
        self.__handles: zonys.core.collection.MultiKeyDict[
            str, "_Handle"
        ] = zonys.core.collection.MultiKeyDict()
        self.__file_system = file_system

        def mount(file_system):
            if not file_system.is_mounted():
                file_system.mount()

            return file_system

        for handle in map(
            lambda x: _ExistingHandle(self.__manager, mount(x)),
            self.__file_system.children,
        ):
            if handle.name is not None:
                self.__handles[(handle.name, str(handle.uuid))] = handle
            else:
                self.__handles[(str(handle.uuid),)] = handle

    def __len__(self) -> int:
        return len(self.__handles.values())

    def __iter__(self) -> typing.Iterator["_Handle"]:
        return iter(self.__handles.values())

    def __contains__(self, value: typing.Union[str, uuid.UUID]) -> bool:
        return str(value) in self.__handles

    def __getitem__(self, value: typing.Union[str, uuid.UUID]) -> "_Handle":
        if value not in self:
            raise NotFoundError(value)

        return self.__handles[str(value)]

    def match(self, value: typing.Union[str, uuid.UUID]) -> typing.List["_Handle"]:
        match_value = str(value)
        result = []

        for handle in self:
            if str(handle.uuid).startswith(match_value) or (
                handle.name is not None and handle.name.startswith(match_value)
            ):
                result.append(handle)

        return result

    def create(self, **kwargs) -> "_Handle":
        configuration = kwargs

        manager = None
        persistence = None
        file_system = None
        file_system_identifier = None

        try:
            manager = zonys.core.configuration.Manager(
                zonys.core.configuration.Target(
                    [configuration],
                    LOCAL_SCHEMA,
                ),
                zonys.core.configuration.Target(
                    [configuration],
                    MERGED_SCHEMA,
                ),
            )

            _uuid = uuid.uuid4()
            file_system_identifier = self.__file_system.identifier.child(str(_uuid))

            persistence = zonys.core.persistence.Base(
                file_system_identifier.path.parent.joinpath(
                    "{}.yaml".format(str(_uuid))
                )
            )

            context = manager.commit(
                "before_create_zone",
                manager=self.__manager,
                file_system=file_system,
                file_system_identifier=file_system_identifier,
                persistence=persistence,
            )

            file_system = context["file_system"]

            if file_system is None:
                file_system = file_system_identifier.create()
            elif file_system.identifier == file_system_identifier:
                raise IllegalFileSystemIdentifierError()

            if not file_system.is_mounted():
                file_system.mount()

            handle = _CreatedHandle(
                self.__manager,
                file_system,
                persistence,
                configuration,
            )

            handle.snapshots.create("initial")

            manager.commit(
                "after_create_zone",
                zone=handle,
            )

            if handle.name is not None and handle.name in self:
                raise NameAlreadyUsedError()

            return handle
        except:
            if manager is not None:
                manager.rollback()

            if persistence is not None:
                persistence.destroy()

            if (
                file_system is None
                and file_system_identifier is not None
                and file_system_identifier.exists()
            ):
                file_system = file_system_identifier.open()

            if file_system is not None:
                file_system.destroy()

            raise

    def deploy(self, **kwargs) -> "_Handle":
        handle = self.create(**kwargs)
        handle.up()

        return handle

    def run(self, **kwargs) -> "_Handle":
        handle = self.create(
            temporary=True,
            **kwargs,
        )
        handle.up()

        return handle

    def autostart(self):
        for zone in self:
            if zone.auto_start:
                zone.up()


class _Handle:
    def __init__(
        self,
        manager: "Manager",
        file_system: "zonys.core.zfs.file_system.Handle",
        persistence: "zonys.core.persistence.Base",
        configuration: typing.Mapping[typing.Any, typing.Any],
    ):
        self.__manager = manager
        self.__file_system = file_system
        self.__uuid = uuid.UUID(self.__file_system.identifier.last)
        self.__snapshots = _Snapshots(self, self.__file_system)
        self.__persistence = persistence
        self.__configuration = _Configuration(self, configuration)
        self.__jail_identifier = zonys.core.freebsd.jail.Identifier(str(self.uuid))

    @property
    def manager(self) -> "Manager":
        return self.__manager

    @property
    def uuid(self) -> "uuid.UUID":
        return self.__uuid

    @property
    def snapshots(self) -> "_Snapshots":
        return self.__snapshots

    @property
    def configuration(self) -> "_Configuration":
        return self.__configuration

    @property
    def path(self) -> pathlib.Path:
        return self.__file_system.path

    @property
    def name(self) -> typing.Optional[str]:
        return self.__persistence.get("name", None)

    @property
    def auto_start(self) -> bool:
        return self.__configuration.merged.get("autostart", False)

    @property
    def identifier(self) -> str:
        if self.name is not None:
            return self.name

        return str(self.uuid)

    @property
    def parent(self) -> typing.Optional["zonys.core.zone._Snapshot"]:
        parent = self.__persistence.get("parent", None)
        if parent is not None:
            return self.manager.zones[parent["zone"]].snapshots[parent["zone_snapshot"]]

        return None

    def is_running(self) -> bool:
        return self.__jail_identifier.exists()

    def start(self):
        manager = None
        jail_handle = None

        try:
            if self.is_running():
                raise AlreadyRunningError(self)

            manager = zonys.core.configuration.Manager(
                zonys.core.configuration.Target(
                    [self.configuration.local],
                    LOCAL_SCHEMA,
                ),
                zonys.core.configuration.Target(
                    [self.configuration.merged],
                    MERGED_SCHEMA,
                ),
            )

            jail_configuration = manager.commit(
                "before_start_zone",
                zone=self,
                jail_configuration={},
            )["jail_configuration"]

            jail_handle = self.__jail_identifier.create(
                **{
                    **jail_configuration,
                    "path": self.__file_system.path,
                }
            )

            manager.commit(
                "after_start_zone",
                zone=self,
                jail=jail_handle,
            )

        except:
            if jail_handle is not None:
                jail_handle.destroy()

            if manager is not None:
                manager.rollback()

            raise

    def stop(self):
        manager = None

        try:
            if not self.is_running():
                raise NotRunningError(self)

            manager = zonys.core.configuration.Manager(
                zonys.core.configuration.Target(
                    [self.configuration.local],
                    LOCAL_SCHEMA,
                ),
                zonys.core.configuration.Target(
                    [self.configuration.merged],
                    MERGED_SCHEMA,
                ),
            )

            jail_handle = self.__jail_identifier.open()

            manager.commit(
                "before_stop_zone",
                zone=self,
                jail=jail_handle,
            )

            jail_handle.destroy()

            manager.commit(
                "after_stop_zone",
                zone=self,
            )
        except:
            if manager is not None:
                manager.rollback()

            raise

    def destroy(self):
        manager = None

        try:
            if self.is_running():
                raise RunningError(self)

            manager = zonys.core.configuration.Manager(
                zonys.core.configuration.Target(
                    [self.configuration.local],
                    LOCAL_SCHEMA,
                ),
                zonys.core.configuration.Target(
                    [self.configuration.merged],
                    MERGED_SCHEMA,
                ),
            )

            manager.commit(
                "before_destroy_zone",
                zone=self,
            )

            self.__file_system.destroy()
            self.__persistence.destroy()

            manager.commit(
                "after_destroy_zone",
                manager=self.__manager,
            )
        except:
            if manager is not None:
                manager.rollback()

            raise

    def restart(self):
        self.stop()
        self.start()

    # pylint: disable=invalid-name
    def up(self):
        if not self.is_running():
            self.start()

    def down(self):
        if self.is_running():
            self.stop()

    def reup(self):
        self.down()
        self.up()

    def undeploy(self):
        self.down()
        self.destroy()

    def redeploy(self, **kwargs) -> "_Handle":
        self.undeploy()
        return self.manager.zones.deploy(**kwargs)

    def send(self, target: typing.Any):
        temp = None

        try:
            temp = self.snapshots.create(str(uuid.uuid4()))
            temp.send(target)
        finally:
            if temp is not None:
                temp.destroy()


class _CreatedHandle(_Handle):
    def __init__(
        self,
        manager: "Manager",
        file_system: "zonys.core.zfs.file_system.Handle",
        persistence: "zonys.core.persistence.Base",
        configuration: typing.Mapping[typing.Any, typing.Any],
    ):
        persistence.update(
            {
                "local": configuration,
            }
        )
        persistence.flush()

        super().__init__(manager, file_system, persistence, configuration)


class _ReceivedHandle(_Handle):
    def __init__(
        self,
        manager: "Manager",
        file_system: "zonys.core.zfs.file_system.Handle",
    ):
        persistence = zonys.core.persistence.Base(
            file_system.path.parent.joinpath("{}.yaml".format(file_system.path.name))
        )

        super().__init__(
            manager,
            file_system,
            persistence,
            persistence.get("local", {}),
        )


class _ExistingHandle(_Handle):
    def __init__(
        self,
        manager: "Manager",
        file_system: "zonys.core.zfs.file_system.Handle",
    ):
        persistence = zonys.core.persistence.Base(
            file_system.path.parent.joinpath("{}.yaml".format(file_system.path.name))
        )

        super().__init__(
            manager,
            file_system,
            persistence,
            persistence.get("local", {}),
        )


class _Configuration:
    def __init__(
        self,
        handle: "_Handle",
        local: typing.Mapping[typing.Any, typing.Any],
    ):
        self.__handle = handle
        self.__local = local

    @property
    def local(self) -> typing.Mapping[typing.Any, typing.Any]:
        return self.__local

    @property
    def entities(self) -> typing.List[typing.Mapping[typing.Any, typing.Any]]:
        result = [self.local]
        parent = self.__handle.parent

        if parent is not None:
            result.extend(parent.zone_handle.configuration.entities)

        return result

    @property
    def merged(self) -> typing.Mapping[typing.Any, typing.Any]:
        result: typing.Dict[typing.Any, typing.Any] = {}

        for entry in self.entities:
            result = mergedeep.merge(
                result,
                entry,
                strategy=mergedeep.Strategy.ADDITIVE,
            )

        return result


class _Snapshots:
    def __init__(
        self, handle: "_Handle", file_system: "zonys.core.zfs.file_system.Handle"
    ):
        self.__handle = handle
        self.__file_system = file_system

    def __contains__(self, key: str) -> bool:
        return key in self.__file_system.snapshots

    def __iter__(self) -> typing.Iterator["_Snapshot"]:
        return map(
            lambda x: _Snapshot(self.__handle, x),
            self.__file_system.snapshots,
        )

    def __getitem__(self, name: str) -> "_Snapshot":
        if name not in self:
            raise NotFoundError()

        return _Snapshot(
            self.__handle,
            self.__file_system.snapshots[name],
        )

    def create(self, name) -> "_Snapshot":
        if name in self:
            raise AlreadyExistsError()

        temp_path = self.__file_system.path.joinpath(
            ".zonys.yaml",
        )

        if temp_path.exists():
            temp_path.unlink()

        shutil.copy2(
            self.__file_system.path.parent.joinpath(
                "{}.yaml".format(self.__handle.uuid)
            ),
            temp_path,
        )

        snapshot = self.__file_system.snapshots.create(name)

        temp_path.unlink()

        return _Snapshot(
            self.__handle,
            snapshot,
        )


class _Snapshot:
    def __init__(
        self,
        zone_handle: "_Handle",
        zfs_snapshot_handle: "zonys.core.zfs.snapshot.Handle",
    ):
        self.__zone_handle = zone_handle
        self.__zfs_snapshot_handle = zfs_snapshot_handle

    @property
    def zone_handle(self) -> "_Handle":
        return self.__zone_handle

    @property
    def zfs_snapshot_handle(self) -> "zonys.core.zfs.snapshot.Handle":
        return self.__zfs_snapshot_handle

    @property
    def name(self) -> str:
        return self.zfs_snapshot_handle.identifier.name

    def destroy(self):
        self.__zfs_snapshot_handle.destroy()

    def send(self, destination: typing.Any):
        if isinstance(destination, int):
            self.__send_descriptor(destination)
        elif isinstance(destination, pathlib.Path):
            self.__send_path(destination)
        else:
            self.__send_path(pathlib.Path(destination))

    def __send_descriptor(self, descriptor: int):
        self.__zfs_snapshot_handle.send(
            descriptor,
            compress=True,
        )

    def __send_path(self, path: pathlib.Path):
        archive_name = None
        archive_format = None

        path_str = str(path)

        if path_str.endswith(".tar.gz"):
            archive_format = "gztar"
            archive_name = path_str[0:-7]
        elif path_str.endswith(".tar.xz"):
            archive_format = "xztar"
            archive_name = path_str[0:-7]
        elif path_str.endswith(".zip"):
            archive_format = "zip"
            archive_name = path_str[0:-4]
        elif path_str.endswith(".tar"):
            archive_format = "tar"
            archive_name = path_str[0:-4]

        if archive_format is not None and archive_name is not None:
            shutil.make_archive(
                archive_name,
                archive_format,
                self.__zfs_snapshot_handle.path,
            )
        else:
            with path.open("w") as handle:
                self.__send_descriptor(handle.fileno())
