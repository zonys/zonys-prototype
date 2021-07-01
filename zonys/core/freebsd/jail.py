import contextlib
import json
import pathlib
import shutil
import subprocess
import tempfile
import typing

import zonys
import zonys.core
import zonys.core.freebsd
import zonys.core.freebsd.mount
import zonys.core.freebsd.mount.devfs


class Error(RuntimeError):
    pass


class AlreadyExistsError(Error):
    pass


class NotExistsError(Error):
    pass


class AlreadyRunningError(RuntimeError):
    pass


class NotRunningError(RuntimeError):
    pass


class Identifier:
    def __init__(self, name):
        self.__name = name

    @property
    def name(self):
        return self.__name

    def exists(self):
        command = [
            "jls",
            "-N",
            "--libxo",
            "json",
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            check=True,
        )

        for i in json.loads(result.stdout)["jail-information"]["jail"]:
            if i["name"] == self.name:
                return True

        return False

    def create(self, **kwargs):
        if self.exists():
            raise AlreadyExistsError(self)

        def mapper(key, value):
            if value is True:
                value = 1
            elif value is False:
                value = 0
            elif value is None:
                return key

            return "{}={}".format(key, value)

        output = list(
            map(
                lambda x: mapper(*x),
                {
                    "exec.clean": None,
                    **kwargs,
                    "name": self.name,
                    "allow.raw_sockets": 1,
                }.items(),
            )
        )

        command = [
            "jail",
            "-c",
            *output,
            "persist",
        ]

        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return Handle(self)

    def open(self):
        if not self.exists():
            raise NotExistsError(self)

        return Handle(self)


class Handle:
    def __init__(self, identifier):
        self.__identifier = identifier

    @property
    def identifier(self):
        return self.__identifier

    @property
    def name(self):
        return self.identifier.name

    def execute(self, command):
        if isinstance(command, str):
            command = [command]
        elif not isinstance(command, list):
            raise ValueError("command must be an instance of str or list")

        command = [
            "jexec",
            "-l",
            self.name,
            *" ".join(command).split(" "),  # wtf
        ]

        subprocess.run(
            command,
            check=True,
            # stdout=subprocess.DEVNULL,
            # stderr=subprocess.DEVNULL,
        )

    def destroy(self):
        command = [
            "jail",
            "-r",
            self.name,
        ]

        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


@contextlib.contextmanager
def temporary(
    name: str,
    path: pathlib.Path,
    **kwargs,
):
    resolv_conf_path = path.joinpath("etc", "resolv.conf")
    temp_handle = None
    identifier = Identifier(name)
    devices_handle = None

    jail = None

    try:
        if resolv_conf_path.exists():
            # pylint: disable=consider-using-with
            temp_handle = tempfile.TemporaryFile()

            with resolv_conf_path.open("rb") as handle:
                shutil.copyfileobj(handle, temp_handle)
                temp_handle.seek(0)

                resolv_conf_path.unlink()

        shutil.copyfile(pathlib.Path("/", "etc", "resolv.conf"), resolv_conf_path)

        mountpoint = zonys.core.freebsd.mount.devfs.Mountpoint(path.joinpath("dev"))
        if mountpoint.exists():
            devices_handle = mountpoint.open()
        else:
            devices_handle = mountpoint.mount()

        devices_handle.rules.unhide_all()

        jail = identifier.create(
            path=path,
            ip4="inherit",
            **{
                "allow.sysvipc": True,
            },
            **kwargs,
        )

        jail.execute("/etc/rc.d/ldconfig start")

        yield jail
    finally:
        if jail is not None:
            jail.execute("/etc/rc.d/ldconfig stop")
            jail.destroy()

        if devices_handle is not None:
           devices_handle.unmount()

        if temp_handle is not None:
            with resolv_conf_path.open("wb") as handle:
                shutil.copyfileobj(temp_handle, handle)

            temp_handle.close()
