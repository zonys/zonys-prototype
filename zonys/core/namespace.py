import pathlib
import typing
import sys

import zonys
import zonys.core
import zonys.core.zone
import zonys.core.persistence
import zonys.core.volume
import zonys.core.freebsd
import zonys.core.freebsd.service
import zonys.core.freebsd.sysrc

_IDENTIFIER_SEPARATOR = "/"

_DEFAULT_IDENTIFIER = _IDENTIFIER_SEPARATOR.join(
    [
        "zroot",
        "zonys",
    ]
)


class Handle:
    def __init__(self, file_system: "zonys.core.zfs.file_system.Handle"):
        self.__file_system = file_system
        self.__zone_manager = zonys.core.zone.Manager(self)
        self.__volume_manager = zonys.core.volume.Manager(self)
        self.__service = _Service(self)
        self.__persistence = zonys.core.persistence.Base(
            self.__file_system.path.joinpath("zonys.core.yaml")
        )

    @property
    def file_system(self) -> "zonys.core.zfs.file_system.Handle":
        return self.__file_system

    @property
    def path(self) -> pathlib.Path:
        return self.__file_system.path

    @property
    def zone_manager(self) -> "zonys.core.zone.Manager":
        return self.__zone_manager

    @property
    def volume_manager(self) -> "zonys.core.volume.Manager":
        return self.__volume_manager

    @property
    def service(self) -> "_Service":
        return self.__service

    @property
    def identifier(self) -> str:
        return _IDENTIFIER_SEPARATOR.join(self.__file_system.identifier.segments)

    def is_default(self) -> bool:
        return self.identifier == _DEFAULT_IDENTIFIER


_RC_DEFINITION = """
#!/bin/sh

# zonys
# This file is generated.
#
# PROVIDE: zonys
# REQUIRE: DAEMON
# KEYWORD: shutdown

. /etc/rc.subr

name=zonys
rcvar=${{name}}_enable

: ${{zonys_enable:=NO}}
: ${{zonys_program:=zonys}}
: ${{zonys_namespaces:=}}

load_rc_config ${{name}}

PATH="${{PATH}}:/usr/local/sbin:/usr/local/bin"

start_cmd="zonys_start"
stop_cmd="zonys_stop"
restart_cmd="zonys_restart"
status_cmd="zonys_status"

zonys_start()
{{
    ${{zonys_program}} service start ${{zonys_namespaces}}
}}

zonys_stop()
{{
    ${{zonys_program}} service stop ${{zonys_namespaces}}
}}

zonys_restart()
{{
    ${{zonys_program}} service restart ${{zonys_namespaces}}
}}

zonys_status()
{{
    ${{zonys_program}} service status ${{zonys_namespaces}}
}}

run_rc_command "$1"
"""

_RC_NAME = "zonys"

_RC_PATH = pathlib.Path("/", "usr", "local", "etc", "rc.d", _RC_NAME)


class _Service:
    def __init__(self, namespace: "Handle"):
        self.__namespace = namespace

    # pylint: disable=no-self-use
    def is_enabled(self) -> bool:
        return _RC_PATH in zonys.core.freebsd.service.enabled()

    def is_disabled(self) -> bool:
        return not self.is_enabled()

    @property
    def namespaces(self) -> typing.List[str]:
        rc_value = zonys.core.freebsd.sysrc.get("zonys_namespaces", "")
        if len(rc_value) == 0:
            return []

        return rc_value.split(" ")

    @namespaces.setter
    def namespaces(self, namespaces: typing.List[str]):
        zonys.core.freebsd.sysrc.update("zonys_namespaces", " ".join(namespaces))

    def enable(self):
        parent = _RC_PATH.parent
        if not parent.exists():
            parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        with _RC_PATH.open("w") as handle:
            handle.write(_RC_DEFINITION.format())

        _RC_PATH.chmod(555)

        zonys.core.freebsd.sysrc.update("zonys_enable", "YES")

        namespaces = self.namespaces
        if self.__namespace.identifier not in namespaces:
            namespaces.append(self.__namespace.identifier)
            self.namespaces = namespaces

    def disable(self):
        namespaces = self.namespaces
        if self.__namespace.identifier in namespaces:
            namespaces.remove(self.__namespace.identifier)
            self.namespaces = namespaces
